"""UltraTech bill generation. Numbering and billing periods stay inside this module."""

from __future__ import annotations

import logging
import tempfile
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.bill_modules.ultratech.billing_period import (
    bill_period_for,
    billing_month_label,
    format_invoice_date,
)
from app.bill_modules.ultratech.excel_processing import write_working_copy
from app.bill_modules.ultratech.invoice_number import invoice_number_for, pdf_filename_for
from app.bill_modules.ultratech.pdf_processing import render_workbook
from app.bill_modules.ultratech.validation import parse_invoice_date

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UltraTechBill:
    invoice_date: date
    invoice_date_display: str
    billing_month: str
    invoice_number: str
    bill_period: str

    @property
    def filename(self) -> str:
        return pdf_filename_for(self.invoice_number)

    def as_dict(self) -> dict[str, str]:
        return {
            "invoiceDate": self.invoice_date.isoformat(),
            "invoiceDateDisplay": self.invoice_date_display,
            "billingMonth": self.billing_month,
            "invoiceNumber": self.invoice_number,
            "billPeriod": self.bill_period,
            "filename": self.filename,
        }


def describe(invoice_date: date) -> UltraTechBill:
    return UltraTechBill(
        invoice_date=invoice_date,
        invoice_date_display=format_invoice_date(invoice_date),
        billing_month=billing_month_label(invoice_date),
        invoice_number=invoice_number_for(invoice_date),
        bill_period=bill_period_for(invoice_date),
    )


def describe_iso(value: str | None) -> UltraTechBill:
    return describe(parse_invoice_date(value))


def generate_pdf(invoice_date: date) -> tuple[bytes, str]:
    bill = describe(invoice_date)
    with tempfile.TemporaryDirectory(prefix="ultratech-") as temp_dir:
        folder = Path(temp_dir)
        workbook = folder / f"ultratech-{uuid.uuid4().hex}.xlsx"
        write_working_copy(
            workbook,
            {
                "invoice_number": bill.invoice_number,
                "invoice_date": bill.invoice_date_display,
                "bill_period": bill.bill_period,
            },
        )
        pdf_path = render_workbook(workbook, folder)
        payload = pdf_path.read_bytes()
    logger.info("UltraTech PDF generated")
    return payload, bill.filename
