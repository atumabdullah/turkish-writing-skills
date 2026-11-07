#!/usr/bin/env python3
"""Offline integration/regression tests: analyzed data -> linked interaction figures."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "turkish-clear-writing" / "scripts"
ANALYSIS = SKILL / "advanced_statistics.py"
PLOTTER = SKILL / "plot_interactions.py"


def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), *map(str, args)],
                          capture_output=True, text=True, timeout=100)


def succeeds(result: subprocess.CompletedProcess, name: str) -> None:
    assert result.returncode == 0, (name, result.stdout, result.stderr)


def fails(result: subprocess.CompletedProcess, expected: str) -> None:
    assert result.returncode != 0 and expected in result.stderr, (
        result.stdout, result.stderr
    )


def artifacts(folder: Path, kind: str, n_rows: int) -> dict:
    meta = json.loads((folder / "interaction_metadata.json").read_text(encoding="utf-8"),
                      parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    assert meta["kind"] == kind
    assert meta["n_input_rows"] == n_rows
    assert meta["model_results_reused"] is True
    assert meta["new_inferential_tests_performed"] is False
    assert len(meta["data_sha256"]) == len(meta["results_json_sha256"]) == 64
    assert meta["engine_version"] == "0.9.1"
    assert len(meta["files"]) == 6, meta
    for ext, marker in (("png", b"\x89PNG"), ("pdf", b"%PDF"), ("svg", b"<?xml")):
        image = folder / ("figure." + ext)
        assert image.stat().st_size > 1000, image
        assert image.read_bytes().startswith(marker), image
    assert (folder / "interaction_table.csv").stat().st_size > 50
    assert (folder / "interaction_caption.md").stat().st_size > 50
    return meta


def test() -> None:
    rng = np.random.default_rng(3109)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cells = []
        for treatment in ("Green ZnO", "Chemical ZnO"):
            for dose in (0, 50, 100):
                for unit in range(5):
                    biomass = (
                        8 + (treatment == "Green ZnO") * .8 + dose * .018
                        + (treatment == "Green ZnO") * dose * .012
                        + rng.normal(0, .38)
                    )
                    cells.append({
                        "pot_id": f"{treatment}-{dose}-{unit}", "treatment": treatment,
                        "dose": dose, "biomass": biomass,
                    })
        factorial = pd.DataFrame(cells)
        raw = root / "factorial.csv"
        factorial.to_csv(raw, index=False)
        model_folder = root / "factorial_model"
        succeeds(run(ANALYSIS, raw, "--analysis", "factorial",
                     "--unit", "pot_id", "--value", "biomass",
                     "--factor-a", "treatment", "--factor-b", "dose",
                     "--output", model_folder), "factorial analysis")
        report_file = model_folder / "results.json"
        report = json.loads(report_file.read_text(encoding="utf-8"))
        assert report["model"]["response_column"] == "biomass"
        output = root / "factorial_figure"
        succeeds(run(PLOTTER, raw, "--results", report_file, "--output", output),
                 "factorial interaction figure")
        meta = artifacts(output, "factorial_interaction", 30)
        assert "cell means" in meta["caption"]
        table = pd.read_csv(output / "interaction_table.csv")
        assert len(table) == 6
        assert table["n"].eq(5).all()
        expected = float(t.ppf(.975, 4) * table.loc[0, "sd"] / np.sqrt(5))
        assert np.isclose(table.loc[0, "halfwidth"], expected, rtol=1e-7)
        assert meta["error_bar_basis"] == "ci95"

        # Codex P2: doses 0, 1, 1000 must remain at exact scientific
        # coordinates for ALL series, not be shifted by total-axis-span dodge.
        sys.path.insert(0, str(SKILL))
        from plot_interactions import series_x_positions, sorted_categories
        doses, exact_x, is_numeric = sorted_categories(["1000", "1", "0"])
        assert is_numeric and doses == ["0", "1", "1000"]
        assert np.array_equal(exact_x, [0.0, 1.0, 1000.0])
        for series_index in range(7):
            shown = series_x_positions(exact_x, numeric=True, index=series_index, nseries=7)
            assert np.array_equal(shown, exact_x), shown

        # SD and SEM must be visibly distinguishable and not mislabeled as CI.
        sd_output = root / "sd_figure"
        succeeds(run(PLOTTER, raw, "--results", report_file, "--uncertainty", "sd",
                     "--output", sd_output), "factorial SD graphic")
        sd_table = pd.read_csv(sd_output / "interaction_table.csv")
        assert np.allclose(sd_table["halfwidth"], sd_table["sd"])
        assert json.loads((sd_output / "interaction_metadata.json").read_text())[
            "error_bar_basis"
        ] == "sd"

        # A changed data file must never be associated with old model p-values.
        changed = factorial.copy()
        changed.loc[0, "biomass"] += 25.0
        changed_file = root / "changed.csv"
        changed.to_csv(changed_file, index=False)
        fails(run(PLOTTER, changed_file, "--results", report_file,
                  "--output", root / "invalid_sha"), "SHA-256 mismatch")

        # Reject a tampered results.json even if the source fingerprint matches.
        corrupt = json.loads(report_file.read_text(encoding="utf-8"))
        corrupt["model"]["cells"][0]["mean"] += 100
        fake_file = root / "corrupted_results.json"
        fake_file.write_text(json.dumps(corrupt), encoding="utf-8")
        fails(run(PLOTTER, raw, "--results", fake_file,
                  "--output", root / "invalid_summary"), "differs from source data")

        # CSV duplicate headers must be rejected *before* pandas normalizes them.
        duplicate_headers = root / "duplicate_headers.csv"
        duplicate_headers.write_text(
            "pot_id,treatment,dose,biomass,biomass\n"
            "A1,A,0,1,2\nA2,A,0,3,4\n", encoding="utf-8"
        )
        fails(run(PLOTTER, duplicate_headers, "--results", report_file,
                  "--output", root / "invalid_headers"), "Duplicate source column headers")

        records = []
        for subject in range(16):
            treatment = "A" if subject < 8 else "B"
            baseline = rng.normal(0, 2.0)
            for day in (0, 1, 2, 3):
                records.append({
                    "subject_id": f"s{subject}", "treatment": treatment, "day": day,
                    "spad": (35.0 + baseline + day * .85 +
                             (3.5 if treatment == "B" else 0) +
                             (.7 * day if treatment == "B" else 0) +
                             rng.normal(0, .65)),
                })
        repeated = pd.DataFrame(records)
        longitudinal = root / "longitudinal.xlsx"
        repeated.to_excel(longitudinal, index=False)
        mixed_folder = root / "mixed_model"
        succeeds(run(ANALYSIS, longitudinal, "--analysis", "mixed",
                     "--unit", "subject_id", "--time", "day", "--value", "spad",
                     "--group", "treatment", "--interaction", "--output", mixed_folder),
                 "mixed analysis and prediction grid")
        mixed_file = mixed_folder / "results.json"
        model = json.loads(mixed_file.read_text(encoding="utf-8"))["model"]
        assert model["response_column"] == "spad"
        assert model["prediction_basis"].startswith("population fixed effects")
        assert len(model["prediction_grid"]) == 8
        assert all(row["ci95_lower"] <= row["fitted_mean"] <= row["ci95_upper"]
                   for row in model["prediction_grid"])
        outcome = root / "mixed_interaction"
        succeeds(run(PLOTTER, longitudinal, "--results", mixed_file,
                     "--output", outcome), "mixed time-by-treatment figure")
        meta = artifacts(outcome, "mixed_interaction", 64)
        assert "not subject-level prediction intervals" in meta["caption"].lower()
        assert meta["error_bar_basis"] == "fixed effect asymptotic 95% CI"
        assert len(pd.read_csv(outcome / "interaction_table.csv")) == 8
        fails(run(PLOTTER, longitudinal, "--results", mixed_file,
                  "--uncertainty", "sd", "--output", root / "invalid_ci"),
              "Mixed model always uses")

        # No-group longitudinal model is a supported single line (All).
        plain_folder = root / "plain_model"
        succeeds(run(ANALYSIS, longitudinal, "--analysis", "mixed",
                     "--unit", "subject_id", "--time", "day", "--value", "spad",
                     "--output", plain_folder), "mixed no-group model")
        plain_fig = root / "plain_figure"
        succeeds(run(PLOTTER, longitudinal, "--results", plain_folder / "results.json",
                     "--output", plain_fig), "mixed no-group figure")
        assert pd.read_csv(plain_fig / "interaction_table.csv")["group"].eq("All").all()

        # A tampered mixed grid must fail, even if the input SHA matches.
        altered = json.loads(mixed_file.read_text())
        altered["model"]["prediction_grid"][0]["observed_mean"] += 15
        broken = root / "invalid_mixed_results.json"
        broken.write_text(json.dumps(altered), encoding="utf-8")
        fails(run(PLOTTER, longitudinal, "--results", broken,
                  "--output", root / "tampered_mixed"), "observed means differ")

        # An unrelated inferential method may not be plotted as an interaction.
        altered = json.loads(mixed_file.read_text())
        altered["analysis"] = "regression"
        broken.write_text(json.dumps(altered), encoding="utf-8")
        fails(run(PLOTTER, longitudinal, "--results", broken,
                  "--output", root / "invalid_method"), "Only factorial or mixed")

    print("PASS: v0.9.1 factorial and mixed-model interactions, 95% CI, source links and failure cases")


if __name__ == "__main__":
    test()
