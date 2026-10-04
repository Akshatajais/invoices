from pypdf import PdfReader

from app.bill_modules.acc_lalan.pdf_processing import add_page_margins as pad_acc_lalan
from app.bill_modules.acc_shila.pdf_processing import add_page_margins as pad_acc_shila
from app.bill_modules.dalmia_lalan.pdf_processing import add_page_margins as pad_lalan
from app.bill_modules.dalmia_shila.pdf_processing import add_page_margins as pad_shila
from app.bill_modules.ultratech.pdf_processing import add_top_margin


def test_bill_margins_add_half_an_inch_on_every_side(tmp_path):
    source = tmp_path / "bill.pdf"
    _write_blank_page(source, width=400, height=300)
    for pad in (pad_lalan, pad_shila, pad_acc_lalan, pad_acc_shila):
        framed = pad(source)
        page = PdfReader(framed).pages[0]
        assert float(page.mediabox.width) == 472
        assert float(page.mediabox.height) == 372


def test_ultratech_margin_adds_half_an_inch_on_top_only(tmp_path):
    source = tmp_path / "ultratech.pdf"
    _write_blank_page(source, width=400, height=300)
    framed = add_top_margin(source)
    page = PdfReader(framed).pages[0]
    assert float(page.mediabox.width) == 400
    assert float(page.mediabox.height) == 336


def _write_blank_page(path, width, height):
    from pypdf import PageObject, PdfWriter

    writer = PdfWriter()
    writer.add_page(PageObject.create_blank_page(width=width, height=height))
    with path.open("wb") as handle:
        writer.write(handle)
