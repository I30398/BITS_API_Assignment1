"""Readable result tables inside the same Prefect run as the activity logs."""
from prefect.context import get_run_context
from prefect.artifacts import create_table_artifact


def publish_table(key, frame, description):
    try:
        get_run_context()
    except RuntimeError:
        return None
    table = frame.astype(object).where(frame.notna(), None).to_dict("records")
    return create_table_artifact(table=table, key=key, description=description)
