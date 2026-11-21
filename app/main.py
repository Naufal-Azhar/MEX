"""FastAPI application entry point with structured error envelopes."""

from __future__ import annotations

from fastapi import FastAPI, Request
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                    "details": error,
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
