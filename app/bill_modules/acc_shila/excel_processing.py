"""Create a temporary ACC Shila workbook and write only the three dynamic cells."""

from __future__ import annotations

import hashlib
import logging
from datetime import date
from pathlib import Path

from app.bill_modules.acc_shila.configuration import CELL_MAP, TEMPLATE_PATH
from app.errors import TemplateError
from app.rendering.xlsx_patch import patch_xlsx

logger = logging.getLogger(__name__)

# Excel's 1900 date system, including the historical leap-day bug.
_EXCEL_EPOCH = date(1899, 12, 30)


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
    try:
        patch_xlsx(
            TEMPLATE_PATH,
            destination,
            {
                CELL_MAP["invoice_number"]: str(values["invoice_number"]),
                CELL_MAP["time_period"]: str(values["time_period"]),
            },
            number_values={CELL_MAP["invoice_date"]: excel_serial(invoice_date)},
        )
    except TemplateError:
        logger.exception("ACC Shila workbook patch failed")
        raise
    after = template_sha256()
    if before != after:
        logger.error("ACC Shila master template changed during generation")
        raise TemplateError("The bill template could not be read. Please try again later.")
