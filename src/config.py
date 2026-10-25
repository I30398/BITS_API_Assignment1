"""
Central configuration for the CCZG506 Assignment I project.

Business problem: Telecom Customer Churn Prediction.
All paths are resolved relative to the project root so the pipelines run the
same way whether launched from the repo root, from src/, or by the Prefect
worker.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
EDA_DIR = OUTPUTS_DIR / "eda"
LOGS_DIR = OUTPUTS_DIR / "logs"
MODELS_DIR = OUTPUTS_DIR / "models"

RAW_DATASET = DATA_DIR / "telco_churn.csv"
CLEAN_DATASET = DATA_DIR / "telco_churn_clean.csv"

# Public source for the dataset (IBM Telco Customer Churn, 7043 records).
DATASET_URL = (
    "https://raw.githubusercontent.com/IBM/"
    "telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
)

# ---------------------------------------------------------------------------
# Dataset semantics
# ---------------------------------------------------------------------------
TARGET_COLUMN = "Churn"
ID_COLUMN = "customerID"

# Columns that are numeric in meaning (TotalCharges is read as object because of
# blank strings and is coerced during preprocessing).
NUMERIC_COLUMNS = ["tenure", "MonthlyCharges", "TotalCharges"]

# ---------------------------------------------------------------------------
# ML configuration
# ---------------------------------------------------------------------------
TEST_SIZE = 0.30          # 70% train / 30% test as required by Activity 2.2
RANDOM_STATE = 42


def ensure_dirs() -> None:
    """Create all output directories (idempotent)."""
    for d in (DATA_DIR, OUTPUTS_DIR, EDA_DIR, LOGS_DIR, MODELS_DIR):
        d.mkdir(parents=True, exist_ok=True)
