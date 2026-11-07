#!/usr/bin/env python3
"""Smoke tests for the optional statistical figure script (synthetic data only)."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/turkish-clear-writing/scripts/analyze_and_plot.py"


def execute(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *arguments], capture_output=True, text=True)


def test() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        input_file = root / "synthetic.csv"
        input_file.write_text("unit,group,biomass\n" + "\n".join(
            f"{label}{i},{label},{v}" for label, vals in (("A", [1, 2, 3, 4]), ("B", [5, 6, 7, 8]), ("C", [3, 4, 5, 6]))
            for i, v in enumerate(vals)), encoding="utf-8")
        args = [str(input_file), "--group", "group", "--value", "biomass", "--unit", "unit"]
        for test_name in ("descriptive", "anova", "welch", "kruskal"):
            out = root / test_name
            execution = execute(*args, "--analysis", test_name, "--output", str(out))
            assert execution.returncode == 0, execution.stderr
            report = json.loads((out / "results.json").read_text(encoding="utf-8"))
            assert len(report["groups"]) == 3
            assert all((out / f"groups.{ext}").stat().st_size > 100 for ext in ("png", "pdf", "svg"))
            if test_name != "descriptive":
                assert 0 <= report["inference"]["p"] <= 1
        invalid = execute(str(input_file), "--group", "group", "--value", "biomass", "--analysis", "anova")
        assert invalid.returncode != 0 and "--unit" in invalid.stderr
        duplicate = root / "duplicate.csv"
        duplicate.write_text("unit,group,biomass\na,A,1\na,A,2\nb,B,4\nc,B,5\n", encoding="utf-8")
        invalid = execute(str(duplicate), "--group", "group", "--value", "biomass", "--unit", "unit", "--analysis", "anova")
        assert invalid.returncode != 0 and "repeat" in invalid.stderr
    print("PASS: independent-group statistics and publication figure export")


if __name__ == "__main__":
    test()
