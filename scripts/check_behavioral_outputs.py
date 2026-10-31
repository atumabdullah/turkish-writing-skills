#!/usr/bin/env python3
"""Check deterministic invariants in the synthetic behavioral smoke test."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "tests" / "behavioral-cases.json"
OUTPUTS_PATH = ROOT / "tests" / "behavioral-outputs.json"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    cases_data = load_json(CASES_PATH)
    outputs_data = load_json(OUTPUTS_PATH)
    package_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    failures: list[str] = []

    if not isinstance(cases_data, dict) or not isinstance(cases_data.get("cases"), list):
        print("FAIL: behavioral-cases.json has an invalid schema")
        return 1
    if not isinstance(outputs_data, dict) or not isinstance(outputs_data.get("outputs"), list):
        print("FAIL: behavioral-outputs.json has an invalid schema")
        return 1
    if outputs_data.get("skill_version") != package_version:
        failures.append("behavioral output version does not match VERSION")

    cases = {case["id"]: case for case in cases_data["cases"]}
    outputs = {output["id"]: output for output in outputs_data["outputs"]}
    if len(cases) != len(cases_data["cases"]):
        failures.append("behavioral cases contain duplicate ids")
    if len(outputs) != len(outputs_data["outputs"]):
        failures.append("behavioral outputs contain duplicate ids")
    if set(cases) != set(outputs):
        failures.append("case and output ids do not match")

    passed = 0
    for case_id, case in cases.items():
        if case_id not in outputs:
            continue
        source = case["source"]
        revision = outputs[case_id]["revision"]
        case_failures: list[str] = []

        if source == revision:
            case_failures.append("revision is identical to source")
        for token in case["preserve"]:
            if token not in source:
                case_failures.append(f"preservation token absent from source: {token!r}")
            if token not in revision:
                case_failures.append(f"preservation token lost: {token!r}")
        for token in case["required_output_tokens"]:
            if token not in revision:
                case_failures.append(f"required output token missing: {token!r}")
        for token in case["forbidden_output_tokens"]:
            if token in revision:
                case_failures.append(f"forbidden output token present: {token!r}")

        source_numbers = Counter(re.findall(r"\d+", source))
        revision_numbers = Counter(re.findall(r"\d+", revision))
        if source_numbers != revision_numbers:
            case_failures.append(
                f"numeric tokens changed: source={dict(source_numbers)}, "
                f"revision={dict(revision_numbers)}"
            )

        if case_failures:
            failures.extend(f"{case_id}: {message}" for message in case_failures)
        else:
            passed += 1

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(f"PASS: {passed} behavioral cases satisfied all deterministic invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
