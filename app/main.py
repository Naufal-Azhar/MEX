"""FastAPI application entry point with structured error envelopes."""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import configure_local_caches, get_logger, load_settings
from app.schemas.fact_specs import FactBatchValidationError
from app.schemas.facts import FactConflictError

configure_local_caches()
logger = get_logger("app.main")

app = FastAPI(
    title="F1 Technical Regulation Expert System",
    version="1.1.0",
    description=(
        "Academic prototype for checking selected Formula 1 technical regulation provisions. "
        "Scope is limited to reviewed provisions in knowledge_base/rules/rules.json; "
        "this is not FIA certification."
    ),
)

def _cors_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://127.0.0.1:3000",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

MAX_REQUEST_BYTES = int(os.getenv("MAX_REQUEST_BYTES", "1000000"))


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    header = request.headers.get("content-length")
    if header:
        try:
            size = int(header)
        except ValueError:
            size = 0
        if size > MAX_REQUEST_BYTES:
            return JSONResponse(
                status_code=413,
                content={
                    "status": "ERROR",
                    "diagnostics": [
                        {
                            "code": "REQUEST_TOO_LARGE",
                            "message": f"Request body exceeds {MAX_REQUEST_BYTES} bytes.",
                            "details": {},
                        }
                    ],
                    "detail": "Request body terlalu besar.",
                },
            )
    return await call_next(request)

app.include_router(router)


@app.exception_handler(FactBatchValidationError)
async def invalid_fact_handler(request: Request, exc: FactBatchValidationError) -> JSONResponse:
    diagnostics = [
        {
            "code": "INVALID_INPUT",
            "message": str(error),
            "details": {"fact": error.name, **error.details},
        }
        for error in exc.errors
    ]
    return JSONResponse(
        status_code=422,
        content={
            "status": "INVALID_INPUT",
            "diagnostics": diagnostics,
            "detail": "Input fakta tidak valid.",
        },
    )


@app.exception_handler(FactConflictError)
async def fact_conflict_handler(request: Request, exc: FactConflictError) -> JSONResponse:
    diagnostics = [
        {
            "code": "CONFLICTING_INPUT",
            "message": f"Conflicting values for fact '{conflict.name}'.",
            "details": conflict.model_dump(mode="json"),
        }
        for conflict in exc.conflicts
    ]
    return JSONResponse(
        status_code=409,
        content={
            "status": "CONFLICTING_INPUT",
            "diagnostics": diagnostics,
            "detail": "Fakta yang bertentangan harus diselesaikan sebelum evaluasi.",
        },
    )


def _safe_validation_error(error: dict) -> dict:
    return {
        "type": error.get("type"),
        "loc": list(error.get("loc", [])),
        "msg": error.get("msg"),
        "input": jsonable_encoder(error.get("input")),
        "ctx": {key: str(value) for key, value in (error.get("ctx") or {}).items()},
    }


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "status": "INVALID_INPUT",
            "diagnostics": [
                {
                    "code": "INVALID_INPUT",
                    "message": "Request schema validation failed.",
                    "details": _safe_validation_error(error),
                }
                for error in exc.errors()
            ],
            "detail": "Request tidak sesuai kontrak API.",
        },
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error")
    return JSONResponse(
        status_code=500,
        content={
            "status": "ERROR",
            "diagnostics": [
                {"code": "INTERNAL_ERROR", "message": "Unexpected system error.", "details": {}}
            ],
            "detail": "Terjadi kesalahan sistem; tidak ada keputusan kepatuhan yang dibuat.",
        },
    )


@app.get("/")
def root() -> dict[str, str]:
    settings = load_settings()
    return {
        "name": "F1 Technical Regulation Expert System",
        "version": "1.1.0",
        "regulation": "FIA 2026 Formula One Technical Regulations — Section C, Issue 21",
        "llm_provider": settings.llm_provider,
        "status_contract": "SATISFIED | VIOLATED | INSUFFICIENT_DATA | UNSUPPORTED | NOT_APPLICABLE | ERROR",
        "docs": "/docs",
        "notice": "Academic prototype; only reviewed provisions are checked. Not FIA certification.",
    }


def run() -> None:
    import uvicorn

    settings = load_settings()
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=False)


if __name__ == "__main__":
    run()
