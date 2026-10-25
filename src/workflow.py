"""A single scheduled cycle runs DataOps before MLOps."""
import os
from datetime import datetime, timezone
from filelock import FileLock
from prefect import flow

from src import config
from src.artifact_io import write_json, source_fingerprint, append_record
from src.data_pipeline import data_pipeline
from src.ml_pipeline import ml_pipeline


@flow(name="telco-assignment-workflow", log_prints=True)
def assignment_workflow():
    config.ensure_dirs()
    with FileLock(str(config.OUTPUTS_DIR / ".workflow.lock"), timeout=180):
        model_input = data_pipeline()
        metrics = ml_pipeline(model_input)
        from prefect.runtime import flow_run
        record = {"completed_at": datetime.now(timezone.utc).isoformat(),
                    "flow_run_id": flow_run.id,
                    "source_sha256": source_fingerprint(),
                    "pipeline_version": config.PIPELINE_VERSION,
                    "environment": os.environ.get("ASSIGNMENT_ENVIRONMENT", "local"),
                    "cloud_deployment_verified": False,
                    "note": "Environment is declared configuration; verify hosting with deployment evidence.",
                    "models": metrics}
        append_record(config.LOGS_DIR / "workflow_history.jsonl", record)
        write_json(record, config.OUTPUTS_DIR / "latest_run.json")
    return metrics


if __name__ == "__main__":
    assignment_workflow()
