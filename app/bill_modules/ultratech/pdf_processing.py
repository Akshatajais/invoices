"""Render a temporary UltraTech workbook to PDF. The master template is never opened."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from app.bill_modules.ultratech.configuration import TEMPLATE_PATH
from app.bill_modules.ultratech.excel_processing import template_sha256
from app.errors import RenderError, TemplateError
from app.rendering.libreoffice_pdf import convert_xlsx_to_pdf

logger = logging.getLogger(__name__)


def render_workbook(xlsx_path: Path, output_dir: Path) -> Path:
    try:
        return convert_xlsx_to_pdf(xlsx_path, output_dir, single_page=True)
    except (RenderError, TemplateError):
        logger.exception("UltraTech PDF render failed")
        raise


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
