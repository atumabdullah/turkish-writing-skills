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
        # Codex P2: a non-finite optional Levene diagnostic must not abort
        # otherwise valid one-way analyses or strict JSON serialization.
        levene_file = root / "undefined_levene.csv"
        levene_file.write_text(
            "unit,group,biomass\\nA1,A,1\\nA2,A,3\\nB1,B,5\\nB2,B,7\n",
            encoding="utf-8",
        )
        for name in ("anova", "welch", "kruskal"):
            out = root / ("undefined_levene_" + name)
            run = execute(
                str(levene_file), "--group", "group", "--value", "biomass",
                "--unit", "unit", "--analysis", name, "--output", str(out)
            )
            assert run.returncode == 0, (name, run.stderr)
            payload = json.loads(
                (out / "results.json").read_text(encoding="utf-8"),
                parse_constant=lambda value: (_ for _ in ()).throw(AssertionError(value))
            )
            assert payload["diagnostics"]["levene_median_p"] is None
            assert any("Levene" in message and "undefined" in message for message in payload["warnings"])
            assert 0 <= payload["inference"]["p"] <= 1
            assert (out / "groups.svg").stat().st_size > 100

        # Codex P2: constant within-group observations may still provide a
        # valid rank comparison when group locations differ.
        distinct_constants = root / "rank_constants.csv"
        distinct_constants.write_text(
            "unit,group,biomass\\nA1,A,1\\nA2,A,1\\nA3,A,1\\nB1,B,2\\nB2,B,2\\nB3,B,2\n",
            encoding="utf-8",
        )
        out = root / "rank_constants_result"
        run = execute(
            str(distinct_constants), "--group", "group", "--value", "biomass",
            "--unit", "unit", "--analysis", "kruskal", "--output", str(out)
        )
        assert run.returncode == 0, run.stderr
        payload = json.loads((out / "results.json").read_text(encoding="utf-8"))
        assert payload["inference"]["test"] == "Kruskal-Wallis"
        assert 0 < payload["inference"]["H"] and 0 <= payload["inference"]["p"] <= 1
        assert payload["diagnostics"]["levene_median_p"] is None
        assert (out / "groups.png").stat().st_size > 100

        # True degeneracy: all pooled ranks identical must remain rejected.
        identical = root / "rank_all_identical.csv"
        identical.write_text(
            "unit,group,biomass\\nA1,A,1\\nA2,A,1\\nB1,B,1\\nB2,B,1\n",
            encoding="utf-8",
        )
        run = execute(
            str(identical), "--group", "group", "--value", "biomass",
            "--unit", "unit", "--analysis", "kruskal", "--output", str(root / "rank_invalid")
        )
        assert run.returncode != 0 and "pooled observations are identical" in run.stderr

    print("PASS: independent-group statistics, edge cases and publication figure export")


if __name__ == "__main__":
    test()
