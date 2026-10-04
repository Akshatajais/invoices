"""UltraTech-only settings. Other bill modules must not import this."""

from datetime import date
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = MODULE_DIR / "template" / "ultratech.xlsx"

FINANCIAL_YEAR_LABEL = "2026-27"
SUPPORTED_START = date(2026, 5, 1)
SUPPORTED_END = date(2027, 4, 30)

# White space added above the printed page. The Excel grid stays as it is.
TOP_MARGIN_INCHES = 0.5

# Sheet "Godwon rent (2)", inspected from the master workbook.
# Labels stay where they are:
#   I8  "Invoice No-"
#   I9  "Invoice Date -"
#   I16 "Bill for the period :"
# The right-hand value column is L (invoice number, date, state, SAC, and so on).
# L9 and L16 are the empty value cells beside those labels. I16 is not written.
CELL_MAP = {
    "invoice_number": "L8",
    "invoice_date": "L9",
    "bill_period": "L16",
}

# One line of a full period is wider than columns L and M at 14pt, which is
# the size of the label. The working copy merges L16:M17 and splits the
# period onto two lines so it stays that size and inside the right border.
# The master file is not edited.
BILL_PERIOD_FIT_RANGE = "L16:M17"

# May 2026 is sequence 1. April 2027 is sequence 12.
SEQUENCE_BY_MONTH = {
    5: 1,
    6: 2,
    7: 3,
    8: 4,
    9: 5,
    10: 6,
    11: 7,
    12: 8,
    1: 9,
    2: 10,
    3: 11,
    4: 12,
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
