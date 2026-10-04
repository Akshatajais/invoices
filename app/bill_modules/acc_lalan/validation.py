"""ACC Lalan date checks. Calendar year 2026 only."""

from datetime import date

from app.bill_modules.acc_lalan.configuration import SUPPORTED_END, SUPPORTED_START
from app.errors import InvalidDateError

INVALID_DATE = "Please select a valid invoice date."


def parse_invoice_date(value: str | None) -> date:
    if value is None or not str(value).strip():
        raise InvalidDateError(INVALID_DATE)
    try:
        parsed = date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise InvalidDateError(INVALID_DATE) from exc
    ensure_supported(parsed)
    return parsed


def ensure_supported(invoice_date: date) -> None:
    if SUPPORTED_START <= invoice_date <= SUPPORTED_END:
        return
    raise InvalidDateError(INVALID_DATE)
