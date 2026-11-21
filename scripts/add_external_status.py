"""Add external status expectations to datasets/expected_results.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "datasets" / "expected_results.json"

MAP = {"TRUE": "SATISFIED", "FALSE": "VIOLATED", "UNKNOWN": "INSUFFICIENT_DATA"}


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    for item in data["results"]:
        external = MAP[item["expected_status"]]
        if item["case_id"] == "TC15":
            external = "NOT_APPLICABLE"
        item["expected_external_status"] = external
    PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {len(data['results'])} expected results")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
