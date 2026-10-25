"""Serve one serialized DataOps -> MLOps workflow every two minutes."""
from datetime import timedelta
from prefect import serve
from src import config
from src.workflow import assignment_workflow

INTERVAL = timedelta(minutes=2)


def make_deployment():
    return assignment_workflow.to_deployment(
        name=config.DEPLOYMENT_NAME,
        interval=INTERVAL,
        concurrency_limit=1,
        tags=["assignment1", "dataops", "mlops"],
        description="Preprocessing and EDA, then train-only ML preprocessing and evaluation; every 120s.",
        version=config.PIPELINE_VERSION,
    )


def main():
    print("Serving one workflow every 120 seconds. DataOps completes before MLOps.")
    print("Use the configured Prefect dashboard; local execution is not cloud evidence.")
    serve(make_deployment(), limit=1)


if __name__ == "__main__":
    main()
