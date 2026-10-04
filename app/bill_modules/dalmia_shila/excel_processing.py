"""Create a temporary Dalmia Shila workbook and write only the three dynamic cells."""

from __future__ import annotations

import hashlib
import logging
import zipfile
from datetime import date
from pathlib import Path

from app.bill_modules.dalmia_shila.configuration import CELL_MAP, TEMPLATE_PATH
from app.errors import TemplateError
from app.rendering.xlsx_patch import patch_xlsx

logger = logging.getLogger(__name__)

_SHEET = "xl/worksheets/sheet1.xml"


def template_sha256() -> str:
    if not TEMPLATE_PATH.is_file():
        raise TemplateError("The bill template could not be read. Please try again later.")
    digest = hashlib.sha256()
    with TEMPLATE_PATH.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def invoice_date_text(invoice_date: date) -> str:
    """E7 is General format, so a date serial would print as a plain number."""
    return invoice_date.strftime("%d/%m/%Y")


def write_working_copy(destination: Path, values: dict[str, object]) -> None:
    """Copy the master template and set invoice number, date, and time period."""
    before = template_sha256()
    invoice_date = values["invoice_date"]
    if not isinstance(invoice_date, date):
        raise TemplateError("The bill template could not be read. Please try again later.")
    staging = destination.with_name(destination.stem + "-stage.xlsx")
    try:
        _stage_from_first_row(staging)
        patch_xlsx(
            staging,
            destination,
            {
                CELL_MAP["invoice_number"]: str(values["invoice_number"]),
                CELL_MAP["invoice_date"]: invoice_date_text(invoice_date),
                CELL_MAP["time_period"]: str(values["time_period"]),
            },
        )
    except TemplateError:
        logger.exception("Dalmia Shila workbook patch failed")
        raise
    finally:
        staging.unlink(missing_ok=True)
    after = template_sha256()
    if before != after:
        logger.error("Dalmia Shila master template changed during generation")
        raise TemplateError("The bill template could not be read. Please try again later.")


def _stage_from_first_row(staging: Path) -> None:
    """The saved view starts at row 13, and LibreOffice prints from that row."""
    try:
        with zipfile.ZipFile(TEMPLATE_PATH, "r") as archive:
            xml = archive.read(_SHEET).decode("utf-8")
            updated = xml.replace('topLeftCell="A13"', 'topLeftCell="A1"', 1)
            if 'topLeftCell="A1"' not in updated:
                raise TemplateError("The bill template could not be read. Please try again later.")
            _write_copy(archive, staging, updated.encode("utf-8"))
    except TemplateError:
        raise
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise TemplateError("The bill template could not be read. Please try again later.") from exc


def _write_copy(source: zipfile.ZipFile, destination: Path, sheet_bytes: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w") as out:
        for item in source.infolist():
            data = sheet_bytes if item.filename == _SHEET else source.read(item.filename)
            info = zipfile.ZipInfo(filename=item.filename, date_time=item.date_time)
            info.compress_type = item.compress_type or zipfile.ZIP_DEFLATED
            info.external_attr = item.external_attr
            out.writestr(info, data)
