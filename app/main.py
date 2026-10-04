"""Responsive invoice web app. UltraTech, Dalmia, and ACC bills are active."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.bill_modules.acc_lalan.configuration import SUPPORTED_END as LALAN_END
from app.bill_modules.acc_lalan.configuration import SUPPORTED_START as LALAN_START
from app.bill_modules.acc_lalan.service import describe_iso as lalan_describe
from app.bill_modules.acc_lalan.service import generate_pdf as lalan_generate_pdf
from app.bill_modules.acc_lalan.validation import parse_invoice_date as parse_lalan_date
from app.bill_modules.acc_shila.configuration import SUPPORTED_END as SHILA_END
from app.bill_modules.acc_shila.configuration import SUPPORTED_START as SHILA_START
from app.bill_modules.acc_shila.service import describe_iso as shila_describe
from app.bill_modules.acc_shila.service import generate_pdf as shila_generate_pdf
from app.bill_modules.acc_shila.validation import parse_invoice_date as parse_shila_date
from app.bill_modules.dalmia_lalan.configuration import SUPPORTED_END as DALMIA_LALAN_END
from app.bill_modules.dalmia_lalan.configuration import SUPPORTED_START as DALMIA_LALAN_START
from app.bill_modules.dalmia_lalan.service import describe_iso as dalmia_lalan_describe
from app.bill_modules.dalmia_lalan.service import generate_pdf as dalmia_lalan_generate_pdf
from app.bill_modules.dalmia_lalan.validation import parse_invoice_date as parse_dalmia_lalan_date
from app.bill_modules.dalmia_shila.configuration import SUPPORTED_END as DALMIA_SHILA_END
from app.bill_modules.dalmia_shila.configuration import SUPPORTED_START as DALMIA_SHILA_START
from app.bill_modules.dalmia_shila.service import describe_iso as dalmia_shila_describe
from app.bill_modules.dalmia_shila.service import generate_pdf as dalmia_shila_generate_pdf
from app.bill_modules.dalmia_shila.validation import parse_invoice_date as parse_dalmia_shila_date
from app.bill_modules.registry import list_bills
from app.bill_modules.ultratech.configuration import SUPPORTED_END, SUPPORTED_START
from app.bill_modules.ultratech.pdf_processing import render_reference_copy
from app.bill_modules.ultratech.service import describe_iso, generate_pdf
from app.bill_modules.ultratech.validation import parse_invoice_date
from app.errors import AppError
from app.rendering.libreoffice_pdf import renderer_available

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
STATIC_DIR = APP_DIR / "static"
DEV_PAGES = APP_DIR / "dev_pages"
ARTIFACTS_DIR = Path(os.environ.get("ARTIFACTS_DIR", PROJECT_DIR / "artifacts"))

app = FastAPI(title="Invoices", docs_url=None, redoc_url=None)
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.on_event("startup")
def log_ready() -> None:
    logger.info(
        "Ready env=%s libreoffice=%s",
        os.environ.get("APP_ENV", "development"),
        renderer_available(),
    )

_pdf_cache: dict[str, tuple[str, bytes]] = {}


def _dev_enabled() -> bool:
    return os.environ.get("APP_ENV", "development").strip().lower() != "production"


def _dev_guard() -> None:
    if not _dev_enabled():
        raise StarletteHTTPException(status_code=404)


@app.exception_handler(AppError)
async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error("Request failed: %s", exc.user_message)
    else:
        logger.info("Rejected request: %s", exc.user_message)
    return JSONResponse(status_code=exc.status_code, content={"error": exc.user_message})


@app.exception_handler(Exception)
async def handle_unexpected(_request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return JSONResponse(status_code=exc.status_code, content={"error": detail})
    logger.exception("Unhandled error")
    return JSONResponse(
        status_code=500,
        content={"error": "Something went wrong. Please try again."},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/health")
def api_health() -> dict[str, object]:
    return {
        "status": "ok",
        "renderer": renderer_available(),
        "devTools": _dev_enabled(),
    }


@app.get("/api/bills")
def bills() -> list[dict[str, object]]:
    return list_bills()


@app.get("/api/ultratech/config")
def ultratech_config() -> dict[str, str]:
    return {
        "minDate": SUPPORTED_START.isoformat(),
        "maxDate": SUPPORTED_END.isoformat(),
    }


@app.get("/api/ultratech/preview")
def ultratech_preview(invoiceDate: str = "") -> dict[str, str]:
    return describe_iso(invoiceDate).as_dict()


@app.get("/api/acc-lalan/config")
def acc_lalan_config() -> dict[str, str]:
    return {
        "minDate": LALAN_START.isoformat(),
        "maxDate": LALAN_END.isoformat(),
    }


@app.get("/api/acc-lalan/preview")
def acc_lalan_preview(invoiceDate: str = "") -> dict[str, str]:
    return lalan_describe(invoiceDate).as_dict()


@app.post("/api/acc-lalan/pdf")
async def acc_lalan_pdf(request: Request) -> Response:
    payload = await _json_body(request)
    bill_date = parse_lalan_date(payload.get("invoiceDate"))
    pdf_bytes, filename = lalan_generate_pdf(bill_date)
    return _pdf_response(pdf_bytes, filename)


@app.get("/api/acc-shila/config")
def acc_shila_config() -> dict[str, str]:
    return {
        "minDate": SHILA_START.isoformat(),
        "maxDate": SHILA_END.isoformat(),
    }


@app.get("/api/acc-shila/preview")
def acc_shila_preview(invoiceDate: str = "") -> dict[str, str]:
    return shila_describe(invoiceDate).as_dict()


@app.post("/api/acc-shila/pdf")
async def acc_shila_pdf(request: Request) -> Response:
    payload = await _json_body(request)
    bill_date = parse_shila_date(payload.get("invoiceDate"))
    pdf_bytes, filename = shila_generate_pdf(bill_date)
    return _pdf_response(pdf_bytes, filename)


@app.get("/api/dalmia-lalan/config")
def dalmia_lalan_config() -> dict[str, str]:
    return {
        "minDate": DALMIA_LALAN_START.isoformat(),
        "maxDate": DALMIA_LALAN_END.isoformat(),
    }


@app.get("/api/dalmia-lalan/preview")
def dalmia_lalan_preview(invoiceDate: str = "") -> dict[str, str]:
    return dalmia_lalan_describe(invoiceDate).as_dict()


@app.post("/api/dalmia-lalan/pdf")
async def dalmia_lalan_pdf(request: Request) -> Response:
    payload = await _json_body(request)
    bill_date = parse_dalmia_lalan_date(payload.get("invoiceDate"))
    pdf_bytes, filename = dalmia_lalan_generate_pdf(bill_date)
    return _pdf_response(pdf_bytes, filename)


@app.get("/api/dalmia-shila/config")
def dalmia_shila_config() -> dict[str, str]:
    return {
        "minDate": DALMIA_SHILA_START.isoformat(),
        "maxDate": DALMIA_SHILA_END.isoformat(),
    }


@app.get("/api/dalmia-shila/preview")
def dalmia_shila_preview(invoiceDate: str = "") -> dict[str, str]:
    return dalmia_shila_describe(invoiceDate).as_dict()


@app.post("/api/dalmia-shila/pdf")
async def dalmia_shila_pdf(request: Request) -> Response:
    payload = await _json_body(request)
    bill_date = parse_dalmia_shila_date(payload.get("invoiceDate"))
    pdf_bytes, filename = dalmia_shila_generate_pdf(bill_date)
    return _pdf_response(pdf_bytes, filename)


@app.post("/api/ultratech/pdf")
async def ultratech_pdf(request: Request) -> Response:
    payload = await _json_body(request)
    bill_date = parse_invoice_date(payload.get("invoiceDate"))
    pdf_bytes, filename = generate_pdf(bill_date)
    return _pdf_response(pdf_bytes, filename)


@app.post("/api/test-ultratech-render")
async def test_ultratech_render(request: Request) -> Response:
    """Development check. Disabled when APP_ENV=production."""
    _dev_guard()
    payload = await _json_body(request)
    raw_date = payload.get("invoiceDate") or "2026-05-15"
    bill_date = parse_invoice_date(str(raw_date))
    pdf_bytes, _filename = generate_pdf(bill_date)
    _write_artifact("test-ultratech.pdf", pdf_bytes)
    reference = _reference_pdf()
    _write_artifact("reference-ultratech.pdf", reference)
    return _pdf_response(pdf_bytes, "test-ultratech.pdf")


@app.get("/api/dev/reference-pdf")
def dev_reference_pdf() -> Response:
    _dev_guard()
    return _pdf_response(_reference_pdf(), "reference-ultratech.pdf", inline=True)


@app.get("/api/dev/test-pdf")
def dev_test_pdf() -> Response:
    _dev_guard()
    pdf_bytes, _filename = generate_pdf(parse_invoice_date("2026-05-15"))
    _write_artifact("test-ultratech.pdf", pdf_bytes)
    return _pdf_response(pdf_bytes, "test-ultratech.pdf", inline=True)


@app.get("/dev/compare")
def dev_compare() -> FileResponse:
    _dev_guard()
    return FileResponse(DEV_PAGES / "compare.html")


@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})


async def _json_body(request: Request) -> dict:
    if not request.headers.get("content-type", "").startswith("application/json"):
        return {}
    try:
        body = await request.json()
    except Exception:
        logger.info("Ignoring an unreadable JSON body")
        return {}
    if not isinstance(body, dict):
        return {}
    return body


def _pdf_response(payload: bytes, filename: str, *, inline: bool = False) -> Response:
    disposition = "inline" if inline else "attachment"
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


def _reference_pdf() -> bytes:
    from app.bill_modules.ultratech.excel_processing import template_sha256

    digest = template_sha256()
    cached = _pdf_cache.get("reference")
    if cached and cached[0] == digest:
        return cached[1]
    import tempfile

    with tempfile.TemporaryDirectory(prefix="ultratech-ref-") as temp_dir:
        pdf_path = render_reference_copy(Path(temp_dir))
        payload = pdf_path.read_bytes()
    _pdf_cache["reference"] = (digest, payload)
    return payload


def _write_artifact(name: str, payload: bytes) -> None:
    try:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        (ARTIFACTS_DIR / name).write_bytes(payload)
    except OSError:
        logger.exception("Could not write development PDF artifact")
