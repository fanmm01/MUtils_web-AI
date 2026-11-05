"""Parser registry and format parsers placeholder (A1 owner).

Capabilities report what would be *attempted*; no file is parsed in P1. A
scanned PDF must fail with ``OCR_REQUIRED`` rather than return an empty success.
"""

from __future__ import annotations

from typing import BinaryIO

from qa_contracts.knowledge import ParsedDocument

from . import unimplemented


class ParserCapability:
    def __init__(self, kind: str, available: bool, diagnostic: str = "") -> None:
        self.kind = kind
        self.available = available
        self.diagnostic = diagnostic


OPTIONAL_FORMATS: tuple[str, ...] = (
    "md",
    "txt",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "pdf",
)


class ParserRegistry:
    def register(self, kind: str, parser: object) -> None:
        raise unimplemented("kb.parsers.registry.register")

    async def parse(self, ref: object, options: object) -> ParsedDocument:
        raise unimplemented("kb.parsers.registry.parse")

    def capabilities(self) -> list[ParserCapability]:
        return [
            ParserCapability(kind, available=False, diagnostic="scaffold build")
            for kind in OPTIONAL_FORMATS
        ]


class TextParser:
    async def parse(self, stream: BinaryIO, options: object) -> ParsedDocument:
        raise unimplemented("kb.parsers.text.parse")


class WordParser:
    async def parse(self, stream: BinaryIO, options: object) -> ParsedDocument:
        raise unimplemented("kb.parsers.word.parse")


class ExcelParser:
    async def parse(self, stream: BinaryIO, options: object) -> ParsedDocument:
        raise unimplemented("kb.parsers.excel.parse")


class PDFParser:
    async def parse(self, stream: BinaryIO, options: object) -> ParsedDocument:
        raise unimplemented("kb.parsers.pdf.parse")


class OCRAdapter:
    async def extract(self, stream: BinaryIO, options: object) -> list[object]:
        raise unimplemented("kb.parsers.ocr.extract")

    def check_dependencies(self) -> ParserCapability:
        return ParserCapability("ocr", available=False, diagnostic="not checked in scaffold")
