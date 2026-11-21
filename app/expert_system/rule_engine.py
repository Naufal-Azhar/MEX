"""Deterministic evaluation of rule conditions.

The engine never guesses: a missing fact or an incompatible unit yields UNKNOWN.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from app.schemas.facts import Fact, MissingFact
from app.schemas.results import ConditionEvaluation, GoalResult, RuleEvaluation, TruthValue
from app.schemas.rules import Condition, Expr, Operand, Operator, Rule
from app.schemas.units import UnitMismatch, convert_unit, is_number


def render_operand(operand: Operand) -> str:
    if operand.const is not None:
        if isinstance(operand.const, list):
            return "[" + ", ".join(str(v) for v in operand.const) + "]"
        return repr(operand.const)
    if operand.fact:
        return operand.fact
    if operand.goal_value:
        return f"value({operand.goal_value})"
    if operand.expr:
        return render_expr(operand.expr)
    return "<invalid operand>"


def render_expr(expr: Expr) -> str:
    symbols = {"add": "+", "sub": "-", "mul": "*", "div": "/"}
    parts = [render_operand(arg) for arg in expr.args]
    return "(" + f" {symbols[expr.op]} ".join(parts) + ")"


@dataclass
class Resolved:
    value: Any = None
    unit: str | None = None
    status: TruthValue = TruthValue.UNKNOWN
    missing: list[MissingFact] = field(default_factory=list)
    note: str | None = None


@dataclass
class ConditionOutcome:
    evaluation: ConditionEvaluation
    missing: list[MissingFact] = field(default_factory=list)


class RuleEngine:
    """Evaluates conditions against a fact store.

    ``subgoal_resolver`` is injected by the backward-chaining engine so that a
    condition referencing ``value(some_goal)`` triggers a real sub-inference.
    """

    def __init__(self, facts: Any) -> None:
        self.facts = facts
        self.subgoal_resolver: Callable[[str], GoalResult] | None = None
        self._accumulators: list[list[GoalResult]] = []

    # ------------------------------------------------------------------ operands
    def resolve_operand(
        self,
        operand: Operand,
        *,
        rule_id: str | None = None,
        article: str | None = None,
        expected_unit: str | None = None,
    ) -> Resolved:
        if operand.const is not None:
            return Resolved(value=operand.const, unit=None, status=TruthValue.TRUE)
        if operand.fact:
            return self._resolve_fact(operand.fact, rule_id, article, expected_unit)
        if operand.goal_value:
            return self._resolve_goal(operand.goal_value)
        if operand.expr:
            return self._resolve_expr(operand.expr, rule_id, article)
        return Resolved(status=TruthValue.UNKNOWN, note="invalid operand")

    def _resolve_fact(
        self, name: str, rule_id: str | None, article: str | None, expected_unit: str | None
    ) -> Resolved:
        fact: Fact | None = self.facts.get(name) if hasattr(self.facts, "get") else None
        if fact is None:
            return Resolved(
                status=TruthValue.UNKNOWN,
                missing=[
                    MissingFact(
                        fact=name,
                        expected_unit=expected_unit,
                        rule_id=rule_id,
                        reason="Fact not provided",
                        source_article=article,
                    )
                ],
                note=f"missing fact '{name}'",
            )
        return Resolved(value=fact.value, unit=fact.unit or expected_unit, status=TruthValue.TRUE)

    def _resolve_goal(self, goal: str) -> Resolved:
        if self.subgoal_resolver is None:
            return Resolved(status=TruthValue.UNKNOWN, note=f"no resolver for subgoal '{goal}'")
        result: GoalResult = self.subgoal_resolver(goal)
        if self._accumulators:
            self._accumulators[-1].append(result)
        if result.status == TruthValue.TRUE and result.value is not None:
            return Resolved(value=result.value, unit=None, status=TruthValue.TRUE)
        return Resolved(
            status=TruthValue.UNKNOWN,
            missing=result.missing_facts,
            note=" | ".join(result.notes) if result.notes else f"subgoal '{goal}' could not be resolved",
        )

    def _resolve_expr(
        self, expr: Expr, rule_id: str | None, article: str | None, expected_unit: str | None = None
    ) -> Resolved:
        resolved = [
            self.resolve_operand(a, rule_id=rule_id, article=article, expected_unit=expected_unit)
            for a in expr.args
        ]
        missing: list[MissingFact] = []
        for item in resolved:
            missing.extend(item.missing)
        if any(item.status != TruthValue.TRUE for item in resolved):
            notes = " | ".join(n for n in (item.note for item in resolved) if n)
            return Resolved(
                status=TruthValue.UNKNOWN,
                missing=missing,
                note=notes or "expression operand unresolved",
            )

        values = [item.value for item in resolved]
        units = [item.unit for item in resolved]
        try:
            if expr.op in ("add", "sub"):
                if not all(is_number(v) for v in values):
                    raise ValueError("add/sub requires numeric operands")
                target_unit = next((u for u in units if u), None)
                numbers = []
                for value, unit in zip(values, units):
                    if unit and target_unit:
                        numbers.append(convert_unit(value, unit, target_unit))
                    else:
                        numbers.append(float(value))
                result = numbers[0]
                for number in numbers[1:]:
                    result = result + number if expr.op == "add" else result - number
                return Resolved(value=result, unit=target_unit, status=TruthValue.TRUE)
            if expr.op == "mul":
                result = 1.0
                for value in values:
                    if not is_number(value):
                        raise ValueError("mul requires numeric operands")
                    result *= float(value)
                distinct = {u for u in units if u}
                unit = distinct.pop() if len(distinct) == 1 else None
                return Resolved(value=result, unit=unit, status=TruthValue.TRUE)
            if expr.op == "div":
                numerator, denominator = values
                if not (is_number(numerator) and is_number(denominator)):
                    raise ValueError("div requires numeric operands")
                if float(denominator) == 0:
                    raise ValueError("division by zero")
                unit = None if units[0] == units[1] else (units[0] if units[1] is None else None)
                return Resolved(value=float(numerator) / float(denominator), unit=unit, status=TruthValue.TRUE)
            raise ValueError(f"unsupported expression op {expr.op}")
        except (ValueError, UnitMismatch) as exc:
            return Resolved(status=TruthValue.UNKNOWN, missing=missing, note=str(exc))

    # ------------------------------------------------------------------ conditions
    def evaluate_condition(
        self, condition: Condition, *, rule_id: str | None = None, article: str | None = None
    ) -> ConditionOutcome:
        left = self.resolve_operand(
            condition.left, rule_id=rule_id, article=article, expected_unit=condition.unit
        )
        right = (
            self.resolve_operand(condition.right, rule_id=rule_id, article=article, expected_unit=condition.unit)
            if condition.right is not None
            else Resolved(value=None, status=TruthValue.TRUE)
        )
        missing = left.missing + right.missing
        expression = condition.render()

        if left.status != TruthValue.TRUE or right.status != TruthValue.TRUE:
            notes = " | ".join(n for n in (left.note, right.note) if n)
            return ConditionOutcome(
                ConditionEvaluation(
                    expression=expression,
                    status=TruthValue.UNKNOWN,
                    left_value=left.value,
                    right_value=right.value,
                    unit=condition.unit or left.unit,
                    detail=notes or "required fact or value is unavailable",
                ),
                missing,
            )

        if left.unit and condition.unit and left.unit != condition.unit and is_number(left.value):
            try:
                left.value = convert_unit(left.value, left.unit, condition.unit)
                left.unit = condition.unit
            except UnitMismatch as exc:
                return ConditionOutcome(
                    ConditionEvaluation(
                        expression=expression,
                        status=TruthValue.UNKNOWN,
                        left_value=left.value,
                        right_value=right.value,
                        unit=left.unit,
                        detail=str(exc),
                    ),
                    missing,
                )

        try:
            status = self._compare(condition, left, right)
            detail = None
        except (ValueError, UnitMismatch) as exc:
            status = TruthValue.UNKNOWN
            detail = str(exc)

        return ConditionOutcome(
            ConditionEvaluation(
                expression=expression,
                status=status,
                left_value=left.value,
                right_value=right.value,
                unit=condition.unit or left.unit,
                detail=detail,
            )
        )

    def _compare(self, condition: Condition, left: Resolved, right: Resolved) -> TruthValue:
        op = condition.operator
        lv, rv = left.value, right.value

        if op in (Operator.IN, Operator.NOT_IN):
            options = rv if isinstance(rv, (list, tuple, set)) else [rv]
            member = lv in options
            return TruthValue.TRUE if (member if op == Operator.IN else not member) else TruthValue.FALSE

        if op in (Operator.EQ, Operator.NE) and (isinstance(lv, (str, bool)) or isinstance(rv, (str, bool))):
            equal = lv == rv
            return TruthValue.TRUE if (equal if op == Operator.EQ else not equal) else TruthValue.FALSE

        if not is_number(lv) or not is_number(rv):
            raise ValueError(f"non-numeric values cannot be ordered: {lv!r} {op.value} {rv!r}")

        if left.unit and right.unit:
            rv = convert_unit(rv, right.unit, left.unit)

        if op == Operator.LE:
            return TruthValue.TRUE if lv <= rv else TruthValue.FALSE
        if op == Operator.LT:
            return TruthValue.TRUE if lv < rv else TruthValue.FALSE
        if op == Operator.GE:
            return TruthValue.TRUE if lv >= rv else TruthValue.FALSE
        if op == Operator.GT:
            return TruthValue.TRUE if lv > rv else TruthValue.FALSE
        if op == Operator.EQ:
            return TruthValue.TRUE if lv == rv else TruthValue.FALSE
        if op == Operator.NE:
            return TruthValue.TRUE if lv != rv else TruthValue.FALSE
        raise ValueError(f"unsupported operator {op.value}")

    # ------------------------------------------------------------------ rules
    def evaluate_rule(self, rule: Rule) -> RuleEvaluation:
        self._accumulators.append([])
        try:
            evaluation = self._evaluate_rule(rule)
        finally:
            collected = self._accumulators.pop()

        seen: set[tuple[str, str, str]] = set()
        for subgoal in collected:
            key = (subgoal.goal, subgoal.status.value, str(subgoal.value))
            if key not in seen:
                seen.add(key)
                evaluation.subgoal_results.append(subgoal)
        return evaluation

    def _evaluate_rule(self, rule: Rule) -> RuleEvaluation:
        evaluation = RuleEvaluation(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            goal=rule.goal,
            status=TruthValue.UNKNOWN,
            rule_status=rule.status,
            source=rule.source,
        )

        applicability: list[ConditionEvaluation] = []
        applicable = True
        unknown_applicability = False
        for condition in rule.applies_if:
            outcome = self.evaluate_condition(condition, rule_id=rule.rule_id, article=rule.source.article)
            applicability.append(outcome.evaluation)
            evaluation.missing_facts.extend(outcome.missing)
            if outcome.evaluation.status == TruthValue.FALSE:
                applicable = False
                break
            if outcome.evaluation.status == TruthValue.UNKNOWN:
                unknown_applicability = True

        evaluation.applicability_conditions = applicability

        if applicable and unknown_applicability:
            evaluation.applicability = TruthValue.UNKNOWN
            evaluation.applicable = False
            evaluation.notes.append("Applicability could not be determined from the given facts.")
            return evaluation

        if not applicable:
            evaluation.applicability = TruthValue.FALSE
            evaluation.applicable = False
            evaluation.notes.append("Rule does not apply to the given context.")
            return evaluation

        evaluation.applicability = TruthValue.TRUE
        evaluation.applicable = True
        for condition in rule.conditions:
            outcome = self.evaluate_condition(condition, rule_id=rule.rule_id, article=rule.source.article)
            evaluation.conditions.append(outcome.evaluation)
            evaluation.missing_facts.extend(outcome.missing)

        statuses = [c.status for c in evaluation.conditions]
        if rule.conclusion.kind == "boolean":
            evaluation.conclusion_value = rule.conclusion.value
            if any(status == TruthValue.FALSE for status in statuses):
                evaluation.status = TruthValue.FALSE
                failed = [c.expression for c in evaluation.conditions if c.status == TruthValue.FALSE]
                evaluation.notes.append(f"Failed condition(s): {'; '.join(failed)}")
            elif any(status == TruthValue.UNKNOWN for status in statuses):
                evaluation.status = TruthValue.UNKNOWN
                evaluation.notes.append("Not all required facts are available.")
            else:
                evaluation.status = TruthValue.TRUE
        else:
            if any(status == TruthValue.FALSE for status in statuses):
                evaluation.status = TruthValue.FALSE
                evaluation.notes.append("A prerequisite condition is false; the value cannot be computed.")
            elif any(status == TruthValue.UNKNOWN for status in statuses):
                evaluation.status = TruthValue.UNKNOWN
                evaluation.notes.append("Not all required facts are available to compute the value.")
            elif rule.conclusion.expr is not None:
                resolved = self._resolve_expr(
                    rule.conclusion.expr, rule.rule_id, rule.source.article, rule.conclusion.unit
                )
                if resolved.status == TruthValue.TRUE:
                    evaluation.status = TruthValue.TRUE
                    evaluation.conclusion_value = resolved.value
                    if rule.conclusion.unit:
                        evaluation.notes.append(f"Computed in {rule.conclusion.unit}.")
                else:
                    evaluation.status = TruthValue.UNKNOWN
                    evaluation.missing_facts.extend(resolved.missing)
                    evaluation.notes.append(resolved.note or "Value could not be computed.")
            else:
                evaluation.status = TruthValue.TRUE
                evaluation.conclusion_value = rule.conclusion.value

        return evaluation
