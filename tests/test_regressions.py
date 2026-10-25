"""Regressions for leakage, file publication and concurrent activity logging."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.artifact_io import atomic_path, write_csv
from src import config, preprocessing as pp, eda
from src.modelling import make_model
from src.ml_pipeline import split


def test_preprocessing_fits_training_values_only():
    train = pd.DataFrame({
        "tenure": [1., 3., np.nan, 5.],
        "MonthlyCharges": [10., np.nan, 30., 50.],
        "TotalCharges": [100., 300., 500., np.nan],
        "Contract": ["monthly", "yearly", "monthly", "yearly"],
    })
    test = pd.DataFrame({"tenure": [9999.], "MonthlyCharges": [9999.],
                         "TotalCharges": [np.nan], "Contract": ["unseen"]})
    model = make_model(LogisticRegression(), train.columns)
    model.fit(train, [0, 1, 0, 1])
    numeric = model.named_steps["preprocessing"].named_transformers_["numeric"]
    expected = train[config.NUMERIC_COLUMNS].median().to_numpy()
    np.testing.assert_allclose(numeric.named_steps["imputer"].statistics_, expected)
    scale_before = numeric.named_steps["scaler"].mean_.copy()
    assert len(model.predict(test)) == 1
    np.testing.assert_allclose(numeric.named_steps["imputer"].statistics_, expected)
    np.testing.assert_array_equal(numeric.named_steps["scaler"].mean_, scale_before)


def test_stratified_split_excludes_id_target_and_duplicate_features(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "LOGS_DIR", tmp_path)
    df = pp.coerce_types(pp.load_raw())
    df, _ = pp.induce_missing(df)
    df["tenure_norm"] = 0.0
    train, test, y_train, y_test = split.fn(df)
    assert (len(train), len(test)) == (4930, 2113)
    assert set(train.index).isdisjoint(test.index)
    assert not {config.ID_COLUMN, config.TARGET_COLUMN, "tenure_norm"} & set(train.columns)
    assert abs(y_train.mean() - y_test.mean()) < 0.001
    assert train[config.NUMERIC_COLUMNS].isna().sum().sum() > 0


def test_failed_publication_preserves_last_complete_file(tmp_path):
    path = tmp_path / "input.csv"
    old = pd.DataFrame({"value": [1, 2, 3]})
    write_csv(old, path, index=False)
    with pytest.raises(RuntimeError):
        with atomic_path(path) as temp:
            temp.write_text("incomplete")
            raise RuntimeError("simulated interrupted writer")
    pd.testing.assert_frame_equal(pd.read_csv(path), old)
    assert not list(tmp_path.glob(".input-*"))


def test_concurrent_reader_never_sees_empty_or_partial_csv(tmp_path):
    path = tmp_path / "input.csv"
    frame = pd.DataFrame({"value": range(400)})
    write_csv(frame, path, index=False)
    def writer():
        for _ in range(35):
            write_csv(frame, path, index=False)
    def reader():
        for _ in range(70):
            pd.testing.assert_frame_equal(pd.read_csv(path), frame)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(writer), pool.submit(reader), pool.submit(reader)]
        for future in futures:
            future.result()


def test_json_logs_are_valid_under_multiple_processes(tmp_path):
    path = tmp_path / "activity.jsonl"
    code = ("from pathlib import Path; from src.artifact_io import append_record; "
            f"p=Path({str(path)!r}); "
            "[append_record(p, {'n': n, 'payload': 'x'*9000}) for n in range(25)]")
    processes = [subprocess.Popen([sys.executable, "-c", code]) for _ in range(4)]
    assert all(p.wait(timeout=30) == 0 for p in processes)
    records = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(records) == 100
    assert all(len(x["payload"]) == 9000 for x in records)


def test_string_dtype_encoding_and_no_duplicate_importance_features():
    df = pp.coerce_types(pp.load_raw().head(200))
    for col in df.select_dtypes(include="object"):
        df[col] = df[col].astype("string")
    df = pp.impute_numeric(df)
    df, _ = pp.normalise(df)
    encoded, mappings = eda.encode_categoricals(df)
    assert "Contract" in mappings and "Churn" in mappings
    assert encoded["Churn"].dtype.kind in "iu"
    corr = eda.correlation_matrix(encoded)
    assert "PaymentMethod" not in corr.columns
    assert not any(c.endswith("_norm") for c in corr.columns)
    importance = eda.feature_importance(encoded)
    assert not any(c.endswith("_norm") for c in importance.index)


def test_categorical_association_does_not_depend_on_category_order():
    frame = pd.DataFrame({"Contract": ["a", "a", "b", "b", "c", "c"],
                          "Churn": ["Yes", "Yes", "No", "No", "Yes", "No"]})
    first = eda.categorical_associations(frame).iloc[0].cramers_v
    frame["Contract"] = pd.Categorical(frame["Contract"], categories=["c", "a", "b"])
    assert eda.categorical_associations(frame).iloc[0].cramers_v == pytest.approx(first)
