import io
from datetime import date

import pytest
from pypdf import PdfReader

from app.bill_modules.acc_lalan.excel_processing import template_sha256 as acc_lalan_hash
from app.bill_modules.acc_shila.excel_processing import template_sha256 as acc_shila_hash
from app.bill_modules.dalmia_lalan.excel_processing import template_sha256 as lalan_hash
from app.bill_modules.dalmia_lalan.service import generate_pdf as generate_lalan
from app.bill_modules.dalmia_shila.excel_processing import template_sha256 as shila_hash
from app.bill_modules.dalmia_shila.service import generate_pdf as generate_shila
from app.bill_modules.ultratech.excel_processing import template_sha256 as ultratech_hash
from app.rendering.libreoffice_pdf import renderer_available

pytestmark = pytest.mark.skipif(
    not renderer_available(),
    reason="LibreOffice is not installed",
)


def test_dalmia_lalan_may_pdf_keeps_the_template():
    before = lalan_hash()
    ultra_before = ultratech_hash()
    acc_before = acc_lalan_hash()
    payload, filename = generate_lalan(date(2026, 5, 15))
    assert lalan_hash() == before
    assert ultratech_hash() == ultra_before
    assert acc_lalan_hash() == acc_before
    assert filename == "Dalmia_Lalan_Invoice_LPJ_26-27_D-5.pdf"
    text = _text(payload)
    assert "LPJ/26-27/D-5" in text
    assert "15/05/2026" in text
    assert "May 2026" in text
    assert "GODOWN BILL - Shahpur" in text
    assert "Lalan Prasad Jaiswal" in text
    reader = PdfReader(io.BytesIO(payload))
    assert len(reader.pages) == 1
    assert len(reader.pages[0].images) >= 1


def test_dalmia_shila_january_2027_pdf_keeps_the_template():
    before = shila_hash()
    acc_before = acc_shila_hash()
    payload, filename = generate_shila(date(2027, 1, 15))
    assert shila_hash() == before
    assert acc_shila_hash() == acc_before
    assert filename == "Dalmia_Shila_Invoice_SHJ_26-27_D-1.pdf"
    text = _text(payload)
    assert "SHJ/26-27/D-1" in text
    assert "January 2027" in text
    assert "15/01/2027" in text
    assert "GODOWN BILL - Shahpur" in text
    assert "Sheela Jaiswal" in text
    reader = PdfReader(io.BytesIO(payload))
    assert len(reader.pages) == 1
    assert len(reader.pages[0].images) >= 1


def _text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
