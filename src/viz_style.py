"""
Shared chart styling for all EDA / MLOps visualisations.

Uses a colourblind-safe categorical palette (validated with the dataviz
palette validator: all CVD / lightness / chroma checks pass). Charts always
carry a legend or direct labels so identity is never colour-alone, and the
grid/axes are kept recessive.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # headless: write PNGs without a display
import matplotlib.pyplot as plt

# Validated categorical theme (fixed order, never cycled).
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"]

# Diverging pair + neutral midpoint for the correlation heatmap.
DIVERGING = "RdBu_r"

SURFACE = "#fcfcfb"
INK = "#1a1a19"
MUTED = "#52514e"
GRID = "#e6e5e1"


def apply_base_style() -> None:
    """Apply recessive, print-friendly defaults to matplotlib."""
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "figure.dpi": 110,
    })
