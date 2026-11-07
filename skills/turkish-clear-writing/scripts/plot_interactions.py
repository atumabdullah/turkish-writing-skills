#!/usr/bin/env python3
"""Link validated v0.9.0 factorial/mixed model output to publication figures.

The script NEVER fits a new inferential model. It rejects source/report
mismatches and plots either independent-cell descriptive means with uncertainty
or existing mixed-model population-level fixed-effect predictions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from advanced_statistics import category, load, numeric, required, verify_unit
from figure_style import MARKERS, PALETTE, finish_axes, publication_style, save_publication_figure


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="Original CSV/XLSX file used by advanced_statistics.py")
    p.add_argument("--results", type=Path, required=True, help="Matching v0.9.1 results.json")
    p.add_argument("--output", type=Path, default=Path("interaction-output"))
    p.add_argument("--uncertainty", choices=("ci95", "sd", "sem", "none"),
                   default="ci95", help="Factorial cell uncertainty; mixed always uses model 95% CI")
    p.add_argument("--dpi", type=int, default=300)
    p.add_argument("--title")
    p.add_argument("--xlabel")
    p.add_argument("--ylabel")
    return p.parse_args()


def equal(a: float, b: float, *, atol=1e-8) -> bool:
    return bool(np.isclose(float(a), float(b), rtol=1e-7, atol=atol))


def finite_number(value, label: str) -> float:
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{label} must be finite") from exc
    if not np.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def sorted_categories(values: list[str]) -> tuple[list[str], np.ndarray, bool]:
    labels = sorted(set(values))
    try:
        x = np.array([float(item) for item in labels], dtype=float)
    except (ValueError, TypeError):
        return labels, np.arange(len(labels), dtype=float), False
    if not np.isfinite(x).all() or len(set(x.tolist())) != len(labels):
        raise ValueError("Ambiguous nonfinite or duplicate numeric category values")
    order = np.argsort(x)
    return [labels[i] for i in order], x[order], True


def series_x_positions(x: np.ndarray, *, numeric: bool, index: int, nseries: int) -> np.ndarray:
    """Never displace scientific numeric x-values away from their real dose/time."""
    values = np.asarray(x, dtype=float)
    if numeric:
        return values.copy()
    return values + 0.035 * (index - (nseries - 1) / 2)


def check_link(raw: pd.DataFrame, args: argparse.Namespace, report: dict) -> str:
    if report.get("analysis") not in ("factorial", "mixed"):
        raise ValueError("Only factorial or mixed analysis results may be plotted")
    fingerprint = hashlib.sha256(args.input.read_bytes()).hexdigest()
    if report.get("input_sha256") != fingerprint:
        raise ValueError("Source SHA-256 mismatch: the model was fitted to different data")
    if report.get("n_input_rows") != len(raw):
        raise ValueError("Model report row count does not match input data")
    unit = report.get("experimental_unit")
    if not isinstance(unit, str) or not unit:
        raise ValueError("Model report does not identify the experimental unit")
    required(raw, [unit])
    verify_unit(raw, unit, repeated=report["analysis"] == "mixed")
    model = report.get("model")
    if not isinstance(model, dict) or not model.get("response_column"):
        raise ValueError("Analysis report lacks v0.9.1 response column metadata; rerun the model")
    return unit


def factorial_panel(fig, raw: pd.DataFrame, report: dict, uncertainty: str) -> tuple[list[dict], str]:
    model = report["model"]
    factors = model.get("factors")
    response = model["response_column"]
    if not isinstance(factors, list) or len(factors) != 2 or len(set(factors + [response])) != 3:
        raise ValueError("Two independent categorical factors and response are required")
    a, b = factors
    required(raw, [a, b, response])
    raw = raw.copy()
    raw[a] = category(raw, a)
    raw[b] = category(raw, b)
    raw[response] = numeric(raw, response)
    groups = sorted(raw[a].unique())
    x_labels, xpos, numeric_x = sorted_categories(raw[b].tolist())
    if not 2 <= len(groups) <= 7 or not 2 <= len(x_labels) <= 12:
        raise ValueError("Figure supports 2–7 series and 2–12 levels of the x factor")
    actual = {}
    for (group, dose), piece in raw.groupby([a, b], sort=True, observed=True):
        data = piece[response].to_numpy(dtype=float)
        if len(data) < 2:
            raise ValueError("At least two independent units per factorial cell required")
        actual[(group, dose)] = {
            "factor_a": group, "factor_b": dose, "n": int(len(data)),
            "mean": float(np.mean(data)), "sd": float(np.std(data, ddof=1)),
        }
    reported_cells = model.get("cells")
    if not isinstance(reported_cells, list) or len(reported_cells) != len(actual):
        raise ValueError("Model cell table does not match the supplied dataset")
    seen = set()
    for cell in reported_cells:
        key = (str(cell["factor_a"]), str(cell["factor_b"]))
        if key not in actual or key in seen:
            raise ValueError("Unexpected or duplicate model cell in results.json")
        seen.add(key)
        baseline = actual[key]
        if int(cell["n"]) != baseline["n"]:
            raise ValueError("Model cell sample sizes differ from source data")
        for measure in ("mean", "sd"):
            if cell.get(measure) is None or not equal(cell[measure], baseline[measure]):
                raise ValueError(f"Model cell {measure} differs from source data")
    if set(actual) != seen:
        raise ValueError("The model does not contain every factorial cell")

    ax = fig.add_subplot(111)
    rows = []
    # For numeric doses, the MINIMUM adjacent gap limits raw-point jitter.
    # Line means and CI endpoints remain exactly on their actual numeric x.
    smallest_gap = float(np.min(np.diff(xpos))) if numeric_x else 1.0
    jitter_radius = 0.015 * smallest_gap
    rng = np.random.default_rng(2026)
    for index, group in enumerate(groups):
        xvals = np.asarray(xpos, dtype=float)
        means, errors = [], []
        for level in x_labels:
            row = actual[(group, level)]
            n, sd = row["n"], row["sd"]
            if uncertainty == "ci95":
                halfwidth = float(stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n))
            elif uncertainty == "sem":
                halfwidth = sd / np.sqrt(n)
            elif uncertainty == "sd":
                halfwidth = sd
            else:
                halfwidth = 0.0
            means.append(row["mean"])
            errors.append(halfwidth)
            rows.append({**row, "uncertainty_type": uncertainty, "halfwidth": halfwidth,
                         "lower": row["mean"] - halfwidth, "upper": row["mean"] + halfwidth})
        shown_x = series_x_positions(xvals, numeric=numeric_x, index=index, nseries=len(groups))
        ax.plot(shown_x, means, marker=MARKERS[index], linewidth=1.8,
                markersize=5, label=group, color=PALETTE[index])
        if uncertainty != "none":
            ax.errorbar(shown_x, means, yerr=errors, capsize=3,
                        fmt="none", color=PALETTE[index], linewidth=1.1)
        # Individual values show experimental-unit variability, not just means.
        for level, displayed_x in zip(x_labels, shown_x):
            values = raw.loc[(raw[a] == group) & (raw[b] == level), response].to_numpy()
            jitter = rng.uniform(-jitter_radius, jitter_radius, size=len(values))
            ax.scatter(np.full(len(values), displayed_x) + jitter, values,
                       color=PALETTE[index], alpha=.25, s=14, linewidths=0)
    ax.set_xticks(xpos, x_labels)
    ax.set_xlabel(b)
    label = {"ci95": "95% t CI", "sd": "SD", "sem": "SEM", "none": "no error bars"}[uncertainty]
    ax.set_ylabel(f"{response} (mean ± {label})" if uncertainty != "none" else response)
    ax.legend(title=a, loc="best", frameon=False)
    finish_axes(ax)
    caption = (f"Independent experimental units: {response} across {a} × {b}; "
               f"cell means and {label}. Light points are individual units. "
               "Uncertainty describes individual cells, not pairwise differences. "
               "Type III ANOVA interaction F/p are in the linked model report; "
               "no significance letters or post-hoc tests were computed by this plot.")
    return rows, caption


def mixed_panel(fig, raw: pd.DataFrame, report: dict) -> tuple[list[dict], str, list[dict]]:
    model = report["model"]
    if model.get("converged") is not True or model.get("prediction_basis") != (
        "population fixed effects; normal approximation 95% CI"
    ):
        raise ValueError("Only converged mixed models with v0.9.1 fixed-effect predictions are supported")
    time = model.get("time_column")
    group = model.get("group_column")
    response = model.get("response_column")
    unit = report["experimental_unit"]
    required(raw, [time, response] + ([group] if group else []))
    raw = raw.copy()
    raw[time] = numeric(raw, time)
    raw[response] = numeric(raw, response)
    if group:
        raw[group] = category(raw, group)

    # Never assign a temporary "_series_label" into the original frame.
    # Real, valid user columns can themselves have that name.
    series_labels = (raw[group] if group else
                     pd.Series(["All"] * len(raw), index=raw.index))
    labels = sorted(series_labels.unique())
    if not 1 <= len(labels) <= 7:
        raise ValueError("Mixed plot supports at most seven treatment series")

    grid = model.get("prediction_grid")
    if not isinstance(grid, list) or not grid:
        raise ValueError("No mixed-model observation grid found; rerun v0.9.1 analysis")
    expected = {}
    for (label, timepoint), sub in raw.groupby([series_labels, raw[time]], sort=True, observed=True):
        expected[(str(label), float(timepoint))] = {
            "n_units_at_time": int(sub[unit].nunique()),
            "observed_mean": float(sub[response].mean()),
        }
    validated = {}
    for entry in grid:
        key = (str(entry["group"]), finite_number(entry["time"], "prediction time"))
        if key not in expected or key in validated:
            raise ValueError("Unexpected or duplicate model observation grid entry")
        ref = expected[key]
        if int(entry["n_units_at_time"]) != ref["n_units_at_time"]:
            raise ValueError("Model prediction group-time sample size mismatch")
        if not equal(entry["observed_mean"], ref["observed_mean"]):
            raise ValueError("Model prediction observed means differ from data")
        vals = {key_: finite_number(entry[key_], key_) for key_ in
                ("fitted_mean", "ci95_lower", "ci95_upper", "fixed_effect_se")}
        if vals["fixed_effect_se"] < 0 or not (
            vals["ci95_lower"] <= vals["fitted_mean"] <= vals["ci95_upper"]
        ):
            raise ValueError("Invalid mixed-model observation confidence interval")
        validated[key] = {**entry, **vals}
    if set(validated) != set(expected):
        raise ValueError("Model observation grid has missing group-time combinations")

    # The nonlinearity of sqrt(X Cov(beta) X^T) means CI boundaries cannot
    # be linearly interpolated between sparse observation times.
    curve = model.get("prediction_curve")
    if not isinstance(curve, list) or not curve:
        raise ValueError("Mixed model has no dense confidence curve; rerun v0.9.1 analysis")
    curves: dict[str, list[dict]] = {label: [] for label in labels}
    curve_keys = set()
    for item in curve:
        label = str(item["group"])
        timepoint = finite_number(item["time"], "curve time")
        key = (label, timepoint)
        if label not in curves or key in curve_keys:
            raise ValueError("Unexpected or duplicate mixed-model confidence curve point")
        curve_keys.add(key)
        nums = {name: finite_number(item[name], name) for name in
                ("fitted_mean", "ci95_lower", "ci95_upper", "fixed_effect_se")}
        if nums["fixed_effect_se"] < 0 or not (
            nums["ci95_lower"] <= nums["fitted_mean"] <= nums["ci95_upper"]
        ):
            raise ValueError("Invalid mixed-model curve confidence interval")
        curves[label].append({"group": label, "time": timepoint, **nums})
    for label in labels:
        measured = sorted(t for group_name, t in expected if group_name == label)
        points = sorted(curves[label], key=lambda row: row["time"])
        if len(measured) < 2 or len(points) < 20:
            raise ValueError("At least two observed times and a dense prediction curve are required per series")
        if not equal(points[0]["time"], measured[0]) or not equal(points[-1]["time"], measured[-1]):
            raise ValueError("Confidence curve must span only the group's observed time range")
        if any(not points[i]["time"] < points[i + 1]["time"] for i in range(len(points) - 1)):
            raise ValueError("Confidence curve time coordinates must increase strictly")
        # Endpoints of the dense model curve must reproduce the modeled
        # confidence intervals evaluated at the original observation times.
        for point in (points[0], points[-1]):
            matched = validated[(label, point["time"])]
            for name in ("fitted_mean", "ci95_lower", "ci95_upper"):
                if not equal(point[name], matched[name]):
                    raise ValueError("Mixed-model confidence curve endpoints do not match observation predictions")
        curves[label] = points

    ax = fig.add_subplot(111)
    observed_rows, curve_rows = [], []
    for index, label in enumerate(labels):
        series = sorted((row for (group_key, _), row in validated.items() if group_key == label),
                        key=lambda row: float(row["time"]))
        smooth = curves[label]
        x = np.array([row["time"] for row in smooth], dtype=float)
        y = np.array([row["fitted_mean"] for row in smooth], dtype=float)
        lo = np.array([row["ci95_lower"] for row in smooth], dtype=float)
        hi = np.array([row["ci95_upper"] for row in smooth], dtype=float)
        observed_x = np.array([row["time"] for row in series], dtype=float)
        observed_y = np.array([row["observed_mean"] for row in series], dtype=float)
        color = PALETTE[index]
        ax.plot(x, y, "-", color=color, linewidth=1.9, label=f"{label} (model)")
        ax.fill_between(x, lo, hi, color=color, alpha=.16, linewidth=0)
        ax.scatter(observed_x, observed_y, color=color, edgecolor="white", linewidth=.8,
                   marker=MARKERS[index], s=32, zorder=4)
        observed_rows.extend(series)
        curve_rows.extend(smooth)
    ax.set_xlabel(time)
    ax.set_ylabel(response)
    if group:
        ax.legend(title=group, frameon=False)
    finish_axes(ax)
    caption = (f"Population-level, random-intercept mixed model: fitted {response} across {time}"
               + (f" by {group}" if group else "") +
               ". Lines are fixed-effect fitted means; shaded regions are asymptotic 95% "
               "confidence intervals evaluated on a dense time grid from the fitted fixed-effect "
               "covariance. Points are observed cell means. Bands are not subject-level "
               "prediction intervals. Repeated measurements are not independent; "
               "no pairwise significance test is implied by band overlap.")
    return observed_rows, caption, curve_rows


def run(args: argparse.Namespace) -> dict:
    if not 200 <= args.dpi <= 600:
        raise ValueError("DPI must be within 200–600")
    raw = load(args.input)
    if not args.results.is_file():
        raise ValueError("Linked results.json not found")
    report = json.loads(args.results.read_text(encoding="utf-8"),
                        parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    if not isinstance(report, dict):
        raise ValueError("Linked results must be a JSON object")
    unit = check_link(raw, args, report)
    analysis = report["analysis"]
    model = report["model"]
    response = model["response_column"]
    if analysis == "mixed" and args.uncertainty != "ci95":
        raise ValueError("Mixed model always uses fixed-effect 95% CI; --uncertainty must be ci95")
    with publication_style():
        fig = plt.figure(figsize=(8.3, 5.6))
        if analysis == "factorial":
            rows, caption = factorial_panel(fig, raw, report, args.uncertainty)
            curve_rows = []
        else:
            rows, caption, curve_rows = mixed_panel(fig, raw, report)
        ax = fig.axes[0]
        if args.xlabel:
            ax.set_xlabel(args.xlabel)
        if args.ylabel:
            ax.set_ylabel(args.ylabel)
        if args.title:
            ax.set_title(args.title, fontsize=11, fontweight="semibold")
        files = save_publication_figure(fig, args.output, args.dpi)

    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "interaction_table.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    if curve_rows:
        with (args.output / "interaction_curve.csv").open(
            "w", newline="", encoding="utf-8"
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=list(curve_rows[0]))
            writer.writeheader()
            writer.writerows(curve_rows)
    (args.output / "interaction_caption.md").write_text(caption + "\n", encoding="utf-8")
    metadata = {
        "engine_version": "0.9.1",
        "kind": f"{analysis}_interaction",
        "data_sha256": report["input_sha256"],
        "results_json_sha256": hashlib.sha256(args.results.read_bytes()).hexdigest(),
        "source_file": args.input.name,
        "experimental_unit": unit,
        "response_column": response,
        "analysis_method": model["method"],
        "error_bar_basis": (args.uncertainty if analysis == "factorial"
                            else "fixed effect asymptotic 95% CI"),
        "n_input_rows": len(raw),
        "model_results_reused": True,
        "new_inferential_tests_performed": False,
        "caption": caption,
        "warnings": list(report.get("warnings", [])),
        "files": files + ["interaction_table.csv"] +
                 (["interaction_curve.csv"] if curve_rows else []) +
                 ["interaction_caption.md", "interaction_metadata.json"],
    }
    (args.output / "interaction_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8"
    )
    return metadata


def main() -> int:
    args = parse_args()
    try:
        result = run(args)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Interaction figure stopped: {exc}") from exc
    print(f"PASS: {result['kind']} -> {', '.join(result['files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
