"""Question routing and grounded-answer orchestration."""

from __future__ import annotations

from pathlib import Path

from app.config import ROOT
from app.learning.retrieval import LearningCorpusIndex
from app.learning.service import TelemetryLearningService
from app.llm.base import LLMProvider, get_provider
from app.rag.grounded_answer import build_deterministic_answer, build_llm_answer
from app.schemas.learning import (
    AskRequest,
    GenerationStatus,
    GroundedAnswer,
    QuestionType,
)

UNSUPPORTED_TERMS = (
    "predict",
    "winner",
    "podium",
    "strategy",
    "setup recommendation",
    "who will win",
    "best setup",
)
REGULATION_TERMS = (
    "fia",
    "regulation",
    "article",
    "section c",
    "wheelbase",
    "minimum mass",
    "scrutineer",
)
TELEMETRY_TERMS = ("telemetry", "lap", "speed trace", "race data", "throttle trace")
THEORY_TERMS = (
    "brake",
    "braking",
    "grip",
    "load transfer",
    "load",
    "drag",
    "downforce",
    "traction",
    "understeer",
    "oversteer",
    "throttle",
    "speed",
    "tyre",
    "tire",
    "relaxation",
    "lateral",
    "longitudinal",
    "dynamics",
    "friction",
    "slip",
    "suspension",
    "vehicle",
)


def classify_question(question: str, has_laps: bool = False) -> QuestionType:
    text = question.lower().strip()
    if not text or any(term in text for term in UNSUPPORTED_TERMS):
        return QuestionType.UNSUPPORTED
    if any(term in text for term in REGULATION_TERMS):
        return QuestionType.REGULATION
    if any(term in text for term in TELEMETRY_TERMS):
        return QuestionType.TELEMETRY_CASE
    if any(term in text for term in THEORY_TERMS):
        return QuestionType.THEORY
    return QuestionType.UNSUPPORTED


def _telemetry_query(question: str) -> str:
    text = question.lower()
    terms: list[str] = []
    if "brake" in text or "braking" in text:
        terms.append("brake onset speed comparison")
    if "throttle" in text:
        terms.append("throttle percentage")
    if "speed" in text:
        terms.append("speed distance time")
    if not terms:
        terms.append("brake onset speed comparison telemetry")
    return " ".join(terms)


class AskService:
    def __init__(
        self,
        corpus: LearningCorpusIndex,
        learning: TelemetryLearningService,
        provider: LLMProvider | None = None,
    ) -> None:
        self.corpus = corpus
        self.learning = learning
        self.provider = provider

    @classmethod
    def default(cls, root: Path | str = ROOT) -> "AskService":
        return cls(
            corpus=LearningCorpusIndex.from_paths(root=root, include_engineering=True),
            learning=TelemetryLearningService.default(),
            provider=get_provider(),
        )

    def ask(self, request: AskRequest) -> GroundedAnswer:
        has_laps = bool(request.lap_a_id and request.lap_b_id)
        question_type = classify_question(request.question, has_laps)

        if question_type is QuestionType.REGULATION:
            return build_deterministic_answer(
                request.question,
                request.level,
                question_type,
                [],
                None,
                generation_status=GenerationStatus.UNAVAILABLE,
                retrieval_backend=self.corpus.backend_name,
                provenance={
                    "provider": "none",
                    "note": "Regulation questions are served by the legacy compliance/RAG surface; /v1/ask does not mix regulation verdicts with telemetry answers.",
                },
            )

        if question_type is QuestionType.TELEMETRY_CASE:
            if not has_laps:
                raise ValueError("lap_a_id and lap_b_id are required for a telemetry-case question")
            analysis = self.learning.analyze(
                request.lap_a_id,
                request.lap_b_id,
                question=request.question,
                level=request.level,
            )
            hits = self.corpus.search(_telemetry_query(request.question), top_k=request.top_k)
            return self._answer(request, question_type, hits, analysis)

        hits = self.corpus.search(request.question, top_k=request.top_k) if question_type is QuestionType.THEORY else []
        return self._answer(request, question_type, hits, None)

    def _answer(self, request: AskRequest, question_type: QuestionType, hits, analysis) -> GroundedAnswer:
        if self.provider is not None and self.provider.is_configured():
            return build_llm_answer(
                self.provider,
                request.question,
                request.level,
                question_type,
                hits,
                analysis,
                retrieval_backend=self.corpus.backend_name,
            )
        return build_deterministic_answer(
            request.question,
            request.level,
            question_type,
            hits,
            analysis,
            generation_status=GenerationStatus.UNAVAILABLE,
            retrieval_backend=self.corpus.backend_name,
        )
