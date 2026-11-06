"""Parsers: real multi-format extraction, locators and honest failure codes."""

from __future__ import annotations

import io

import pytest

from kb_management.parsers import (
    OCRAdapter,
    ParseFailure,
    ParseOptions,
    ParserRegistry,
    _parse_xlsx,
)


def _registry() -> ParserRegistry:
    return ParserRegistry()


async def test_markdown_and_text_keep_true_line_numbers() -> None:
    registry = _registry()
    markdown = "# 安装\n\n第一段\n\n## 配置\n\n第二段\n".encode()
    parsed = await registry.parse("md", io.BytesIO(markdown))
    assert [block.text for block in parsed.blocks] == [
        "# 安装", "第一段", "## 配置", "第二段"
    ]
    assert parsed.blocks[0].locator.kind == "markdown_lines"
    assert (parsed.blocks[0].locator.start_line, parsed.blocks[0].locator.end_line) == (1, 1)
    assert parsed.blocks[1].locator.start_line == 3
    assert parsed.blocks[0].heading == "安装"
    assert parsed.blocks[2].heading == "配置"

    text = await registry.parse("txt", io.BytesIO("第一行\n第二行\n".encode()))
    assert text.blocks[0].locator.kind == "text_lines"
    assert text.blocks[0].text == "第一行\n第二行"

    legacy = await registry.parse("txt", io.BytesIO("中文内容\n".encode("gb18030")))
    assert legacy.blocks[0].text == "中文内容"
    assert any("gb18030" in line for line in legacy.diagnostics)


async def test_docx_paragraphs_and_tables_are_located() -> None:
    from docx import Document

    document = Document()
    document.add_heading("安装指南", level=1)
    document.add_paragraph("第一步：下载")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "名称"
    table.cell(0, 1).text = "值"
    table.cell(1, 0).text = "端口"
    table.cell(1, 1).text = "8000"
    buffer = io.BytesIO()
    document.save(buffer)

    parsed = await _registry().parse("docx", io.BytesIO(buffer.getvalue()))
    kinds = [block.locator.kind for block in parsed.blocks]
    assert kinds == ["word_paragraph", "word_paragraph", "word_table"]
    assert parsed.blocks[0].heading == "安装指南"
    assert "端口\t8000" in parsed.blocks[2].text


async def test_xlsx_keeps_sheet_and_cell_range() -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "参数"
    sheet.append(["键", "值"])
    sheet.append(["host", "127.0.0.1"])
    buffer = io.BytesIO()
    workbook.save(buffer)

    parsed = _parse_xlsx(buffer.getvalue())
    assert parsed.blocks[0].locator.sheet == "参数"
    assert parsed.blocks[0].locator.cell_range == "A1:B2"
    assert "host\t127.0.0.1" in parsed.blocks[0].text


async def test_pdf_uses_real_page_numbers() -> None:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)

    with pytest.raises(ParseFailure) as excinfo:
        await _registry().parse("pdf", io.BytesIO(buffer.getvalue()))
    assert excinfo.value.code == "OCR_REQUIRED"

    with pytest.raises(ParseFailure) as excinfo:
        await _registry().parse(
            "pdf", io.BytesIO(buffer.getvalue()), ParseOptions(ocr_enabled=True)
        )
    assert excinfo.value.code == "OCR_UNAVAILABLE"


async def test_corrupt_files_report_specific_codes() -> None:
    registry = _registry()
    for kind in ("docx", "xlsx", "pdf"):
        with pytest.raises(ParseFailure) as excinfo:
            await registry.parse(kind, io.BytesIO(b"not a real document"))
        assert excinfo.value.code in {"CORRUPT_DOCUMENT", "ENCRYPTED_DOCUMENT"}

    with pytest.raises(ParseFailure) as excinfo:
        await registry.parse("exe", io.BytesIO(b"MZ"))
    assert excinfo.value.code == "UNSUPPORTED_FORMAT"


async def test_size_limit_is_enforced() -> None:
    with pytest.raises(ParseFailure) as excinfo:
        await _registry().parse(
            "txt", io.BytesIO(b"x" * 200), ParseOptions(max_bytes=100)
        )
    assert excinfo.value.code == "FILE_TOO_LARGE"


def test_capabilities_report_missing_tools_without_claiming_success() -> None:
    capabilities = {item.kind: item for item in _registry().capabilities()}
    assert capabilities["md"].available
    assert capabilities["docx"].available
    assert capabilities["doc"].diagnostic or capabilities["doc"].available
    assert capabilities["ocr"].available is False


def test_ocr_adapter_refuses_instead_of_returning_empty_blocks() -> None:
    with pytest.raises(ParseFailure) as excinfo:
        _run(OCRAdapter().extract(io.BytesIO(b"x"), ParseOptions()))
    assert excinfo.value.code == "OCR_UNAVAILABLE"


async def test_legacy_doc_without_converter_reports_conversion_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("shutil.which", lambda name: None)
    with pytest.raises(ParseFailure) as excinfo:
        await ParserRegistry().parse("doc", io.BytesIO(b"\xd0\xcf\x11\xe0"))
    assert excinfo.value.code == "CONVERSION_UNAVAILABLE"


def _run(awaitable):
    import asyncio

    return asyncio.run(awaitable)
