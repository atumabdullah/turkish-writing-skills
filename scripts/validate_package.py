#!/usr/bin/env python3
"""Validate package structure without third-party dependencies."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "turkish-clear-writing"
SKILL_MD = SKILL_DIR / "SKILL.md"


def fail(message: str) -> None:
    raise ValueError(message)


def validate() -> None:
    required = [
        ROOT / "README.md",
        ROOT / "LICENSE",
        ROOT / "VERSION",
        ROOT / "tests" / "cases.json",
        ROOT / "tests" / "behavioral-cases.json",
        ROOT / "tests" / "behavioral-outputs.json",
        ROOT / "tests" / "behavioral-report.md",
        ROOT / "scripts" / "check_behavioral_outputs.py",
        SKILL_MD,
        SKILL_DIR / "agents" / "openai.yaml",
        SKILL_DIR / "references" / "turkish-guidelines.md",
        SKILL_DIR / "references" / "tdk-writing-and-punctuation.md",
        SKILL_DIR / "references" / "academic-article-workflow.md",
        SKILL_DIR / "references" / "research-ethics-and-reporting.md",
        SKILL_DIR / "references" / "evidence-and-limitations.md",
        SKILL_DIR / "references" / "examples.md",
        SKILL_DIR / "references" / "evaluation.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")

    text = SKILL_MD.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        fail("SKILL.md has no valid frontmatter fence")

    frontmatter = match.group(1)
    name_match = re.search(r"^name:\s*([^\n]+)$", frontmatter, re.MULTILINE)
    description_match = re.search(r"^description:\s*([^\n]+)$", frontmatter, re.MULTILINE)
    version_match = re.search(r'^\s+version:\s*"([^"]+)"$', frontmatter, re.MULTILINE)
    if not name_match or name_match.group(1).strip() != "turkish-clear-writing":
        fail("frontmatter name is missing or invalid")
    if not description_match or len(description_match.group(1).strip()) > 1024:
        fail("frontmatter description is missing or too long")
    if not version_match:
        fail("metadata.version is missing")

    package_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if version_match.group(1) != package_version:
        fail("SKILL.md and VERSION disagree")

    if re.search(r"TODO|PLACEHOLDER|TBD", text, re.IGNORECASE):
        fail("SKILL.md contains an unfinished placeholder")

    for target in re.findall(r"\]\((references/[^)]+\.md)\)", text):
        if not (SKILL_DIR / target).is_file():
            fail(f"broken local reference: {target}")

    cases = json.loads((ROOT / "tests" / "cases.json").read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        fail("tests/cases.json must contain a non-empty list")

    behavioral = json.loads(
        (ROOT / "tests" / "behavioral-cases.json").read_text(encoding="utf-8")
    )
    if not isinstance(behavioral, dict) or not behavioral.get("cases"):
        fail("tests/behavioral-cases.json must contain non-empty cases")


def main() -> int:
    try:
        validate()
    except (ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: package structure, metadata, references, version, and test data are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
