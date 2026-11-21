"""HTTP API: versioned compliance, retrieval and extraction endpoints."""

from __future__ import annotations

import json
import threading
from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import DATASETS_DIR, get_logger, load_settings
from app.expert_system.knowledge_base import default_facts_path
from app.expert_system.service import ComplianceService
from app.learning.service import TelemetryLearningService
from app.llm.base import LLMError
from app.llm.fact_extractor import DeterministicFactExtractor, get_extractor
from app.schemas.analysis import TelemetryAnalysisReport, TelemetryAnalyzeRequest
from app.schemas.api import (
    CheckAllRequest,
    CheckRequest,
    ExtractRequest,
    GoalInfo,
    LegacyCheckRequest,
    SearchRequest,
)
from app.schemas.results import CheckReport, RetrievalHit

logger = get_logger("app.api")
router = APIRouter()

_service: ComplianceService | None = None
_retriever: Any = None
_retriever_lock = threading.Lock()
_learning_service: TelemetryLearningService | None = None


def service() -> ComplianceService:
    global _service
    if _service is None:
        _service = ComplianceService()
    return _service


def learning_service() -> TelemetryLearningService:
    global _learning_service
    if _learning_service is None:
        _learning_service = TelemetryLearningService.default()
    return _learning_service


def _telemetry_manifest() -> dict[str, Any]:
    path = DATASETS_DIR / "telemetry" / "manifest.json"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Telemetry fixture manifest not found.")
    return json.loads(path.read_text(encoding="utf-8"))


def retriever():
    global _retriever
    if _retriever is None:
        with _retriever_lock:
            if _retriever is None:
                from app.rag.retriever import Retriever

                logger.info("Loading or building retrieval index")
                _retriever = Retriever.load_or_build()
    return _retriever


def _goals_payload() -> list[GoalInfo]:
    kb = service().kb
    output: list[GoalInfo] = []
    for goal in kb.goals():
        rules = kb.rules_for_goal(goal)
        if not any(rule.conclusion.kind == "boolean" for rule in rules):
            continue
        rule = rules[0]
        output.append(
            GoalInfo(
                goal_id=goal,
                name=rule.name,
                rule_id=rule.rule_id,
                rule_status=rule.status.value,
                article=rule.source.article,
                page=rule.source.page,
                document=rule.source.document,
                issue=rule.source.issue,
                quote=rule.source.quote,
                scope=kb.scope,
                requirements=service().requirements(goal),
            )
        )
    return output


def _rules_payload() -> list[dict[str, Any]]:
    return [
        {
            "rule_id": rule.rule_id,
            "name": rule.name,
            "goal_id": rule.goal,
            "kind": rule.conclusion.kind,
            "status": rule.status.value,
            "source": rule.source.model_dump(),
            "validation": rule.validation.model_dump() if rule.validation else None,
            "notes": rule.notes,
        }
        for rule in service().kb.all_rules()
    ]


def _health_payload() -> dict[str, Any]:
    kb = service().kb
    return {
        "status": "ok",
        "regulation": kb.regulation,
        "issue": kb.regulation_issue,
        "document_id": kb.document_id,
        "scope": kb.scope,
        "subdomain": kb.subdomain,
        "rules": {
            "active": len(kb.active_rules()),
            "reviewed": len(kb.reviewed_rules()),
            "draft": len(kb.draft_rules()),
            "deprecated": len(kb.deprecated_rules()),
            "runnable": len(kb.runnable_rules()),
        },
        "demo_mode": kb.demo_mode,
        "allow_reviewed_rules": kb.allow_reviewed,
        "goals": kb.goals(),
        "llm_provider": load_settings().llm_provider,
        "retrieval_index_loaded": _retriever is not None,
    }


@router.get("/health")
@router.get("/v1/health")
def health() -> dict[str, Any]:
    return _health_payload()


@router.get("/goals", response_model=list[GoalInfo])
@router.get("/v1/goals", response_model=list[GoalInfo])
def goals() -> list[GoalInfo]:
    return _goals_payload()


@router.get("/rules")
def rules() -> list[dict[str, Any]]:
    return _rules_payload()


@router.get("/v1/races")
def races() -> list[dict[str, Any]]:
    manifest = _telemetry_manifest()
    session = manifest["session"]
    return [
        {
            "session_id": manifest["session_id"],
            "season": session["season"],
            "event": session["event"],
            "session_type": session["session_type"],
            "provider": manifest["provider"],
            "license": manifest["license"],
            "lap_count": len(manifest["laps"]),
        }
    ]


@router.get("/v1/races/{session_id}/laps")
def race_laps(session_id: str) -> list[dict[str, Any]]:
    manifest = _telemetry_manifest()
    if session_id != manifest["session_id"]:
        raise HTTPException(status_code=404, detail=f"Unknown session '{session_id}'.")
    return learning_service().telemetry.available_laps()


@router.post("/v1/telemetry/analyze", response_model=TelemetryAnalysisReport)
def telemetry_analyze(request: TelemetryAnalyzeRequest) -> TelemetryAnalysisReport:
    segment = None
    if request.segment_start_m is not None and request.segment_end_m is not None:
        segment = (request.segment_start_m, request.segment_end_m)
    try:
        return learning_service().analyze(
            request.lap_a_id,
            request.lap_b_id,
            segment=segment,
            question=request.question,
            level=request.level,
        )
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - never expose a stack trace
        logger.exception("telemetry analysis failed")
        raise HTTPException(status_code=500, detail="Telemetry analysis failed.") from exc


def _check(goal_id: str, facts, document_issue: str | None) -> CheckReport:
    store = service().build_fact_store(facts)
    logger.info("check goal=%s facts=%d issue=%s", goal_id, len(store), document_issue)
    return service().check(goal_id, store, document_issue=document_issue)


@router.post("/v1/check", response_model=CheckReport)
def check_v1(request: CheckRequest) -> CheckReport:
    return _check(request.goal_id, request.facts, request.document_issue)


@router.post("/check", response_model=CheckReport)
def check_legacy(request: LegacyCheckRequest) -> CheckReport:
    return _check(request.goal, request.facts, request.document_issue)


@router.post("/check/all", response_model=list[CheckReport])
@router.post("/v1/check/all", response_model=list[CheckReport])
def check_all(request: CheckAllRequest) -> list[CheckReport]:
    store = service().build_fact_store(request.facts)
    return service().check_all(store)


@router.post("/v1/search", response_model=list[RetrievalHit])
def search_v1(request: SearchRequest) -> list[RetrievalHit]:
    return _search(
        request,
        include_methodology=request.include_methodology,
    )


@router.post("/retrieve", response_model=list[RetrievalHit])
def retrieve_legacy(request: SearchRequest) -> list[RetrievalHit]:
    # Legacy endpoint searches all indexed documents, including methodology papers.
    return _search(request, include_methodology=True)


def _search(request: SearchRequest, include_methodology: bool) -> list[RetrievalHit]:
    from app.rag.embeddings import EmbeddingError

    try:
        return retriever().search(
            request.query,
            top_k=request.top_k,
            article=request.article,
            document_id=request.document_id,
            include_methodology=include_methodology,
        )
    except (ValueError, EmbeddingError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/retrieval/status")
@router.get("/v1/retrieval/status")
def retrieval_status() -> dict[str, Any]:
    if _retriever is None:
        return {"loaded": False, "message": "Index is built lazily on first search call."}
    return {"loaded": True, "index": _retriever.describe()}


@router.post("/v1/extract-facts")
@router.post("/extract-facts")
def extract_facts(request: ExtractRequest) -> dict[str, Any]:
    settings = load_settings()
    try:
        if request.use_llm:
            extractor = get_extractor(settings)
        else:
            extractor = DeterministicFactExtractor()
        result = extractor.extract(request.text)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=f"Fact extraction failed: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - surface provider errors
        logger.exception("fact extraction failed")
        raise HTTPException(status_code=502, detail=f"Fact extraction failed: {exc}") from exc
    return result.model_dump()


@router.get("/sample-facts")
def sample_facts() -> dict[str, Any]:
    path = default_facts_path()
    if not path.exists():
        raise HTTPException(status_code=404, detail="Sample facts file not found.")
    return json.loads(path.read_text(encoding="utf-8"))
