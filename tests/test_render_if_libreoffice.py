from datetime import date
from pathlib import Path

import pytest

from app.bill_modules.ultratech.excel_processing import template_sha256
from app.bill_modules.ultratech.service import describe, generate_pdf
from app.rendering.libreoffice_pdf import renderer_available

pytestmark = pytest.mark.skipif(
    not renderer_available(),
    reason="LibreOffice is not installed",
)


def _text(pdf_bytes: bytes) -> str:
    from pypdf import PdfReader
    import io

    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_may_pdf_matches_template_structure():
    before = template_sha256()
    payload, filename = generate_pdf(date(2026, 5, 15))
    assert template_sha256() == before
    assert filename == "UltraTech_Invoice_2026-27-Q1.pdf"
    assert payload.startswith(b"%PDF")

    from pypdf import PdfReader
    import io

    reader = PdfReader(io.BytesIO(payload))
    assert len(reader.pages) == 1
    text = _text(payload)
    bill = describe(date(2026, 5, 15))
    assert bill.invoice_number in text
    assert bill.invoice_date_display in text
    assert "09 May 2026" in text
    assert "08 June 2026" in text
    assert "MAYANK JAISWAL HUF" in text
    assert "UltraTech" in text
    assert "Authorized Signatory" in text
    assert len(reader.pages[0].images) >= 1
