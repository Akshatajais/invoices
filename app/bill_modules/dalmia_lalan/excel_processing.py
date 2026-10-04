"""Create a temporary Dalmia Lalan workbook and write only the three dynamic cells."""

from __future__ import annotations

import hashlib
import logging
import re
import zipfile
from datetime import date
from pathlib import Path

from app.bill_modules.dalmia_lalan.configuration import (
    CELL_MAP,
    PERIOD_CELL_STYLE,
    TEMPLATE_PATH,
)
from app.errors import TemplateError
from app.rendering.xlsx_patch import patch_xlsx

logger = logging.getLogger(__name__)

# Excel's 1900 date system, including the historical leap-day bug.
_EXCEL_EPOCH = date(1899, 12, 30)
_SHEET = "xl/worksheets/sheet1.xml"


def template_sha256() -> str:
    if not TEMPLATE_PATH.is_file():
        raise TemplateError("The bill template could not be read. Please try again later.")
    digest = hashlib.sha256()
    with TEMPLATE_PATH.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def excel_serial(invoice_date: date) -> str:
    """Keep E7 as a date so the template's existing date format still applies."""
    return str((invoice_date - _EXCEL_EPOCH).days)


def write_working_copy(destination: Path, values: dict[str, object]) -> None:
    """Copy the master template and set invoice number, date, and time period."""
    before = template_sha256()
    invoice_date = values["invoice_date"]
    if not isinstance(invoice_date, date):
        raise TemplateError("The bill template could not be read. Please try again later.")
    staging = destination.with_name(destination.stem + "-stage.xlsx")
    try:
        _stage_with_period_cell(staging)
        patch_xlsx(
            staging,
            destination,
            {
                CELL_MAP["invoice_number"]: str(values["invoice_number"]),
                CELL_MAP["time_period"]: str(values["time_period"]),
            },
            number_values={CELL_MAP["invoice_date"]: excel_serial(invoice_date)},
        )
    except TemplateError:
        logger.exception("Dalmia Lalan workbook patch failed")
        raise
    finally:
        staging.unlink(missing_ok=True)
    after = template_sha256()
    if before != after:
        logger.error("Dalmia Lalan master template changed during generation")
        raise TemplateError("The bill template could not be read. Please try again later.")


def _stage_with_period_cell(staging: Path) -> None:
    """Add a blank E10 on the working copy. The master sheet does not store that cell."""
    try:
        with zipfile.ZipFile(TEMPLATE_PATH, "r") as archive:
            xml = archive.read(_SHEET).decode("utf-8")
            updated = _insert_period_cell(xml)
            _write_copy(archive, staging, updated.encode("utf-8"))
    except TemplateError:
        raise
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise TemplateError("The bill template could not be read. Please try again later.") from exc


def _insert_period_cell(xml: str) -> str:
    # The saved view starts at row 2, and LibreOffice prints from that row.
    xml = xml.replace('topLeftCell="A2"', 'topLeftCell="A1"', 1)
    if re.search(r'<c r="E10"', xml):
        return xml
    updated, count = re.subn(
        r'(<c r="D10\b[^>]*?(?:/>|>.*?</c>))(?=<c r="F10")',
        rf'\1<c r="E10" s="{PERIOD_CELL_STYLE}"/>',
        xml,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1 or updated.count('<c r="E10"') != 1:
        logger.error("Dalmia Lalan time-period cell could not be added")
        raise TemplateError("The bill template is missing a required field. Please try again later.")
    return updated


def _write_copy(source: zipfile.ZipFile, destination: Path, sheet_bytes: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w") as out:
        for item in source.infolist():
            data = sheet_bytes if item.filename == _SHEET else source.read(item.filename)
            info = zipfile.ZipInfo(filename=item.filename, date_time=item.date_time)
            info.compress_type = item.compress_type or zipfile.ZIP_DEFLATED
            info.external_attr = item.external_attr
            out.writestr(info, data)
