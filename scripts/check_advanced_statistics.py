#!/usr/bin/env python3
"""Deterministic offline regression tests for v0.9.0 advanced statistical inference."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/turkish-clear-writing/scripts/advanced_statistics.py"


def invoke(source: Path, output: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(source), "--output", str(output), *args],
        capture_output=True, text=True, timeout=80
    )


def positive_result(source: Path, root: Path, name: str, *args: str) -> dict:
    output = root / name
    call = invoke(source, output, *args)
    assert call.returncode == 0, (name, call.stdout, call.stderr)
    report = json.loads((output / "results.json").read_text(encoding="utf-8"),
                        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    assert report["analysis"] == name, name
    assert len(report["input_sha256"]) == 64
    assert report["files"] == ["table.csv", "results.json", "results.md"]
    assert (output / "table.csv").stat().st_size > 25
    assert (output / "results.md").stat().st_size > 80
    assert "RESEARCHER MUST VERIFY" in report["study_design"]
    assert "software" in report
    return report


def fails(source: Path, root: Path, tag: str, expected: str, *args: str) -> None:
    call = invoke(source, root / ("invalid_" + tag), *args)
    assert call.returncode != 0 and expected in call.stderr, (tag, call.stdout, call.stderr)


def test() -> None:
    rng = np.random.default_rng(2026)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        records = []
        for a, source in enumerate(("Green ZnO", "Chemical ZnO")):
            for dose in (0, 50, 100):
                for replicate in range(5):
                    measured = (7.7 + a * 0.8 + dose * 0.012
                                + a * dose * 0.018 + rng.normal(0, 0.35))
                    records.append({
                        "pot_id": f"{a}-{dose}-{replicate}", "source": source,
                        "dose": dose, "biomass": measured,
                        "spad": 32 + dose * .025 + a + rng.normal(0, 1.4),
                        "tissue_Zn": 45 + dose * 0.8 + a * 4 + rng.normal(0, 7),
                    })
        factor = pd.DataFrame(records)
        factor_path = root / "factorial.xlsx"
        factor.to_excel(factor_path, index=False)
        fit = positive_result(factor_path, root, "factorial", "--analysis", "factorial",
                              "--unit", "pot_id", "--value", "biomass",
                              "--factor-a", "source", "--factor-b", "dose")
        effects = fit["model"]["effects"]
        assert len(effects) == 3, effects
        assert any(":" in effect["term"] for effect in effects)
        assert all(0 <= effect["p"] <= 1 for effect in effects)
        assert len(fit["model"]["cells"]) == 6
        assert all(cell["n"] == 5 for cell in fit["model"]["cells"])
        assert fit["model"]["anova_type"] == "III"

        covariates = rng.normal(size=(50, 2))
        reg = pd.DataFrame({
            "sample_id": [f"r{i}" for i in range(50)],
            "x_one": covariates[:, 0], "x_two": covariates[:, 1],
            "response": 10 + 2 * covariates[:, 0] - .75 * covariates[:, 1]
                        + rng.normal(0, .8, 50)
        })
        reg_path = root / "regression.csv"
        reg.to_csv(reg_path, index=False)
        fitted = positive_result(reg_path, root, "regression", "--analysis", "regression",
                                 "--unit", "sample_id", "--value", "response",
                                 "--predictors", "x_one,x_two")
        assert fitted["model"]["covariance"] == "HC3"
        assert fitted["model"]["r_squared"] > 0.65
        coefficients = fitted["model"]["coefficients"]
        assert len(coefficients) == 3
        assert all(coef["p"] is not None and 0 <= coef["p"] <= 1 for coef in coefficients)
        assert all(coef["ci95_lower"] <= coef["estimate"] <= coef["ci95_upper"] for coef in coefficients)

        reg_missing = reg.copy()
        reg_missing.loc[0, "x_one"] = np.nan
        missing_path = root / "corr_with_missing.csv"
        reg_missing.to_csv(missing_path, index=False)
        corr = positive_result(missing_path, root, "correlation", "--analysis", "correlation",
                               "--unit", "sample_id", "--columns", "x_one,x_two,response",
                               "--method", "spearman", "--adjust", "holm")
        assert corr["model"]["n_adjusted_tests"] == 3
        assert sorted(x["n_pairs"] for x in corr["model"]["comparisons"]) == [49, 49, 50]
        assert all(0 <= x["p_adjusted"] <= 1 for x in corr["model"]["comparisons"])
        assert any("pairwise" in w for w in corr["warnings"])

        long = []
        for index in range(16):
            group = "A" if index < 8 else "B"
            intercept = rng.normal(0, 2.5)
            for time in (0, 1, 2, 3, 4):
                long.append({
                    "subject": f"s{index:02d}", "treatment": group, "day": time,
                    "spad": 35 + intercept + .95 * time
                            + (4.0 if group == "B" else 0)
                            + (.5 * time if group == "B" else 0)
                            + rng.normal(0, .55)
                })
        repeated = pd.DataFrame(long)
        longitudinal_path = root / "repeated.xlsx"
        repeated.to_excel(longitudinal_path, index=False)
        mixed = positive_result(longitudinal_path, root, "mixed", "--analysis", "mixed",
                                "--unit", "subject", "--time", "day", "--value", "spad",
                                "--group", "treatment", "--interaction")
        assert mixed["model"]["converged"] is True
        assert mixed["model"]["units"] == 16
        assert mixed["model"]["time_by_group_interaction"] is True
        assert mixed["model"]["subject_intercept_variance"] >= 0
        assert len(mixed["model"]["fixed_effects"]) == 4

        # Explicit scientific design violations must fail, not silently fall back.
        fails(factor_path, root, "missingfactor", "--factor-b",
              "--analysis", "factorial", "--unit", "pot_id",
              "--value", "biomass", "--factor-a", "source")
        missing_cell = factor.loc[~((factor["source"] == "Green ZnO") & (factor["dose"] == 100))]
        missing_cell_path = root / "missing_cell.csv"
        missing_cell.to_csv(missing_cell_path, index=False)
        fails(missing_cell_path, root, "missingcell", "Incomplete factorial cells",
              "--analysis", "factorial", "--unit", "pot_id", "--value", "biomass",
              "--factor-a", "source", "--factor-b", "dose")
        duplicate = factor.copy()
        duplicate.loc[0, "pot_id"] = duplicate.loc[1, "pot_id"]
        duplicate_path = root / "duplicate.csv"
        duplicate.to_csv(duplicate_path, index=False)
        fails(duplicate_path, root, "duplicate", "Duplicate experimental-unit IDs",
              "--analysis", "factorial", "--unit", "pot_id", "--value", "biomass",
              "--factor-a", "source", "--factor-b", "dose")
        collinear = reg.copy()
        collinear["x_two"] = collinear["x_one"] * 2
        collinear_path = root / "collinear.csv"
        collinear.to_csv(collinear_path, index=False)
        fails(collinear_path, root, "collinear", "rank deficient",
              "--analysis", "regression", "--unit", "sample_id",
              "--value", "response", "--predictors", "x_one,x_two")
        repeated_bad = repeated.copy()
        repeated_bad.loc[0, "day"] = repeated_bad.loc[1, "day"]
        repeated_bad_path = root / "duplicate_time.csv"
        repeated_bad.to_csv(repeated_bad_path, index=False)
        fails(repeated_bad_path, root, "duplicate-time", "Duplicate unit-time",
              "--analysis", "mixed", "--unit", "subject",
              "--time", "day", "--value", "spad", "--group", "treatment")
        treatment_switch = repeated.copy()
        treatment_switch.loc[0, "treatment"] = "B"
        treatment_switch_path = root / "treatment_switch.csv"
        treatment_switch.to_csv(treatment_switch_path, index=False)
        fails(treatment_switch_path, root, "group-switch", "must remain constant",
              "--analysis", "mixed", "--unit", "subject", "--time", "day",
              "--value", "spad", "--group", "treatment")
        duplicate_headers = root / "headers.csv"
        duplicate_headers.write_text("unit,x,x,y\nu1,1,2,3\nu2,2,3,4\n", encoding="utf-8")
        fails(duplicate_headers, root, "duplicate-headers", "Duplicate source column headers",
              "--analysis", "correlation", "--unit", "unit", "--columns", "x,y")

        # Undefined correlation: null, no invented p-value.
        with_constant = reg.copy()
        with_constant["constant"] = 4.0
        constant_path = root / "constant.csv"
        with_constant.to_csv(constant_path, index=False)
        constant_report = positive_result(constant_path, root / "constant_output", "correlation",
                                          "--analysis", "correlation", "--unit", "sample_id",
                                          "--columns", "constant,response")
        pair = constant_report["model"]["comparisons"][0]
        assert pair["r"] is None and pair["p_raw"] is None and pair["p_adjusted"] is None
    print("PASS: factorial Type III, Pearson/Spearman, HC3 OLS, mixed effects and design safety")


if __name__ == "__main__":
    test()
