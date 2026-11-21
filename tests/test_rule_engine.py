import pytest

from app.expert_system.rule_engine import RuleEngine, UnitMismatch, convert_unit
from app.schemas.facts import Fact, FactStore
from app.schemas.results import TruthValue
from app.schemas.rules import (
    Conclusion,
    Condition,
    Operator,
    Operand,
    Rule,
    RuleSource,
    RuleStatus,
)


def store(**facts) -> FactStore:
    result = FactStore()
    for name, item in facts.items():
        value, unit = item if isinstance(item, tuple) else (item, None)
        result.add(Fact(name=name, value=value, unit=unit))
    return result


def condition(fact, operator, value, unit=None) -> Condition:
    return Condition(
        left=Operand(fact=fact),
        operator=operator,
        right=Operand(const=value),
        unit=unit,
    )


def test_unit_conversion():
    assert convert_unit(1000, "mm", "m") == 1
    assert convert_unit(2, "kg", "g") == 2000
    with pytest.raises(UnitMismatch):
        convert_unit(1, "mm", "kg")


def test_condition_true_and_false():
    engine = RuleEngine(store(wheelbase=(3400, "mm")))
    assert engine.evaluate_condition(condition("wheelbase", Operator.LE, 3400, "mm")).evaluation.status == TruthValue.TRUE
    assert engine.evaluate_condition(condition("wheelbase", Operator.LT, 3400, "mm")).evaluation.status == TruthValue.FALSE


def test_missing_fact_yields_unknown_with_reported_unit():
    engine = RuleEngine(FactStore())
    outcome = engine.evaluate_condition(condition("wheelbase", Operator.LE, 3400, "mm"))
    assert outcome.evaluation.status == TruthValue.UNKNOWN
    assert outcome.missing[0].fact == "wheelbase"
    assert outcome.missing[0].expected_unit == "mm"


def test_unit_mismatch_is_unknown_not_false():
    engine = RuleEngine(store(wheelbase=(3.4, "kg")))
    outcome = engine.evaluate_condition(condition("wheelbase", Operator.LE, 3400, "mm"))
    assert outcome.evaluation.status == TruthValue.UNKNOWN
    assert "incompatible" in outcome.evaluation.detail.lower()


def test_in_operator_and_boolean_equality():
    engine = RuleEngine(store(session_type="Q", heat_hazard_declared=True))
    in_condition = Condition(
        left=Operand(fact="session_type"),
        operator=Operator.IN,
        right=Operand(const=["SQ", "Q"]),
    )
    assert engine.evaluate_condition(in_condition).evaluation.status == TruthValue.TRUE

    bool_condition = Condition(
        left=Operand(fact="heat_hazard_declared"),
        operator=Operator.EQ,
        right=Operand(const=True),
    )
    assert engine.evaluate_condition(bool_condition).evaluation.status == TruthValue.TRUE


def test_arithmetic_expression():
    engine = RuleEngine(store(wheelbase=(3000, "mm")))
    expr = Operand(expr={"op": "add", "args": [{"fact": "wheelbase"}, {"const": 400}]})
    outcome = engine.evaluate_condition(
        Condition(left=expr, operator=Operator.LE, right=Operand(const=3400), unit="mm")
    )
    assert outcome.evaluation.status == TruthValue.TRUE


def test_no_rounding_of_limit_values():
    # C2.5: limits are compared as written, without rounding.
    engine = RuleEngine(store(wheelbase=(3400.1, "mm")))
    outcome = engine.evaluate_condition(condition("wheelbase", Operator.LE, 3400, "mm"))
    assert outcome.evaluation.status == TruthValue.FALSE


def test_rule_not_applicable_returns_not_applicable():
    rule = Rule(
        rule_id="TEST-NOT-APPLICABLE",
        name="Test rule",
        source=RuleSource(
            document_id="doc", document="FIA", issue="21", article="C4.2", page=59, quote="Test quote."
        ),
        applies_if=[condition("session_type", Operator.IN, ["Q", "SQ"])],
        conditions=[condition("front_axle_mass", Operator.GE, 100, "kg")],
        conclusion=Conclusion(goal="test_goal", kind="boolean", value=True),
        status=RuleStatus.DRAFT,
    )
    evaluation = RuleEngine(store(session_type="R", front_axle_mass=(200, "kg"))).evaluate_rule(rule)
    assert evaluation.applicable is False
    assert evaluation.applicability == TruthValue.FALSE
    assert evaluation.status == TruthValue.UNKNOWN
