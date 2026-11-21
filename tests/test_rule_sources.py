import json

import pytest
from pydantic import ValidationError

from app.config import PROCESSED_DIR, ROOT
from app.expert_system.knowledge_base import KnowledgeBase
from app.expert_system.service import normalize_text
from app.schemas.rules import Conclusion, Rule, RuleSource, RuleStatus, RuleValidation

RULES_PATH = ROOT / "knowledge_base" / "rules" / "rules.json"


def _rules() -> list[dict]:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))["rules"]


def test_all_rule_quotes_exist_on_cited_pages():
    cache: dict[str, dict[int, str]] = {}
    for rule in _rules():
        source = rule["source"]
        document_id = source["document_id"]
        if document_id not in cache:
            document = json.loads((PROCESSED_DIR / f"{document_id}.json").read_text(encoding="utf-8"))
            cache[document_id] = {
                int(page["page"]): normalize_text(page.get("text") or "") for page in document["pages"]
            }
        page = source["page"]
        assert page is not None
        assert normalize_text(source["quote"]) in cache[document_id][page], rule["rule_id"]


def test_rules_are_reviewed_but_not_human_approved():
    for rule in _rules():
        assert rule["status"] == "reviewed"
        validation = rule["validation"]
        assert validation["human_approved"] is False
        assert validation["reviewer"]
        assert validation["reviewed_at"]
        assert validation["test_case_ids"]


def test_active_rule_requires_human_approval():
    with pytest.raises(ValidationError):
        Rule(
            rule_id="ACTIVE-WITHOUT-APPROVAL",
            name="Invalid active rule",
            source=RuleSource(
                document_id="doc",
                document="FIA",
                issue="21",
                article="C2.3.3",
                page=11,
                quote="Test quote.",
            ),
            conclusion=Conclusion(goal="test_goal", kind="boolean", value=True),
            status=RuleStatus.ACTIVE,
            validation=RuleValidation(
                verified_against="test",
                verified_on="2026-11-17",
                method="test",
                reviewer="reviewer",
                reviewed_at="2026-11-17",
                human_approved=False,
            ),
        )


def test_reviewed_rules_can_be_disabled_for_production():
    demo = KnowledgeBase.from_file(allow_reviewed=True)
    strict = KnowledgeBase.from_file(allow_reviewed=False)
    assert len(demo.runnable_rules()) == 13
    assert demo.demo_mode is True
    assert strict.runnable_rules() == []
    assert strict.goals() == []
