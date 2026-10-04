"""ACC Shila invoice numbers. January is 1. Not an UltraTech rule."""

from datetime import date

from app.bill_modules.acc_shila.configuration import FINANCIAL_YEAR_TOKEN, INVOICE_PREFIX
from app.bill_modules.acc_shila.validation import ensure_supported


def invoice_number_for(invoice_date: date) -> str:
    ensure_supported(invoice_date)
    return f"{INVOICE_PREFIX}/{FINANCIAL_YEAR_TOKEN}/{invoice_date.month}"


def pdf_filename_for(invoice_number: str) -> str:
    token = invoice_number.replace("/", "_")
    return f"ACC_Shila_Invoice_{token}.pdf"
