"""Split the labelled cases into development and held-out sets.

The split is deterministic and preserves TRUE/FALSE/UNKNOWN balance as closely as
possible. Existing case facts and expected results are not modified.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "datasets"

HELDOUT = {"TC03", "TC07", "TC12", "TC14", "TC17", "TC18"}


def main() -> int:
    source = json.loads((DATASETS / "test_cases.json").read_text(encoding="utf-8"))
    development = []
    heldout = []

    for case in source["cases"]:
        case = dict(case)
        case["split"] = "heldout" if case["case_id"] in HELDOUT else "development"
        (heldout if case["split"] == "heldout" else development).append(case)

    base_meta = {
        "dataset_version": source.get("dataset_version", "1.0.0"),
        "description": source.get("description", ""),
        "regulation": source.get("regulation"),
        "issue": source.get("issue"),
    }

    (DATASETS / "development_cases.json").write_text(
        json.dumps({**base_meta, "split": "development", "cases": development}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (DATASETS / "heldout_cases.json").write_text(
        json.dumps({**base_meta, "split": "heldout", "cases": heldout}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    # Keep the combined file as a generated convenience artifact.
    source["cases"] = development + heldout
    (DATASETS / "test_cases.json").write_text(
        json.dumps(source, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"development={len(development)} heldout={len(heldout)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
