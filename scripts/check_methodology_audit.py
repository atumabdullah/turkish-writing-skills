#!/usr/bin/env python3
"""No-network, no-third-party scientific method audit regression tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "skills/turkish-clear-writing/scripts/audit_methodology.py"
EXAMPLE = ROOT / "examples/methodology-factorial-pot.json"
OBSERVATIONAL = ROOT / "examples/methodology-cross-sectional.json"


def execute(path: Path, out: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), str(path),
                           "--output", str(out), *args],
                          capture_output=True, text=True, timeout=30)


def dump(path: Path, content: dict) -> None:
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2),
                    encoding="utf-8")


def result(out: Path) -> dict:
    content = (out / "methodology_report.json").read_text(encoding="utf-8")
    report = json.loads(content,
                        parse_constant=lambda val: (_ for _ in ()).throw(ValueError(val)))
    assert (out / "methodology_report.md").stat().st_size > 50
    assert report["design_verified"] is False
    assert report["quality_score"] is None
    assert report["summary"]["expert_review_required"] is True
    assert len(report["protocol_sha256"]) == 64
    assert len({f["id"] for f in report["findings"]}) == len(report["findings"])
    assert all(f["evidence_paths"] and f["recommended_action"] for f in report["findings"])
    assert all(f["classification"] in (
        "confirmed_inconsistency", "documentation_gap", "review_point")
        for f in report["findings"])
    return report


def ids(report: dict) -> set[str]:
    return {f["id"] for f in report["findings"]}


def check() -> None:
    reference = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    cross = json.loads(OBSERVATIONAL.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        assert reference["sampling"]["independent_units"] == 36
        for fixture, label in ((EXAMPLE, "factorial"), (OBSERVATIONAL, "cross")):
            out = root / label
            run = execute(fixture, out)
            assert run.returncode == 0, (run.stdout, run.stderr)
            report = result(out)
            assert not report["findings"], report["findings"]
            assert report["protocol_sha256"] == hashlib.sha256(
                fixture.read_bytes()).hexdigest()

        def modified(label: str, mutate, *, options=()) -> tuple[dict, subprocess.CompletedProcess]:
            content = copy.deepcopy(reference)
            mutate(content)
            data = root / (label + ".json")
            dump(data, content)
            out = root / (label + "_out")
            run = execute(data, out, *options)
            assert run.returncode in (0, 3), (label, run.stdout, run.stderr)
            return result(out), run

        report, run = modified("factorial_oneway",
                               lambda d: d["analysis"].update(methods=["one_way_anova"]))
        assert "M027" in ids(report)
        report, _ = modified("repeat",
                             lambda d: (
                                 d["sampling"].update(repeated_measurements=True),
                                 d["analysis"].update(methods=["one_way_anova"]),
                                 d["measurements"].update(timepoints=[0, 1, 2])
                             ))
        assert {"M023", "M027"} <= ids(report)
        report, _ = modified("subsamples",
                             lambda d: d["sampling"].pop("subsample_handling"))
        assert "M021" in ids(report)
        report, _ = modified("cluster",
                             lambda d: d["sampling"].update(
                                 clustered=True, unit_of_randomization="batch_id"))
        assert "M020" in ids(report)
        report, _ = modified("uneven",
                             lambda d: d["sampling"].update(independent_units=32))
        assert "M029" in ids(report)
        report, _ = modified("randomized_without_random",
                             lambda d: (
                                 d["study"].update(design="randomized_trial"),
                                 d["procedures"].update(randomization="no")
                             ), options=("--fail-on-high",))
        assert "M010" in ids(report) and report["summary"]["severity_counts"]["high"] >= 1
        assert run.returncode == 3, (
            "fail-on-high exit code", run.args, run.returncode,
            run.stdout, run.stderr, report["summary"]
        )
        report, _ = modified("no_design",
                             lambda d: d["study"].pop("design"))
        assert "M002" in ids(report)
        assert next(x for x in report["findings"] if x["id"] == "M002")[
            "classification"] == "documentation_gap"

        def obs_risk(d: dict) -> None:
            d.clear()
            d.update(copy.deepcopy(cross))
            d["study"]["causal_claim"] = True
            d["analysis"].pop("confounder_plan")
        report, _ = modified("causal", obs_risk)
        assert {"M053", "M054"} <= ids(report)
        report, _ = modified("ethics",
                             lambda d: (
                                 d["ethics"].update(human_participants=True,
                                                    approval="no", consent="unknown")
                             ))
        assert {"M060", "M061"} <= ids(report)
        report, _ = modified("unknown",
                             lambda d: d["procedures"].update(randomization="unknown"))
        assert "M011" in ids(report)
        assert next(x for x in report["findings"] if x["id"] == "M011")[
            "classification"] == "documentation_gap"

        def bad_schema(label: str, fn, substring: str) -> None:
            data = copy.deepcopy(reference)
            fn(data)
            path = root / (label + ".json")
            dump(path, data)
            fail = execute(path, root / ("reject_" + label))
            assert fail.returncode != 0 and substring in fail.stderr, (
                label, fail.stdout, fail.stderr)
            assert not (root / ("reject_" + label) / "methodology_report.json").exists()

        bad_schema("wrong_version", lambda d: d.update(schema_version="2.0"), "schema_version")
        bad_schema("bad_factor", lambda d: d["sampling"].update(factors="not an array"), "factors")
        bad_schema("bad_integer", lambda d: d["sampling"].update(independent_units=True),
                   "independent_units")
        bad_schema("bad_consent", lambda d: d["ethics"].update(consent="maybe"), "consent")
        bad_schema("bad_time", lambda d: d["measurements"].update(timepoints=[1, 1]),
                   "timepoints")
        bad_schema("bad_design", lambda d: d["study"].update(design="not_a_design"), "study.design")

        # The linked reports are fixtures modeled on v0.9.1 metadata; no model
        # is refitted by the methodology checker.
        actual = {
            "analysis": "factorial", "experimental_unit": "pot_id",
            "input_sha256": "a" * 64,
            "model": {"factors": ["source", "dose"], "response_column": "dry_mass_g"}
        }
        graph = {
            "kind": "factorial_interaction", "experimental_unit": "pot_id",
            "data_sha256": "a" * 64, "model_results_reused": True,
            "new_inferential_tests_performed": False
        }
        linked_path, figure_path = root / "results.json", root / "interaction_metadata.json"
        dump(linked_path, actual)
        dump(figure_path, graph)
        linked_out = root / "linked_ok"
        run = execute(EXAMPLE, linked_out, "--analysis-results", str(linked_path),
                      "--figure-metadata", str(figure_path))
        assert run.returncode == 0, run.stderr
        linked_result = result(linked_out)
        assert not linked_result["findings"]
        assert linked_result["scope"]["linked_interaction_figure"]

        actual["analysis"] = "mixed"
        actual["experimental_unit"] = "plant_id"
        graph["kind"] = "factorial_interaction"
        graph["data_sha256"] = "b" * 64
        dump(linked_path, actual)
        dump(figure_path, graph)
        run = execute(EXAMPLE, root / "linked_bad", "--analysis-results", str(linked_path),
                      "--figure-metadata", str(figure_path))
        assert run.returncode == 0
        linked_result = result(root / "linked_bad")
        assert {"M080", "M081", "M090", "M091", "M093"} <= ids(linked_result)

        # A figure may never be assessed without its paired statistical report.
        run = execute(EXAMPLE, root / "figure_without_model",
                      "--figure-metadata", str(figure_path))
        assert run.returncode != 0 and "--analysis-results" in run.stderr

        # Reject non-JSON numerical NaN instead of quietly writing invalid JSON.
        nanfile = root / "nan.json"
        nanfile.write_text('{"schema_version":"1.0","study":{"causal_claim":NaN}}',
                           encoding="utf-8")
        run = execute(nanfile, root / "nan_out")
        assert run.returncode != 0 and "strict UTF-8 JSON" in run.stderr

    print("PASS: conservative methodology audit, scientific-design risks, integration and strict JSON")


if __name__ == "__main__":
    check()
