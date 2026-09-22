"""Builds tiny in-memory PDFs for ingestion tests, without extra dependencies."""

from __future__ import annotations

import io

from pypdf import PdfWriter
from pypdf.generic import (
    DictionaryObject,
    NameObject,
    StreamObject,
)


def _helvetica_resources(writer: PdfWriter) -> DictionaryObject:
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    resources = DictionaryObject()
    resources[NameObject("/Font")] = DictionaryObject({NameObject("/F1"): font_ref})
    return resources


def _escape_pdf_string(line: str) -> str:
    return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(pages_text: list[str]) -> bytes:
    """Build a minimal multi-page PDF where each page renders the given text.

    Each string in `pages_text` becomes one page; lines within a string
    (split on "\\n") are drawn top-to-bottom so heading/paragraph structure
    in the source text survives extraction.

    The content stream is written as plain, standards-compliant PDF syntax:
    PyMuPDF (used by the ingestion pipeline) is much stricter about syntax
    than pypdf, which tolerates the quirks of pypdf's ContentStream writer.
    """
    writer = PdfWriter()

    for page_text in pages_text:
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = _helvetica_resources(writer)

        operations: list[bytes] = [b"BT", b"/F1 12 Tf"]
        y = 750
        for line in page_text.split("\n"):
            operations.append(f"1 0 0 1 50 {y} Tm".encode("ascii"))
            operations.append(f"({_escape_pdf_string(line)}) Tj".encode("ascii"))
            y -= 16
        operations.append(b"ET")

        content = StreamObject()
        content.set_data(b"\n".join(operations))
        page[NameObject("/Contents")] = writer._add_object(content)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
