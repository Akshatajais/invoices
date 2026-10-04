"""UltraTech invoice numbers for financial year 2026-27. Not a global rule."""

from datetime import date

from app.bill_modules.ultratech.configuration import FINANCIAL_YEAR_LABEL, SEQUENCE_BY_MONTH
from app.bill_modules.ultratech.validation import ensure_supported


def invoice_number_for(invoice_date: date) -> str:
    ensure_supported(invoice_date)
    sequence = SEQUENCE_BY_MONTH[invoice_date.month]
    return f"{FINANCIAL_YEAR_LABEL}/Q{sequence}"


def pdf_filename_for(invoice_number: str) -> str:
    token = invoice_number.replace("/", "-")
    return f"UltraTech_Invoice_{token}.pdf"
