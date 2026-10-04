"""Render a temporary UltraTech workbook to PDF. The master template is never opened."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

from app.bill_modules.ultratech.configuration import TEMPLATE_PATH, TOP_MARGIN_INCHES
from app.bill_modules.ultratech.excel_processing import template_sha256
from app.errors import RenderError, TemplateError
from app.rendering.libreoffice_pdf import convert_xlsx_to_pdf

logger = logging.getLogger(__name__)


def render_workbook(xlsx_path: Path, output_dir: Path) -> Path:
    try:
        pdf_path = convert_xlsx_to_pdf(xlsx_path, output_dir, single_page=True)
        return add_top_margin(pdf_path)
    except (RenderError, TemplateError):
        logger.exception("UltraTech PDF render failed")
        raise


def add_top_margin(pdf_path: Path, margin_inches: float = TOP_MARGIN_INCHES) -> Path:
    """Add white space above the printed bill. The other three sides stay as they are."""
    margin = margin_inches * 72
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        framed = PageObject.create_blank_page(width=width, height=height + margin)
        framed.merge_transformed_page(page, Transformation().translate(tx=0, ty=0))
        writer.add_page(framed)
    framed_path = pdf_path.with_name(f"{pdf_path.stem}-margin.pdf")
    with framed_path.open("wb") as handle:
        writer.write(handle)
    return framed_path


def render_reference_copy(output_dir: Path) -> Path:
    """Render the untouched template so it can be compared with a generated bill."""
    before = template_sha256()
    working = output_dir / "ultratech-reference.xlsx"
    shutil.copyfile(TEMPLATE_PATH, working)
    pdf_path = render_workbook(working, output_dir)
    after = template_sha256()
    if before != after:
        logger.error("UltraTech master template changed during reference render")
        raise TemplateError("The bill template could not be read. Please try again later.")
    return pdf_path
