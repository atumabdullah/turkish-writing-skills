#!/usr/bin/env python3
"""Reproducible one-factor independent-group analysis and publication figures.

This is a deliberately narrow helper, not an automatic experimental-design classifier.
"""
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.oneway import anova_oneway

COLORS = ["#0072B2", "#009E73", "#D55E00", "#CC79A7", "#E69F00", "#56B4E9", "#999999"]


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="CSV or XLSX with one independent experimental unit per row")
    parser.add_argument("--group", required=True, help="Categorical experimental treatment column")
    parser.add_argument("--value", required=True, help="Numeric response column")
    parser.add_argument("--unit", help="Unique experimental-unit identifier (mandatory for inferential tests)")
    parser.add_argument("--analysis", choices=["descriptive", "anova", "welch", "kruskal"], default="descriptive")
    parser.add_argument("--output", type=Path, default=Path("analysis-output"))
    return parser.parse_args()


def run(args: argparse.Namespace) -> dict:
    if args.input.suffix.lower() == ".csv":
        frame = pd.read_csv(args.input)
    elif args.input.suffix.lower() in {".xlsx", ".xlsm"}:
        frame = pd.read_excel(args.input)
    else:
        raise ValueError("Only .csv, .xlsx and .xlsm inputs are supported")
    cols = [args.group, args.value] + ([args.unit] if args.unit else [])
    if len(set(cols)) != len(cols) or any(column not in frame.columns for column in cols):
        raise ValueError("Choose distinct, existing column names for group, value and unit")
    selected = frame[cols].copy()
    if selected.empty or selected.isna().any().any():
        raise ValueError("Missing data are present: resolve and document handling before analysis")
    numeric = pd.to_numeric(selected[args.value], errors="coerce")
    if numeric.isna().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Response must be numeric and finite; check decimal separators and data cleaning")
    selected[args.value] = numeric.astype(float)
    selected[args.group] = selected[args.group].astype(str)
    if args.unit:
        if selected[args.unit].duplicated().any():
            raise ValueError("Experimental-unit IDs repeat. Repeated measures/subsamples need a design-specific analysis")
    if args.analysis != "descriptive" and not args.unit:
        raise ValueError("Inferential tests require --unit so independence can be audited")
    ordered = list(dict.fromkeys(selected[args.group].tolist()))
    if len(ordered) < 2 and args.analysis != "descriptive":
        raise ValueError("A group comparison requires at least two groups")
    groups = [selected.loc[selected[args.group] == name, args.value].to_numpy(dtype=float) for name in ordered]
    if args.analysis != "descriptive" and any(len(values) < 2 for values in groups):
        raise ValueError("At least two independent experimental units per group are required")
    # Rank tests can compare constant *within-group* data when pooled values differ.
    # Parametric tests retain the original safeguard against zero within-group variance.
    if args.analysis == "kruskal" and np.ptp(selected[args.value].to_numpy(dtype=float)) == 0:
        raise ValueError("All pooled observations are identical; Kruskal-Wallis is undefined")
    if args.analysis in {"anova", "welch"} and all(np.var(a) == 0 for a in groups):
        raise ValueError("All groups have zero within-group variance; parametric comparison is undefined")

    result = {"source": args.input.name, "group_column": args.group, "value_column": args.value,
              "unit_column": args.unit, "analysis": args.analysis,
              "scope": "independent one-factor groups; design and randomization must be verified by researcher",
              "groups": [{"name": name, "n": len(a), "mean": float(np.mean(a)),
                          "sd": float(np.std(a, ddof=1)) if len(a) > 1 else None,
                          "median": float(np.median(a)), "minimum": float(np.min(a)),
                          "maximum": float(np.max(a))} for name, a in zip(ordered, groups)],
              "diagnostics": {}, "inference": None, "warnings": []}
    if args.analysis != "descriptive":
        residuals = np.concatenate([a - np.mean(a) for a in groups])
        if 3 <= len(residuals) <= 5000 and np.std(residuals) > 0:
            result["diagnostics"]["shapiro_residual_p"] = float(stats.shapiro(residuals).pvalue)
        else:
            result["warnings"].append("Residual normality diagnostic unavailable for this sample")
        if all(len(a) >= 2 for a in groups):
            levene_p = float(stats.levene(*groups, center="median").pvalue)
            if np.isfinite(levene_p):
                result["diagnostics"]["levene_median_p"] = levene_p
            else:
                # For instance, identical absolute deviations can make Levene
                # undefined while the requested inferential test remains valid.
                result["diagnostics"]["levene_median_p"] = None
                result["warnings"].append(
                    "Median-centered Levene diagnostic is undefined for these data; recorded as null"
                )
        result["warnings"].append("Diagnostics are not automatic pass/fail gates; inspect residuals, design and sample size")
        if args.analysis == "anova":
            test = stats.f_oneway(*groups)
            grand = float(selected[args.value].mean())
            ss_between = sum(len(a) * (float(np.mean(a)) - grand)**2 for a in groups)
            ss_total = float(((selected[args.value] - grand)**2).sum())
            tukey = pairwise_tukeyhsd(endog=selected[args.value].to_numpy(), groups=selected[args.group].to_numpy())
            result["inference"] = {"test": "ordinary one-way ANOVA", "F": float(test.statistic),
                                   "p": float(test.pvalue), "df_between": len(groups)-1,
                                   "df_within": len(selected)-len(groups),
                                   "eta_squared": ss_between / ss_total if ss_total > 0 else None,
                                   "posthoc": "Tukey HSD", "posthoc_table": str(tukey.summary())}
        elif args.analysis == "welch":
            test = anova_oneway(selected[args.value].to_numpy(), selected[args.group].to_numpy(), use_var="unequal")
            pairs = []
            for (left, a), (right, b) in combinations(zip(ordered, groups), 2):
                t = stats.ttest_ind(a, b, equal_var=False)
                pairs.append({"left": left, "right": right, "mean_difference": float(np.mean(a)-np.mean(b)),
                              "p_raw": float(t.pvalue)})
            if pairs:
                adjusted = multipletests([pair["p_raw"] for pair in pairs], method="holm")[1]
                for pair, p in zip(pairs, adjusted):
                    pair["p_holm"] = float(p)
            result["inference"] = {"test": "Welch one-way ANOVA", "F": float(test.statistic),
                                   "p": float(test.pvalue), "df": [float(v) for v in test.df],
                                   "posthoc": "pairwise Welch t-tests with Holm adjustment", "comparisons": pairs}
        else:
            test = stats.kruskal(*groups)
            result["inference"] = {"test": "Kruskal-Wallis", "H": float(test.statistic),
                                   "p": float(test.pvalue), "posthoc": "not computed"}

    args.output.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                                 "axes.spines.top": False, "axes.spines.right": False,
                                 "svg.fonttype": "none", "pdf.fonttype": 42,
                                 "savefig.bbox": "tight"})
    fig, ax = plt.subplots(figsize=(max(5.4, len(groups)*1.25), 4.2))
    box = ax.boxplot(groups, positions=range(1, len(groups)+1), widths=0.48,
                     patch_artist=True, showfliers=False, medianprops={"color": "black", "linewidth": 1.5})
    rng = np.random.default_rng(2026)
    for i, (name, values, patch) in enumerate(zip(ordered, groups, box["boxes"]), 1):
        color = COLORS[(i-1) % len(COLORS)]
        patch.set_facecolor(color)
        patch.set_alpha(0.25)
        patch.set_edgecolor(color)
        jitter = rng.uniform(-0.13, 0.13, size=len(values))
        ax.scatter(i + jitter, values, s=24, color=color, edgecolors="black", linewidths=.35, alpha=.85, zorder=3)
    ax.set_xticks(range(1, len(groups)+1), [f"{name}\n(n={len(a)})" for name, a in zip(ordered, groups)])
    ax.set_ylabel(args.value)
    ax.set_xlabel(args.group)
    ax.grid(axis="y", color="#DDDDDD", alpha=.6, linewidth=.6)
    fig.tight_layout()
    for ext in ["png", "pdf", "svg"]:
        fig.savefig(args.output / f"groups.{ext}", dpi=300)
    plt.close(fig)
    result["figure_files"] = [f"groups.{ext}" for ext in ("png", "pdf", "svg")]
    (args.output / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    return result


def main() -> int:
    try:
        run(arguments())
    except (ValueError, FileNotFoundError, KeyError) as error:
        raise SystemExit(f"Analysis stopped: {error}") from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
