"""Project configuration constants for the cyber-threat detection pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_RAW_DIR = ROOT / "data" / "raw"
DATA_PROCESSED_DIR = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"
OUTPUTS_FIGURES_DIR = ROOT / "outputs" / "figures"
OUTPUTS_METRICS_DIR = ROOT / "outputs" / "metrics"

TARGET_COLUMN = "Label"
RANDOM_STATE = 42
TEST_SIZE = 0.2
SAMPLE_SIZE = 200000

RAW_COMBINED_PATH = DATA_PROCESSED_DIR / "raw_combined.csv"
X_TRAIN_PATH = DATA_PROCESSED_DIR / "X_train.csv"
X_TEST_PATH = DATA_PROCESSED_DIR / "X_test.csv"
Y_TRAIN_PATH = DATA_PROCESSED_DIR / "y_train.csv"
Y_TEST_PATH = DATA_PROCESSED_DIR / "y_test.csv"

SCALER_PATH = MODELS_DIR / "scaler.joblib"
SELECTED_FEATURES_PATH = MODELS_DIR / "selected_features.json"

MODEL_PATHS = {
    "logistic_regression": MODELS_DIR / "logistic_regression.joblib",
    "random_forest": MODELS_DIR / "random_forest.joblib",
    "gradient_boosting": MODELS_DIR / "gradient_boosting.joblib",
}

METRICS_SUMMARY_PATH = OUTPUTS_METRICS_DIR / "metrics_summary.json"
BEST_MODEL_PATH = OUTPUTS_METRICS_DIR / "best_model.json"
