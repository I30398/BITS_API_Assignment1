"""
Activity 1.3 - Data Pre-processing.

Each function returns a small dict/DataFrame of results so the Prefect flow can
log the details and the report generator can tabulate them. Steps covered:

  * display summary statistics
  * check for missing values
  * induce (inject) missing data into numeric columns
  * display data types
  * normalise numeric data
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from src import config


def load_raw() -> pd.DataFrame:
    """Load the raw Telco churn dataset (Activity 1.2 - Data Ingestion)."""
    df = pd.read_csv(config.RAW_DATASET)
    return df


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """TotalCharges arrives as text with blank strings -> coerce to numeric."""
    df = df.copy()
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    return df


def summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Return describe() for numeric columns (transposed for readability)."""
    return df.describe(include=[np.number]).T


def data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Return a two-column frame of column name -> dtype."""
    return (
        df.dtypes.astype(str)
        .rename("dtype")
        .reset_index()
        .rename(columns={"index": "column"})
    )


def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """Count and percentage of missing values per column (non-zero only)."""
    counts = df.isna().sum()
    pct = (counts / len(df) * 100).round(2)
    report = pd.DataFrame({"missing_count": counts, "missing_pct": pct})
    return report[report["missing_count"] > 0].sort_values(
        "missing_count", ascending=False
    )


def induce_missing(
    df: pd.DataFrame, fraction: float = 0.05, seed: int = config.RANDOM_STATE
) -> tuple[pd.DataFrame, dict]:
    """Inject NaNs into numeric columns to simulate real-world dirty data.

    Returns the modified frame and a dict of how many cells were nulled per
    column (Activity 1.3 - 'inducing missing data for numeric columns').
    """
    rng = np.random.default_rng(seed)
    df = df.copy()
    induced: dict[str, int] = {}
    for col in config.NUMERIC_COLUMNS:
        df[col] = df[col].astype(float)
        n = int(len(df) * fraction)
        idx = rng.choice(df.index, size=n, replace=False)
        df.loc[idx, col] = np.nan
        induced[col] = n
    return df, induced


def impute_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Fill numeric NaNs (original + induced) with the column median."""
    df = df.copy()
    for col in config.NUMERIC_COLUMNS:
        df[col] = df[col].fillna(df[col].median())
    return df


def normalise(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Min-Max scale the numeric columns to [0, 1].

    Returns (frame with normalised columns added, before/after preview).
    """
    df = df.copy()
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[config.NUMERIC_COLUMNS])
    norm_cols = [f"{c}_norm" for c in config.NUMERIC_COLUMNS]
    df[norm_cols] = scaled

    preview = pd.concat(
        [
            df[config.NUMERIC_COLUMNS].head(5).reset_index(drop=True),
            df[norm_cols].head(5).round(4).reset_index(drop=True),
        ],
        axis=1,
    )
    return df, preview
