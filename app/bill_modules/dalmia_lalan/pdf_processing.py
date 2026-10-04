"""Render a temporary Dalmia Lalan workbook to PDF. The master template is never edited."""

from __future__ import annotations

import logging
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

from app.bill_modules.dalmia_lalan.configuration import PAGE_MARGIN_INCHES
from app.errors import RenderError, TemplateError
from app.rendering.libreoffice_pdf import convert_xlsx_to_pdf

logger = logging.getLogger(__name__)


def render_workbook(xlsx_path: Path, output_dir: Path) -> Path:
    try:
        pdf_path = convert_xlsx_to_pdf(xlsx_path, output_dir, single_page=True)
        return add_page_margins(pdf_path)
    except (RenderError, TemplateError):
        logger.exception("Dalmia Lalan PDF render failed")
        raise


def add_page_margins(pdf_path: Path, margin_inches: float = PAGE_MARGIN_INCHES) -> Path:
    """Place the printed bill on a larger page with equal space on every side."""
    margin = margin_inches * 72
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        framed = PageObject.create_blank_page(width=width + (2 * margin), height=height + (2 * margin))
        framed.merge_transformed_page(page, Transformation().translate(tx=margin, ty=margin))
        writer.add_page(framed)
    framed_path = pdf_path.with_name(f"{pdf_path.stem}-margin.pdf")
    with framed_path.open("wb") as handle:
        writer.write(handle)
    return framed_path
