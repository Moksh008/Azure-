"""Builds tiny in-memory PDFs for ingestion tests, without extra dependencies."""

from __future__ import annotations

import io

from pypdf import PdfWriter
from pypdf.generic import (
    ContentStream,
    DictionaryObject,
    NameObject,
    NumberObject,
    TextStringObject,
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


def make_pdf(pages_text: list[str]) -> bytes:
    """Build a minimal multi-page PDF where each page renders the given text.

    Each string in `pages_text` becomes one page; lines within a string
    (split on "\\n") are drawn top-to-bottom so heading/paragraph structure
    in the source text survives extraction.
    """
    writer = PdfWriter()

    for page_text in pages_text:
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = _helvetica_resources(writer)

        stream = ContentStream(None, writer)
        operations: list[tuple[list, bytes]] = [([], b"BT"), ([NameObject("/F1"), NumberObject(12)], b"Tf")]

        y = 750
        one = NumberObject(1)
        zero = NumberObject(0)
        for line in page_text.split("\n"):
            operations.append(([one, zero, zero, one, NumberObject(50), NumberObject(y)], b"Tm"))
            operations.append(([TextStringObject(line)], b"Tj"))
            y -= 16
        operations.append(([], b"ET"))

        stream.operations = operations
        page[NameObject("/Contents")] = stream

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
