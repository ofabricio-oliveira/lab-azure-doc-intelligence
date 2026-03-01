"""
Azure Document Intelligence — Extrator de Documentos LAB
Main FastAPI application.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Union

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.models import AnalysisResult, ReadResult
from app.services.document_intelligence_service import analyze_document
from app.utils.exporter import generate_csv, generate_xlsx
from app.utils.normalizer import normalize_result, normalize_read_result

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Azure Document Intelligence — Extrator de Documentos LAB")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# Static and template setup
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Ensure data directories exist
UPLOADS_DIR = Path("data/uploads")
RESULTS_DIR = Path("data/results")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions and MIME types
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_MIMES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}

MAX_FILE_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024

# In-memory result store (keyed by analysis_id)
# In a real app this would be a database; for this lab a simple dict is enough.
_results: dict[str, Union[AnalysisResult, ReadResult]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize_filename(name: str) -> str:
    """Remove unsafe characters from a filename."""
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    return safe or "upload"


def _validate_upload(file: UploadFile, contents: bytes) -> None:
    """Raise HTTPException if the upload is invalid."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo '{ext}' não permitido. Use: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Best-effort MIME check (browsers may send generic types)
    if file.content_type and file.content_type not in ALLOWED_MIMES:
        logger.warning("Unexpected MIME type: %s (allowing anyway)", file.content_type)

    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. Máximo permitido: {settings.MAX_FILE_SIZE_MB} MB.",
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the upload form."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "max_size": settings.MAX_FILE_SIZE_MB},
    )


@app.post("/analyze")
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = Form("receipt"),
):
    """
    Receive an uploaded document, send it to Azure Document Intelligence,
    normalise the result and render the result page.
    """
    analysis_id = uuid.uuid4().hex[:12]
    logger.info("analysis_id=%s — starting (type=%s, file=%s)", analysis_id, document_type, file.filename)

    # --- Validate ---
    contents = await file.read()
    _validate_upload(file, contents)

    if document_type not in ("receipt", "invoice", "read"):
        raise HTTPException(status_code=400, detail="Tipo de documento inválido.")

    # --- Save upload ---
    safe_name = _sanitize_filename(file.filename or "upload")
    upload_path = UPLOADS_DIR / f"{analysis_id}_{safe_name}"
    upload_path.write_bytes(contents)
    logger.info("analysis_id=%s — saved upload to %s", analysis_id, upload_path)

    # --- Call Azure Document Intelligence ---
    try:
        raw_result = analyze_document(str(upload_path), document_type)
    except RuntimeError as exc:
        logger.error("analysis_id=%s — Azure call failed: %s", analysis_id, exc)
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        logger.exception("analysis_id=%s — unexpected error", analysis_id)
        raise HTTPException(status_code=500, detail=f"Falha na análise: {exc}")

    # --- Save raw JSON (educational) ---
    json_path = RESULTS_DIR / f"{analysis_id}.json"
    json_path.write_text(json.dumps(raw_result, indent=2, default=str), encoding="utf-8")
    logger.info("analysis_id=%s — raw JSON saved to %s", analysis_id, json_path)

    # --- Normalise & render ---
    # OCR Read uses a different normalizer and template than Receipt/Invoice
    if document_type == "read":
        result = normalize_read_result(
            raw=raw_result,
            analysis_id=analysis_id,
            source_filename=file.filename or safe_name,
        )
        _results[analysis_id] = result
        return templates.TemplateResponse(
            "read_result.html",
            {"request": request, "result": result},
        )

    # Receipt / Invoice
    result = normalize_result(
        raw=raw_result,
        document_type=document_type,
        analysis_id=analysis_id,
        source_filename=file.filename or safe_name,
    )
    _results[analysis_id] = result

    # --- Render result page ---
    return templates.TemplateResponse(
        "result.html",
        {"request": request, "result": result},
    )


# ---------------------------------------------------------------------------
# Download routes
# ---------------------------------------------------------------------------

def _get_result(analysis_id: str) -> Union[AnalysisResult, ReadResult]:
    """Retrieve a cached result or raise 404."""
    result = _results.get(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Resultado não encontrado. Execute uma nova análise.")
    return result


@app.get("/download/csv/{analysis_id}")
async def download_csv(analysis_id: str):
    """Download analysis result as CSV (Receipt/Invoice only)."""
    result = _get_result(analysis_id)
    if isinstance(result, ReadResult):
        raise HTTPException(status_code=400, detail="OCR Read não suporta download CSV. Use o texto extraído na tela.")
    csv_text = generate_csv(result)
    logger.info("analysis_id=%s — CSV download", analysis_id)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="analysis_{analysis_id}.csv"'},
    )


@app.get("/download/xlsx/{analysis_id}")
async def download_xlsx(analysis_id: str):
    """Download analysis result as Excel (Receipt/Invoice only)."""
    result = _get_result(analysis_id)
    if isinstance(result, ReadResult):
        raise HTTPException(status_code=400, detail="OCR Read não suporta download Excel. Use o texto extraído na tela.")
    xlsx_bytes = generate_xlsx(result)
    logger.info("analysis_id=%s — XLSX download", analysis_id)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="analysis_{analysis_id}.xlsx"'},
    )


@app.get("/download/txt/{analysis_id}")
async def download_txt(analysis_id: str):
    """Download OCR Read extracted text as .txt (Read only)."""
    result = _get_result(analysis_id)
    if not isinstance(result, ReadResult):
        raise HTTPException(status_code=400, detail="Download TXT disponível apenas para OCR Read.")
    logger.info("analysis_id=%s — TXT download", analysis_id)
    return Response(
        content=result.content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="ocr_{analysis_id}.txt"'},
    )
