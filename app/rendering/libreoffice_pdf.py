"""Convert a workbook to PDF with LibreOffice. No commercial conversion API."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from app.errors import RenderError, TemplateError, UnsupportedRuntimeError
from app.rendering.xlsx_patch import reveal_black_borders

logger = logging.getLogger(__name__)

_BUNDLED_FONTS = Path(__file__).resolve().parents[2] / "deploy" / "fonts"
_FONT_PROFILE = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Office.Common/Font/Substitution">
  <prop oor:name="Replacement" oor:op="fuse"><value>true</value></prop>
</item>
<item oor:path="/org.openoffice.Office.Common/Font/Substitution/FontPairs">
  <node oor:name="_0" oor:op="replace">
    <prop oor:name="Always" oor:op="fuse"><value>true</value></prop>
    <prop oor:name="OnScreenOnly" oor:op="fuse"><value>false</value></prop>
    <prop oor:name="ReplaceFont" oor:op="fuse"><value>Calibri</value></prop>
    <prop oor:name="SubstituteFont" oor:op="fuse"><value>Carlito</value></prop>
  </node>
  <node oor:name="_1" oor:op="replace">
    <prop oor:name="Always" oor:op="fuse"><value>true</value></prop>
    <prop oor:name="OnScreenOnly" oor:op="fuse"><value>false</value></prop>
    <prop oor:name="ReplaceFont" oor:op="fuse"><value>Century Schoolbook</value></prop>
    <prop oor:name="SubstituteFont" oor:op="fuse"><value>TeX Gyre Schola</value></prop>
  </node>
</item>
</oor:items>
"""

# LibreOffice locks its user profile, so conversions run one at a time.
_CONVERT_LOCK = threading.Lock()

_CANDIDATE_PATHS = (
    os.environ.get("LIBREOFFICE_PATH", ""),
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/usr/bin/soffice",
    "/usr/bin/libreoffice",
    "/usr/lib/libreoffice/program/soffice",
)


def find_soffice() -> str | None:
    env_path = os.environ.get("LIBREOFFICE_PATH", "").strip()
    if env_path and Path(env_path).is_file():
        return env_path
    for candidate in _CANDIDATE_PATHS:
        if candidate and Path(candidate).is_file():
            return candidate
    return shutil.which("soffice") or shutil.which("libreoffice")


def renderer_available() -> bool:
    return find_soffice() is not None


def convert_xlsx_to_pdf(xlsx_path: Path, output_dir: Path, *, single_page: bool = True) -> Path:
    """Convert one workbook. The caller supplies a disposable copy, never the master template."""
    soffice = find_soffice()
    if not soffice:
        logger.error("LibreOffice executable was not found")
        raise UnsupportedRuntimeError()

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        reveal_black_borders(xlsx_path)
    except TemplateError as exc:
        logger.error("Could not prepare workbook borders for PDF conversion")
        raise RenderError() from exc
    modes = (True, False) if single_page else (False,)
    last_error: RenderError | None = None
    for mode in modes:
        try:
            return _convert_once(soffice, xlsx_path, output_dir, single_page=mode)
        except RenderError as exc:
            last_error = exc
            logger.warning("LibreOffice PDF export failed (single_page=%s)", mode)
    assert last_error is not None
    raise last_error


def _convert_once(soffice: str, xlsx_path: Path, output_dir: Path, *, single_page: bool) -> Path:
    expected = output_dir / f"{xlsx_path.stem}.pdf"
    if expected.exists():
        expected.unlink()

    convert_to = "pdf:calc_pdf_Export"
    if single_page:
        # The UltraTech sheet is already fit-to-1-page. This export option keeps
        # that on hosts where LibreOffice would otherwise ignore fitToPage.
        convert_to += ':{"SinglePageSheets":{"type":"boolean","value":"true"}}'

    with _CONVERT_LOCK:
        with tempfile.TemporaryDirectory(prefix="lo-profile-") as profile_dir:
            profile_path = Path(profile_dir)
            _prepare_profile(profile_path)
            profile = profile_path.resolve().as_uri()
            command = [
                soffice,
                "--headless",
                "--norestore",
                "--nolockcheck",
                "--nologo",
                "--nofirststartwizard",
                f"-env:UserInstallation={profile}",
                "--convert-to",
                convert_to,
                "--outdir",
                str(output_dir),
                str(xlsx_path),
            ]
            logger.info("Starting LibreOffice PDF conversion")
            try:
                completed = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    timeout=120,
                    env=_subprocess_env(),
                )
            except subprocess.TimeoutExpired as exc:
                logger.error("LibreOffice conversion timed out")
                raise RenderError() from exc
            except OSError as exc:
                logger.error("LibreOffice could not be started")
                raise RenderError() from exc

    if completed.returncode != 0 or not expected.is_file():
        logger.error(
            "LibreOffice conversion failed (code=%s, pdf_exists=%s)",
            completed.returncode,
            expected.is_file(),
        )
        _log_process_output(completed)
        raise RenderError()

    logger.info("LibreOffice PDF conversion finished")
    return expected


def _prepare_profile(profile_dir: Path) -> None:
    """Load metric-compatible fonts for Calibri and Century Schoolbook."""
    if not _BUNDLED_FONTS.is_dir():
        return
    fonts = [
        path
        for path in _BUNDLED_FONTS.iterdir()
        if path.suffix.lower() in {".ttf", ".otf", ".ttc"}
    ]
    if not fonts:
        return
    destination = profile_dir / "user" / "fonts"
    destination.mkdir(parents=True, exist_ok=True)
    for font in fonts:
        shutil.copyfile(font, destination / font.name)
    (profile_dir / "user" / "registrymodifications.xcu").write_text(
        _FONT_PROFILE,
        encoding="utf-8",
    )


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env["SAL_NO_NATIVE_FILE_DIALOG"] = "1"
    # A writable home avoids LibreOffice trying to init under a missing directory.
    env.setdefault("HOME", tempfile.gettempdir())
    return env


def _log_process_output(completed: subprocess.CompletedProcess[bytes]) -> None:
    stderr = completed.stderr.decode("utf-8", errors="replace").strip()
    stdout = completed.stdout.decode("utf-8", errors="replace").strip()
    if stdout:
        logger.error("LibreOffice stdout: %s", stdout[-2000:])
    if stderr:
        logger.error("LibreOffice stderr: %s", stderr[-2000:])
