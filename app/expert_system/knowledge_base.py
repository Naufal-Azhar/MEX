"""Knowledge base: reviewed/active rules, source metadata, and fact loading."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from app.schemas.facts import Fact, FactOrigin, FactStore
from app.schemas.rules import Rule, RuleSet, RuleStatus

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES_PATH = ROOT / "knowledge_base" / "rules" / "rules.json"
DEFAULT_FACTS_PATH = ROOT / "knowledge_base" / "facts" / "sample_facts.json"
DEFAULT_MANIFEST_PATH = ROOT / "knowledge_base" / "document_manifest.json"


def _allow_reviewed_default() -> bool:
    value = os.getenv("ALLOW_REVIEWED_RULES", "true").strip().lower()
    return value in ("1", "true", "yes", "on")


class KnowledgeBase:
    """Holds the rule set and exposes only runnable rules to the engine.

    ``active`` rules always run. ``reviewed`` rules run only when demo mode is
    enabled (the default until a human reviewer approves them), and the report
    must carry a validation warning.
    """

    def __init__(self, rule_set: RuleSet, allow_reviewed: bool | None = None) -> None:
        self.rule_set = rule_set
        self.allow_reviewed = _allow_reviewed_default() if allow_reviewed is None else allow_reviewed
        self._by_goal: dict[str, list[Rule]] = {}

        for rule in rule_set.rules:
            if rule.is_runnable(self.allow_reviewed):
                self._by_goal.setdefault(rule.goal, []).append(rule)

        for goal, rules in self._by_goal.items():
            kinds = {rule.conclusion.kind for rule in rules}
            if len(kinds) > 1:
                raise ValueError(f"goal '{goal}' mixes boolean and value rules: {sorted(kinds)}")
            rules.sort(key=lambda rule: 0 if rule.status is RuleStatus.ACTIVE else 1)

    @classmethod
    def from_file(cls, path: Path | str = DEFAULT_RULES_PATH, allow_reviewed: bool | None = None) -> "KnowledgeBase":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(RuleSet.model_validate(data), allow_reviewed=allow_reviewed)

    @classmethod
    def from_dict(cls, data: dict[str, Any], allow_reviewed: bool | None = None) -> "KnowledgeBase":
        return cls(RuleSet.model_validate(data), allow_reviewed=allow_reviewed)

    @property
    def document_id(self) -> str:
        return self.rule_set.document_id

    @property
    def regulation(self) -> str:
        return self.rule_set.regulation

    @property
    def regulation_issue(self) -> str:
        return self.rule_set.regulation_issue

    @property
    def scope(self) -> str:
        return self.rule_set.scope or (
            "Selected reviewed provisions only; not a whole-car compliance certification."
        )

    @property
    def subdomain(self) -> str | None:
        return self.rule_set.subdomain

    @property
    def demo_mode(self) -> bool:
        return any(rule.status is RuleStatus.REVIEWED for rule in self.runnable_rules())

    def rules_for_goal(self, goal: str) -> list[Rule]:
        return list(self._by_goal.get(goal, []))

    def has_goal(self, goal: str) -> bool:
        return goal in self._by_goal

    def goals(self) -> list[str]:
        return sorted(self._by_goal)

    def get_rule(self, rule_id: str) -> Rule | None:
        for rule in self.rule_set.rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def runnable_rules(self) -> list[Rule]:
        return [rule for rule in self.rule_set.rules if rule.is_runnable(self.allow_reviewed)]

    def active_rules(self) -> list[Rule]:
        return [rule for rule in self.rule_set.rules if rule.status is RuleStatus.ACTIVE]

    def reviewed_rules(self) -> list[Rule]:
        return [rule for rule in self.rule_set.rules if rule.status is RuleStatus.REVIEWED]

    def draft_rules(self) -> list[Rule]:
        return [rule for rule in self.rule_set.rules if rule.status is RuleStatus.DRAFT]

    def deprecated_rules(self) -> list[Rule]:
        return [rule for rule in self.rule_set.rules if rule.status is RuleStatus.DEPRECATED]

    # Backwards-compatible alias used by older call sites.
    def validated_rules(self) -> list[Rule]:
        return self.runnable_rules()

    def pending_rules(self) -> list[Rule]:
        return self.draft_rules()

    def all_rules(self) -> list[Rule]:
        return list(self.rule_set.rules)

    def regulation_metadata(self) -> dict[str, str]:
        metadata = {
            "regulation": self.regulation,
            "issue": self.regulation_issue,
            "document_id": self.document_id,
            "scope": self.scope,
        }
        if self.subdomain:
            metadata["subdomain"] = self.subdomain
        return metadata


def default_facts_path() -> Path:
    return DEFAULT_FACTS_PATH


def load_facts_from_file(path: Path | str = DEFAULT_FACTS_PATH) -> FactStore:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data["facts"] if isinstance(data, dict) else data
    store = FactStore()
    for item in items:
        store.add(
            Fact(
                name=item["name"],
                value=item["value"],
                unit=item.get("unit"),
                origin=FactOrigin(item.get("origin", "user")),
                note=item.get("note"),
            )
        )
    return store


def load_document_manifest(path: Path | str = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))
