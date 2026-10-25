"""
Generate the Word submission document for CCZG506 Assignment I.

Assembles explanations + the generated charts + dashboard screenshots + API
output into a structured .docx mapped section-by-section to the rubric. Run
AFTER both pipelines, the scheduled deployments, and src.api_access have run.

Usage:  python -m src.generate_report
Output: report/CCZG506_Assignment1_Report.docx
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from src import config

REPORT_DIR = config.PROJECT_ROOT / "report"
DOC_PATH = REPORT_DIR / "CCZG506_Assignment1_Report.docx"
ASSETS_DIR = config.PROJECT_ROOT / "assets"
HEADER_LOGO = ASSETS_DIR / "header_bits_logo.png"
FOOTER_BANNER = ASSETS_DIR / "footer_banner.png"

ACCENT = RGBColor(0x2A, 0x78, 0xD6)


def apply_header_footer(doc):
    """Add the BITS Pilani logo header and innovate/achieve/lead footer banner
    (extracted from the assignment template) to every page."""
    section = doc.sections[0]

    # Header - BITS Pilani logo, left-aligned (as in the template).
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.text = ""
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if HEADER_LOGO.exists():
        hp.add_run().add_picture(str(HEADER_LOGO), width=Inches(2.6))

    # Footer - innovate/achieve/lead banner, right-aligned (as in the template).
    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.text = ""
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if FOOTER_BANNER.exists():
        fp.add_run().add_picture(str(FOOTER_BANNER), width=Inches(1.8))


def add_index(doc):
    """Insert an auto-generated Table of Contents (Index) built from the
    Heading 1/2 styles. Word fills in the entries and page numbers when the
    document is opened (and fields are updated)."""
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("Index")
    r.bold = True
    r.font.size = Pt(14)

    p = doc.add_paragraph()
    run = p.add_run()

    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    # \o "1-2" = headings 1..2, \h = hyperlinks, \z = hide tab leader in web,
    # \u = use outline levels.
    instr.text = 'TOC \\o "1-2" \\h \\z \\u'

    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")

    placeholder_txt = OxmlElement("w:t")
    placeholder_txt.text = ("Right-click here and choose 'Update Field' to "
                            "build the Index (table of contents).")

    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")

    rpr = run._r
    rpr.append(fld_begin)
    rpr.append(instr)
    rpr.append(fld_sep)
    rpr.append(placeholder_txt)
    rpr.append(fld_end)


def set_update_fields_on_open(doc):
    """Tell Word to refresh all fields (incl. the TOC) when the file opens,
    so the Index populates without manual action."""
    settings = doc.settings.element
    upd = settings.find(qn("w:updateFields"))
    if upd is None:
        upd = OxmlElement("w:updateFields")
        settings.append(upd)
    upd.set(qn("w:val"), "true")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def h(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    return p


def para(doc, text, italic=False, bold=False, size=11):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.italic = italic
    run.bold = bold
    run.font.size = Pt(size)
    return p


def placeholder(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(f"[ SCREENSHOT: {text} ]")
    run.bold = True
    run.font.color.rgb = RGBColor(0xC9, 0x85, 0x00)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def add_image(doc, path: Path, width_in=6.0, caption=None):
    if path.exists():
        doc.add_picture(str(path), width=Inches(width_in))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if caption:
            c = doc.add_paragraph()
            run = c.add_run(caption)
            run.italic = True
            run.font.size = Pt(9)
            c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        placeholder(doc, f"{caption or path.name} (missing: {path.name})")


def add_table_from_df(doc, df: pd.DataFrame, max_rows=12, index_label=None):
    df = df.head(max_rows).copy()
    cols = ([index_label] if index_label else []) + list(df.columns)
    table = doc.add_table(rows=1, cols=len(cols))
    table.style = "Light Grid Accent 1"
    for i, col in enumerate(cols):
        table.rows[0].cells[i].text = str(col)
    for idx, row in df.iterrows():
        cells = table.add_row().cells
        offset = 0
        if index_label:
            cells[0].text = str(idx)
            offset = 1
        for j, col in enumerate(df.columns):
            val = row[col]
            if isinstance(val, float):
                val = f"{val:.4f}"
            cells[j + offset].text = str(val)
    return table


def load_json(path: Path, default=None):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


# ---------------------------------------------------------------------------
# document
# ---------------------------------------------------------------------------
def build():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    doc = Document()
    apply_header_footer(doc)

    # Title page ------------------------------------------------------------
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = t.add_run("CCZG506 - API-driven Cloud Native Solutions\nAssignment I")
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = ACCENT

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = sub.add_run(
        "Cloud-based Data Science / Machine Learning Application\n"
        "Telecom Customer Churn Prediction\n"
        "(Data Pipeline + ML Pipeline + API Access using Prefect)")
    r2.font.size = Pt(13)

    doc.add_paragraph()
    para(doc, "Group No: __________", bold=True)
    tbl = doc.add_table(rows=1, cols=4)
    tbl.style = "Light Grid Accent 1"
    for i, c in enumerate(["S.No", "BITS ID", "Name", "Contribution %"]):
        tbl.rows[0].cells[i].text = c
    for n in range(1, 4):
        cells = tbl.add_row().cells
        cells[0].text = str(n)

    doc.add_page_break()

    # Index / Table of Contents --------------------------------------------
    add_index(doc)
    doc.add_page_break()

    # Overview --------------------------------------------------------------
    h(doc, "1. Project Overview", 1)
    para(doc,
         "This project implements an end-to-end, cloud-native Data Science / "
         "Machine Learning application for predicting telecom customer churn. "
         "The solution is orchestrated with Prefect, which provides the flows, "
         "scheduled deployments, a web dashboard (the cloud dashboard), and a "
         "built-in REST API used for the API-access sub-objective.")
    para(doc, "Technology stack:", bold=True)
    for item in [
        "Orchestration / dashboard / API: Prefect 3.8",
        "Data & ML: pandas, NumPy, scikit-learn",
        "Visualisation: matplotlib, seaborn",
        "Dataset: IBM Telco Customer Churn (7,043 records, 21 columns)",
    ]:
        doc.add_paragraph(item, style="List Bullet")

    # ---- Sub-Objective 1 --------------------------------------------------
    h(doc, "2. Sub-Objective 1 - Data Pipeline (8 marks)", 1)

    h(doc, "1.1 Business Understanding", 2)
    para(doc,
         "Customer churn - customers discontinuing their subscription - is a "
         "major revenue risk for telecom operators, since acquiring a new "
         "customer costs far more than retaining an existing one. The business "
         "problem is: given a customer's demographics, account, and service "
         "usage attributes, predict whether the customer will churn, so the "
         "retention team can target high-risk customers proactively. This is a "
         "binary classification problem.")

    h(doc, "1.2 Data Ingestion", 2)
    para(doc,
         "The dataset is the public IBM Telco Customer Churn dataset (also "
         "distributed on Kaggle), with 7,043 records and 21 columns covering "
         "demographics (gender, SeniorCitizen, Partner, Dependents), account "
         "information (tenure, Contract, PaymentMethod, charges), and subscribed "
         "services. The target column is 'Churn' (Yes/No). The data pipeline's "
         "ingest task loads this CSV, with retries configured for resilience.")
    add_image(doc, config.EDA_DIR / "univariate_churn_distribution.png", 4.5,
              "Target class balance: 5,174 'No' vs 1,869 'Yes' (ingested data).")

    h(doc, "1.3 Data Pre-processing", 2)
    para(doc, "The following pre-processing activities are automated as Prefect "
              "tasks:")
    for item in [
        "Summary statistics via describe() on numeric features.",
        "Data types captured for every column.",
        "Missing-value check before and after processing.",
        "Inducing missing data: 5% of values in each numeric column "
        "(tenure, MonthlyCharges, TotalCharges) are randomly set to NaN to "
        "simulate dirty data.",
        "Imputation of numeric NaNs with the column median.",
        "Normalisation: Min-Max scaling of numeric columns to [0, 1].",
    ]:
        doc.add_paragraph(item, style="List Bullet")

    stats_path = config.OUTPUTS_DIR / "summary_statistics.csv"
    if stats_path.exists():
        para(doc, "Summary statistics (numeric features):", bold=True)
        sdf = pd.read_csv(stats_path, index_col=0)
        add_table_from_df(doc, sdf.round(2), index_label="feature")

    norm_path = config.OUTPUTS_DIR / "normalisation_preview.csv"
    if norm_path.exists():
        para(doc, "Normalisation preview (original vs _norm columns):", bold=True)
        add_table_from_df(doc, pd.read_csv(norm_path), max_rows=5)
    add_image(doc, config.PROJECT_ROOT / "outputs/screenshots/06_data_run_logs.png",
              6.5, "Data-pipeline run on the dashboard - the [1.3-*] log lines show "
              "summary stats, data types, the missing-value check, the induced "
              "missing data (352 cells per numeric column), median imputation and "
              "Min-Max normalisation.")

    h(doc, "1.4 Exploratory Data Analysis (EDA)", 2)
    para(doc, "EDA activities, all automated inside the data pipeline:")
    for item in [
        "Correlation coefficients across all (encoded) features.",
        "Correlation of numeric & categorical features with churn.",
        "Binning: 'tenure' grouped into bands (0-1 yr ... 5+ yr).",
        "Encoding: label-encoding of categorical features.",
        "Feature importance via a Random Forest.",
        "Univariate & bivariate visualisations.",
    ]:
        doc.add_paragraph(item, style="List Bullet")

    add_image(doc, config.EDA_DIR / "correlation_heatmap.png", 6.0,
              "Correlation matrix across all encoded features (diverging palette).")
    add_image(doc, config.EDA_DIR / "feature_importance.png", 6.0,
              "Random-Forest feature importance (top features w.r.t. churn).")
    add_image(doc, config.EDA_DIR / "univariate_tenure_histogram.png", 5.0,
              "Univariate analysis: distribution of customer tenure.")
    add_image(doc, config.EDA_DIR / "bivariate_churn_by_contract.png", 5.5,
              "Bivariate analysis: churn rate by contract type "
              "(month-to-month customers churn far more).")
    add_image(doc, config.EDA_DIR / "bivariate_charges_by_churn.png", 5.5,
              "Bivariate analysis: monthly charges by churn outcome.")

    h(doc, "1.5 DataOps - Automation, Scheduling & Dashboard", 2)
    para(doc,
         "Steps 1.3 and 1.4 are implemented as tasks inside a single Prefect "
         "flow (telco-data-pipeline). The flow is served as a deployment with "
         "an interval schedule of 2 minutes, so it runs automatically every 2 "
         "minutes. Every task logs its activity both to the Prefect dashboard "
         "and to a JSON-lines activity log. The screenshots below show the "
         "scheduled runs on the Prefect cloud dashboard.")
    add_image(doc, config.PROJECT_ROOT / "outputs/screenshots/02_flow_runs.png",
              6.5, "Prefect dashboard - flow runs auto-scheduled every 2 minutes "
              "(note the 'auto-scheduled' tag and 2-minute spacing).")
    add_image(doc, config.PROJECT_ROOT / "outputs/screenshots/03_deployments.png",
              6.5, "Prefect dashboard - the two deployments with their schedules.")
    add_image(doc, config.PROJECT_ROOT / "outputs/screenshots/01_dashboard.png",
              6.5, "Prefect main dashboard overview.")
    add_image(doc, config.PROJECT_ROOT / "outputs/screenshots/06_data_run_logs.png",
              6.5, "A single telco-data-pipeline run opened on the dashboard - the "
              "task run graph and the per-task activity logs for steps 1.3 and 1.4.")

    # ---- Sub-Objective 2 --------------------------------------------------
    h(doc, "3. Sub-Objective 2 - Machine Learning Pipeline (5 marks)", 1)

    h(doc, "2.1 Model Preparation", 2)
    para(doc,
         "Churn prediction is a binary classification task. Two complementary "
         "algorithms were selected: (1) Logistic Regression - a fast, "
         "interpretable linear baseline, and (2) Random Forest - a non-linear "
         "ensemble that captures feature interactions. Features are label-"
         "encoded; Logistic Regression additionally standardises features in a "
         "scikit-learn pipeline.")

    h(doc, "2.2 Model Training", 2)
    para(doc,
         "The cleaned dataset is split 70% train / 30% test using a stratified "
         "split (preserving the churn ratio) with a fixed random seed for "
         "reproducibility. Both models are trained on the training set.")

    h(doc, "2.3 Model Evaluation", 2)
    metrics = load_json(config.MODELS_DIR / "latest_metrics.json")
    if metrics:
        para(doc, "Evaluation on the 30% hold-out test set:", bold=True)
        mdf = pd.DataFrame(metrics["models"])[
            ["model", "accuracy", "precision", "recall", "f1_score", "roc_auc"]
        ]
        add_table_from_df(doc, mdf)
        para(doc,
             f"Best model by F1-score: {metrics['best']['model']} "
             f"(F1 = {metrics['best']['f1_score']}, "
             f"accuracy = {metrics['best']['accuracy']}).")
    add_image(doc, config.MODELS_DIR / "model_comparison.png", 6.0,
              "Model evaluation metrics for both algorithms.")
    add_image(doc, config.MODELS_DIR / "confusion_matrices.png", 6.0,
              "Confusion matrices on the hold-out test set.")

    h(doc, "2.4 MLOps - Monitoring & Metric Logging", 2)
    para(doc,
         "The ML pipeline (telco-ml-pipeline) is also a scheduled Prefect "
         "deployment running every 2 minutes. For every run it logs at least "
         "four metrics - accuracy, precision, recall, F1-score and ROC-AUC - to "
         "the dashboard and appends them to a metrics-history CSV so model "
         "performance can be monitored for drift over time.")
    add_image(doc, config.PROJECT_ROOT / "outputs/screenshots/05_ml_run_logs.png",
              6.5, "A completed telco-ml-pipeline run on the dashboard - the task "
              "graph plus the [2.4-mlops] log lines recording accuracy, precision, "
              "recall, F1-score and ROC-AUC for both models.")

    # ---- Sub-Objective 3 --------------------------------------------------
    h(doc, "4. Sub-Objective 3 - API Access (2 marks)", 1)
    para(doc,
         "Key application details are retrieved programmatically using "
         "Prefect's built-in REST API (via the official Python client). The "
         "script src/api_access.py retrieves and displays the following "
         "application details:")
    api = load_json(config.OUTPUTS_DIR / "api_details.json")
    if api:
        for item in [
            f"Flows registered: {len(api.get('flows', []))}",
            f"Deployments (with schedules): {len(api.get('deployments', []))}",
            f"Recent flow runs and their states: "
            f"{len(api.get('recent_flow_runs', []))} shown",
            f"Run statistics: {api.get('run_statistics', {})}",
        ]:
            doc.add_paragraph(item, style="List Bullet")

        para(doc, "Deployments retrieved via API:", bold=True)
        ddf = pd.DataFrame([
            {"name": d["name"], "paused": d["paused"],
             "schedule": ", ".join(
                 f"every {int(s['interval_seconds'])}s"
                 for s in d["schedules"] if s.get("interval_seconds")),
             "tags": ", ".join(d["tags"])}
            for d in api.get("deployments", [])
        ])
        if not ddf.empty:
            add_table_from_df(doc, ddf)

        para(doc, "Recent flow runs retrieved via API:", bold=True)
        rdf = pd.DataFrame(api.get("recent_flow_runs", []))
        if not rdf.empty:
            add_table_from_df(doc, rdf, max_rows=10)

    para(doc, "Console output of src/api_access.py:", bold=True)
    console = config.OUTPUTS_DIR / "api_access_console.txt"
    if console.exists():
        mono = doc.add_paragraph()
        run = mono.add_run(console.read_text(encoding="utf-8"))
        run.font.name = "Consolas"
        run.font.size = Pt(8)
    para(doc, "(The full console output above is the live result of running "
              "python -m src.api_access against the Prefect API.)", italic=True,
         size=9)

    # ---- Appendix ---------------------------------------------------------
    h(doc, "5. How to Run (Appendix)", 1)
    for step in [
        "pip install -r requirements.txt",
        "Terminal 1:  prefect server start   (dashboard at http://127.0.0.1:4200)",
        "Terminal 2:  set PREFECT_API_URL=http://127.0.0.1:4200/api",
        "             python -m src.data_pipeline    (run data pipeline once)",
        "             python -m src.ml_pipeline       (run ML pipeline once)",
        "             python -m src.deploy            (schedule both every 2 min)",
        "             python -m src.api_access        (retrieve API details)",
    ]:
        doc.add_paragraph(step, style="List Number")

    set_update_fields_on_open(doc)
    doc.save(DOC_PATH)
    print(f"Report written to: {DOC_PATH}")


if __name__ == "__main__":
    build()
