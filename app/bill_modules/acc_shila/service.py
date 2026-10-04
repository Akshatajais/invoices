"""ACC Shila bill generation. Numbering and time periods stay inside this module."""

from __future__ import annotations

import logging
import tempfile
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.bill_modules.acc_shila.excel_processing import write_working_copy
from app.bill_modules.acc_shila.invoice_number import invoice_number_for, pdf_filename_for
from app.bill_modules.acc_shila.pdf_processing import render_workbook
from app.bill_modules.acc_shila.time_period import time_period_for
from app.bill_modules.acc_shila.validation import parse_invoice_date

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AccShilaBill:
    invoice_date: date
    invoice_number: str
    time_period: str

    @property
    def filename(self) -> str:
        return pdf_filename_for(self.invoice_number)

    def as_dict(self) -> dict[str, str]:
        return {
            "invoiceDate": self.invoice_date.isoformat(),
            "invoiceNumber": self.invoice_number,
            "timePeriod": self.time_period,
            "filename": self.filename,
        }


def describe(invoice_date: date) -> AccShilaBill:
    return AccShilaBill(
        invoice_date=invoice_date,
        invoice_number=invoice_number_for(invoice_date),
        time_period=time_period_for(invoice_date),
    )


def describe_iso(value: str | None) -> AccShilaBill:
    return describe(parse_invoice_date(value))


def generate_pdf(invoice_date: date) -> tuple[bytes, str]:
    bill = describe(invoice_date)
    with tempfile.TemporaryDirectory(prefix="acc-shila-") as temp_dir:
        folder = Path(temp_dir)
        workbook = folder / f"acc-shila-{uuid.uuid4().hex}.xlsx"
        write_working_copy(
            workbook,
            {
                "invoice_number": bill.invoice_number,
                "invoice_date": bill.invoice_date,
                "time_period": bill.time_period,
            },
        )
        pdf_path = render_workbook(workbook, folder)
        payload = pdf_path.read_bytes()
    logger.info("ACC Shila PDF generated")
    return payload, bill.filename
