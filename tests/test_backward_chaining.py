from app.expert_system.backward_chaining import BackwardChainingEngine
from app.expert_system.knowledge_base import KnowledgeBase
from app.expert_system.service import ComplianceService
from app.schemas.results import ExternalStatus, TruthValue
from app.schemas.rules import (
    Conclusion,
    Condition,
    Operand,
    Operator,
    Rule,
    RuleSet,
    RuleSource,
    RuleStatus,
    RuleValidation,
)

VALIDATION = RuleValidation(
    verified_against="test",
    verified_on="2026-11-17",
    method="test",
    reviewer="test_reviewer",
    reviewed_at="2026-11-17",
    human_approved=True,
)


def _source(article="C2.3.3") -> RuleSource:
    return RuleSource(document_id="doc", document="FIA", issue="21", article=article, page=1, quote="Test quote.")


def _rule(rule_id, goal, conditions=None, applies_if=None, kind="boolean", value=True, expr=None) -> Rule:
    conclusion = Conclusion(goal=goal, kind=kind, value=value if kind == "boolean" else value, expr=expr)
    return Rule(
        rule_id=rule_id,
        name=rule_id,
        source=_source(),
        applies_if=applies_if or [],
        conditions=conditions or [],
        conclusion=conclusion,
        status=RuleStatus.REVIEWED,
        validation=VALIDATION,
    )


def _rule_set(rules) -> RuleSet:
    return RuleSet(
        version="test",
        regulation="Test",
        regulation_issue="21",
        document_id="doc",
        rules=rules,
    )


def test_wheelbase_boundaries(service, facts_factory):
    at_limit = service.check("wheelbase_compliance", facts_factory(wheelbase=(3400, "mm")))
    assert at_limit.status == ExternalStatus.SATISFIED
    assert at_limit.source.article == "C2.3.3"

    above = service.check("wheelbase_compliance", facts_factory(wheelbase=(3400.5, "mm")))
    assert above.status == ExternalStatus.VIOLATED


def test_missing_fact_is_unknown_not_false(service, facts_factory):
    report = service.check("wheelbase_compliance", facts_factory())
    assert report.status == ExternalStatus.INSUFFICIENT_DATA
    assert report.internal_status == TruthValue.UNKNOWN
    assert [item.fact for item in report.missing_facts] == ["wheelbase"]


def test_minimum_mass_resolves_subgoal(service, facts_factory):
    facts = facts_factory(
        car_mass=(796, "kg"),
        nominal_tyre_mass=(70, "kg"),
        session_type="Q",
        session_category="TTCS",
        heat_hazard_declared=False,
        competition_heat_hazard_declared=False,
    )
    report = service.check("minimum_mass_compliance", facts)
    assert report.status == ExternalStatus.SATISFIED
    assert report.trace is not None
    child = next(child for child in report.trace.children if child.goal == "minimum_mass")
    assert child.value == 796.0
    assert child.status == TruthValue.TRUE

    engine = BackwardChainingEngine(service.kb, facts)
    assert engine.prove("minimum_mass").value == 796.0


def test_heat_hazard_increases_minimum_mass(service, facts_factory):
    declared = facts_factory(
        car_mass=(800, "kg"),
        nominal_tyre_mass=(70, "kg"),
        session_type="Q",
        session_category="TTCS",
        heat_hazard_declared=True,
        competition_heat_hazard_declared=True,
    )
    assert service.check("minimum_mass_compliance", declared).status == ExternalStatus.VIOLATED

    competition_only = facts_factory(
        car_mass=(800, "kg"),
        nominal_tyre_mass=(70, "kg"),
        session_type="Q",
        session_category="TTCS",
        heat_hazard_declared=False,
        competition_heat_hazard_declared=True,
    )
    assert service.check("minimum_mass_compliance", competition_only).status == ExternalStatus.SATISFIED


def test_missing_nominal_tyre_mass_propagates_from_subgoal(service, facts_factory):
    facts = facts_factory(
        car_mass=(800, "kg"),
        session_type="Q",
        session_category="TTCS",
        heat_hazard_declared=False,
        competition_heat_hazard_declared=False,
    )
    report = service.check("minimum_mass_compliance", facts)
    assert report.status == ExternalStatus.INSUFFICIENT_DATA
    assert "nominal_tyre_mass" in {item.fact for item in report.missing_facts}


def test_mass_distribution_not_applicable_outside_qualifying(service, facts_factory):
    facts = facts_factory(
        session_type="R",
        nominal_tyre_mass=(70, "kg"),
        front_axle_mass=(500, "kg"),
        rear_axle_mass=(500, "kg"),
    )
    report = service.check("mass_distribution_compliance", facts)
    assert report.status == ExternalStatus.NOT_APPLICABLE
    assert report.internal_status == TruthValue.UNKNOWN
    assert report.applicability_conditions
    assert report.applicability_conditions[0].status == TruthValue.FALSE


def test_cycle_detection_returns_unknown():
    rules = [
        _rule("A", "value_a", kind="value", value=None, expr={"op": "add", "args": [{"goal_value": "value_b"}, {"const": 0}]}),
        _rule("B", "value_b", kind="value", value=None, expr={"op": "add", "args": [{"goal_value": "value_a"}, {"const": 0}]}),
    ]
    kb = KnowledgeBase(_rule_set(rules))
    from app.schemas.facts import FactStore

    engine = BackwardChainingEngine(kb, FactStore())
    result = engine.prove("value_a")
    assert result.status == TruthValue.UNKNOWN
    assert any("Cycle" in note for note in result.notes)


def test_conflicting_rules_are_flagged():
    always_true = _rule(
        "TRUE-RULE",
        "conflict_goal",
        conditions=[Condition(left=Operand(fact="x"), operator=Operator.GE, right=Operand(const=0))],
    )
    always_false = _rule(
        "FALSE-RULE",
        "conflict_goal",
        conditions=[Condition(left=Operand(fact="x"), operator=Operator.LT, right=Operand(const=0))],
    )
    kb = KnowledgeBase(_rule_set([always_true, always_false]))
    service = ComplianceService(kb, verify_sources=False)
    from app.schemas.facts import Fact, FactStore

    store = FactStore()
    store.add(Fact(name="x", value=5))
    report = service.check("conflict_goal", store)
    assert report.status == ExternalStatus.VIOLATED
    assert report.conflict is True
