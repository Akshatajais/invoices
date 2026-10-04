"""Create reference and test PDFs for the UltraTech workbook.

Usage (from the project root):
    python scripts/render_proof.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.bill_modules.ultratech.excel_processing import template_sha256  # noqa: E402
from app.bill_modules.ultratech.pdf_processing import render_reference_copy  # noqa: E402
from app.bill_modules.ultratech.service import describe, generate_pdf  # noqa: E402
from app.rendering.libreoffice_pdf import renderer_available  # noqa: E402

ARTIFACTS = ROOT / "artifacts"
CASES = (
    date(2026, 5, 15),
    date(2026, 6, 15),
    date(2026, 7, 15),
)


def main() -> int:
    if not renderer_available():
        print("LibreOffice was not found. Install it, then run this script again.")
        return 1

    before = template_sha256()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    import tempfile

    with tempfile.TemporaryDirectory(prefix="ultratech-proof-") as temp_dir:
        reference = render_reference_copy(Path(temp_dir))
        reference_bytes = reference.read_bytes()
    (ARTIFACTS / "reference-ultratech.pdf").write_bytes(reference_bytes)
    _report("reference", reference_bytes)

    for index, day in enumerate(CASES):
        bill = describe(day)
        payload, filename = generate_pdf(day)
        (ARTIFACTS / filename).write_bytes(payload)
        if index == 0:
            (ARTIFACTS / "test-ultratech.pdf").write_bytes(payload)
        _report(filename, payload)
        text = _pdf_text(payload)
        _expect(bill.invoice_number in text, f"{filename} contains {bill.invoice_number}")
        _expect(bill.invoice_date_display in text, f"{filename} contains {bill.invoice_date_display}")
        _expect(bill.bill_period.split(" \u2013 ")[0] in text, f"{filename} contains the period start")
        _expect(bill.bill_period.split(" \u2013 ")[1] in text, f"{filename} contains the period end")

    after = template_sha256()
    _expect(before == after, "master template hash is unchanged")
    print(f"Template SHA-256: {after}")
    print(f"PDFs written to {ARTIFACTS}")
    return 0


def _report(label: str, payload: bytes) -> None:
    from pypdf import PdfReader
    import io

    reader = PdfReader(io.BytesIO(payload))
    page = reader.pages[0]
    box = page.mediabox
    images = len(page.images)
    print(
        f"{label}: pages={len(reader.pages)} "
        f"size={float(box.width):.1f}x{float(box.height):.1f}pt images={images}"
    )


def _pdf_text(payload: bytes) -> str:
    from pypdf import PdfReader
    import io

    reader = PdfReader(io.BytesIO(payload))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _expect(condition: bool, message: str) -> None:
    print(("OK  " if condition else "FAIL") + " " + message)
    if not condition:
        raise SystemExit(1)


if __name__ == "__main__":
    raise SystemExit(main())
