"""One-off migration: align rules.json with the review lifecycle.

Rules move from the legacy ``validated`` status to ``reviewed``. They are NOT
marked active because human sign-off has not happened. No thresholds or
conditions are changed.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "knowledge_base" / "rules" / "rules.json"

TEST_IDS = {
    "wheelbase_compliance": ["TC01", "TC06", "TC11"],
    "cockpit_position_compliance": ["TC02", "TC07", "TC12"],
    "half_width_compliance": ["TC03", "TC08"],
    "minimum_mass_compliance": ["TC04", "TC09", "TC13", "TC14", "TC16", "TC17", "TC18"],
    "mass_distribution_compliance": ["TC05", "TC10", "TC15"],
    "base_minimum_mass": ["TC04", "TC09", "TC13", "TC14", "TC16", "TC17", "TC18"],
    "heat_hazard_mass_increase": ["TC04", "TC09", "TC13", "TC14", "TC16", "TC17", "TC18"],
    "minimum_mass": ["TC04", "TC09", "TC13", "TC14", "TC16", "TC17", "TC18"],
    "minimum_mass_excluding_heat_hazard": ["TC05", "TC10", "TC15"],
}


def main() -> int:
    data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    data.setdefault("scope", "Selected reviewed provisions only; not a whole-car compliance certification.")
    data.setdefault("subdomain", "Fundamental dimensions and mass (C2.3 and C4)")

    for rule in data["rules"]:
        rule["status"] = "reviewed"
        validation = dict(rule.get("validation") or {})
        validation["reviewer"] = "internal_agent_check"
        validation["reviewed_at"] = "2026-11-17"
        validation["human_approved"] = False
        validation["test_case_ids"] = TEST_IDS.get(rule["conclusion"]["goal"], [])
        validation.setdefault(
            "notes",
            "Source text, operator and unit checked against the supplied FIA PDF. Human sign-off pending.",
        )
        rule["validation"] = validation

    RULES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {len(data['rules'])} rules to status=reviewed in {RULES_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
