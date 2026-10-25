"""
Shared logging helpers.

Every pipeline run appends JSON-lines activity records to outputs/logs so that
the DataOps / MLOps requirement ("logging all activity details") is satisfied
even outside the Prefect UI. The same messages are also emitted through the
Prefect run logger when a run context is available, so they appear on the
Cloud dashboard.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.artifact_io import append_record


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_activity(logfile: str, step: str, message: str, **fields) -> dict:
    """Append one structured activity record to outputs/logs/<logfile>.

    Returns the record so callers can also push it to the Prefect logger.
    """
    config.ensure_dirs()
    record = {"ts": _timestamp(), "step": step, "message": message,
              "pipeline_version": config.PIPELINE_VERSION}
    try:
        from prefect.context import get_run_context
        context = get_run_context()
        if hasattr(context, "task_run"):
            record["flow_run_id"] = str(context.task_run.flow_run_id)
            record["task_run_id"] = str(context.task_run.id)
        elif hasattr(context, "flow_run"):
            record["flow_run_id"] = str(context.flow_run.id)
    except RuntimeError:
        pass
    record.update(fields)
    path = config.LOGS_DIR / logfile
    append_record(path, record)
    return record


def read_activity(logfile: str, limit: int | None = None) -> list[dict]:
    """Read back structured activity records (most recent last)."""
    path = config.LOGS_DIR / logfile
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if limit is not None:
        lines = lines[-limit:]
    out = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out
