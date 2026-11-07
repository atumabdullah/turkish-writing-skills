#!/usr/bin/env python3
"""Offline, synthetic regression checks for all five publication figure types."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "turkish-clear-writing" / "scripts" / "plot_scientific.py"
STYLE = ROOT / "skills" / "turkish-clear-writing" / "scripts" / "figure_style.py"


def call(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60)


def verify_figure(path: Path, kind: str) -> dict:
    metadata_path = path / "plot_metadata.json"
    assert metadata_path.is_file(), f"No metadata for {kind}"
    report = json.loads(metadata_path.read_text(encoding="utf-8"),
                        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    assert report["plot_kind"] == kind, report
    assert report["no_inferential_statistics"] is True
    assert len(report["sha256"]) == 64
    assert report["n_input_rows"] == 18
    assert report["files"] == ["figure.png", "figure.pdf", "figure.svg"]
    for extension, expected in (("png", b"\x89PNG"), ("pdf", b"%PDF"), ("svg", b"<?xml")):
        image = path / f"figure.{extension}"
        assert image.stat().st_size > 1000, image
        assert image.read_bytes()[:len(expected)] == expected, image
    assert (path / "figure.png").stat().st_size > 15000
    return report


def test() -> None:
    assert SCRIPT.is_file() and STYLE.is_file()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        rows = []
        for group_index, group in enumerate(("Green ZnO", "Chemical ZnO")):
            for dose in (0, 50, 100):
                for replicate in range(3):
                    rows.append({
                        "pot_id": f"{group_index}-{dose}-{replicate}",
                        "treatment": group,
                        "dose": dose,
                        "biomass": 7.0 + group_index * 0.7 + dose * 0.019 + replicate * 0.17,
                        "spad": 35 + group_index * 1.2 + dose * 0.026 + replicate * 0.9,
                        "enzyme": 14 - dose * 0.02 + group_index * 1.3 + replicate * 0.65,
                    })
        data = pd.DataFrame(rows)
        csv = root / "synthetic.csv"
        xlsx = root / "synthetic.xlsx"
        data.to_csv(csv, index=False)
        data.to_excel(xlsx, index=False)
        kinds = [
            ("box_jitter", csv, ["--group", "treatment", "--y", "biomass"]),
            ("grouped_bar", csv, ["--group", "treatment", "--subgroup", "dose",
                                  "--y", "biomass", "--error", "sem"]),
            ("line_plot", xlsx, ["--x", "dose", "--y", "biomass", "--group", "treatment"]),
            ("correlation_heatmap", csv, ["--columns", "biomass,spad,enzyme", "--method", "spearman"]),
            ("multi_panel", csv, ["--group", "treatment", "--columns", "biomass,spad,enzyme"]),
        ]
        for kind, source, params in kinds:
            destination = root / kind
            run = call(str(source), "--kind", kind, "--unit", "pot_id",
                       "--output", str(destination), "--dpi", "300", *params)
            assert run.returncode == 0, (kind, run.stdout, run.stderr)
            report = verify_figure(destination, kind)
            if kind == "grouped_bar":
                assert len(report["results"]["groups"]) == 6
                assert all(row["n"] == 3 for row in report["results"]["groups"])
            if kind == "line_plot":
                assert any("repeated x values" in x for x in report["warnings"])
            if kind == "correlation_heatmap":
                assert report["results"]["pairwise_n"][0][1] == 18
                assert len(report["results"]["correlations"]) == 3

        def must_fail(data_file: Path, kind: str, text: str, *flags: str) -> None:
            res = call(str(data_file), "--kind", kind, "--output", str(root / "invalid"),
                       *flags)
            assert res.returncode != 0 and text in res.stderr, (res.stdout, res.stderr)

        must_fail(csv, "box_jitter", "requires --group", "--y", "biomass")
        must_fail(csv, "box_jitter", "Missing input columns", "--group", "treatment", "--y", "nonexistent")
        must_fail(csv, "correlation_heatmap", "needs 2–12", "--columns", "biomass")
        must_fail(csv, "multi_panel", "two to four", "--group", "treatment", "--columns", "biomass")
        must_fail(csv, "line_plot", "requires --x", "--y", "biomass")

        # Codex review: pandas mangles duplicate input headers by appending
        # suffixes, which would otherwise silently select the wrong variable.
        duplicate_headers_csv = root / "duplicate_headers.csv"
        duplicate_headers_csv.write_text(
            "pot_id,treatment,biomass,biomass\\nA1,A,1,2\\nB1,B,3,4\\n".replace("\\n", "\n"),
            encoding="utf-8"
        )
        must_fail(duplicate_headers_csv, "box_jitter", "Duplicate column headers",
                  "--group", "treatment", "--y", "biomass")

        duplicate_headers_xlsx = root / "duplicate_headers.xlsx"
        pd.DataFrame(
            [["A1", "A", 1, 2], ["B1", "B", 3, 4]],
            columns=["pot_id", "treatment", "biomass", "biomass"],
        ).to_excel(duplicate_headers_xlsx, index=False)
        must_fail(duplicate_headers_xlsx, "box_jitter", "Duplicate column headers",
                  "--group", "treatment", "--y", "biomass")

        blank_headers_csv = root / "blank_headers.csv"
        blank_headers_csv.write_text("pot_id,,biomass\\nA1,A,1\\n".replace("\\n", "\n"), encoding="utf-8")
        must_fail(blank_headers_csv, "box_jitter", "empty column headers",
                  "--group", "treatment", "--y", "biomass")

        bad = data.copy()
        bad.loc[0, "biomass"] = None
        missing_csv = root / "missing.csv"
        bad.to_csv(missing_csv, index=False)
        must_fail(missing_csv, "box_jitter", "missing values", "--group", "treatment", "--y", "biomass")
        # Heatmaps explicitly use pairwise complete observations, without silent imputation.
        heat = root / "heat_missing"
        res = call(str(missing_csv), "--kind", "correlation_heatmap",
                   "--columns", "biomass,spad,enzyme", "--output", str(heat))
        assert res.returncode == 0, res.stderr
        payload = json.loads((heat / "plot_metadata.json").read_text(encoding="utf-8"))
        assert payload["results"]["pairwise_n"][0][1] == 17
        assert any("pairwise complete" in warning for warning in payload["warnings"])

        bad = data.copy()
        bad.loc[0, "pot_id"] = bad.loc[1, "pot_id"]
        duplicates = root / "duplicates.csv"
        bad.to_csv(duplicates, index=False)
        must_fail(duplicates, "box_jitter", "identifiers must be present and unique",
                  "--group", "treatment", "--y", "biomass", "--unit", "pot_id")

        constant = data.copy()
        constant["biomass"] = 1
        constant["spad"] = 2
        constant.to_csv(root / "constant.csv", index=False)
        must_fail(root / "constant.csv", "correlation_heatmap", "No defined correlations",
                  "--columns", "biomass,spad")

    print("PASS: five publication chart types, CSV/XLSX, vector exports, metadata and invalid inputs")


if __name__ == "__main__":
    test()
