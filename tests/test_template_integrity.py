import zipfile
from pathlib import Path

import pytest

from app.bill_modules.ultratech.configuration import CELL_MAP, TEMPLATE_PATH
from app.bill_modules.ultratech.excel_processing import template_sha256, write_working_copy
from app.errors import TemplateError
from app.rendering.xlsx_patch import patch_xlsx, read_inline_cell, reveal_black_borders


def test_working_copy_changes_only_the_sheet_and_three_cells(tmp_path: Path):
    before = template_sha256()
    destination = tmp_path / "working.xlsx"
    write_working_copy(
        destination,
        {
            "invoice_number": "2026-27/Q1",
            "invoice_date": "15 May 2026",
            "bill_period": "09 May 2026 \u2013 08 June 2026",
        },
    )
    assert template_sha256() == before
    assert TEMPLATE_PATH.read_bytes()[:4] == b"PK\x03\x04"

    with zipfile.ZipFile(TEMPLATE_PATH) as original, zipfile.ZipFile(destination) as patched:
        assert original.namelist() == patched.namelist()
        changed = []
        for name in original.namelist():
            if original.read(name) != patched.read(name):
                changed.append(name)
        assert changed == ["xl/worksheets/sheet1.xml", "xl/styles.xml"]
        sheet = patched.read("xl/worksheets/sheet1.xml").decode("utf-8")
        assert original.read("xl/drawings/drawing1.xml") == patched.read("xl/drawings/drawing1.xml")
        assert original.read("xl/media/image1.png") == patched.read("xl/media/image1.png")
        assert original.read("xl/sharedStrings.xml") == patched.read("xl/sharedStrings.xml")

    assert '<c r="I8" t="s" s="27"><v>7</v></c>' in sheet
    assert '<c r="I9" t="s" s="33"><v>10</v></c>' in sheet
    assert '<c r="I16" t="s" s="33"><v>24</v></c>' in sheet
    assert '<mergeCell ref="L16:M17"/>' in sheet
    assert read_inline_cell(destination, CELL_MAP["invoice_number"]) == "2026-27/Q1"
    assert read_inline_cell(destination, CELL_MAP["invoice_date"]) == "15 May 2026"
    assert read_inline_cell(destination, CELL_MAP["bill_period"]) == "09 May 2026\n\u2013 08 June 2026"
    assert "xl/media/image1.png" in zipfile.ZipFile(destination).namelist()
    assert "xl/drawings/drawing1.xml" in zipfile.ZipFile(destination).namelist()


def test_border_fix_paints_the_table_black_without_touching_the_template(tmp_path: Path):
    before = template_sha256()
    working = tmp_path / "borders.xlsx"
    working.write_bytes(TEMPLATE_PATH.read_bytes())
    reveal_black_borders(working)
    assert template_sha256() == before

    with zipfile.ZipFile(working) as archive:
        styles = archive.read("xl/styles.xml").decode("utf-8")
    borders = styles.split("<borders", 1)[1].split("</borders>", 1)[0]
    assert 'indexed="8"' not in borders
    assert 'rgb="FF000000"' in borders
    assert 'indexed="8"' in styles  # font colors stay as they were


def test_missing_cell_does_not_touch_the_template(tmp_path: Path):
    before = template_sha256()
    with pytest.raises(TemplateError):
        patch_xlsx(TEMPLATE_PATH, tmp_path / "broken.xlsx", {"Z99": "nope"})
    assert template_sha256() == before
    assert not (tmp_path / "broken.xlsx").exists()
