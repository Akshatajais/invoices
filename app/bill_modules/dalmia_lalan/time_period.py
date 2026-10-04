"""Dalmia Lalan time period: calendar month and year only."""

from datetime import date

from app.bill_modules.dalmia_lalan.configuration import MONTH_NAMES
from app.bill_modules.dalmia_lalan.validation import ensure_supported


def time_period_for(invoice_date: date) -> str:
    ensure_supported(invoice_date)
    return f"{MONTH_NAMES[invoice_date.month]} {invoice_date.year}"
