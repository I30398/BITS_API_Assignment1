"""
Activity 1.5 - DataOps data pipeline (Prefect flow).

Automates the pre-processing (1.3) and EDA (1.4) activities as Prefect tasks
inside a single flow. Every task logs its activity both to the Prefect run
logger (visible on the dashboard) and to outputs/logs/data_pipeline.jsonl.

Run once:        python -m src.data_pipeline
Schedule (2 min): see src/deploy.py / README.
"""
from __future__ import annotations

from prefect import flow, task, get_run_logger

from src import config, preprocessing as pp, eda
from src.logging_utils import log_activity
from src.artifact_io import write_csv, write_json
from src.dashboard_artifacts import publish_table

LOGFILE = "data_pipeline.jsonl"


def _log(step: str, message: str, **fields):
    """Log to both the Prefect dashboard and the JSON activity file."""
    rec = log_activity(LOGFILE, step, message, **fields)
    try:
        get_run_logger().info(f"[{step}] {message} | {fields}")
    except Exception:
        # Outside a flow run context (e.g. ad-hoc call) - file log is enough.
        pass
    return rec


# ---------------------------------------------------------------------------
# Tasks - Activity 1.3 (pre-processing)
# ---------------------------------------------------------------------------
@task(name="ingest-data", retries=2, retry_delay_seconds=5)
def ingest():
    df = pp.load_raw()
    _log("1.2-ingestion", "Loaded raw dataset",
         rows=int(df.shape[0]), cols=int(df.shape[1]))
    return df


@task(name="coerce-and-summarise")
def summarise(df):
    df = pp.coerce_types(df)
    stats = pp.summary_statistics(df)
    dtypes = pp.data_types(df)
    _log("1.3-summary-stats", "Computed summary statistics",
         numeric_features=list(stats.index))
    _log("1.3-data-types", "Captured column data types",
         n_numeric=len(df.select_dtypes(include="number").columns),
         n_non_numeric=len(df.select_dtypes(exclude="number").columns),
         column_types=dict(zip(dtypes["column"], dtypes["dtype"])))
    write_csv(stats, config.OUTPUTS_DIR / "summary_statistics.csv")
    write_csv(dtypes, config.OUTPUTS_DIR / "data_types.csv", index=False)
    publish_table("telco-summary-statistics", stats.reset_index(names="feature"),
                  "Full-data exploratory statistics before missing-value induction.")
    publish_table("telco-data-types", dtypes, "Actual types for every source column.")
    return df


@task(name="check-and-induce-missing")
def handle_missing(df):
    before = pp.missing_report(df)
    _log("1.3-missing-check", "Checked missing values (pre-induction)",
         columns_with_missing=before.index.tolist(),
         total_missing=int(before["missing_count"].sum()))

    df_induced, induced = pp.induce_missing(df)
    write_csv(df_induced, config.MODEL_INPUT_DATASET, index=False)
    write_csv(before, config.OUTPUTS_DIR / "missing_before.csv")
    _log("1.3-induce-missing", "Induced missing data into numeric columns",
         induced=induced)

    after = pp.missing_report(df_induced)
    write_csv(after, config.OUTPUTS_DIR / "missing_after_induction.csv")
    publish_table("telco-missing-values", after.reset_index(names="feature"),
                  "Numeric missing values after deterministic 5% induction.")
    _log("1.3-missing-check-post", "Checked missing values (post-induction)",
         total_missing=int(after["missing_count"].sum()))

    df_imputed = pp.impute_numeric(df_induced)
    remaining = int(pp.missing_report(df_imputed)["missing_count"].sum()) \
        if not pp.missing_report(df_imputed).empty else 0
    _log("1.3-impute", "Imputed numeric missing values with median",
         remaining_missing=remaining)
    return df_imputed, df_induced


@task(name="normalise-data")
def normalise(df):
    df_norm, preview = pp.normalise(df)
    write_csv(preview, config.OUTPUTS_DIR / "normalisation_preview.csv", index=False)
    publish_table("telco-normalisation", preview, "Min-Max preview for EDA only; ML fits preprocessing on train.")
    _log("1.3-normalise", "Min-Max normalised numeric columns to [0,1]",
         normalised=config.NUMERIC_COLUMNS)
    return df_norm


# ---------------------------------------------------------------------------
# Tasks - Activity 1.4 (EDA)
# ---------------------------------------------------------------------------
@task(name="eda-encode-and-bin")
def encode_and_bin(df):
    df_binned = eda.bin_tenure(df)
    df_encoded, mappings = eda.encode_categoricals(df_binned.drop(
        columns=["tenure_group"]))
    _log("1.4-binning", "Binned tenure into tenure_group",
         bins=df_binned["tenure_group"].value_counts().to_dict())
    _log("1.4-encoding", "Label-encoded categorical features",
         n_encoded=len(mappings))
    write_json(mappings, config.OUTPUTS_DIR / "encoding_mappings.json")
    write_csv(df_binned["tenure_group"].value_counts().rename("records"),
              config.OUTPUTS_DIR / "tenure_bins.csv")
    publish_table("telco-tenure-bins", df_binned["tenure_group"].value_counts().rename(
                  "records").reset_index(), "Tenure grouped into five bands.")
    return df_binned, df_encoded


@task(name="eda-correlation")
def correlation(df_encoded):
    corr = eda.correlation_matrix(df_encoded)
    tgt = eda.target_correlations(corr)
    write_csv(corr, config.OUTPUTS_DIR / "correlation_matrix.csv")
    heatmap = eda.plot_correlation_heatmap(corr)
    _log("1.4-correlation", "Computed correlation coefficients",
         top_target_correlations={k: round(float(v), 3)
                                   for k, v in tgt.head(5).items()},
         chart=heatmap)
    return corr


@task(name="eda-feature-importance")
def importance(df_encoded):
    imp = eda.feature_importance(df_encoded)
    chart = eda.plot_feature_importance(imp)
    write_csv(imp, config.OUTPUTS_DIR / "feature_importance.csv", header=["importance"])
    publish_table("telco-feature-importance", imp.rename("importance").rename_axis(
                  "feature").reset_index(), "Exploratory importance aggregated from one-hot levels; no duplicate normalised columns.")
    _log("1.4-feature-importance", "Assessed feature importance (Random Forest)",
         top_features={k: round(float(v), 4) for k, v in imp.head(5).items()},
         chart=chart)
    return imp


@task(name="eda-visualise")
def visualise(df_binned):
    associations = eda.categorical_associations(df_binned)
    write_csv(associations, config.OUTPUTS_DIR / "categorical_associations.csv", index=False)
    publish_table("telco-categorical-associations", associations,
                  "Cramer's V between categorical features and churn; no artificial category ordering.")
    _log("1.4-categorical-association", "Calculated Cramer's V for categorical features",
         top_associations=associations.head(5).to_dict("records"))
    charts = {
        "churn_distribution": eda.plot_target_distribution(df_binned),
        "tenure_histogram": eda.plot_tenure_histogram(df_binned),
        "churn_by_contract": eda.plot_churn_by_contract(df_binned),
        "charges_by_churn": eda.plot_charges_by_churn(df_binned),
    }
    _log("1.4-visualise", "Generated univariate & bivariate charts",
         charts=charts)
    return charts


@task(name="persist-clean-dataset")
def persist(df_encoded):
    write_csv(df_encoded, config.CLEAN_DATASET, index=False)
    _log("1.3-persist", "Saved full-data EDA dataset; ML fits its own preprocessing",
         path=str(config.CLEAN_DATASET), rows=int(df_encoded.shape[0]))


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------
@flow(name="telco-data-pipeline", log_prints=True)
def data_pipeline():
    """DataOps flow: ingestion -> preprocessing (1.3) -> EDA (1.4)."""
    config.ensure_dirs()
    _log("flow-start", "Data pipeline run started")

    df = ingest()
    df = summarise(df)
    df, model_input = handle_missing(df)
    df = normalise(df)

    df_binned, df_encoded = encode_and_bin(df)
    correlation(df_encoded)
    importance(df_encoded)
    visualise(df_binned)
    persist(df_encoded)

    _log("flow-end", "Data pipeline run completed successfully")
    # Pass the pre-imputation snapshot to ML directly. Never train from EDA data.
    return model_input


if __name__ == "__main__":
    data_pipeline()
