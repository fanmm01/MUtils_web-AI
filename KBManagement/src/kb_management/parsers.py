"""Format parsers with honest, per-file diagnostics.

Supported kinds: ``md``/``txt`` (line locators), ``docx`` (paragraph/table
locators), ``xlsx``/``xls`` (sheet + cell range), ``pdf`` (real page numbers).
``doc`` is read through a controlled LibreOffice conversion; when no converter
is available the file fails with ``CONVERSION_UNAVAILABLE`` instead of pretending
to be empty. A PDF without a text layer reports ``needs_ocr`` and fails with
``OCR_REQUIRED`` unless OCR is explicitly enabled and available; it never turns
into an empty success.
"""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

from qa_contracts.knowledge import Locator, ParsedBlock, ParsedDocument

SUPPORTED_EXTENSIONS: tuple[str, ...] = ("md", "txt", "doc", "docx", "xls", "xlsx", "pdf")

_TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "gb18030")


class ParseFailure(Exception):
    """A single file could not be parsed; the message is safe for clients."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


@dataclass(slots=True)
class ParseOptions:
    max_bytes: int = 50 * 1024 * 1024
    ocr_enabled: bool = False
    conversion_timeout_seconds: int = 60
    diagnostics: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParserCapability:
    kind: str
    available: bool
    diagnostic: str = ""


def detect_kind(relative_path: str) -> str | None:
    suffix = Path(relative_path).suffix.lower().lstrip(".")
    return suffix or None


def _decode(data: bytes) -> tuple[str, str]:
    for encoding in _TEXT_ENCODINGS:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ParseFailure("UNSUPPORTED_ENCODING", "text encoding could not be detected")


def _line_blocks(text: str, kind: str) -> list[ParsedBlock]:
    """Group lines into blocks; a Markdown heading always starts a new block."""
    blocks: list[ParsedBlock] = []
    start: int | None = None
    heading: str | None = None
    buffer: list[str] = []

    def flush(end: int) -> None:
        nonlocal start, buffer
        if start is not None and buffer:
            body = "\n".join(buffer).strip()
            if body:
                blocks.append(
                    ParsedBlock(
                        text=body,
                        locator=Locator(
                            kind=("markdown_lines" if kind == "md" else "text_lines"),
                            start_line=start,
                            end_line=end,
                            heading=heading,
                        ),
                        heading=heading,
                    )
                )
        start, buffer = None, []

    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            flush(max(start or number - 1, number - 1))
            continue
        if kind == "md" and stripped.startswith("#"):
            flush(number - 1)
            heading = stripped.lstrip("#").strip() or None
            start = number
            buffer = [line]
            continue
        if start is None:
            start = number
        buffer.append(line)
    flush(len(text.splitlines()))
    return blocks


class TextParser:
    async def parse(self, stream: BinaryIO, options: ParseOptions) -> ParsedDocument:
        data = stream.read()
        if len(data) > options.max_bytes:
            raise ParseFailure("FILE_TOO_LARGE", "file exceeds the configured size limit")
        text, encoding = _decode(data)
        return ParsedDocument(blocks=_line_blocks(text, "md" if _looks_markdown(text) else "txt"),
                              diagnostics=[f"decoded as {encoding}"])


def _looks_markdown(text: str) -> bool:
    return any(line.lstrip().startswith("#") for line in text.splitlines()[:50])


class WordParser:
    async def parse(self, stream: BinaryIO, options: ParseOptions) -> ParsedDocument:
        data = stream.read()
        if len(data) > options.max_bytes:
            raise ParseFailure("FILE_TOO_LARGE", "file exceeds the configured size limit")
        try:
            from docx import Document
            from docx.table import Table
            from docx.text.paragraph import Paragraph
        except ImportError as exc:  # pragma: no cover - dependency is declared
            raise ParseFailure("PARSER_UNAVAILABLE", "python-docx is not installed") from exc
        try:
            document = Document(io.BytesIO(data))
        except Exception as exc:
            raise ParseFailure("CORRUPT_DOCUMENT", "Word document could not be opened") from exc
        blocks: list[ParsedBlock] = []
        paragraph_index = 0
        table_index = 0
        for item in document.iter_inner_content():
            if isinstance(item, Paragraph):
                text = item.text.strip()
                if text:
                    style = (item.style.name if item.style is not None else "") or ""
                    blocks.append(
                        ParsedBlock(
                            text=text,
                            locator=Locator(
                                kind="word_paragraph", paragraph=paragraph_index,
                                heading=text if style.lower().startswith("heading") else None,
                            ),
                            heading=text if style.lower().startswith("heading") else None,
                        )
                    )
                paragraph_index += 1
            elif isinstance(item, Table):
                rows = [
                    "\t".join(cell.text.strip().replace("\n", " ") for cell in row.cells)
                    for row in item.rows
                ]
                text = "\n".join(row for row in rows if row.strip())
                if text:
                    blocks.append(
                        ParsedBlock(
                            text=text,
                            locator=Locator(
                                kind="word_table", paragraph=table_index,
                                heading=f"table {table_index + 1}",
                            ),
                        )
                    )
                table_index += 1
        return ParsedDocument(blocks=blocks, diagnostics=["parsed docx paragraphs and tables"])


class ExcelParser:
    async def parse(self, stream: BinaryIO, options: ParseOptions) -> ParsedDocument:
        data = stream.read()
        if len(data) > options.max_bytes:
            raise ParseFailure("FILE_TOO_LARGE", "file exceeds the configured size limit")
        if data[:4] == b"\xd0\xcf\x11\xe0":
            return _parse_xls(data)
        return _parse_xlsx(data)


def _col(index: int) -> str:
    name = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _sheet_blocks(sheets: list[tuple[str, list[list[str]]]]) -> list[ParsedBlock]:
    blocks: list[ParsedBlock] = []
    for sheet, rows in sheets:
        populated = [(number, row) for number, row in enumerate(rows) if any(row)]
        if not populated:
            continue
        width = max(len(row) for _, row in populated)
        first = populated[0][0] + 1
        last = populated[-1][0] + 1
        text = "\n".join("\t".join(row).rstrip() for _, row in populated)
        blocks.append(
            ParsedBlock(
                text=text,
                locator=Locator(
                    kind="excel_range", sheet=sheet,
                    cell_range=f"A{first}:{_col(width - 1)}{last}",
                ),
                heading=sheet,
            )
        )
    return blocks


def _parse_xlsx(data: bytes) -> ParsedDocument:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise ParseFailure("PARSER_UNAVAILABLE", "openpyxl is not installed") from exc
    try:
        workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as exc:
        raise ParseFailure("CORRUPT_DOCUMENT", "Excel workbook could not be opened") from exc
    sheets: list[tuple[str, list[list[str]]]] = []
    for sheet in workbook.worksheets:
        rows = []
        for row in sheet.iter_rows(values_only=True):
            rows.append(["" if value is None else str(value) for value in row])
        sheets.append((sheet.title, rows))
    workbook.close()
    return ParsedDocument(blocks=_sheet_blocks(sheets), diagnostics=["read cached cell values"])


def _parse_xls(data: bytes) -> ParsedDocument:
    try:
        import xlrd
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise ParseFailure("PARSER_UNAVAILABLE", "xlrd is not installed") from exc
    try:
        workbook = xlrd.open_workbook(file_contents=data, on_demand=True)
    except Exception as exc:
        raise ParseFailure("CORRUPT_DOCUMENT", "legacy Excel workbook could not be opened") from exc
    sheets: list[tuple[str, list[list[str]]]] = []
    for index in range(workbook.nsheets):
        sheet = workbook.sheet_by_index(index)
        rows = [
            ["" if sheet.cell_value(row, col) is None else str(sheet.cell_value(row, col))
             for col in range(sheet.ncols)]
            for row in range(sheet.nrows)
        ]
        sheets.append((sheet.name, rows))
    return ParsedDocument(blocks=_sheet_blocks(sheets), diagnostics=["read legacy xls cells"])


class PDFParser:
    async def parse(self, stream: BinaryIO, options: ParseOptions) -> ParsedDocument:
        data = stream.read()
        if len(data) > options.max_bytes:
            raise ParseFailure("FILE_TOO_LARGE", "file exceeds the configured size limit")
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover - dependency is declared
            raise ParseFailure("PARSER_UNAVAILABLE", "pypdf is not installed") from exc
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception as exc:
                    raise ParseFailure(
                        "ENCRYPTED_DOCUMENT", "PDF requires a password"
                    ) from exc
            pages: list[ParsedBlock] = []
            empty_pages = 0
            for number, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                if not text:
                    empty_pages += 1
                    continue
                pages.append(
                    ParsedBlock(text=text, locator=Locator(kind="pdf_page", page=number))
                )
        except ParseFailure:
            raise
        except Exception as exc:
            raise ParseFailure("CORRUPT_DOCUMENT", "PDF could not be opened") from exc
        diagnostics = [f"{len(reader.pages)} page(s) read"]
        if empty_pages:
            diagnostics.append(f"{empty_pages} page(s) have no text layer")
        if empty_pages and not pages:
            if not options.ocr_enabled:
                raise ParseFailure(
                    "OCR_REQUIRED", "the PDF has no text layer; enable OCR explicitly"
                )
            raise ParseFailure(
                "OCR_UNAVAILABLE", "OCR is enabled but no OCR adapter is configured"
            )
        return ParsedDocument(blocks=pages, diagnostics=diagnostics, needs_ocr=bool(empty_pages))


class OCRAdapter:
    """Dependency report only; OCR execution is not configured in P2-A1."""

    def check_dependencies(self) -> ParserCapability:
        binary = shutil.which("tesseract")
        if binary is None:
            return ParserCapability("ocr", available=False, diagnostic="tesseract is not on PATH")
        return ParserCapability(
            "ocr", available=False,
            diagnostic="tesseract found, but page rasterization/OCR is not configured yet",
        )

    async def extract(self, stream: BinaryIO, options: ParseOptions) -> list[ParsedBlock]:
        del stream, options
        raise ParseFailure("OCR_UNAVAILABLE", "OCR extraction is not configured in this phase")


class LegacyWordAdapter:
    """Convert ``.doc`` with a controlled, timeout-bound LibreOffice process."""

    def check_dependencies(self) -> ParserCapability:
        binary = shutil.which("soffice") or shutil.which("libreoffice")
        return ParserCapability(
            "doc", available=binary is not None,
            diagnostic="" if binary else "LibreOffice (soffice) is not on PATH",
        )

    def convert(self, data: bytes, options: ParseOptions) -> bytes:
        binary = shutil.which("soffice") or shutil.which("libreoffice")
        if binary is None:
            raise ParseFailure(
                "CONVERSION_UNAVAILABLE", ".doc requires a local LibreOffice converter"
            )
        with tempfile.TemporaryDirectory(prefix="qa-doc-") as workdir:
            source = Path(workdir) / "input.doc"
            source.write_bytes(data)
            try:
                subprocess.run(
                    [binary, "--headless", "--convert-to", "docx", "--outdir", workdir,
                     str(source)],
                    cwd=workdir,
                    check=True,
                    timeout=options.conversion_timeout_seconds,
                    capture_output=True,
                )
            except subprocess.TimeoutExpired as exc:
                raise ParseFailure("CONVERSION_TIMEOUT", "document conversion timed out") from exc
            except subprocess.CalledProcessError as exc:
                raise ParseFailure("CONVERSION_FAILED", "document conversion failed") from exc
            converted = Path(workdir) / "input.docx"
            if not converted.is_file():
                raise ParseFailure("CONVERSION_FAILED", "converter produced no document")
            return converted.read_bytes()


class ParserRegistry:
    def __init__(
        self,
        *,
        ocr: OCRAdapter | None = None,
        legacy_word: LegacyWordAdapter | None = None,
    ) -> None:
        self._text = TextParser()
        self._word = WordParser()
        self._excel = ExcelParser()
        self._pdf = PDFParser()
        self._ocr = ocr or OCRAdapter()
        self._legacy_word = legacy_word or LegacyWordAdapter()

    def capabilities(self) -> list[ParserCapability]:
        document = self._legacy_word.check_dependencies()
        return [
            ParserCapability("md", available=True),
            ParserCapability("txt", available=True),
            ParserCapability("docx", available=True),
            ParserCapability("xlsx", available=True),
            ParserCapability("xls", available=True),
            ParserCapability("pdf", available=True),
            ParserCapability("doc", available=document.available, diagnostic=document.diagnostic),
            self._ocr.check_dependencies(),
        ]

    async def parse(
        self, kind: str, stream: BinaryIO, options: ParseOptions | None = None
    ) -> ParsedDocument:
        resolved = options or ParseOptions()
        if kind == "md":
            return await self._text.parse(stream, resolved)
        if kind == "txt":
            return await self._text.parse(stream, resolved)
        if kind == "docx":
            return await self._word.parse(stream, resolved)
        if kind == "xlsx" or kind == "xls":
            return await self._excel.parse(stream, resolved)
        if kind == "pdf":
            return await self._pdf.parse(stream, resolved)
        if kind == "doc":
            converted = self._legacy_word.convert(stream.read(), resolved)
            parsed = await self._word.parse(io.BytesIO(converted), resolved)
            parsed.diagnostics.append(
                "positions map to the converted document, not the .doc binary"
            )
            return parsed
        raise ParseFailure("UNSUPPORTED_FORMAT", f"no parser for .{kind}")
