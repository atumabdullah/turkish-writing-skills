#!/usr/bin/env python3
"""Five reproducible publication figures from explicit CSV/XLSX columns.

All plots are descriptive. No inferential tests, significance letters or p-values
are computed. A line per group shows means across observations at each x-value;
it is NOT a longitudinal mixed model. Use the statistical analysis module for
supported inferential designs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from figure_style import MARKERS, PALETTE, finish_axes, publication_style, save_publication_figure


KINDS = ("box_jitter", "grouped_bar", "line_plot", "correlation_heatmap", "multi_panel")
METHODS = ("pearson", "spearman")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="CSV or XLSX data file")
    p.add_argument("--kind", choices=KINDS, required=True)
    p.add_argument("--group", help="Categorical treatment or group column")
    p.add_argument("--subgroup", help="Second categorical factor for grouped bars")
    p.add_argument("--x", help="Numeric dose/time column for line_plot")
    p.add_argument("--y", help="Numeric response column")
    p.add_argument("--columns", help="Comma-separated numeric columns for heatmap or multi_panel")
    p.add_argument("--unit", help="Optional unique experimental-unit column; duplicates are rejected")
    p.add_argument("--method", choices=METHODS, default="pearson")
    p.add_argument("--error", choices=("sd", "sem", "none"), default="sd")
    p.add_argument("--title", help="Figure title (optional)")
    p.add_argument("--xlabel", help="X-axis label override")
    p.add_argument("--ylabel", help="Y-axis label override")
    p.add_argument("--dpi", type=int, default=300)
    p.add_argument("--output", type=Path, default=Path("figure-output"))
    return p


def require_columns(frame: pd.DataFrame, names: list[str]) -> None:
    if len(names) != len(set(names)):
        raise ValueError("Column names must be distinct")
    missing = [name for name in names if name not in frame.columns]
    if missing:
        raise ValueError("Missing input columns: " + ", ".join(missing))


def numeric_column(frame: pd.DataFrame, column: str, *, allow_missing=False) -> pd.Series:
    raw = frame[column]
    converted = pd.to_numeric(raw, errors="coerce")
    if (raw.notna() & converted.isna()).any():
        raise ValueError(f"Column {column!r} has nonnumeric values; check decimal separators")
    non_null = converted.dropna().to_numpy(dtype=float)
    if not np.isfinite(non_null).all():
        raise ValueError(f"Column {column!r} contains infinite values")
    if not allow_missing and converted.isna().any():
        raise ValueError(f"Column {column!r} contains missing values; clean data explicitly")
    return converted.astype(float)


def category_column(frame: pd.DataFrame, column: str) -> pd.Series:
    raw = frame[column]
    if raw.isna().any() or raw.astype(str).str.strip().eq("").any():
        raise ValueError(f"Column {column!r} contains missing or empty category labels")
    values = raw.astype(str)
    if values.nunique() > 30:
        raise ValueError(f"Column {column!r} has more than 30 categories; subset the display")
    return values


def ordered(values: pd.Series) -> list[str]:
    """Sorted categories ensure stable outputs when input row order changes."""
    return sorted(values.unique().tolist())


def grouped_stats(frame: pd.DataFrame, keys: list[str], value: str) -> list[dict]:
    result = frame.groupby(keys, observed=True, sort=True)[value].agg(["count", "mean", "std"]).reset_index()
    result = result.rename(columns={"count": "n", "std": "sd"})
    return json.loads(result.where(pd.notna(result), None).to_json(orient="records"))


def error_value(values: np.ndarray, error: str) -> float:
    if error == "none" or len(values) < 2:
        return 0.0
    sd = float(np.std(values, ddof=1))
    return sd if error == "sd" else sd / float(np.sqrt(len(values)))


def draw_box(ax, frame: pd.DataFrame, group: str, y: str) -> None:
    labels = ordered(frame[group])
    if len(labels) > 18:
        raise ValueError("Box-jitter supports at most 18 groups in one panel")
    data = [frame.loc[frame[group] == label, y].to_numpy(dtype=float) for label in labels]
    boxes = ax.boxplot(data, positions=np.arange(1, len(labels) + 1), widths=0.52,
                       patch_artist=True, showfliers=False,
                       medianprops={"color": "#222222", "linewidth": 1.5})
    rng = np.random.default_rng(2026)
    for index, (values, patch) in enumerate(zip(data, boxes["boxes"])):
        color = PALETTE[index % len(PALETTE)]
        patch.set(facecolor=color, edgecolor=color, alpha=0.28)
        jitter = rng.uniform(-0.13, 0.13, size=len(values))
        ax.scatter(index + 1 + jitter, values, s=27, alpha=0.82, color=color,
                   edgecolor="#333333", linewidth=0.35, zorder=3)
    ax.set_xticks(np.arange(1, len(labels) + 1), [f"{label}\n(n={len(items)})" for label, items in zip(labels, data)])
    ax.set_xlabel(group)
    ax.set_ylabel(y)
    finish_axes(ax)


def draw_grouped_bar(ax, frame: pd.DataFrame, group: str, subgroup: str, y: str, error: str) -> None:
    groups, subgroups = ordered(frame[group]), ordered(frame[subgroup])
    if len(groups) > 14 or len(subgroups) > 7:
        raise ValueError("Grouped bars support at most 14 groups and 7 subgroups")
    x = np.arange(len(groups), dtype=float)
    width = 0.82 / len(subgroups)
    for subindex, sub in enumerate(subgroups):
        heights, errors = [], []
        for main in groups:
            values = frame.loc[(frame[group] == main) & (frame[subgroup] == sub), y].to_numpy(dtype=float)
            heights.append(float(np.mean(values)) if len(values) else np.nan)
            errors.append(error_value(values, error))
        position = x - 0.41 + width * (subindex + 0.5)
        ax.bar(position, heights, width * 0.92, color=PALETTE[subindex],
               edgecolor="#333333", linewidth=0.6, label=sub)
        if error != "none":
            for x_pos, mean, spread in zip(position, heights, errors):
                if np.isfinite(mean) and spread > 0:
                    ax.errorbar(x_pos, mean, yerr=spread, color="#333333",
                                fmt="none", capsize=2.6, linewidth=0.9)
    ax.set_xticks(x, groups)
    ax.set_xlabel(group)
    ax.set_ylabel(f"{y} (mean ± {error.upper()})" if error != "none" else f"{y} (mean)")
    ax.legend(title=subgroup, frameon=False, loc="best")
    finish_axes(ax)


def draw_line(ax, frame: pd.DataFrame, x: str, y: str, group: str | None, error: str, notes: list[str]) -> None:
    labels = ordered(frame[group]) if group else [""]
    if len(labels) > 7:
        raise ValueError("Line chart supports at most seven series")
    for index, label in enumerate(labels):
        portion = frame.loc[frame[group] == label] if group else frame
        summary = portion.groupby(x, sort=True)[y].agg(["mean", "std", "count"]).reset_index()
        if len(summary) < 2:
            raise ValueError("Each line series requires at least two distinct numeric x-values")
        xx = summary[x].to_numpy(dtype=float)
        yy = summary["mean"].to_numpy(dtype=float)
        count = summary["count"].to_numpy(dtype=float)
        spread = summary["std"].fillna(0.0).to_numpy(dtype=float)
        spread = spread / np.sqrt(count) if error == "sem" else spread
        color = PALETTE[index]
        ax.plot(xx, yy, color=color, marker=MARKERS[index], linewidth=1.8,
                markersize=5.2, label=label or None)
        if error != "none" and np.any(spread > 0):
            ax.errorbar(xx, yy, yerr=spread, fmt="none", ecolor=color, capsize=2.7, linewidth=0.9)
        if (summary["count"] > 1).any():
            notes.append(f"Series {label or 'all'}: repeated x values are summarized by arithmetic mean; no repeated-measures inference")
    if group:
        ax.legend(title=group, frameon=False)
    ax.set_xlabel(x)
    ax.set_ylabel(f"{y} (mean ± {error.upper()})" if error != "none" else y)
    finish_axes(ax)


def draw_heatmap(ax, frame: pd.DataFrame, columns: list[str], method: str, notes: list[str]) -> dict:
    if not (2 <= len(columns) <= 12):
        raise ValueError("Heatmap needs 2–12 numeric columns")
    measures = frame[columns]
    counts = measures.notna().astype(int).T.dot(measures.notna().astype(int))
    correlation = measures.corr(method=method, min_periods=3)
    if not np.isfinite(correlation.to_numpy(dtype=float)).any():
        raise ValueError("No defined correlations: at least three paired observations and nonconstant variables are required")
    if measures.isna().any().any():
        notes.append("Heatmap uses pairwise complete observations; pairwise sample sizes are recorded")
    if correlation.isna().any().any():
        notes.append("Some correlations are undefined because variables are constant or too few paired observations exist")
    matrix = np.ma.masked_invalid(correlation.to_numpy(dtype=float))
    colors = plt.get_cmap("coolwarm").copy()
    colors.set_bad("#E8E8E8")
    im = ax.imshow(matrix, cmap=colors, vmin=-1, vmax=1, aspect="equal")
    ax.set_xticks(np.arange(len(columns)), columns, rotation=40, ha="right")
    ax.set_yticks(np.arange(len(columns)), columns)
    for i in range(len(columns)):
        for j in range(len(columns)):
            val = correlation.iloc[i, j]
            text = "NA" if pd.isna(val) else f"{val:.2f}"
            ax.text(j, i, text, ha="center", va="center",
                    color="white" if pd.notna(val) and abs(val) >= 0.62 else "#222222", fontsize=8)
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.045, label=f"{method.title()} r")
    ax.set_title(f"{method.title()} correlations (descriptive)")
    # Preserve undefined comparisons as JSON null, not NaN.
    corr_rows = [[None if pd.isna(v) else float(v) for v in row] for row in correlation.to_numpy()]
    return {"columns": columns, "correlations": corr_rows, "pairwise_n": counts.astype(int).values.tolist()}


def draw_multi(fig, frame: pd.DataFrame, group: str, columns: list[str]) -> None:
    if not (2 <= len(columns) <= 4):
        raise ValueError("Multi-panel figure needs two to four numeric response columns")
    axes = fig.subplots(2, 2)
    for index, (ax, name) in enumerate(zip(axes.flat, columns)):
        draw_box(ax, frame, group, name)
        ax.set_title(f"{chr(65 + index)}. {name}", loc="left")
    for ax in list(axes.flat)[len(columns):]:
        ax.set_visible(False)


def plot(args: argparse.Namespace) -> dict:
    if not args.input.is_file():
        raise ValueError(f"Input file not found: {args.input}")
    if args.input.suffix.lower() == ".csv":
        frame = pd.read_csv(args.input)
    elif args.input.suffix.lower() in {".xlsx", ".xlsm"}:
        frame = pd.read_excel(args.input)
    else:
        raise ValueError("Only CSV, XLSX and XLSM files are supported")
    if frame.empty or frame.columns.duplicated().any():
        raise ValueError("Input must have data and uniquely named columns")
    if not (200 <= args.dpi <= 600):
        raise ValueError("DPI must be between 200 and 600")
    columns = [c.strip() for c in (args.columns or "").split(",") if c.strip()]
    if args.kind in ("box_jitter", "grouped_bar", "multi_panel") and not args.group:
        raise ValueError(f"{args.kind} requires --group")
    if args.kind == "grouped_bar" and not args.subgroup:
        raise ValueError("grouped_bar requires --subgroup")
    if args.kind in ("box_jitter", "grouped_bar", "line_plot") and not args.y:
        raise ValueError(f"{args.kind} requires --y")
    if args.kind == "line_plot" and not args.x:
        raise ValueError("line_plot requires --x")
    if args.kind in ("correlation_heatmap", "multi_panel") and not columns:
        raise ValueError(f"{args.kind} requires --columns")
    used = [a for a in (args.unit, args.group, args.subgroup, args.x, args.y) if a]
    used += columns
    require_columns(frame, list(dict.fromkeys(used)))
    if args.unit:
        if frame[args.unit].isna().any() or frame[args.unit].duplicated().any():
            raise ValueError("Experimental-unit identifiers must be present and unique; repeated units require design-specific handling")

    group = args.group
    if group and args.kind != "correlation_heatmap":
        frame[group] = category_column(frame, group)
    if args.kind == "grouped_bar":
        frame[args.subgroup] = category_column(frame, args.subgroup)
    if args.kind == "line_plot" and args.x == group:
        raise ValueError("Line chart x and group must be different columns")
    if args.kind == "grouped_bar" and group == args.subgroup:
        raise ValueError("--group and --subgroup must be different")
    if args.kind in ("box_jitter", "grouped_bar", "line_plot"):
        frame[args.y] = numeric_column(frame, args.y)
    if args.kind == "line_plot":
        frame[args.x] = numeric_column(frame, args.x)
    if args.kind in ("correlation_heatmap", "multi_panel"):
        if len(columns) != len(set(columns)):
            raise ValueError("--columns entries must be unique")
        if args.kind == "multi_panel" and group in columns:
            raise ValueError("Response columns must differ from --group")
        for name in columns:
            frame[name] = numeric_column(frame, name, allow_missing=args.kind == "correlation_heatmap")
    notes = ["Descriptive visualization only; no statistical significance, tests, or causal claims implied"]
    summary: dict = {}
    with publication_style():
        if args.kind == "multi_panel":
            fig = plt.figure(figsize=(10.6, 7.7))
            draw_multi(fig, frame, group, columns)
            summary["group_counts"] = {name: int(n) for name, n in frame.groupby(group).size().items()}
        else:
            width = max(6.0, min(11.0, 0.68 * frame[group].nunique() + 4.2)) if group and args.kind != "correlation_heatmap" else 7.0
            fig, ax = plt.subplots(figsize=(width, 5.0))
            if args.kind == "box_jitter":
                draw_box(ax, frame, group, args.y)
                summary["groups"] = grouped_stats(frame, [group], args.y)
            elif args.kind == "grouped_bar":
                draw_grouped_bar(ax, frame, group, args.subgroup, args.y, args.error)
                summary["groups"] = grouped_stats(frame, [group, args.subgroup], args.y)
                notes.append("Bars display means; error bars are SD/SEM (not confidence intervals); n per cell is in metadata")
            elif args.kind == "line_plot":
                draw_line(ax, frame, args.x, args.y, group, args.error, notes)
                summary["rows_per_series"] = {name: int(n) for name, n in frame.groupby(group).size().items()} if group else {"all": len(frame)}
            else:
                summary.update(draw_heatmap(ax, frame, columns, args.method, notes))
            if args.xlabel and args.kind != "correlation_heatmap":
                ax.set_xlabel(args.xlabel)
            if args.ylabel and args.kind != "correlation_heatmap":
                ax.set_ylabel(args.ylabel)
        if args.title:
            fig.suptitle(args.title, fontsize=12, fontweight="semibold")
        fig_names = save_publication_figure(fig, args.output, args.dpi)

    metadata = {
        "plot_kind": args.kind,
        "source_file": args.input.name,
        "sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "n_input_rows": len(frame),
        "columns_used": used,
        "config": {"group": group, "subgroup": args.subgroup, "x": args.x, "y": args.y,
                   "columns": columns, "error": args.error, "method": args.method, "dpi": args.dpi},
        "no_inferential_statistics": True,
        "warnings": list(dict.fromkeys(notes)),
        "results": summary,
        "files": fig_names,
        "software": {"python_plotter": "0.8.0", "pandas": pd.__version__,
                     "matplotlib": matplotlib.__version__, "numpy": np.__version__},
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "plot_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    return metadata


def main() -> int:
    args = parser().parse_args()
    try:
        report = plot(args)
    except (ValueError, KeyError, OSError) as exc:
        raise SystemExit(f"Figure generation stopped: {exc}") from exc
    print(f"PASS: {report['plot_kind']} exported to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
