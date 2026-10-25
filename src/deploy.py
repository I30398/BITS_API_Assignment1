"""
Activity 1.5 - DataOps scheduling.

Serves the data pipeline (and the ML pipeline) as Prefect deployments scheduled
to run every 2 minutes, using an interval schedule. Prefect runs a local API
server + dashboard (the "Cloud dashboard") and executes the scheduled runs.

Usage (two terminals):

  Terminal 1 - start the Prefect server + dashboard:
      prefect server start
      # dashboard at http://127.0.0.1:4200

  Terminal 2 - point the client at that server and launch the deployments:
      prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api
      python -m src.deploy

This call blocks and serves both flows on a 2-minute interval. Open the
dashboard to watch the scheduled runs, task logs, and activity details.
"""
from __future__ import annotations

from datetime import timedelta

from prefect import serve

from src.data_pipeline import data_pipeline
from src.ml_pipeline import ml_pipeline

INTERVAL = timedelta(minutes=2)  # Activity 1.5: run every 2 minutes


def main() -> None:
    data_deploy = data_pipeline.to_deployment(
        name="telco-data-pipeline-every-2min",
        interval=INTERVAL,
        tags=["dataops", "assignment1"],
        description="Ingestion + preprocessing (1.3) + EDA (1.4), every 2 min.",
    )
    ml_deploy = ml_pipeline.to_deployment(
        name="telco-ml-pipeline-every-2min",
        interval=INTERVAL,
        tags=["mlops", "assignment1"],
        description="Train + evaluate 2 models and log >=4 metrics, every 2 min.",
    )
    print("Serving deployments on a 2-minute interval. "
          "Open the dashboard at http://127.0.0.1:4200  (Ctrl+C to stop).")
    serve(data_deploy, ml_deploy)


if __name__ == "__main__":
    main()
