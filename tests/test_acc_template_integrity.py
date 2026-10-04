import re
import zipfile
from datetime import date
from pathlib import Path

from app.bill_modules.acc_lalan.configuration import CELL_MAP as LALAN_CELLS
from app.bill_modules.acc_lalan.configuration import TEMPLATE_PATH as LALAN_TEMPLATE
from app.bill_modules.acc_lalan.excel_processing import excel_serial as lalan_serial
from app.bill_modules.acc_lalan.excel_processing import template_sha256 as lalan_hash
from app.bill_modules.acc_lalan.excel_processing import write_working_copy as write_lalan
from app.bill_modules.acc_shila.configuration import CELL_MAP as SHILA_CELLS
from app.bill_modules.acc_shila.configuration import TEMPLATE_PATH as SHILA_TEMPLATE
from app.bill_modules.acc_shila.excel_processing import excel_serial as shila_serial
from app.bill_modules.acc_shila.excel_processing import template_sha256 as shila_hash
from app.bill_modules.acc_shila.excel_processing import write_working_copy as write_shila
from app.rendering.xlsx_patch import read_inline_cell


def test_acc_lalan_copy_changes_only_the_three_dynamic_cells(tmp_path: Path):
    _assert_three_cells(
        tmp_path / "lalan.xlsx",
        template=LALAN_TEMPLATE,
        digest=lalan_hash,
        write=write_lalan,
        cells=LALAN_CELLS,
        invoice_number="LPJ/26-27/5",
        serial=lalan_serial(date(2026, 5, 15)),
        period="May 2026",
    )


def test_acc_shila_copy_changes_only_the_three_dynamic_cells(tmp_path: Path):
    _assert_three_cells(
        tmp_path / "shila.xlsx",
        template=SHILA_TEMPLATE,
        digest=shila_hash,
        write=write_shila,
        cells=SHILA_CELLS,
        invoice_number="SHJ/26-27/12",
        serial=shila_serial(date(2026, 12, 20)),
        period="December 2026",
    )


def _cell_xml(sheet: str, ref: str) -> str:
    match = re.search(rf'<c r="{ref}"[^>]*?(?:/>|>.*?</c>)', sheet)
    assert match, ref
    return match.group(0)


def _assert_three_cells(destination, *, template, digest, write, cells, invoice_number, serial, period):
    before = digest()
    invoice_date = date(2026, 5, 15) if invoice_number.endswith("/5") else date(2026, 12, 20)
    write(
        destination,
        {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "time_period": period,
        },
    )
    assert digest() == before

    with zipfile.ZipFile(template) as original, zipfile.ZipFile(destination) as patched:
        changed = [
            name
            for name in original.namelist()
            if original.read(name) != patched.read(name)
        ]
        assert changed == ["xl/worksheets/sheet1.xml"]
        assert original.read("xl/media/image1.png") == patched.read("xl/media/image1.png")
        assert original.read("xl/drawings/drawing1.xml") == patched.read("xl/drawings/drawing1.xml")
        sheet = patched.read("xl/worksheets/sheet1.xml").decode("utf-8")
        original_sheet = original.read("xl/worksheets/sheet1.xml").decode("utf-8")

    assert read_inline_cell(destination, cells["invoice_number"]) == invoice_number
    assert read_inline_cell(destination, cells["time_period"]) == period
    assert f'<c r="{cells["invoice_date"]}" s="31"><v>{serial}</v></c>' in sheet
    assert _cell_xml(original_sheet, "D6") == _cell_xml(sheet, "D6")
    assert _cell_xml(original_sheet, "D7") == _cell_xml(sheet, "D7")
    assert _cell_xml(original_sheet, "D10") == _cell_xml(sheet, "D10")
    assert sheet.count("<mergeCell") == original_sheet.count("<mergeCell")
