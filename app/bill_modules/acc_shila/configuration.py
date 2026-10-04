"""ACC Shila settings. Other bill modules must not import this."""

from datetime import date
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = MODULE_DIR / "template" / "acc_sheela.xlsx"

# Calendar year 2026 only. Every example uses the fixed prefix SHJ/26-27.
# January is month 1. This is not the UltraTech May = Q1 sequence.
FINANCIAL_YEAR_TOKEN = "26-27"
INVOICE_PREFIX = "SHJ"
SUPPORTED_START = date(2026, 1, 1)
SUPPORTED_END = date(2026, 12, 31)

# White space added on every side of the printed page. The Excel grid stays as it is.
PAGE_MARGIN_INCHES = 0.5

# Sheet "Format ACC Sheela", inspected from acc_sheela.xlsx.
# Labels stay where they are:
#   D6  "Tax Invoice No. :  "
#   D7  "Date of Invoice:"
#   D10 "Time Period:"
# E6:F6 already holds the invoice-number prefix. E7:F7 is the empty date.
# E10 is the empty time-period cell. F10 is empty, so a month name can sit beside it.
CELL_MAP = {
    "invoice_number": "E6",
    "invoice_date": "E7",
    "time_period": "E10",
}

MONTH_NAMES = (
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
