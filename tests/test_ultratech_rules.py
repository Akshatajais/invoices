from datetime import date

import pytest

from app.bill_modules.ultratech.service import describe
from app.errors import InvalidDateError
from app.bill_modules.ultratech.validation import parse_invoice_date

PERIOD = "\u2013"


def test_may_2026():
    bill = describe(date(2026, 5, 15))
    assert bill.invoice_number == "2026-27/Q1"
    assert bill.billing_month == "May 2026"
    assert bill.invoice_date_display == "15 May 2026"
    assert bill.bill_period == f"09 May 2026 {PERIOD} 08 June 2026"
    assert bill.filename == "UltraTech_Invoice_2026-27-Q1.pdf"


def test_june_2026():
    bill = describe(date(2026, 6, 15))
    assert bill.invoice_number == "2026-27/Q2"
    assert bill.bill_period == f"09 June 2026 {PERIOD} 08 July 2026"
    assert bill.filename == "UltraTech_Invoice_2026-27-Q2.pdf"


def test_july_2026():
    bill = describe(date(2026, 7, 15))
    assert bill.invoice_number == "2026-27/Q3"
    assert bill.bill_period == f"09 July 2026 {PERIOD} 08 August 2026"


@pytest.mark.parametrize(
    ("day", "number", "start", "end"),
    [
        (date(2026, 5, 15), "2026-27/Q1", "09 May 2026", "08 June 2026"),
        (date(2026, 6, 15), "2026-27/Q2", "09 June 2026", "08 July 2026"),
        (date(2026, 7, 15), "2026-27/Q3", "09 July 2026", "08 August 2026"),
        (date(2026, 8, 15), "2026-27/Q4", "09 August 2026", "08 September 2026"),
        (date(2026, 9, 15), "2026-27/Q5", "09 September 2026", "08 October 2026"),
        (date(2026, 10, 15), "2026-27/Q6", "09 October 2026", "08 November 2026"),
        (date(2026, 11, 15), "2026-27/Q7", "09 November 2026", "08 December 2026"),
        (date(2026, 12, 15), "2026-27/Q8", "09 December 2026", "08 January 2027"),
        (date(2027, 1, 15), "2026-27/Q9", "09 January 2027", "08 February 2027"),
        (date(2027, 2, 15), "2026-27/Q10", "09 February 2027", "08 March 2027"),
        (date(2027, 3, 15), "2026-27/Q11", "09 March 2027", "08 April 2027"),
        (date(2027, 4, 15), "2026-27/Q12", "09 April 2027", "08 May 2027"),
    ],
)
def test_full_financial_year(day, number, start, end):
    bill = describe(day)
    assert bill.invoice_number == number
    assert bill.bill_period == f"{start} {PERIOD} {end}"


def test_first_and_last_supported_days():
    assert describe(date(2026, 5, 1)).invoice_number == "2026-27/Q1"
    assert describe(date(2027, 4, 30)).invoice_number == "2026-27/Q12"


def test_early_days_follow_the_invoice_date_month():
    # Isolated edge: 8 June is still named as the June billing month.
    bill = describe(date(2026, 6, 8))
    assert bill.billing_month == "June 2026"
    assert bill.invoice_number == "2026-27/Q2"
    assert bill.bill_period == f"09 June 2026 {PERIOD} 08 July 2026"


@pytest.mark.parametrize(
    "value",
    ["2026-04-30", "2027-05-01", "2025-12-15", "2028-01-01"],
)
def test_dates_outside_financial_year_are_rejected(value):
    with pytest.raises(InvalidDateError) as caught:
        parse_invoice_date(value)
    assert "2026-27" in caught.value.user_message


@pytest.mark.parametrize("value", ["", "   ", "15-05-2026", "2026-02-31", "not-a-date"])
def test_invalid_dates_are_rejected(value):
    with pytest.raises(InvalidDateError):
        parse_invoice_date(value)
