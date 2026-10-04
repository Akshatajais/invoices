"""Copy an xlsx and replace specific cell values without rewriting the workbook.

openpyxl drops grouped drawings when it saves. This template's signature is a
grouped picture, so the working copy is patched inside the zip. Styles, merges,
drawings, images, and every other part stay byte-for-byte identical.
"""

from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, unescape

from app.errors import TemplateError

logger = logging.getLogger(__name__)

_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def patch_xlsx(
    source: Path,
    destination: Path,
    cell_values: dict[str, str],
    *,
    number_values: dict[str, str] | None = None,
) -> str:
    """Write a new workbook at destination. Returns the worksheet XML path that changed.

    String cells are stored as inline text. Number cells keep the template's
    number format, which is how a date cell stays a date.
    """
    if not source.is_file():
        raise TemplateError("The bill template could not be read. Please try again later.")
    if not cell_values and not number_values:
        raise TemplateError("The bill template could not be read. Please try again later.")

    try:
        with zipfile.ZipFile(source, "r") as archive:
            sheet_path = _worksheet_path(archive)
            xml = archive.read(sheet_path).decode("utf-8")
            updated = _set_cells(xml, cell_values)
            if number_values:
                updated = _set_number_cells(updated, number_values)
            _write_copy(archive, destination, sheet_path, updated.encode("utf-8"))
    except TemplateError:
        raise
    except zipfile.BadZipFile as exc:
        raise TemplateError("The bill template could not be read. Please try again later.") from exc
    except OSError as exc:
        raise TemplateError("The bill template could not be read. Please try again later.") from exc

    return sheet_path


def _worksheet_path(archive: zipfile.ZipFile) -> str:
    try:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    except KeyError as exc:
        raise TemplateError("The bill template could not be read. Please try again later.") from exc
    except ET.ParseError as exc:
        raise TemplateError("The bill template could not be read. Please try again later.") from exc

    sheets = workbook.findall(f"{{{_MAIN}}}sheets/{{{_MAIN}}}sheet")
    if len(sheets) != 1:
        raise TemplateError("The bill template could not be read. Please try again later.")

    relation_id = sheets[0].attrib.get(f"{{{_REL}}}id")
    if not relation_id:
        raise TemplateError("The bill template could not be read. Please try again later.")

    for rel in rels:
        if rel.attrib.get("Id") != relation_id:
            continue
        target = rel.attrib.get("Target", "")
        if target.startswith("/"):
            return target.lstrip("/")
        if target.startswith("xl/"):
            return target
        return "xl/" + target.lstrip("/")

    raise TemplateError("The bill template could not be read. Please try again later.")


def _set_number_cells(xml: str, number_values: dict[str, str]) -> str:
    for cell_ref, number in number_values.items():
        if not re.fullmatch(r"\d+", number):
            logger.error("Refusing a non-numeric workbook value for %s", cell_ref)
            raise TemplateError("The bill template could not be read. Please try again later.")
        xml = _replace_number_cell(xml, cell_ref, number)
    return xml


def _replace_number_cell(xml: str, cell_ref: str, number: str) -> str:
    pattern = re.compile(
        rf'<c r="{re.escape(cell_ref)}"(?P<attrs>[^>/]*)(?P<close>/>|>.*?</c>)',
        re.DOTALL,
    )
    matches = list(pattern.finditer(xml))
    if len(matches) != 1:
        logger.error("Configured cell %s is missing from the workbook", cell_ref)
        raise TemplateError("The bill template is missing a required field. Please try again later.")
    match = matches[0]
    attrs = re.sub(r'\st="[^"]*"', "", match.group("attrs"))
    replacement = f'<c r="{cell_ref}"{attrs}><v>{number}</v></c>'
    return xml[: match.start()] + replacement + xml[match.end() :]


def _set_cells(xml: str, cell_values: dict[str, str]) -> str:
    for cell_ref, value in cell_values.items():
        xml = _replace_cell(xml, cell_ref, value)
    return xml


def _replace_cell(xml: str, cell_ref: str, value: str) -> str:
    pattern = re.compile(
        rf'<c r="{re.escape(cell_ref)}"(?P<attrs>[^>/]*)(?P<close>/>|>.*?</c>)',
        re.DOTALL,
    )
    matches = list(pattern.finditer(xml))
    if len(matches) != 1:
        logger.error("Configured cell %s is missing from the workbook", cell_ref)
        raise TemplateError("The bill template is missing a required field. Please try again later.")

    match = matches[0]
    attrs = re.sub(r'\st="[^"]*"', "", match.group("attrs"))
    attrs = attrs + ' t="inlineStr"'
    text = escape(value)
    replacement = (
        f'<c r="{cell_ref}"{attrs}>'
        f'<is><t xml:space="preserve">{text}</t></is></c>'
    )
    return xml[: match.start()] + replacement + xml[match.end() :]


def _write_copy(
    source: zipfile.ZipFile,
    destination: Path,
    sheet_path: str,
    sheet_bytes: bytes,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w") as out:
        for item in source.infolist():
            data = sheet_bytes if item.filename == sheet_path else source.read(item.filename)
            info = zipfile.ZipInfo(filename=item.filename, date_time=item.date_time)
            info.compress_type = item.compress_type or zipfile.ZIP_DEFLATED
            info.external_attr = item.external_attr
            out.writestr(info, data)


def reveal_black_borders(xlsx_path: Path) -> None:
    """Make existing black borders visible to LibreOffice.

    This workbook stores black lines as palette index 8. Excel draws that as
    black. LibreOffice imports the same index as white, so the invoice grid
    (Sl No, Particulars, No of Month, Rate, Amount) disappears. The temporary
    workbook is rewritten to explicit black. The master template is not opened.
    """
    styles_name = "xl/styles.xml"
    try:
        with zipfile.ZipFile(xlsx_path, "r") as archive:
            styles = archive.read(styles_name).decode("utf-8")
            originals = {item.filename: archive.read(item.filename) for item in archive.infolist()}
            infos = list(archive.infolist())
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        logger.error("Could not read workbook styles before PDF conversion")
        raise TemplateError("The bill template could not be read. Please try again later.") from exc

    updated_styles = _paint_border_index_black(styles)
    if updated_styles == styles:
        return
    originals[styles_name] = updated_styles.encode("utf-8")
    _rewrite_existing_zip(xlsx_path, infos, originals)


def _paint_border_index_black(styles: str) -> str:
    match = re.search(r"<borders\b[^>]*>.*?</borders>", styles, flags=re.DOTALL)
    if not match:
        return styles
    block = re.sub(
        r'<color\b[^>]*\bindexed="8"[^>]*/>',
        '<color rgb="FF000000"/>',
        match.group(0),
    )
    return styles[: match.start()] + block + styles[match.end() :]


def _rewrite_existing_zip(
    path: Path,
    infos: list[zipfile.ZipInfo],
    contents: dict[str, bytes],
) -> None:
    temporary = path.with_suffix(".zip-tmp")
    with zipfile.ZipFile(temporary, "w") as out:
        for item in infos:
            info = zipfile.ZipInfo(filename=item.filename, date_time=item.date_time)
            info.compress_type = item.compress_type or zipfile.ZIP_DEFLATED
            info.external_attr = item.external_attr
            out.writestr(info, contents[item.filename])
    temporary.replace(path)


def read_inline_cell(xlsx_path: Path, cell_ref: str) -> str | None:
    """Return an inline string written by patch_xlsx, if that cell has one."""
    with zipfile.ZipFile(xlsx_path, "r") as archive:
        xml = archive.read(_worksheet_path(archive)).decode("utf-8")
    match = re.search(
        rf'<c r="{re.escape(cell_ref)}"[^>]*t="inlineStr"[^>]*>.*?<t[^>]*>(.*?)</t>',
        xml,
        re.DOTALL,
    )
    if not match:
        return None
    return unescape(match.group(1))
