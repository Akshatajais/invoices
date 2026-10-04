"""Dalmia Lalan settings. Other bill modules must not import this."""

from datetime import date
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = MODULE_DIR / "template" / "dalmia_lalan.xlsx"

# The invoice prefix stays 26-27, including January 2027.
# January is month 1. This is not the UltraTech May = Q1 sequence.
FINANCIAL_YEAR_TOKEN = "26-27"
INVOICE_PREFIX = "LPJ/26-27/D-"
SUPPORTED_START = date(2026, 1, 1)
SUPPORTED_END = date(2027, 1, 31)

# White space added on every side of the printed page. The Excel grid stays as it is.
PAGE_MARGIN_INCHES = 0.5

# Sheet "Format Dalmia -lalan", inspected from dalmia_lalan.xlsx.
# Labels stay where they are:
#   D6  "Tax Invoice No. :  "
#   D7  "Date of Invoice:"
#   D10 "Time Period:"
# E6:F6 already holds "LPJ/26-27/D". E7:F7 is the empty date (Excel format 14).
# E10 is not stored in the sheet because it was blank. The working copy adds it.
# F10 stays empty so the month name can sit beside E10.
CELL_MAP = {
    "invoice_number": "E6",
    "invoice_date": "E7",
    "time_period": "E10",
}

# Style 100 is the invoice-number text style: 12pt Calibri, no border.
PERIOD_CELL_STYLE = "100"

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
