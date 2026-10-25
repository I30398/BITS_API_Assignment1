"""Train-only preprocessing shared by the two churn classifiers."""
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src import config


def make_model(estimator, columns):
    numeric = list(config.NUMERIC_COLUMNS)
    categorical = [c for c in columns if c not in numeric]
    transformer = ColumnTransformer([
        ("numeric", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), numeric),
        ("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), categorical),
    ])
    return Pipeline([("preprocessing", transformer), ("classifier", estimator)])
