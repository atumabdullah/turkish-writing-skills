"""Shared publication style and deterministic export helpers."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Distinguishable colour-blind-aware categorical palette; line and marker
# encodings remain necessary where more than seven series are shown.
PALETTE = ("#0072B2", "#009E73", "#D55E00", "#CC79A7",
           "#E69F00", "#56B4E9", "#666666")
MARKERS = ("o", "s", "D", "^", "v", "P", "X")
FORMATS = ("png", "pdf", "svg")


@contextmanager
def publication_style():
    """Avoid leaking plot settings into other analyses running in-process."""
    with plt.rc_context({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "semibold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "savefig.facecolor": "white",
    }):
        yield


def finish_axes(ax, *, grid=True):
    if grid:
        ax.grid(axis="y", color="#DADADA", alpha=0.55, linewidth=0.7)
        ax.set_axisbelow(True)


def save_publication_figure(fig, destination: Path, dpi: int) -> list[str]:
    """Export vector formats and raster art without overwriting other analyses."""
    if not (200 <= dpi <= 600):
        raise ValueError("DPI must be between 200 and 600")
    destination.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=1.6)
    paths = []
    try:
        for ext in FORMATS:
            path = destination / f"figure.{ext}"
            fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.16)
            paths.append(path.name)
    finally:
        plt.close(fig)
    return paths
