"""UltraTech billing periods. The cycle is the 9th through the 8th of the next month.

The billing month is the calendar month of the invoice date. That is the rule
shown for 15 May, 15 June, and 15 July.

Dates on the 1st through the 8th are an edge case: those days still fall inside
the previous cycle (which ends on the 8th), but the stated rule names the
billing month from the invoice date itself. This function keeps that choice in
one place so it can be changed without touching Excel or PDF code.
"""

from datetime import date

from app.bill_modules.ultratech.configuration import MONTH_NAMES
from app.bill_modules.ultratech.validation import ensure_supported


def billing_month_label(invoice_date: date) -> str:
    ensure_supported(invoice_date)
    return f"{MONTH_NAMES[invoice_date.month]} {invoice_date.year}"


def bill_period_for(invoice_date: date) -> str:
    ensure_supported(invoice_date)
    start = date(invoice_date.year, invoice_date.month, 9)
    if invoice_date.month == 12:
        end = date(invoice_date.year + 1, 1, 8)
    else:
        end = date(invoice_date.year, invoice_date.month + 1, 8)
    return f"{_format_day(start)} \u2013 {_format_day(end)}"


def format_invoice_date(invoice_date: date) -> str:
    return _format_day(invoice_date)


def _format_day(value: date) -> str:
    return f"{value.day:02d} {MONTH_NAMES[value.month]} {value.year}"
