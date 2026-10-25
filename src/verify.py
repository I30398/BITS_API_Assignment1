"""Capture verifiable evidence from the configured, running Prefect server."""
from __future__ import annotations
import argparse
import asyncio
from datetime import datetime, timezone
import json
import time

import pandas as pd
from prefect.client.orchestration import get_client
from prefect.client.schemas.filters import FlowFilter, FlowFilterName

from src import config
from src.api_access import main as capture_api
from src.artifact_io import sha256_file, source_fingerprint, write_json


async def completed_scheduled_runs():
    history = config.LOGS_DIR / "workflow_history.jsonl"
    # Historical runs must not satisfy verification for edited source code.
    completed_ids = {r["flow_run_id"] for r in (
        json.loads(line) for line in history.read_text().splitlines())
        if r["source_sha256"] == source_fingerprint()} if history.exists() else set()
    async with get_client() as client:
        runs = await client.read_flow_runs(limit=100, flow_filter=FlowFilter(
            name=FlowFilterName(any_=["telco-assignment-workflow"])))
    return sorted([{"id": str(r.id), "name": r.name,
                    "start_time": r.start_time.isoformat(),
                    "deployment_id": str(r.deployment_id)} for r in runs
                   if r.deployment_id and r.state_name == "Completed" and r.start_time
                   and str(r.id) in completed_ids],
                  key=lambda r: r["start_time"])


def verify(wait_scheduled=False, timeout=330):
    deadline = time.monotonic() + timeout
    runs = asyncio.run(completed_scheduled_runs())
    while wait_scheduled and len(runs) < 2 and time.monotonic() < deadline:
        time.sleep(5)
        runs = asyncio.run(completed_scheduled_runs())
    if wait_scheduled and len(runs) < 2:
        raise TimeoutError("Need two completed scheduled parent runs; server and runner must stay running.")
    config.ensure_dirs()
    capture_api()
    checks = {}
    metadata = json.loads((config.MODELS_DIR / "latest_metrics.json").read_text())
    checks["current_source_matches_metrics"] = metadata["source_sha256"] == source_fingerprint()
    checks["train_only_preprocessing"] = metadata["preprocessing_fit_scope"] == "training_only"
    checks["split_4930_2113"] = (metadata["train_rows"], metadata["test_rows"]) == (4930, 2113)
    checks["two_models_five_metrics"] = len(metadata["models"]) == 2 and all(
        all(0 <= m[k] <= 1 for k in ["accuracy", "precision", "recall", "f1_score", "roc_auc"])
        for m in metadata["models"])
    checks["no_duplicate_normalised_model_features"] = not any(
        c.endswith("_norm") for c in metadata["features"])
    checks["id_and_target_excluded"] = not {config.ID_COLUMN, config.TARGET_COLUMN} & set(metadata["features"])
    raw_model = pd.read_csv(config.MODEL_INPUT_DATASET)
    checks["missing_values_retained_for_train_only_imputation"] = bool(
        raw_model[config.NUMERIC_COLUMNS].isna().sum().sum() > 0)
    clean = pd.read_csv(config.CLEAN_DATASET)
    checks["clean_eda_no_missing_values"] = not clean.isna().any().any()
    checks["eda_normalisation_bounds"] = all(clean[c + "_norm"].between(-1e-12, 1+1e-12).all()
                                              for c in config.NUMERIC_COLUMNS)
    for name in ["data_pipeline.jsonl", "ml_pipeline.jsonl"]:
        records = [json.loads(line) for line in (config.LOGS_DIR / name).read_text().splitlines()]
        checks[name + "_valid_with_context"] = bool(records) and all(
            "flow_run_id" in r and r["pipeline_version"] == config.PIPELINE_VERSION for r in records)
    api = json.loads((config.OUTPUTS_DIR / "api_details.json").read_text())
    checks["project_flows_retrieved"] = set(config.FLOW_NAMES) <= {f["name"] for f in api["flows"]}
    deployed = [d for d in api["deployments"] if d["name"] == config.DEPLOYMENT_NAME]
    checks["deployment_interval_120_concurrency_one"] = bool(deployed) and all(
        d["concurrency_limit"] == 1 and any(s["active"] and s["interval_seconds"] == 120
                                         for s in d["schedules"]) for d in deployed)
    checks["at_least_two_scheduled_completed_cycles"] = len(runs) >= 2
    paths = [p for p in config.OUTPUTS_DIR.rglob("*") if p.is_file()
             and p.suffix in [".csv", ".png", ".jsonl", ".pkl"]]
    result = {"verified_at": datetime.now(timezone.utc).isoformat(),
              "source_sha256": source_fingerprint(),
              "environment": "local", "cloud_deployment_verified": False,
              "checks": {k: bool(v) for k, v in checks.items()},
              "scheduled_parent_runs": runs,
              "files": [{"path": str(p.relative_to(config.OUTPUTS_DIR)),
                         "sha256": sha256_file(p)} for p in sorted(paths)]}
    write_json(result, config.OUTPUTS_DIR / "verification.json")
    print(json.dumps(result["checks"], indent=2))
    failed = [k for k, v in checks.items() if not v and (wait_scheduled or k !=
              "at_least_two_scheduled_completed_cycles")]
    if failed:
        raise RuntimeError("Verification failed: " + ", ".join(failed))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait-scheduled", action="store_true")
    parser.add_argument("--timeout", type=int, default=330)
    args = parser.parse_args()
    verify(args.wait_scheduled, args.timeout)
