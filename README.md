# CCZG506 Assignment I — Cloud-based Data Science / ML Application

**Business problem:** Telecom Customer Churn Prediction (binary classification).
**Orchestration / dashboard / API:** [Prefect](https://www.prefect.io/) 3.8.

The project implements all three sub-objectives:

| Sub-objective | What | Where |
|---|---|---|
| 1. Data Pipeline (8) | Ingestion, preprocessing, EDA, DataOps (scheduled every 2 min, logged to dashboard) | `src/data_pipeline.py`, `src/preprocessing.py`, `src/eda.py` |
| 2. ML Pipeline (5) | 2 models, 70/30 split, evaluation, MLOps (≥4 metrics logged) | `src/ml_pipeline.py` |
| 3. API Access (2) | Retrieve & display ≥4 application details via Prefect's built-in REST API | `src/api_access.py` |

## Dataset
IBM Telco Customer Churn — 7,043 records, 21 columns. Downloaded to
`data/telco_churn.csv` (public, no auth). Source URL is in `src/config.py`.

## Setup
```bash
pip install -r requirements.txt
```
> Note: Prefect 3.8's scheduler is incompatible with SQLAlchemy ≥ 2.1
> (bulk-DML change). `requirements.txt` pins `sqlalchemy<2.1`.

## Run

> Run Prefect via `python -m prefect` (not the bare `prefect` command). On this
> machine the `prefect.exe` launcher is installed to a Scripts folder that is
> **not on PATH**, so `prefect server start` fails with
> *"prefect is not recognized..."*. `python -m prefect` always works.

**Terminal 1 — start the Prefect server + dashboard:**
```powershell
python -m prefect server start
# dashboard: http://127.0.0.1:4200
```

**Terminal 2 — point the client at the server, then run the pieces:**
```powershell
# PowerShell:
$env:PREFECT_API_URL = "http://127.0.0.1:4200/api"

python -m src.data_pipeline      # run the data pipeline once
python -m src.ml_pipeline         # run the ML pipeline once
python -m src.deploy              # schedule BOTH flows every 2 minutes (blocks)
python -m src.api_access          # retrieve & print key app details
python -m src.generate_report     # build the Word submission doc
```

Setting the API URL in other shells:
```bash
# bash:          export PREFECT_API_URL=http://127.0.0.1:4200/api
# cmd.exe:       set PREFECT_API_URL=http://127.0.0.1:4200/api
```

Open the dashboard to watch the scheduled 2-minute runs, per-task logs, and
activity details.

<details>
<summary>Optional: make the bare <code>prefect</code> command work</summary>

Add the Scripts folder to PATH for the current PowerShell session:
```powershell
$env:Path += ";C:\Users\I30398\AppData\Roaming\Python\Python314\Scripts"
prefect server start
```
To make it permanent, add that folder to your user PATH via *Edit environment
variables for your account*, then reopen the terminal.
</details>

## Outputs
- `outputs/eda/` — EDA charts (univariate, bivariate, correlation, importance)
- `outputs/models/` — trained models, metrics history, comparison + confusion charts
- `outputs/logs/*.jsonl` — structured activity logs for every task
- `outputs/api_details.json` — API response captured for the report
- `outputs/screenshots/` — dashboard screenshots
- `report/CCZG506_Assignment1_Report.docx` — submission document

## Structure
```
src/
  config.py          # paths, dataset + ML config
  logging_utils.py   # structured JSON activity logging
  viz_style.py       # colourblind-safe chart palette/style
  preprocessing.py   # Activity 1.3
  eda.py             # Activity 1.4
  data_pipeline.py   # Prefect flow: 1.3 + 1.4 (Activity 1.5)
  ml_pipeline.py     # Prefect flow: 2.1–2.4
  deploy.py          # schedule both flows every 2 minutes
  api_access.py      # Sub-objective 3
  generate_report.py # build the .docx
```
