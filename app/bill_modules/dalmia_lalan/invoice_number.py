"""Dalmia Lalan invoice numbers. January is 1. The prefix stays LPJ/26-27/D-."""

from datetime import date

from app.bill_modules.dalmia_lalan.configuration import INVOICE_PREFIX
from app.bill_modules.dalmia_lalan.validation import ensure_supported


def invoice_number_for(invoice_date: date) -> str:
    ensure_supported(invoice_date)
    month = invoice_date.month
    if month < 1 or month > 12:
        raise ValueError("month")
    return f"{INVOICE_PREFIX}{month}"


def pdf_filename_for(invoice_number: str) -> str:
    token = invoice_number.replace("/", "_")
    return f"Dalmia_Lalan_Invoice_{token}.pdf"
