import re
import zipfile
from datetime import date
from pathlib import Path

from app.bill_modules.dalmia_lalan.configuration import CELL_MAP as LALAN_CELLS
from app.bill_modules.dalmia_lalan.configuration import TEMPLATE_PATH as LALAN_TEMPLATE
from app.bill_modules.dalmia_lalan.excel_processing import excel_serial as lalan_serial
from app.bill_modules.dalmia_lalan.excel_processing import template_sha256 as lalan_hash
from app.bill_modules.dalmia_lalan.excel_processing import write_working_copy as write_lalan
from app.bill_modules.dalmia_shila.configuration import CELL_MAP as SHILA_CELLS
from app.bill_modules.dalmia_shila.configuration import TEMPLATE_PATH as SHILA_TEMPLATE
from app.bill_modules.dalmia_shila.excel_processing import invoice_date_text as shila_date_text
from app.bill_modules.dalmia_shila.excel_processing import template_sha256 as shila_hash
from app.bill_modules.dalmia_shila.excel_processing import write_working_copy as write_shila
from app.rendering.xlsx_patch import read_inline_cell


def test_dalmia_lalan_copy_changes_only_the_three_dynamic_cells(tmp_path: Path):
    destination = tmp_path / "lalan.xlsx"
    before = lalan_hash()
    invoice_date = date(2026, 5, 15)
    write_lalan(
        destination,
        {
            "invoice_number": "LPJ/26-27/D-5",
            "invoice_date": invoice_date,
            "time_period": "May 2026",
        },
    )
    assert lalan_hash() == before

    with zipfile.ZipFile(LALAN_TEMPLATE) as original, zipfile.ZipFile(destination) as patched:
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

    assert '<c r="E10"' not in original_sheet
    assert read_inline_cell(destination, LALAN_CELLS["invoice_number"]) == "LPJ/26-27/D-5"
    assert read_inline_cell(destination, LALAN_CELLS["time_period"]) == "May 2026"
    serial = lalan_serial(invoice_date)
    assert f'<c r="{LALAN_CELLS["invoice_date"]}" s="98"><v>{serial}</v></c>' in sheet
    assert _cell_xml(original_sheet, "D6") == _cell_xml(sheet, "D6")
    assert _cell_xml(original_sheet, "D7") == _cell_xml(sheet, "D7")
    assert _cell_xml(original_sheet, "D10") == _cell_xml(sheet, "D10")
    assert sheet.count("<mergeCell") == original_sheet.count("<mergeCell")
    assert 'topLeftCell="A2"' in original_sheet
    assert 'topLeftCell="A1"' in sheet
    assert _without(original_sheet, ("E6", "E7")).replace(
        'topLeftCell="A2"', 'topLeftCell="A1"', 1
    ) == _without(sheet, ("E6", "E7", "E10"))


def test_dalmia_shila_copy_changes_only_the_three_dynamic_cells(tmp_path: Path):
    destination = tmp_path / "shila.xlsx"
    before = shila_hash()
    invoice_date = date(2027, 1, 15)
    write_shila(
        destination,
        {
            "invoice_number": "SHJ/26-27/D-1",
            "invoice_date": invoice_date,
            "time_period": "January 2027",
        },
    )
    assert shila_hash() == before

    with zipfile.ZipFile(SHILA_TEMPLATE) as original, zipfile.ZipFile(destination) as patched:
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

    assert read_inline_cell(destination, SHILA_CELLS["invoice_number"]) == "SHJ/26-27/D-1"
    assert read_inline_cell(destination, SHILA_CELLS["invoice_date"]) == shila_date_text(invoice_date)
    assert read_inline_cell(destination, SHILA_CELLS["time_period"]) == "January 2027"
    assert _cell_xml(original_sheet, "D6") == _cell_xml(sheet, "D6")
    assert _cell_xml(original_sheet, "D7") == _cell_xml(sheet, "D7")
    assert _cell_xml(original_sheet, "D10") == _cell_xml(sheet, "D10")
    assert sheet.count("<mergeCell") == original_sheet.count("<mergeCell")
    assert 'topLeftCell="A13"' in original_sheet
    assert 'topLeftCell="A1"' in sheet
    assert _without(original_sheet, ("E6", "E7", "E10")).replace(
        'topLeftCell="A13"', 'topLeftCell="A1"', 1
    ) == _without(sheet, ("E6", "E7", "E10"))


def _cell_xml(sheet: str, ref: str) -> str:
    match = re.search(rf'<c r="{ref}"[^>]*?(?:/>|>.*?</c>)', sheet)
    assert match, ref
    return match.group(0)


def _without(sheet: str, refs: tuple[str, ...]) -> str:
    text = sheet
    for ref in refs:
        text = re.sub(rf'<c r="{ref}"[^>]*?(?:/>|>.*?</c>)', "", text)
    return text
