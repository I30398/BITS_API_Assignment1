"""
Sub-Objective 2 - Machine Learning pipeline (Prefect flow).

  2.1 Model preparation : Logistic Regression + Random Forest (two algorithms)
  2.2 Model training     : 70/30 train/test split
  2.3 Model evaluation   : accuracy (plus more)
  2.4 MLOps              : log >= 4 metrics (accuracy, precision, recall, F1, ROC-AUC)

Metrics for every run are logged to the Prefect dashboard and appended to
outputs/logs/ml_pipeline.jsonl and outputs/models/metrics_history.csv.

Run once: python -m src.ml_pipeline
"""
from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from prefect import flow, task, get_run_logger
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix,
)

from src import config, viz_style as vs
from src.logging_utils import log_activity

LOGFILE = "ml_pipeline.jsonl"


def _log(step: str, message: str, **fields):
    rec = log_activity(LOGFILE, step, message, **fields)
    try:
        get_run_logger().info(f"[{step}] {message} | {fields}")
    except Exception:
        pass
    return rec


# ---------------------------------------------------------------------------
# 2.1 / 2.2 - prepare & split
# ---------------------------------------------------------------------------
@task(name="load-clean-data")
def load_clean():
    if not config.CLEAN_DATASET.exists():
        # Fall back to running the data pipeline's cleaning inline.
        from src import preprocessing as pp, eda
        df = pp.coerce_types(pp.load_raw())
        df = pp.impute_numeric(df)
        df, _ = eda.encode_categoricals(df)
    else:
        df = pd.read_csv(config.CLEAN_DATASET)
    _log("2.1-load", "Loaded cleaned dataset for modelling",
         rows=int(df.shape[0]), cols=int(df.shape[1]))
    return df


@task(name="train-test-split")
def split(df):
    X = df.drop(columns=[config.ID_COLUMN, config.TARGET_COLUMN], errors="ignore")
    y = df[config.TARGET_COLUMN]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.TEST_SIZE,
        random_state=config.RANDOM_STATE, stratify=y,
    )
    _log("2.2-split", "Split data 70/30 (stratified)",
         train_rows=int(len(X_train)), test_rows=int(len(X_test)),
         test_size=config.TEST_SIZE)
    return X_train, X_test, y_train, y_test


# ---------------------------------------------------------------------------
# 2.2 / 2.3 / 2.4 - train, evaluate, log metrics
# ---------------------------------------------------------------------------
def _evaluate(name, model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    metrics = {
        "model": name,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred)), 4),
        "recall": round(float(recall_score(y_test, y_pred)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    cm = confusion_matrix(y_test, y_pred)
    return metrics, cm, y_proba


@task(name="train-logistic-regression")
def train_logreg(X_train, X_test, y_train, y_test):
    # Scale features so Logistic Regression converges cleanly.
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=config.RANDOM_STATE),
    )
    model.fit(X_train, y_train)
    metrics, cm, proba = _evaluate("LogisticRegression", model, X_test, y_test)
    _persist_model("logistic_regression", model)
    _log("2.4-mlops", "Trained & evaluated Logistic Regression", **metrics)
    return model, metrics, cm


@task(name="train-random-forest")
def train_rf(X_train, X_test, y_train, y_test):
    model = RandomForestClassifier(
        n_estimators=200, random_state=config.RANDOM_STATE, n_jobs=-1
    )
    model.fit(X_train, y_train)
    metrics, cm, proba = _evaluate("RandomForest", model, X_test, y_test)
    _persist_model("random_forest", model)
    _log("2.4-mlops", "Trained & evaluated Random Forest", **metrics)
    return model, metrics, cm


def _persist_model(name, model):
    config.ensure_dirs()
    with (config.MODELS_DIR / f"{name}.pkl").open("wb") as fh:
        pickle.dump(model, fh)


# ---------------------------------------------------------------------------
# MLOps monitoring artefacts
# ---------------------------------------------------------------------------
@task(name="record-metrics-history")
def record_history(all_metrics: list[dict]):
    """Append this run's metrics to a CSV so drift can be monitored over time."""
    config.ensure_dirs()
    path = config.MODELS_DIR / "metrics_history.csv"
    df = pd.DataFrame(all_metrics)
    header = not path.exists()
    df.to_csv(path, mode="a", header=header, index=False)
    _log("2.4-mlops", "Appended metrics to monitoring history",
         path=str(path), models=[m["model"] for m in all_metrics])
    return path


@task(name="plot-model-comparison")
def plot_comparison(all_metrics: list[dict]):
    vs.apply_base_style()
    metric_names = ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
    models = [m["model"] for m in all_metrics]
    x = np.arange(len(metric_names))
    w = 0.38
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, m in enumerate(all_metrics):
        vals = [m[k] for k in metric_names]
        bars = ax.bar(x + (i - 0.5) * w, vals, w,
                      label=m["model"], color=vs.CATEGORICAL[i])
        ax.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)
    ax.set_xticks(x, [n.replace("_", " ").title() for n in metric_names])
    ax.set_ylim(0, 1.05)
    ax.set_title("MLOps: Model Evaluation Metrics")
    ax.set_ylabel("Score")
    ax.legend(frameon=False)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    path = config.MODELS_DIR / "model_comparison.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    _log("2.4-mlops", "Saved model comparison chart", chart=str(path))
    return str(path)


@task(name="plot-confusion-matrices")
def plot_confusions(results):
    vs.apply_base_style()
    fig, axes = plt.subplots(1, len(results), figsize=(5 * len(results), 4.3))
    if len(results) == 1:
        axes = [axes]
    for ax, (name, cm) in zip(axes, results):
        im = ax.imshow(cm, cmap="Blues")
        for (r, c), v in np.ndenumerate(cm):
            ax.text(c, r, str(v), ha="center", va="center",
                    color=vs.INK, fontweight="bold")
        ax.set_xticks([0, 1], ["No", "Yes"])
        ax.set_yticks([0, 1], ["No", "Yes"])
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title(name)
        ax.grid(False)
    fig.suptitle("MLOps: Confusion Matrices", fontweight="bold")
    fig.tight_layout()
    path = config.MODELS_DIR / "confusion_matrices.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    _log("2.4-mlops", "Saved confusion matrices", chart=str(path))
    return str(path)


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------
@flow(name="telco-ml-pipeline", log_prints=True)
def ml_pipeline():
    config.ensure_dirs()
    _log("flow-start", "ML pipeline run started")

    df = load_clean()
    X_train, X_test, y_train, y_test = split(df)

    lr_model, lr_metrics, lr_cm = train_logreg(X_train, X_test, y_train, y_test)
    rf_model, rf_metrics, rf_cm = train_rf(X_train, X_test, y_train, y_test)

    all_metrics = [lr_metrics, rf_metrics]
    record_history(all_metrics)
    plot_comparison(all_metrics)
    plot_confusions([("LogisticRegression", lr_cm), ("RandomForest", rf_cm)])

    best = max(all_metrics, key=lambda m: m["f1_score"])
    _log("flow-end", "ML pipeline run completed",
         best_model=best["model"], best_f1=best["f1_score"])

    # Write a compact summary for the report / API consumers.
    (config.MODELS_DIR / "latest_metrics.json").write_text(
        json.dumps({"run_ts": datetime.now(timezone.utc).isoformat(),
                    "models": all_metrics, "best": best}, indent=2),
        encoding="utf-8",
    )
    return all_metrics


if __name__ == "__main__":
    ml_pipeline()
