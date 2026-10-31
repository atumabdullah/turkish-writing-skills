#!/usr/bin/env python3
"""Run minimal preservation checks on the bundled before/after examples."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "tests" / "cases.json"


def main() -> int:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []

    for case in cases:
        name = case["name"]
        source = case["source"]
        revision = case["revision"]

        if source == revision:
            failures.append(f"{name}: revision is identical to source")

        for token in case["must_preserve"]:
            if token not in source:
                failures.append(f"{name}: test token is absent from source: {token!r}")
            if token not in revision:
                failures.append(f"{name}: required token was lost: {token!r}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(f"PASS: {len(cases)} example cases preserved all required invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
