"""Build a review or submission report from current implementation evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from src import config
from src.artifact_io import source_fingerprint


def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def table(doc, columns, rows, widths=None):
    result = doc.add_table(rows=1, cols=len(columns))
    result.alignment = WD_TABLE_ALIGNMENT.CENTER
    result.autofit = False
    if widths is None:
        widths = [6.5 / len(columns)] * len(columns)
    for col, width in zip(result.columns, widths):
        col.width = Inches(width)
    for cell, title in zip(result.rows[0].cells, columns):
        cell.text = title
    for row in rows:
        for cell, value in zip(result.add_row().cells, row):
            cell.text = str(value)
    repeat = OxmlElement("w:tblHeader")
    result.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row_index, row in enumerate(result.rows):
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for col_index, cell in enumerate(row.cells):
            cell.width = Inches(widths[col_index])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            props = cell._tc.get_or_add_tcPr()
            borders = OxmlElement("w:tcBorders")
            for edge in ["top", "left", "bottom", "right"]:
                element = OxmlElement(f"w:{edge}")
                for key, val in {"val": "single", "sz": "4", "color": "D9D9D9"}.items():
                    element.set(qn(f"w:{key}"), val)
                borders.append(element)
            props.append(borders)
            shading = OxmlElement("w:shd")
            shading.set(qn("w:fill"), "243746" if row_index == 0 else
                        ("F2F5F7" if row_index % 2 else "FFFFFF"))
            props.append(shading)
            margins = OxmlElement("w:tcMar")
            for edge in ["top", "left", "bottom", "right"]:
                element = OxmlElement(f"w:{edge}")
                element.set(qn("w:w"), "85")
                element.set(qn("w:type"), "dxa")
                margins.append(element)
            props.append(margins)
            for paragraph in cell.paragraphs:
                if row_index == 0:
                    paragraph.paragraph_format.keep_with_next = True
                paragraph.paragraph_format.space_after = Pt(3)
                paragraph.paragraph_format.space_before = Pt(3)
                for run in paragraph.runs:
                    run.font.size = Pt(9)
                    if row_index == 0:
                        run.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return result


def image(doc, path, caption, width=6.2):
    if not path.exists():
        return
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.keep_with_next = True
    paragraph.add_run().add_picture(str(path), width=Inches(width))
    caption_paragraph = doc.add_paragraph(caption)
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in caption_paragraph.runs:
        run.italic = True
        run.font.size = Pt(9)


def validate_group(group):
    import re
    members = group.get("members", [])
    if not group.get("group_id") or not 2 <= len(members) <= 6:
        raise ValueError("Provide group_id and 2 to 6 actual members in config/group.json.")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", group["group_id"]):
        raise ValueError("Group ID must contain letters, digits, underscores or hyphens.")
    for member in members:
        if not all(member.get(k) for k in ["bits_id", "name", "contribution"]):
            raise ValueError("Every member needs a BITS ID, name and qualitative contribution.")
    if abs(sum(float(m.get("percentage", 0)) for m in members) - 100) > 0.001:
        raise ValueError("Member contribution percentages must total 100.")
    return group


def build(draft=False, group_path=None):
    group_path = group_path or config.PROJECT_ROOT / "config/group.json"
    group = read_json(group_path, {})
    metrics = read_json(config.MODELS_DIR / "latest_metrics.json")
    run = read_json(config.OUTPUTS_DIR / "latest_run.json", {})
    api = read_json(config.OUTPUTS_DIR / "api_details.json", {})
    if not metrics:
        raise ValueError("Run the revised workflow before generating a report.")
    if metrics.get("source_sha256") != source_fingerprint():
        raise ValueError("Current evidence was produced by different source code. Rerun the workflow.")
    if not draft:
        validate_group(group)
        if not group.get("video_url"):
            raise ValueError("Add the uploaded demonstration video's URL before final generation.")
        if not group.get("cloud_evidence_confirmed"):
            raise ValueError("Cloud hosting evidence is not confirmed. Use --draft for local review.")
        for name in ["01_dashboard.png", "02_flow_runs.png", "03_deployments.png",
                     "05_ml_run_logs.png", "06_data_run_logs.png"]:
            if not (config.SCREENSHOTS_DIR / name).exists():
                raise ValueError(f"Capture current dashboard evidence: {name}")
        if api.get("source_sha256") != source_fingerprint():
            raise ValueError("Capture fresh API details from the current implementation.")
    doc = Document()
    # The bundled Word template may carry a blue rule beneath its Title style.
    for root in [doc.styles.element, doc.element]:
        for border in root.xpath(".//w:pBdr"):
            border.getparent().remove(border)
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(0.7)
    section.left_margin = section.right_margin = Inches(1)
    for name in ["Normal", "Title", "Subtitle", "Heading 1", "Heading 2"]:
        style = doc.styles[name]
        style.font.name = "Calibri"
        style.font.color.rgb = RGBColor(0, 0, 0)
    normal = doc.styles["Normal"]
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.line_spacing = 1.08
    for name in ["Heading 1", "Heading 2"]:
        doc.styles[name].paragraph_format.keep_with_next = True
    doc.add_paragraph("Telecom Customer Churn Prediction", "Title")
    doc.add_paragraph("CCZG506 API driven Cloud Native Solutions", "Subtitle")
    doc.add_paragraph("Assignment I" + (" review copy" if draft else ""))
    doc.add_paragraph(
        "This project identifies customers at risk of leaving a telecom service. "
        "A scheduled Prefect workflow performs data preparation and exploration, "
        "then trains and evaluates two classifiers. Prefect APIs expose the "
        "application's flows, deployments and execution details.")
    doc.add_paragraph(f"Group number: {group.get('group_id', '________________')}")
    members = group.get("members") or [{"bits_id": "", "name": "", "contribution": "", "percentage": ""} for _ in range(2)]
    table(doc, ["BITS ID", "Name", "Contribution", "%"],
          [[m.get(k, "") for k in ["bits_id", "name", "contribution", "percentage"]] for m in members],
          [1.1, 1.3, 3.6, 0.5])
    doc.add_paragraph("Execution and evidence", "Heading 1")
    doc.add_paragraph(f"Execution environment: {run.get('environment', 'local')}. "
        f"Latest completed cycle: {run.get('completed_at', 'not captured')}. "
        "The original repository outputs are retained separately from these results.")
    if not group.get("cloud_evidence_confirmed"):
        doc.add_paragraph("The evidence in this review demonstrates local execution. "
                          "Cloud hosting has not yet been demonstrated.")
    doc.add_paragraph("1 Data pipeline", "Heading 1")
    doc.add_paragraph("1.1 Business understanding and data ingestion", "Heading 2")
    doc.add_paragraph("The business objective is to support retention decisions by predicting "
        "customer churn from account, service and demographic attributes. The public IBM "
        "Telco Customer Churn dataset contains 7043 records and 21 columns. Churn is a "
        "binary Yes or No target; customerID is excluded from model features.")
    doc.add_paragraph(f"Dataset source: {config.DATASET_URL}")
    image(doc, config.EDA_DIR / "univariate_churn_distribution.png", "Figure 1 Customer churn class balance", 4.5)
    doc.add_paragraph("1.2 Preprocessing", "Heading 2")
    doc.add_paragraph("The workflow coerces TotalCharges to numeric, identifies missing values, "
        "and induces 352 missing entries in each of tenure, MonthlyCharges and TotalCharges "
        "using a fixed random seed. Full-data EDA uses median imputation and Min-Max "
        "normalisation. The pre-imputation snapshot is passed separately to ML so that "
        "test records cannot influence training preprocessing.")
    stats = pd.read_csv(config.OUTPUTS_DIR / "summary_statistics.csv", index_col=0)
    table(doc, ["Feature", "Count", "Mean", "Std", "Min", "Max"],
          [[idx, int(row['count']), *[f"{row[k]:.2f}" for k in ['mean', 'std', 'min', 'max']]]
           for idx, row in stats.iterrows()], [1.45, 0.7, 1.1, 1.1, 1.0, 1.15])
    types = pd.read_csv(config.OUTPUTS_DIR / "data_types.csv")
    table(doc, ["Column", "Data type"], types.values.tolist(), [4.3, 2.2])
    preview = pd.read_csv(config.OUTPUTS_DIR / "normalisation_preview.csv")
    table(doc, ["Numeric feature", "Original example", "Normalised example"],
          [[c, f"{preview.iloc[0][c]:.2f}", f"{preview.iloc[0][c + '_norm']:.4f}"]
           for c in config.NUMERIC_COLUMNS], [2.5, 2, 2])
    doc.add_paragraph("1.3 Exploratory data analysis", "Heading 2")
    doc.add_paragraph("Tenure is binned into five bands. Encoding mappings and bin counts "
        "are saved. Pearson coefficients are calculated for numeric features and the binary "
        "target. Cramer's V measures categorical association without assuming an ordering "
        "between category codes. Random Forest exploratory importance is aggregated "
        "from one-hot category levels, using each original numeric feature once.")
    assoc = pd.read_csv(config.OUTPUTS_DIR / "categorical_associations.csv").head(6)
    table(doc, ["Categorical feature", "Association with churn"],
          [[row.feature, f"{row.cramers_v:.3f}"] for row in assoc.itertuples()], [3.5, 3])
    for name, caption in [
        ("correlation_heatmap.png", "Figure 2 Numeric correlations"),
        ("feature_importance.png", "Figure 3 Exploratory feature importance"),
        ("univariate_tenure_histogram.png", "Figure 4 Univariate tenure distribution"),
        ("bivariate_churn_by_contract.png", "Figure 5 Churn rate by contract"),
        ("bivariate_charges_by_churn.png", "Figure 6 Charges by churn outcome")]:
        image(doc, config.EDA_DIR / name, caption, 5.5)
    doc.add_paragraph("1.4 DataOps scheduling and monitoring", "Heading 2")
    doc.add_paragraph("One deployment runs every 120 seconds with concurrency limited to "
        "one cycle. DataOps completes before MLOps starts. Complete files are published by "
        "atomic replacement, and cross-process locks protect appended logs. Every task "
        "records its activity in the Prefect dashboard and JSONL logs; result tables are "
        "also available as Prefect artifacts.")
    for name, caption in [("03_deployments.png", "Figure 7 Deployment interval and status"),
                          ("02_flow_runs.png", "Figure 8 Scheduled execution history"),
                          ("06_data_run_logs.png", "Figure 9 Data preparation activity logs")]:
        image(doc, config.SCREENSHOTS_DIR / name, caption)
    doc.add_paragraph("2 Machine learning pipeline", "Heading 1")
    doc.add_paragraph("2.1 Preparation training and evaluation", "Heading 2")
    doc.add_paragraph("Logistic Regression provides a linear baseline; Random Forest "
        "captures non-linear relationships. A stratified 70/30 split produces 4930 "
        "training records and 2113 test records. Each model contains its own fitted "
        "preprocessing pipeline: numeric median imputation and standardisation, plus "
        "categorical imputation and one-hot encoding. All fitted parameters are learned "
        "from training records. Test records are transformed without refitting.")
    table(doc, ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC AUC"],
          [[m['model'], *[f"{m[k]:.4f}" for k in ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']]]
           for m in metrics['models']], [1.6, .98, .98, .98, .98, .98])
    image(doc, config.MODELS_DIR / "model_comparison.png", "Figure 10 Five metrics for each model")
    image(doc, config.MODELS_DIR / "confusion_matrices.png", "Figure 11 Holdout confusion matrices")
    doc.add_paragraph("2.2 MLOps and interpretation", "Heading 2")
    doc.add_paragraph("Every cycle records accuracy, precision, recall, F1 and ROC AUC "
        "for both models. The metrics history records timestamps, pipeline version and "
        "source fingerprint. Repeating evaluation on this fixed dataset demonstrates "
        "monitoring and logging; it does not establish drift detection or performance "
        "on a changing production population. Recall measures the proportion of actual "
        "churners identified, while precision measures how many flagged customers churn.")
    image(doc, config.SCREENSHOTS_DIR / "05_ml_run_logs.png", "Figure 12 ML task logs and metrics")
    doc.add_paragraph("3 API access", "Heading 1")
    doc.add_paragraph("The official Prefect client retrieves details through built-in APIs. "
        "Project filters keep unrelated flows out of the evidence. The saved response "
        "contains registered flows, deployment schedules and concurrency, recent run "
        "states, start times and durations. Aggregate statistics describe a bounded "
        "sample of up to 200 project runs and include child flows.")
    table(doc, ["Detail", "Retrieved value"], [
        ["Retrieved at", api.get('retrieved_at', 'Not captured')],
        ["Project flows", ', '.join(f['name'] for f in api.get('flows', []))],
        ["Deployments", ', '.join(d['name'] for d in api.get('deployments', []))],
        ["Recent executed runs", len(api.get('recent_flow_runs', []))],
        ["Sampled run states", str(api.get('run_statistics', {}).get('runs_by_state', {}))],
    ], [1.7, 4.8])
    image(doc, config.SCREENSHOTS_DIR / "01_dashboard.png", "Figure 13 Dashboard overview")
    doc.add_paragraph("4 Reproduction and demonstration", "Heading 1")
    doc.add_paragraph("Follow README.md for the tested Python 3.12 setup, local server "
        "and scheduled workflow. The local dashboard is at http://127.0.0.1:4207. "
        "Run python -m src.api_access to capture current API details. The Docker Compose "
        "package provides the same server and runner arrangement for local or cloud VM "
        "execution; selecting cloud configuration alone is not proof of deployment.")
    if group.get("video_url"):
        doc.add_paragraph("Demonstration video: " + group['video_url'])
    doc.add_paragraph("Dataset SHA256: " + metrics['raw_dataset_sha256'])
    output_dir = config.PROJECT_ROOT / "report/current"
    output_dir.mkdir(parents=True, exist_ok=True)
    name = "CCZG506_Assignment1_Review.docx" if draft else group['group_id'] + '.docx'
    output = output_dir / name
    doc.save(output)
    print(output)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", action="store_true", help="Generate a local review with incomplete submission details.")
    parser.add_argument("--group", type=Path)
    args = parser.parse_args()
    build(args.draft, args.group)
