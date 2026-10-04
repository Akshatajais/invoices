from datetime import date

import pytest

from app.bill_modules.dalmia_lalan.service import describe as describe_lalan
from app.bill_modules.dalmia_lalan.validation import parse_invoice_date as parse_lalan
from app.bill_modules.dalmia_shila.service import describe as describe_shila
from app.bill_modules.dalmia_shila.validation import parse_invoice_date as parse_shila
from app.errors import InvalidDateError


@pytest.mark.parametrize(
    ("raw", "number", "period"),
    [
        ("2026-01-15", "LPJ/26-27/D-1", "January 2026"),
        ("2026-05-15", "LPJ/26-27/D-5", "May 2026"),
        ("2026-12-15", "LPJ/26-27/D-12", "December 2026"),
        ("2027-01-15", "LPJ/26-27/D-1", "January 2027"),
    ],
)
def test_dalmia_lalan_calendar_month_numbering(raw, number, period):
    bill = describe_lalan(parse_lalan(raw))
    assert bill.invoice_number == number
    assert bill.time_period == period
    assert bill.filename == f"Dalmia_Lalan_Invoice_{number.replace('/', '_')}.pdf"


@pytest.mark.parametrize(
    ("raw", "number", "period"),
    [
        ("2026-01-15", "SHJ/26-27/D-1", "January 2026"),
        ("2026-05-15", "SHJ/26-27/D-5", "May 2026"),
        ("2026-12-15", "SHJ/26-27/D-12", "December 2026"),
        ("2027-01-15", "SHJ/26-27/D-1", "January 2027"),
    ],
)
def test_dalmia_shila_calendar_month_numbering(raw, number, period):
    bill = describe_shila(parse_shila(raw))
    assert bill.invoice_number == number
    assert bill.time_period == period
    assert bill.filename == f"Dalmia_Shila_Invoice_{number.replace('/', '_')}.pdf"


@pytest.mark.parametrize("parser", [parse_lalan, parse_shila])
@pytest.mark.parametrize(
    "raw",
    ["", "   ", "not-a-date", "2025-12-31", "2027-02-01", "2026-04-31", "2027-01-32"],
)
def test_dalmia_dates_outside_the_supported_window_are_rejected(parser, raw):
    with pytest.raises(InvalidDateError, match="Please select a valid invoice date."):
        parser(raw)


def test_dalmia_rules_do_not_follow_ultratech_or_acc_numbering():
    lalan = describe_lalan(date(2026, 5, 15))
    shila = describe_shila(date(2026, 5, 15))
    assert lalan.invoice_number == "LPJ/26-27/D-5"
    assert shila.invoice_number == "SHJ/26-27/D-5"
    assert lalan.time_period == "May 2026"
    assert "Q1" not in lalan.invoice_number
    assert lalan.invoice_number != "LPJ/26-27/5"
    assert "–" not in lalan.time_period

    january = describe_lalan(date(2027, 1, 15))
    assert january.invoice_number == "LPJ/26-27/D-1"
    assert january.time_period == "January 2027"
