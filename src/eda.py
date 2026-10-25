"""
Activity 1.4 - Exploratory Data Analysis.

Covers: correlation coefficients, numeric & categorical correlation,
binning, encoding, feature importance, and univariate + bivariate charts.
All figures are written to outputs/eda as PNGs for the report and dashboard.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from src import config
from src import viz_style as vs


# ---------------------------------------------------------------------------
# Encoding & binning
# ---------------------------------------------------------------------------
def encode_categoricals(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Label-encode categorical columns (Activity 1.4 - encoding).

    Returns the encoded frame and a mapping of column -> {label: code} so the
    encoding can be shown in the report.
    """
    df = df.copy()
    mappings: dict[str, dict] = {}
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    cat_cols = [c for c in cat_cols if c != config.ID_COLUMN]
    for col in cat_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        mappings[col] = {
            label: int(code) for code, label in enumerate(le.classes_)
        }
    return df, mappings


def bin_tenure(df: pd.DataFrame) -> pd.DataFrame:
    """Bin the numeric 'tenure' column into labelled groups (Activity 1.4)."""
    df = df.copy()
    df["tenure_group"] = pd.cut(
        df["tenure"],
        bins=[-1, 12, 24, 48, 60, np.inf],
        labels=["0-1 yr", "1-2 yr", "2-4 yr", "4-5 yr", "5+ yr"],
    )
    return df


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------
def correlation_matrix(df_encoded: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation across all (now numeric) features."""
    cols = [c for c in df_encoded.columns if c != config.ID_COLUMN]
    return df_encoded[cols].corr(numeric_only=True)


def target_correlations(corr: pd.DataFrame) -> pd.Series:
    """Correlation of each feature with the target, sorted by magnitude."""
    s = corr[config.TARGET_COLUMN].drop(labels=[config.TARGET_COLUMN])
    return s.reindex(s.abs().sort_values(ascending=False).index)


# ---------------------------------------------------------------------------
# Feature importance
# ---------------------------------------------------------------------------
def feature_importance(df_encoded: pd.DataFrame) -> pd.Series:
    """Random-forest feature importance w.r.t. churn (Activity 1.4)."""
    X = df_encoded.drop(columns=[config.ID_COLUMN, config.TARGET_COLUMN])
    y = df_encoded[config.TARGET_COLUMN]
    rf = RandomForestClassifier(
        n_estimators=200, random_state=config.RANDOM_STATE, n_jobs=-1
    )
    rf.fit(X, y)
    return pd.Series(rf.feature_importances_, index=X.columns).sort_values(
        ascending=False
    )


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def _save(fig, name: str) -> str:
    config.ensure_dirs()
    path = config.EDA_DIR / name
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def plot_target_distribution(df: pd.DataFrame) -> str:
    """Univariate: churn class balance (bar with direct value labels)."""
    vs.apply_base_style()
    counts = df[config.TARGET_COLUMN].value_counts()
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(
        counts.index.astype(str), counts.values,
        color=[vs.CATEGORICAL[0], vs.CATEGORICAL[1]], width=0.6,
    )
    ax.bar_label(bars, padding=3, fontweight="bold")
    ax.set_title("Univariate: Customer Churn Distribution")
    ax.set_xlabel("Churn")
    ax.set_ylabel("Number of customers")
    ax.grid(axis="x", visible=False)
    return _save(fig, "univariate_churn_distribution.png")


def plot_tenure_histogram(df: pd.DataFrame) -> str:
    """Univariate: distribution of customer tenure."""
    vs.apply_base_style()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(df["tenure"], bins=30, color=vs.CATEGORICAL[0], edgecolor=vs.SURFACE)
    ax.set_title("Univariate: Customer Tenure (months)")
    ax.set_xlabel("Tenure (months)")
    ax.set_ylabel("Number of customers")
    ax.grid(axis="x", visible=False)
    return _save(fig, "univariate_tenure_histogram.png")


def plot_churn_by_contract(df: pd.DataFrame) -> str:
    """Bivariate: churn rate across contract types."""
    vs.apply_base_style()
    ct = pd.crosstab(df["Contract"], df[config.TARGET_COLUMN], normalize="index") * 100
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(ct.index))
    w = 0.38
    b1 = ax.bar(x - w / 2, ct["No"], w, label="No churn", color=vs.CATEGORICAL[0])
    b2 = ax.bar(x + w / 2, ct["Yes"], w, label="Churn", color=vs.CATEGORICAL[1])
    ax.bar_label(b1, fmt="%.0f%%", padding=2, fontsize=9)
    ax.bar_label(b2, fmt="%.0f%%", padding=2, fontsize=9)
    ax.set_xticks(x, ct.index, rotation=0)
    ax.set_title("Bivariate: Churn Rate by Contract Type")
    ax.set_xlabel("Contract")
    ax.set_ylabel("% of customers")
    ax.legend(frameon=False)
    ax.grid(axis="x", visible=False)
    return _save(fig, "bivariate_churn_by_contract.png")


def plot_charges_by_churn(df: pd.DataFrame) -> str:
    """Bivariate: monthly charges distribution split by churn."""
    vs.apply_base_style()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    data = [
        df.loc[df[config.TARGET_COLUMN] == "No", "MonthlyCharges"].dropna(),
        df.loc[df[config.TARGET_COLUMN] == "Yes", "MonthlyCharges"].dropna(),
    ]
    bp = ax.boxplot(data, tick_labels=["No churn", "Churn"], patch_artist=True,
                    widths=0.5)
    for patch, color in zip(bp["boxes"], [vs.CATEGORICAL[0], vs.CATEGORICAL[1]]):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
    for median in bp["medians"]:
        median.set_color(vs.INK)
    ax.set_title("Bivariate: Monthly Charges by Churn")
    ax.set_ylabel("Monthly charges")
    ax.grid(axis="x", visible=False)
    return _save(fig, "bivariate_charges_by_churn.png")


def plot_correlation_heatmap(corr: pd.DataFrame) -> str:
    """Correlation heatmap across all encoded features (diverging palette)."""
    vs.apply_base_style()
    fig, ax = plt.subplots(figsize=(11, 9))
    im = ax.imshow(corr.values, cmap=vs.DIVERGING, vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)), corr.columns, rotation=90, fontsize=8)
    ax.set_yticks(range(len(corr.index)), corr.index, fontsize=8)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Pearson correlation")
    ax.set_title("Correlation Matrix (all encoded features)")
    ax.grid(False)
    return _save(fig, "correlation_heatmap.png")


def plot_feature_importance(importance: pd.Series, top: int = 12) -> str:
    """Horizontal bar of top-N feature importances with direct labels."""
    vs.apply_base_style()
    imp = importance.head(top)[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    bars = ax.barh(imp.index, imp.values, color=vs.CATEGORICAL[2], height=0.7)
    ax.bar_label(bars, fmt="%.3f", padding=3, fontsize=8)
    ax.set_title(f"Feature Importance (top {top}, Random Forest)")
    ax.set_xlabel("Importance")
    ax.grid(axis="y", visible=False)
    return _save(fig, "feature_importance.png")
