"""UltraTech date checks for financial year 2026-27 only."""

from datetime import date

from app.bill_modules.ultratech.configuration import SUPPORTED_END, SUPPORTED_START
from app.errors import InvalidDateError


def parse_invoice_date(value: str | None) -> date:
    if value is None or not str(value).strip():
        raise InvalidDateError("Choose an invoice date.")
    raw = str(value).strip()
    try:
        parsed = date.fromisoformat(raw)
    except ValueError as exc:
        raise InvalidDateError("Enter a valid invoice date.") from exc
    ensure_supported(parsed)
    return parsed


def ensure_supported(invoice_date: date) -> None:
    if SUPPORTED_START <= invoice_date <= SUPPORTED_END:
        return
    raise InvalidDateError(
        "This date is outside the UltraTech financial year 2026-27 "
        "(1 May 2026 to 30 April 2027)."
    )
