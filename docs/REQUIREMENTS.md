# Assignment I requirement mapping

| Rubric item | Implementation | Fresh evidence |
| --- | --- | --- |
| Business problem | Telecom churn; README and report | Domain explanation and dataset |
| Public dataset | data/telco_churn.csv; src/config.py | Source URL, shape and SHA256 |
| Summary and types | src/preprocessing.py; src/data_pipeline.py | summary_statistics.csv, data_types.csv, Prefect tables |
| Missing checks and numeric induction | handle_missing task | missing_before.csv, missing_after_induction.csv, logs |
| Normalisation | normalise task for EDA | normalisation_preview.csv and dashboard table |
| Correlations | numeric Pearson and categorical Cramer's V | correlation_matrix.csv, categorical_associations.csv |
| Binning and encoding | encode_and_bin task | tenure_bins.csv, encoding_mappings.json |
| Feature importance | one-hot RF importance aggregated by original feature | feature_importance.csv and chart |
| Univariate/bivariate EDA | visualise task | Six current EDA charts |
| Every 2 minutes | src/deploy.py; serialized parent workflow | Active 120s schedule, completed scheduled parent run IDs |
| Activity logs and dashboard | src/logging_utils.py; src/dashboard_artifacts.py | JSONL records and Prefect run logs/artifacts |
| Two algorithms | Logistic Regression and Random Forest | Serialized fitted preprocessing+model pipelines |
| 70/30 training/testing | split task before fitting transformations | 4930/2113 split, train-only regression check |
| Evaluation and MLOps | src/ml_pipeline.py | Five metrics per model, confusion matrices, timestamped history |
| Built-in APIs and four details | src/api_access.py | Current JSON/console response, report tables |
| Cloud application/dashboard | Portable Compose package | Actual cloud execution evidence still requires hosting |
| Report and contributions | src/generate_report.py; config/group.json | Reviewed report, actual member details and contributions |
| Video | docs/DEMONSTRATION.md | Actual uploaded whole-project demo URL |

Original outputs and screenshots are historical. New checks and hashes are saved
in outputs/current/verification.json and cover the revised implementation only.
