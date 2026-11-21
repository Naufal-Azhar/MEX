"""Verify that every rule quote exists on its cited page and write a review log.

This does NOT approve rules. It records automated evidence only.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import PROCESSED_DIR  # noqa: E402
from app.expert_system.service import normalize_text  # noqa: E402

RULES_PATH = ROOT / "knowledge_base" / "rules" / "rules.json"
LOG_PATH = ROOT / "research" / "rule_validation_log.md"


def main() -> int:
    data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    page_cache: dict[str, dict[int, str]] = {}
    rows = []
    failed = 0

    for rule in data["rules"]:
        source = rule["source"]
        document_id = source["document_id"]
        if document_id not in page_cache:
            document = json.loads((PROCESSED_DIR / f"{document_id}.json").read_text(encoding="utf-8"))
            page_cache[document_id] = {
                int(page["page"]): normalize_text(page.get("text") or "") for page in document["pages"]
            }
        page = source.get("page")
        quote = normalize_text(source["quote"])
        found = bool(page and quote in page_cache[document_id].get(int(page), ""))
        failed += int(not found)
        validation = rule.get("validation") or {}
        rows.append(
            {
                "rule_id": rule["rule_id"],
                "goal": rule["conclusion"]["goal"],
                "article": source["article"],
                "page": page,
                "status": rule["status"],
                "quote_check": "PASS" if found else "FAIL",
                "human_approved": validation.get("human_approved", False),
                "reviewer": validation.get("reviewer") or "-",
                "test_cases": ", ".join(validation.get("test_case_ids") or []) or "-",
                "notes": rule.get("notes") or "-",
            }
        )

    lines = [
        "# Rule Validation Log",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Automated source check only. Rules remain `reviewed` and are **not** human-approved. "
        "The system therefore reports them as demo-only.",
        "",
        "| Rule | Goal | Article | Page | Status | Quote check | Human approved | Reviewer | Test cases |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['rule_id']} | {row['goal']} | {row['article']} | {row['page']} | {row['status']} | "
            f"{row['quote_check']} | {row['human_approved']} | {row['reviewer']} | {row['test_cases']} |"
        )

    lines.extend(["", "## Rule notes", ""])
    for row in rows:
        lines.append(f"- `{row['rule_id']}`: {row['notes']}")

    lines.extend(
        [
            "",
            "## Sign-off",
            "",
            "Reviewer: ____________________  Date: ____________",
            "",
            "To activate a rule, set `human_approved: true`, add `reviewer` and `reviewed_at`, "
            "then change its status from `reviewed` to `active`.",
        ]
    )
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Quote checks: {len(rows) - failed}/{len(rows)} passed. Log: {LOG_PATH}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
