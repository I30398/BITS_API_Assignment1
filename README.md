# CCZG506 Assignment I — Telecom Customer Churn

A Prefect workflow prepares and explores the IBM Telco dataset, then trains and
compares Logistic Regression and Random Forest classifiers. The assignment's
8-mark data pipeline, 5-mark ML pipeline and 2-mark API access objectives are
mapped in `docs/REQUIREMENTS.md`.

## What changed

- One scheduled parent workflow runs **DataOps first, then MLOps** every 120 seconds.
  The deployment and runner both limit concurrency to one cycle.
- ML receives a pre-imputation data snapshot. The 70/30 stratified split happens
  before fitting median imputation, standardisation and one-hot encoding.
- Numeric features appear once in each model. EDA uses numeric Pearson
  correlations and Cramer's V for categorical associations.
- Atomic replacement publishes complete files; file locks protect append logs.
- Actual column types, preprocessing tables and five metrics per model appear
  in the Prefect dashboard as artifacts as well as task logs.
- New outputs are under `outputs/current/`. The original files under `outputs/`,
  `data/telco_churn_clean.csv` and `report/` are **historical baseline evidence**.
  They do not validate the revised code.

## Local setup

Use **Python 3.12**. The complete runtime dependency set is pinned in
`requirements-lock.txt`; `requirements.txt` lists the direct dependencies.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
```

On Windows, create the environment with `py -3.12 -m venv .venv` and activate it
with `.venv\Scripts\Activate.ps1` in PowerShell.

### One-command local launcher

After setup, run `python scripts/local.py`. It starts the dashboard and schedule
and prints the local URL. Keep the window open; Ctrl+C stops the services that
this launcher started. An already running server is reused and left running.
Use `python scripts/local.py --once` for a single complete cycle.
Readiness allows 180 seconds by default; use `--startup-timeout 300` for a slow
cold start. SQLite requires local disk. NFS/SMB database paths are rejected;
configure PostgreSQL for such hosts (see `docs/DEPLOYMENT.md`).

The separate-terminal commands below are useful when inspecting each component.

**Terminal 1 — server and dashboard**

```bash
python -m prefect server start --host 127.0.0.1 --port 4207
```

Open [the local dashboard](http://127.0.0.1:4207).

**Terminal 2 — use that server**

```bash
source .venv/bin/activate
export PREFECT_API_URL=http://127.0.0.1:4207/api
python -m src.workflow       # run one complete cycle
python -m src.deploy         # serve the 120-second schedule; keep running
```

In PowerShell use `$env:PREFECT_API_URL = "http://127.0.0.1:4207/api"` instead
of `export`. Keep both terminals running for scheduled execution.

**Terminal 3 — capture application details and verify**

```bash
source .venv/bin/activate
export PREFECT_API_URL=http://127.0.0.1:4207/api
python -m src.verify --wait-scheduled
python -m src.generate_report --draft
```

Verification waits up to 330 seconds for two completed scheduled parent runs.
It saves current API results, integrity checks, scheduled run IDs and artifact
hashes to `outputs/current/verification.json`. It does not verify cloud hosting.
To capture only the API evidence, run `python -m src.api_access`.

The draft report is `report/current/CCZG506_Assignment1_Review.docx`.

## Docker deployment

Docker Desktop or Docker Engine with Compose can run the same project without
a local Python installation:

```bash
docker compose up --build -d
docker compose logs -f runner
```

The dashboard is still [http://127.0.0.1:4207](http://127.0.0.1:4207).
Persistent named volumes retain the server database and application outputs.

```bash
docker compose exec runner python -m src.verify --wait-scheduled
docker compose cp runner:/app/outputs/current/. outputs/test-docker/
docker compose down
```

`down` stops this Compose project and retains its volumes. Only one server should
bind host port 4207 at a time; stop the Python server before starting Compose.

The package can also run on a cloud VM. Follow `docs/DEPLOYMENT.md` for a private
SSH-tunnel arrangement. A local web dashboard, a Docker image or the setting
`ASSIGNMENT_ENVIRONMENT=cloud` alone does **not** demonstrate cloud deployment.

## Results and limitations

The raw public CSV has 7043 records and 21 columns. Its source is recorded in
`src/config.py`. A fixed seed induces 5% missing values in three numeric columns.
The ML pipeline keeps 4930 training records and 2113 test records, and logs
accuracy, precision, recall, F1 and ROC AUC for each model.

Repeated evaluation on this fixed dataset demonstrates metric logging and
history. It does not establish production drift detection, live customer churn
performance or a continuously changing ingestion source. The baseline and
revised model metrics should not be treated as directly comparable experiments:
preprocessing and categorical encoding changed.

Standalone `python -m src.data_pipeline` and `python -m src.ml_pipeline` remain
available for inspection. The ML command prepares its own raw-data snapshot;
it never reads the full-data EDA CSV. Use the scheduled parent workflow for the
complete assignment demonstration.

## Testing

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The regressions cover train-only fitting, unseen categories, the stratified
split, interrupted publication, concurrent readers/writers and cross-process
JSON logging. `src.verify` checks the actual server and generated evidence.

## Reviewed checkpoint

See `docs/VALIDATION.md` and `evidence/README.md` for the frozen local and Docker
verification results. The frozen report is
`evidence/local-review/CCZG506_Assignment1_Review.docx`. Live outputs continue to
change as scheduled cycles run; the frozen review does not.

## Before submission

`config/group.json` contains Group 15's five supplied members and their 20%
contribution allocations. Review the contribution descriptions with the group
and add the completed video URL. The reviewed cloud output set and six cropped
application/provider screenshots are in `evidence/cloud-prayogshala-20261026/`.
The cloud review is `report/cloud-review/CCZG506_Assignment1_Review.docx`.
For another group, start from `config/group.example.json` and supply its actual
details. Use `docs/DEMONSTRATION.md` when recording the project.

Reproduce the cloud review with:

```bash
python -m src.generate_report --draft \
  --snapshot-root evidence/cloud-prayogshala-20261026 \
  --output-dir report/cloud-review
```

After entering the actual video URL, generate the final report with the same
command and omit `--draft`. It writes `report/cloud-review/15.docx` and refuses stale
model/API evidence, incomplete group details, absent screenshots or unconfirmed
cloud evidence. `cloud_evidence_confirmed` is a human confirmation after checking
actual hosting evidence, not an automatic cloud detection result. The frozen
cloud inventory and screenshot hashes are checked before report generation.
Leave the flag false for local-only review. Only one member
uploads the final Word/PDF document to the portal.

Assignment I's supplied brief says **30 October 2026, 11:55 pm**. Confirm any
subsequent faculty announcement separately.
