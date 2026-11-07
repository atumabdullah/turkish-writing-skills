#!/usr/bin/env python3
"""Design-gated inferential statistics for independent and longitudinal studies.

Supported scopes:
  factorial   two-factor between-unit ANOVA (Type III, sum coding)
  correlation Pearson/Spearman pairwise independent-unit correlations
  regression  numeric-predictor OLS with HC3 robust standard errors
  mixed       random-intercept longitudinal model, numeric time, optional
              between-unit treatment and time-by-treatment interaction

No inferential method is auto-selected. Results require design verification;
a statistically computable model is not proof of scientific appropriateness.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy import stats
import statsmodels
from statsmodels.api import OLS, add_constant
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.formula.api import mixedlm, ols


METHODS = ("factorial", "correlation", "regression", "mixed")


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="CSV, XLSX or XLSM, one observation per row")
    parser.add_argument("--analysis", choices=METHODS, required=True)
    parser.add_argument("--unit", required=True, help="Independent experimental unit or subject ID")
    parser.add_argument("--value", help="Response column for factorial, regression and mixed")
    parser.add_argument("--factor-a", help="First categorical factor for factorial")
    parser.add_argument("--factor-b", help="Second categorical factor for factorial")
    parser.add_argument("--columns", help="Comma-separated numeric columns for correlation")
    parser.add_argument("--method", choices=("pearson", "spearman"), default="pearson")
    parser.add_argument("--adjust", choices=("holm", "fdr_bh", "none"), default="holm")
    parser.add_argument("--predictors", help="Comma-separated numeric OLS predictors")
    parser.add_argument("--time", help="Numeric time for longitudinal mixed model")
    parser.add_argument("--group", help="Between-unit categorical group for mixed model")
    parser.add_argument("--interaction", action="store_true", help="Include time-by-group interaction in mixed model")
    parser.add_argument("--output", type=Path, default=Path("statistics-output"))
    return parser.parse_args()


def names(spec: str | None) -> list[str]:
    return [name.strip() for name in (spec or "").split(",") if name.strip()]


def required(frame: pd.DataFrame, columns: list[str]) -> None:
    if len(columns) != len(set(columns)):
        raise ValueError("Selected column names must be distinct")
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError("Columns not found: " + ", ".join(missing))


def raw_header_guard(path: Path) -> None:
    """Check original headers; pandas silently changes duplicate names."""
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            header = next(csv.reader(stream), None)
    else:
        from openpyxl import load_workbook
        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            header = next(workbook.worksheets[0].iter_rows(max_row=1, values_only=True), None)
        finally:
            workbook.close()
    if not header:
        raise ValueError("No header row")
    labels = [str(x).strip() if x is not None else "" for x in header]
    if any(not x for x in labels):
        raise ValueError("Empty source column header")
    if len(labels) != len(set(labels)):
        raise ValueError("Duplicate source column headers; rename before analysis")


def load(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise ValueError("Input file not found")
    if path.suffix.lower() not in {".csv", ".xlsx", ".xlsm"}:
        raise ValueError("Supported inputs: CSV, XLSX, XLSM")
    raw_header_guard(path)
    frame = pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)
    if frame.empty:
        raise ValueError("Input has no observations")
    return frame


def numeric(frame: pd.DataFrame, column: str, *, missing=False) -> pd.Series:
    original = frame[column]
    converted = pd.to_numeric(original, errors="coerce")
    if (original.notna() & converted.isna()).any():
        raise ValueError(f"Nonnumeric values in {column!r}; check decimal separators")
    if not np.isfinite(converted.dropna().to_numpy(dtype=float)).all():
        raise ValueError(f"Infinite values in {column!r}")
    if not missing and converted.isna().any():
        raise ValueError(f"Missing values in {column!r}; document handling before inference")
    return converted.astype(float)


def category(frame: pd.DataFrame, column: str) -> pd.Series:
    original = frame[column]
    if original.isna().any():
        raise ValueError(f"Missing category in {column!r}")
    values = original.astype(str).str.strip()
    if values.eq("").any():
        raise ValueError(f"Empty category in {column!r}")
    if values.nunique() > 20:
        raise ValueError(f"Too many category levels in {column!r}")
    return values


def q(name: str) -> str:
    """Quote user-supplied column names safely for Patsy formulas."""
    return "Q(" + json.dumps(name, ensure_ascii=True) + ")"


def finite(value) -> float | None:
    """Strict JSON: undefined or nonfinite statistics must be represented by null."""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def add_warning(report: dict, message: str) -> None:
    if message not in report["warnings"]:
        report["warnings"].append(message)


def normality_diagnostic(residuals, report: dict) -> float | None:
    a = np.asarray(residuals, dtype=float)
    if 3 <= len(a) <= 5000 and np.std(a) > 0 and np.isfinite(a).all():
        return finite(stats.shapiro(a).pvalue)
    add_warning(report, "Residual Shapiro-Wilk diagnostic unavailable for this sample")
    return None


def verify_unit(frame: pd.DataFrame, unit: str, *, repeated: bool) -> None:
    if frame[unit].isna().any() or frame[unit].astype(str).str.strip().eq("").any():
        raise ValueError("Experimental-unit IDs cannot be missing or empty")
    if repeated:
        if frame[unit].nunique() < 6:
            raise ValueError("Mixed model requires at least six independent experimental units")
    elif frame[unit].duplicated().any():
        raise ValueError("Duplicate experimental-unit IDs indicate repeated measures or subsamples")


def factorial(frame: pd.DataFrame, args: argparse.Namespace, report: dict) -> list[dict]:
    if not all((args.value, args.factor_a, args.factor_b)):
        raise ValueError("Factorial analysis requires --value, --factor-a and --factor-b")
    cols = [args.value, args.factor_a, args.factor_b]
    required(frame, cols)
    for col in (args.factor_a, args.factor_b):
        frame[col] = category(frame, col)
    frame[args.value] = numeric(frame, args.value)
    if frame[args.value].nunique() < 2:
        raise ValueError("Response is constant: factorial ANOVA is undefined")
    levels = [frame[col].nunique() for col in (args.factor_a, args.factor_b)]
    if any(not 2 <= count <= 12 for count in levels):
        raise ValueError("Each factorial factor must have two to twelve levels")
    counts = frame.groupby([args.factor_a, args.factor_b], observed=True).size()
    if len(counts) != levels[0] * levels[1]:
        raise ValueError("Incomplete factorial cells; interaction is not fully estimable")
    if counts.min() < 2:
        raise ValueError("At least two independent experimental units per factorial cell required")

    left = f"C({q(args.factor_a)}, Sum)"
    right = f"C({q(args.factor_b)}, Sum)"
    fitted = ols(f"{q(args.value)} ~ {left} * {right}", data=frame).fit()
    design = fitted.model.exog
    if np.linalg.matrix_rank(design) != design.shape[1] or fitted.df_resid <= 0:
        raise ValueError("Factorial design is rank deficient or has insufficient residual degrees of freedom")
    table = anova_lm(fitted, typ=3)
    residual_ss = finite(table.loc["Residual", "sum_sq"])
    if residual_ss is None or residual_ss <= 0:
        raise ValueError("Factorial ANOVA residual variance is zero")
    effects = []
    for name, row in table.iterrows():
        if name in ("Intercept", "Residual"):
            continue
        ss = finite(row["sum_sq"])
        effects.append({
            "term": name, "df_num": finite(row["df"]), "df_den": finite(fitted.df_resid),
            "F": finite(row["F"]), "p": finite(row["PR(>F)"]),
            "sum_squares": ss,
            "partial_eta_squared": finite(ss / (ss + residual_ss)) if ss is not None else None,
        })
    if any(effect["p"] is None for effect in effects):
        raise ValueError("Undefined factorial test statistic")
    cells = []
    for (a, b), group in frame.groupby([args.factor_a, args.factor_b], observed=True, sort=True):
        response = group[args.value].to_numpy(dtype=float)
        cells.append({"factor_a": str(a), "factor_b": str(b), "n": int(len(response)),
                      "mean": finite(np.mean(response)), "sd": finite(np.std(response, ddof=1))})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        p_levene = finite(stats.levene(*[
            group[args.value].to_numpy(dtype=float)
            for _, group in frame.groupby([args.factor_a, args.factor_b], observed=True)
        ], center="median").pvalue)
    if p_levene is None:
        add_warning(report, "Median-centered Levene diagnostic undefined; no p-value imputed")
    report["diagnostics"] = {
        "shapiro_residual_p": normality_diagnostic(fitted.resid, report),
        "levene_cell_p": p_levene,
        "residual_df": finite(fitted.df_resid),
        "residual_mean_square": finite(fitted.mse_resid),
    }
    if counts.max() != counts.min():
        add_warning(report, "Unequal cell sizes: Type III sum-contrast tests require careful interpretation")
    add_warning(report, "Type III sum-to-zero contrasts; interpret interaction before main effects")
    add_warning(report, "No post-hoc pairwise comparisons or significance letters are generated")
    report["model"] = {
        "method": "two-factor between-unit ANOVA", "anova_type": "III",
        "contrasts": "sum-to-zero", "factors": [args.factor_a, args.factor_b],
        "r_squared": finite(fitted.rsquared), "effects": effects, "cells": cells
    }
    return effects


def correlations(frame: pd.DataFrame, args: argparse.Namespace, report: dict) -> list[dict]:
    cols = names(args.columns)
    if not 2 <= len(cols) <= 12:
        raise ValueError("Correlation analysis needs 2–12 numeric columns via --columns")
    required(frame, cols)
    for col in cols:
        frame[col] = numeric(frame, col, missing=True)
    rows = []
    p_values = []
    indices = []
    for a, b in combinations(cols, 2):
        subset = frame[[a, b]].dropna()
        n = int(len(subset))
        corr = p = None
        if n >= 3 and subset[a].nunique() > 1 and subset[b].nunique() > 1:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                test = stats.pearsonr(subset[a], subset[b]) if args.method == "pearson" else stats.spearmanr(subset[a], subset[b])
            corr, p = finite(test.statistic), finite(test.pvalue)
        if corr is None or p is None:
            add_warning(report, f"Correlation {a} vs {b} undefined (constant variable or fewer than three paired observations)")
        row = {"left": a, "right": b, "n_pairs": n, "r": corr, "p_raw": p, "p_adjusted": None}
        if p is not None:
            indices.append(len(rows))
            p_values.append(p)
        rows.append(row)
    if p_values:
        adjusted = p_values if args.adjust == "none" else multipletests(p_values, method=args.adjust)[1]
        for index, p in zip(indices, adjusted):
            rows[index]["p_adjusted"] = finite(p)
    if frame[cols].isna().any().any():
        add_warning(report, "Missing data handled pairwise; sample sizes differ by comparison")
    add_warning(report, "Correlations are associations, not causal effects; independent units required")
    report["model"] = {"method": f"{args.method} correlation",
                       "adjustment": args.adjust, "comparisons": rows,
                       "n_adjusted_tests": len(p_values)}
    return rows


def regression(frame: pd.DataFrame, args: argparse.Namespace, report: dict) -> list[dict]:
    preds = names(args.predictors)
    if not args.value or not 1 <= len(preds) <= 8:
        raise ValueError("Regression requires --value and 1–8 numeric --predictors")
    required(frame, [args.value] + preds)
    for col in [args.value] + preds:
        frame[col] = numeric(frame, col)
    if len(frame) < max(10, 5 * (len(preds) + 1)):
        raise ValueError("Insufficient independent units for this regression (minimum 5 per fitted coefficient, at least 10)")
    if frame[args.value].nunique() < 2:
        raise ValueError("Constant response cannot be regressed")
    matrix = add_constant(frame[preds], has_constant="add")
    if np.linalg.matrix_rank(matrix.to_numpy(dtype=float)) != matrix.shape[1]:
        raise ValueError("Collinear or constant predictors: design matrix is rank deficient")
    fit = OLS(frame[args.value], matrix).fit(cov_type="HC3")
    if not np.isfinite(np.asarray(fit.pvalues, dtype=float)).all():
        raise ValueError("Nonfinite HC3 coefficient tests; review extreme leverage")
    intervals = fit.conf_int(alpha=0.05)
    rows = []
    for name in fit.params.index:
        rows.append({"term": name, "estimate": finite(fit.params[name]),
                     "se_hc3": finite(fit.bse[name]),
                     "z": finite(fit.tvalues[name]),
                     "p": finite(fit.pvalues[name]),
                     "ci95_lower": finite(intervals.loc[name].iloc[0]),
                     "ci95_upper": finite(intervals.loc[name].iloc[1])})
    vif = [{"predictor": name, "vif": finite(variance_inflation_factor(matrix.to_numpy(), i))}
           for i, name in enumerate(matrix.columns) if i > 0]
    if any(row["vif"] is None or row["vif"] > 5 for row in vif):
        add_warning(report, "Possible predictor multicollinearity (VIF > 5 or undefined)")
    bp_p = finite(het_breuschpagan(fit.resid, matrix.to_numpy(dtype=float))[1])
    report["diagnostics"] = {"shapiro_residual_p": normality_diagnostic(fit.resid, report),
                              "breusch_pagan_p": bp_p,
                              "condition_number": finite(fit.condition_number),
                              "variance_inflation_factors": vif}
    add_warning(report, "HC3 robust standard errors, two-sided asymptotic tests; observational regression is not causal")
    report["model"] = {"method": "multiple linear OLS regression",
                       "covariance": "HC3", "n": int(fit.nobs),
                       "predictors": preds, "r_squared": finite(fit.rsquared),
                       "r_squared_adjusted": finite(fit.rsquared_adj),
                       "coefficients": rows}
    return rows


def mixed(frame: pd.DataFrame, args: argparse.Namespace, report: dict) -> list[dict]:
    if not args.value or not args.time:
        raise ValueError("Mixed model requires --value and numeric --time")
    if args.interaction and not args.group:
        raise ValueError("--interaction requires --group")
    cols = [args.value, args.time] + ([args.group] if args.group else [])
    required(frame, cols)
    frame[args.value] = numeric(frame, args.value)
    frame[args.time] = numeric(frame, args.time)
    if frame[args.value].nunique() < 2:
        raise ValueError("Constant response cannot be modelled")
    if frame[args.time].nunique() < 2:
        raise ValueError("At least two distinct measurement times are required")
    if frame[[args.unit, args.time]].duplicated().any():
        raise ValueError("Duplicate unit-time observations: subsamples need explicit aggregation or a richer model")
    per_unit = frame.groupby(args.unit).size()
    if per_unit.min() < 2:
        raise ValueError("Every experimental unit needs at least two observations for this repeated-measures model")
    if args.group:
        frame[args.group] = category(frame, args.group)
        if not 2 <= frame[args.group].nunique() <= 6:
            raise ValueError("Mixed-model treatment requires 2–6 categories")
        if (frame.groupby(args.unit)[args.group].nunique() != 1).any():
            raise ValueError("Between-unit treatment must remain constant within each unit")
        unit_counts = frame.drop_duplicates(subset=[args.unit]).groupby(args.group).size()
        if unit_counts.min() < 3:
            raise ValueError("Each between-unit treatment needs at least three independent units")

    formula = q(args.value) + " ~ " + q(args.time)
    if args.group:
        fixed_group = f"C({q(args.group)}, Sum)"
        formula += f" * {fixed_group}" if args.interaction else f" + {fixed_group}"
    if len(frame) <= (3 + int(args.group is not None) * 3) * 2:
        raise ValueError("Too few repeated observations for the requested mixed-model fixed effects")
    last_error = None
    fitted = None
    for optimizer in ("lbfgs", "powell"):
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                candidate = mixedlm(formula, data=frame, groups=frame[args.unit], re_formula="1").fit(
                    reml=False, method=optimizer, maxiter=500, disp=False
                )
            if candidate.converged:
                fitted = candidate
                if optimizer != "lbfgs":
                    add_warning(report, "Mixed model required derivative-free Powell optimization")
                for warning in caught:
                    message = str(warning.message)
                    if "boundary" in message.lower() or "singular" in message.lower():
                        add_warning(report, "Random-intercept covariance may be on boundary or singular")
                break
            last_error = "Non-convergence"
        except (np.linalg.LinAlgError, ValueError, ArithmeticError) as exc:
            last_error = str(exc)
    if fitted is None:
        raise ValueError("Mixed model did not converge: " + str(last_error))
    variance = finite(fitted.cov_re.iloc[0, 0])
    residual_var = finite(fitted.scale)
    if variance is None or variance < 0 or residual_var is None or residual_var <= 0:
        raise ValueError("Mixed model has invalid random-effect or residual variance")
    if variance <= 1e-9:
        add_warning(report, "Estimated subject random-intercept variance is near zero (boundary fit)")
    conf = fitted.conf_int(alpha=0.05)
    rows = []
    for term in fitted.fe_params.index:
        rows.append({"term": term, "estimate": finite(fitted.fe_params[term]),
                     "se": finite(fitted.bse_fe[term]), "z": finite(fitted.tvalues[term]),
                     "p": finite(fitted.pvalues[term]),
                     "ci95_lower": finite(conf.loc[term].iloc[0]),
                     "ci95_upper": finite(conf.loc[term].iloc[1])})
    if any(row["p"] is None for row in rows):
        raise ValueError("Undefined fixed-effect inference; inspect model identifiability")
    add_warning(report, "Random-intercept model assumes independent subjects, conditional normality and no additional serial correlation")
    add_warning(report, "Time is modelled as a linear numeric effect; no random slope, blocking or post-hoc comparisons")
    report["model"] = {"method": "linear mixed-effects model", "estimation": "ML",
                       "random_effects": "unit random intercept", "converged": True,
                       "units": int(frame[args.unit].nunique()), "observations": len(frame),
                       "time_column": args.time, "group_column": args.group,
                       "time_by_group_interaction": bool(args.interaction),
                       "subject_intercept_variance": variance,
                       "residual_variance": residual_var, "fixed_effects": rows}
    report["diagnostics"] = {"unit_observations_min": int(per_unit.min()),
                              "unit_observations_max": int(per_unit.max())}
    return rows


def run(args: argparse.Namespace) -> dict:
    frame = load(args.input)
    required(frame, [args.unit])
    if args.analysis != "mixed" and args.interaction:
        raise ValueError("--interaction is only supported for the mixed model")
    verify_unit(frame, args.unit, repeated=args.analysis == "mixed")
    report = {
        "analysis": args.analysis, "input_filename": args.input.name,
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "n_input_rows": int(len(frame)), "experimental_unit": args.unit,
        "study_design": "RESEARCHER MUST VERIFY; no design is automatically inferred",
        "warnings": [], "diagnostics": {}, "model": {}, "files": [],
        "software": {"numpy": np.__version__, "pandas": pd.__version__,
                     "scipy": scipy.__version__, "statsmodels": statsmodels.__version__}
    }
    runners = {"factorial": factorial, "correlation": correlations,
               "regression": regression, "mixed": mixed}
    rows = runners[args.analysis](frame.copy(), args, report)
    # Export only summaries; never embed raw participant/experimental-unit IDs.
    args.output.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row.keys()))
    if fields:
        with (args.output / "table.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        report["files"].append("table.csv")
    report["files"].extend(["results.json", "results.md"])
    markdown = [f"# {args.analysis.title()} analysis", "",
                f"- Source: {report['input_filename']} (SHA-256: {report['input_sha256']})",
                f"- Independent unit: {args.unit}",
                f"- Observations: {len(frame)}",
                "- Study design and assumptions must be checked by the researcher.",
                "", "## Model", "", f"- {report['model']['method']}", "",
                "## Warnings and interpretation limits"]
    markdown += [f"- {notice}" for notice in report["warnings"]] or ["- None reported"]
    markdown += ["", "## Structured results", "", "See results.json and table.csv for exact numerical results.", ""]
    (args.output / "results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    (args.output / "results.md").write_text("\n".join(markdown), encoding="utf-8")
    return report


def main() -> int:
    try:
        report = run(cli())
    except (ValueError, OSError, KeyError, TypeError, np.linalg.LinAlgError) as error:
        raise SystemExit(f"Analysis stopped: {error}") from error
    print(f"PASS: {report['analysis']} -> {', '.join(report['files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
