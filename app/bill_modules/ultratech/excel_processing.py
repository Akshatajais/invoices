"""Create a temporary UltraTech workbook and write only the three dynamic cells."""

from __future__ import annotations

import hashlib
import logging
import re
import zipfile
from pathlib import Path

from app.bill_modules.ultratech.configuration import (
    BILL_PERIOD_FIT_RANGE,
    CELL_MAP,
    TEMPLATE_PATH,
)
from app.errors import TemplateError
from app.rendering.xlsx_patch import patch_xlsx

logger = logging.getLogger(__name__)

# 14pt Times New Roman, the same face and size as the period label.
# The value is two lines inside L16:M17, so it is not shrunk to fit.
# borderId 9 has no edges, so the merge does not draw a line through the value.
_PERIOD_STYLE = (
    '<xf numFmtId="0" fontId="8" fillId="2" borderId="9" '
    'applyNumberFormat="0" applyFont="1" applyFill="1" applyBorder="1" '
    'applyAlignment="1" applyProtection="0">'
    '<alignment horizontal="left" vertical="center" wrapText="1"/>'
    "</xf>"
)


def template_sha256() -> str:
    if not TEMPLATE_PATH.is_file():
        raise TemplateError("The bill template could not be read. Please try again later.")
    digest = hashlib.sha256()
    with TEMPLATE_PATH.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_working_copy(destination: Path, values: dict[str, str]) -> None:
    """Copy the master template and set invoice number, date, and bill period."""
    before = template_sha256()
    cell_values = {
        CELL_MAP["invoice_number"]: values["invoice_number"],
        CELL_MAP["invoice_date"]: values["invoice_date"],
        CELL_MAP["bill_period"]: _period_for_cell(values["bill_period"]),
    }
    try:
        patch_xlsx(TEMPLATE_PATH, destination, cell_values)
        _fit_bill_period(destination)
    except TemplateError:
        logger.exception("UltraTech workbook patch failed")
        raise
    after = template_sha256()
    if before != after:
        logger.error("UltraTech master template changed during generation")
        raise TemplateError("The bill template could not be read. Please try again later.")


def _fit_bill_period(workbook: Path) -> None:
    """Show the period on two lines at the same size as the label."""
    try:
        with zipfile.ZipFile(workbook, "r") as archive:
            styles_name = "xl/styles.xml"
            sheet_name = "xl/worksheets/sheet1.xml"
            styles = archive.read(styles_name).decode("utf-8")
            sheet = archive.read(sheet_name).decode("utf-8")
            originals = {item.filename: archive.read(item.filename) for item in archive.infolist()}
            infos = list(archive.infolist())
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise TemplateError("The bill template could not be read. Please try again later.") from exc

    style_index = _append_period_style(styles)
    styles = _append_period_style_xml(styles)
    sheet = _point_period_cell_at_style(sheet, style_index)
    sheet = _merge_period_range(sheet)

    updated = dict(originals)
    updated[styles_name] = styles.encode("utf-8")
    updated[sheet_name] = sheet.encode("utf-8")
    _rewrite_zip(workbook, infos, updated)


def _period_for_cell(period: str) -> str:
    """Split a one-line period so both dates fit at full size."""
    parts = period.split(" \u2013 ", 1)
    if len(parts) != 2:
        return period
    return f"{parts[0]}\n\u2013 {parts[1]}"


def _append_period_style(styles: str) -> int:
    match = re.search(r'<cellXfs count="(\d+)">', styles)
    if not match:
        raise TemplateError("The bill template could not be read. Please try again later.")
    return int(match.group(1))


def _append_period_style_xml(styles: str) -> str:
    match = re.search(r'<cellXfs count="(\d+)">', styles)
    if not match or "</cellXfs>" not in styles:
        raise TemplateError("The bill template could not be read. Please try again later.")
    count = int(match.group(1))
    styles = styles.replace(match.group(0), f'<cellXfs count="{count + 1}">', 1)
    return styles.replace("</cellXfs>", _PERIOD_STYLE + "</cellXfs>", 1)


def _point_period_cell_at_style(sheet: str, style_index: int) -> str:
    cell = CELL_MAP["bill_period"]
    pattern = re.compile(rf'(<c r="{cell}"[^>]*?)\ss="\d+"')
    updated, replacements = pattern.subn(rf'\1 s="{style_index}"', sheet, count=1)
    if replacements != 1:
        logger.error("Could not restyle the bill-period cell")
        raise TemplateError("The bill template is missing a required field. Please try again later.")
    return updated


def _merge_period_range(sheet: str) -> str:
    match = re.search(r'<mergeCells count="(\d+)">', sheet)
    if not match or "</mergeCells>" not in sheet:
        raise TemplateError("The bill template could not be read. Please try again later.")
    count = int(match.group(1))
    if f'ref="{BILL_PERIOD_FIT_RANGE}"' in sheet:
        return sheet
    sheet = sheet.replace(match.group(0), f'<mergeCells count="{count + 1}">', 1)
    return sheet.replace(
        "</mergeCells>",
        f'<mergeCell ref="{BILL_PERIOD_FIT_RANGE}"/></mergeCells>',
        1,
    )


def _rewrite_zip(path: Path, infos: list[zipfile.ZipInfo], contents: dict[str, bytes]) -> None:
    temporary = path.with_suffix(".zip-tmp")
    with zipfile.ZipFile(temporary, "w") as out:
        for item in infos:
            info = zipfile.ZipInfo(filename=item.filename, date_time=item.date_time)
            info.compress_type = item.compress_type or zipfile.ZIP_DEFLATED
            info.external_attr = item.external_attr
            out.writestr(info, contents[item.filename])
    temporary.replace(path)
