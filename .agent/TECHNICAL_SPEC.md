# TECHNICAL SPECIFICATION
## Smart Cybersecurity Threat Prediction Platform

---

## requirements.txt

```
pandas==2.1.4
numpy==1.26.2
scikit-learn==1.3.2
imbalanced-learn==0.11.0
xgboost==2.0.3
streamlit==1.29.0
matplotlib==3.8.2
seaborn==0.13.0
joblib==1.3.2
shap==0.44.0
```

---

## config.py (place at project root)

```python
from pathlib import Path

ROOT = Path(__file__).parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"
OUTPUTS_DIR = ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
METRICS_DIR = OUTPUTS_DIR / "metrics"

# CICIDS2017 column config
TARGET_COLUMN = " Label"          # Note: has leading space in CICIDS2017 files
BINARY_TARGET = "label_binary"    # 0=Normal, 1=Attack
MULTI_TARGET = "label_multi"      # Attack type string

# Drop these columns before training (identifiers, not features)
COLS_TO_DROP = [
    "Flow ID", " Source IP", " Source Port",
    " Destination IP", " Destination Port", " Timestamp"
]

# Train/test split
TEST_SIZE = 0.2
RANDOM_STATE = 42

# Feature selection
TOP_N_FEATURES = 20               # Keep top 20 features by RF importance

# Models
MODEL_NAMES = ["logistic_regression", "random_forest", "gradient_boosting"]
```

---

## 01_ingest.py

```python
"""
Stage 1: Data Ingestion
Loads CICIDS2017 CSV files, validates columns, combines into single DataFrame.
Outputs: data/processed/raw_combined.csv
"""
import logging
import pandas as pd
from pathlib import Path
from config import DATA_RAW, DATA_PROCESSED, TARGET_COLUMN

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS_SAMPLE = [TARGET_COLUMN, " Total Fwd Packets", " Total Backward Packets"]


def load_cicids2017(data_dir: Path) -> pd.DataFrame:
    """Load all CICIDS2017 day-files from data_dir and concatenate them."""
    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")
    
    logger.info(f"Found {len(csv_files)} CSV files: {[f.name for f in csv_files]}")
    frames = []
    for f in csv_files:
        logger.info(f"Loading {f.name} ...")
        df = pd.read_csv(f, low_memory=False)
        logger.info(f"  → {len(df)} rows, {len(df.columns)} columns")
        frames.append(df)
    
    combined = pd.concat(frames, ignore_index=True)
    logger.info(f"Combined dataset: {len(combined)} rows")
    return combined


def validate_columns(df: pd.DataFrame) -> None:
    """Raise ValueError if required columns are missing."""
    for col in REQUIRED_COLUMNS_SAMPLE:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found. Check dataset format.")
    logger.info("Column validation passed.")


def save(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved combined dataset to {output_path}")


if __name__ == "__main__":
    df = load_cicids2017(DATA_RAW)
    validate_columns(df)
    save(df, DATA_PROCESSED / "raw_combined.csv")
    logger.info("Stage 1 complete.")
```

---

## 02_preprocess.py

```python
"""
Stage 2: Preprocessing and Feature Engineering
Implements the preprocessing pipeline described in Methodology Section 3.14:
- Data cleaning (duplicates, nulls, infinite values)
- Label encoding
- Min-Max normalization
- SMOTE oversampling (training set only)
- Train/test split (80/20 stratified)
- Feature selection via RF importance scores

Outputs:
- data/processed/X_train.csv, X_test.csv, y_train.csv, y_test.csv
- models/scaler.joblib
- outputs/metrics/selected_features.json
"""
import json
import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE

from config import (DATA_PROCESSED, MODELS_DIR, METRICS_DIR,
                    TARGET_COLUMN, BINARY_TARGET, COLS_TO_DROP,
                    TEST_SIZE, RANDOM_STATE, TOP_N_FEATURES)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_raw(path: Path) -> pd.DataFrame:
    logger.info(f"Loading raw data from {path}")
    return pd.read_csv(path, low_memory=False)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates, handle infinite and null values."""
    initial = len(df)
    df = df.drop_duplicates()
    logger.info(f"Removed {initial - len(df)} duplicate rows")

    # Drop identifier columns not useful for ML
    drop_cols = [c for c in COLS_TO_DROP if c in df.columns]
    df = df.drop(columns=drop_cols)
    logger.info(f"Dropped columns: {drop_cols}")

    # Replace infinite values with NaN then fill
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    null_counts = df.isnull().sum().sum()
    logger.info(f"Filling {null_counts} null/inf values with column mean")
    df.fillna(df.mean(numeric_only=True), inplace=True)

    return df


def encode_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create binary label column: BENIGN=0, all attacks=1.
    Also store the original label for multi-class reference.
    """
    df["label_original"] = df[TARGET_COLUMN].str.strip()
    df[BINARY_TARGET] = (df["label_original"] != "BENIGN").astype(int)
    logger.info(f"Label distribution:\n{df[BINARY_TARGET].value_counts()}")
    return df


def split_features_target(df: pd.DataFrame):
    """Separate feature matrix X from target y."""
    drop = [TARGET_COLUMN, "label_original", BINARY_TARGET]
    drop = [c for c in drop if c in df.columns]
    X = df.drop(columns=drop).select_dtypes(include=[np.number])
    y = df[BINARY_TARGET]
    logger.info(f"Feature matrix shape: {X.shape}")
    return X, y


def normalize(X_train, X_test):
    """Apply Min-Max scaling — fit on train, transform both."""
    scaler = MinMaxScaler()
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
    X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)
    logger.info("Min-Max normalization applied.")
    return X_train_scaled, X_test_scaled, scaler


def select_features(X_train, y_train, top_n: int = TOP_N_FEATURES):
    """
    Use Random Forest feature importance to select top N features.
    This reduces dimensionality and improves model efficiency per methodology Section 3.15.
    """
    logger.info(f"Running feature selection — keeping top {top_n} features...")
    rf = RandomForestClassifier(n_estimators=50, random_state=RANDOM_STATE, n_jobs=-1)
    rf.fit(X_train, y_train)
    importances = pd.Series(rf.feature_importances_, index=X_train.columns)
    selected = importances.nlargest(top_n).index.tolist()
    logger.info(f"Selected features: {selected}")
    return selected


def apply_smote(X_train, y_train):
    """
    Apply SMOTE to address class imbalance in training set ONLY.
    Per methodology: 'SMOTE technique was used to synthetically generate minor class samples.'
    NEVER apply SMOTE to the test set.
    """
    logger.info(f"Class distribution before SMOTE: {dict(y_train.value_counts())}")
    sm = SMOTE(random_state=RANDOM_STATE)
    X_res, y_res = sm.fit_resample(X_train, y_train)
    logger.info(f"Class distribution after SMOTE: {dict(pd.Series(y_res).value_counts())}")
    return X_res, y_res


def save_splits(X_train, X_test, y_train, y_test, path: Path):
    path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(X_train).to_csv(path / "X_train.csv", index=False)
    pd.DataFrame(X_test).to_csv(path / "X_test.csv", index=False)
    pd.Series(y_train).to_csv(path / "y_train.csv", index=False, header=["label"])
    pd.Series(y_test).to_csv(path / "y_test.csv", index=False, header=["label"])
    logger.info(f"Train/test splits saved to {path}")


if __name__ == "__main__":
    df = load_raw(DATA_PROCESSED / "raw_combined.csv")
    df = clean(df)
    df = encode_labels(df)
    X, y = split_features_target(df)

    # Stratified 80/20 split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Normalize
    X_train, X_test, scaler = normalize(X_train, X_test)

    # Feature selection
    selected_features = select_features(X_train, y_train)
    X_train = X_train[selected_features]
    X_test = X_test[selected_features]

    # SMOTE on training set only
    X_train_sm, y_train_sm = apply_smote(X_train, y_train)

    # Save
    save_splits(X_train_sm, X_test, y_train_sm, y_test, DATA_PROCESSED)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, MODELS_DIR / "scaler.joblib")
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(METRICS_DIR / "selected_features.json", "w") as f:
        json.dump(selected_features, f)
    logger.info("Stage 2 complete.")
```

---

## 03_train.py

```python
"""
Stage 3: Model Training
Trains three classifiers per methodology Section 3.16:
  1. Logistic Regression (interpretable baseline)
  2. Random Forest (ensemble, primary)
  3. Gradient Boosting (sequential ensemble)

All models saved to models/ with joblib.
"""
import logging
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from config import DATA_PROCESSED, MODELS_DIR, RANDOM_STATE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_splits():
    X_train = pd.read_csv(DATA_PROCESSED / "X_train.csv")
    y_train = pd.read_csv(DATA_PROCESSED / "y_train.csv")["label"]
    return X_train, y_train


def train_logistic_regression(X_train, y_train):
    """
    Logistic Regression: interpretable baseline classifier.
    Max_iter increased to ensure convergence on large dataset.
    """
    logger.info("Training Logistic Regression...")
    model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE, n_jobs=-1)
    model.fit(X_train, y_train)
    logger.info("Logistic Regression training complete.")
    return model


def train_random_forest(X_train, y_train):
    """
    Random Forest: ensemble of 100 decision trees.
    Per literature: achieves ~92% accuracy in banking cybersecurity tasks.
    """
    logger.info("Training Random Forest...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    logger.info("Random Forest training complete.")
    return model


def train_gradient_boosting(X_train, y_train):
    """
    Gradient Boosting: sequential ensemble where each tree corrects previous errors.
    Per literature: achieves ~94% ROC-AUC in banking cybersecurity tasks.
    Using sklearn's implementation (substitute with xgboost if preferred).
    """
    logger.info("Training Gradient Boosting (this may take several minutes)...")
    model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=RANDOM_STATE
    )
    model.fit(X_train, y_train)
    logger.info("Gradient Boosting training complete.")
    return model


def save_model(model, name: str):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / f"{name}.joblib"
    joblib.dump(model, path)
    logger.info(f"Saved {name} to {path}")


if __name__ == "__main__":
    X_train, y_train = load_splits()
    logger.info(f"Training on {X_train.shape[0]} samples, {X_train.shape[1]} features")

    lr = train_logistic_regression(X_train, y_train)
    save_model(lr, "logistic_regression")

    rf = train_random_forest(X_train, y_train)
    save_model(rf, "random_forest")

    gb = train_gradient_boosting(X_train, y_train)
    save_model(gb, "gradient_boosting")

    logger.info("Stage 3 complete. All models saved.")
```

---

## 04_evaluate.py

```python
"""
Stage 4: Model Evaluation
Evaluates all 3 models on held-out test set.
Generates:
- outputs/metrics/metrics_summary.json (Accuracy, Precision, Recall, F1, ROC-AUC)
- outputs/figures/confusion_matrix_<model>.png
- outputs/figures/feature_importance_rf.png

Per methodology Section 3.18: recall is the primary criterion.
A missed attack (false negative) is more costly than a false alarm.
"""
import json
import logging
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)
from config import DATA_PROCESSED, MODELS_DIR, FIGURES_DIR, METRICS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL_NAMES = ["logistic_regression", "random_forest", "gradient_boosting"]
DISPLAY_NAMES = {
    "logistic_regression": "Logistic Regression",
    "random_forest": "Random Forest",
    "gradient_boosting": "Gradient Boosting"
}


def load_test_data():
    X_test = pd.read_csv(DATA_PROCESSED / "X_test.csv")
    y_test = pd.read_csv(DATA_PROCESSED / "y_test.csv")["label"]
    return X_test, y_test


def evaluate_model(model, X_test, y_test, name: str) -> dict:
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

    metrics = {
        "model": DISPLAY_NAMES[name],
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4) if y_prob is not None else None,
    }
    logger.info(f"{name}: {metrics}")
    return metrics, y_pred


def plot_confusion_matrix(y_test, y_pred, name: str):
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                xticklabels=["Normal", "Attack"],
                yticklabels=["Normal", "Attack"])
    ax.set_title(f"Confusion Matrix — {DISPLAY_NAMES[name]}")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    plt.tight_layout()
    out = FIGURES_DIR / f"confusion_matrix_{name}.png"
    fig.savefig(out, dpi=100)
    plt.close(fig)
    logger.info(f"Saved confusion matrix to {out}")


def plot_feature_importance(rf_model, feature_names: list):
    importances = pd.Series(rf_model.feature_importances_, index=feature_names)
    top15 = importances.nlargest(15).sort_values()
    fig, ax = plt.subplots(figsize=(8, 6))
    top15.plot(kind="barh", ax=ax, color="steelblue")
    ax.set_title("Top 15 Feature Importances — Random Forest")
    ax.set_xlabel("Importance Score")
    plt.tight_layout()
    out = FIGURES_DIR / "feature_importance_rf.png"
    fig.savefig(out, dpi=100)
    plt.close(fig)
    logger.info(f"Saved feature importance chart to {out}")


if __name__ == "__main__":
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    X_test, y_test = load_test_data()
    all_metrics = []

    for name in MODEL_NAMES:
        model = joblib.load(MODELS_DIR / f"{name}.joblib")
        metrics, y_pred = evaluate_model(model, X_test, y_test, name)
        all_metrics.append(metrics)
        plot_confusion_matrix(y_test, y_pred, name)

    with open(METRICS_DIR / "metrics_summary.json", "w") as f:
        json.dump(all_metrics, f, indent=2)
    logger.info("Metrics saved to outputs/metrics/metrics_summary.json")

    # Feature importance from Random Forest
    rf = joblib.load(MODELS_DIR / "random_forest.joblib")
    plot_feature_importance(rf, X_test.columns.tolist())

    # Determine best model by recall
    best = max(all_metrics, key=lambda m: m["recall"])
    logger.info(f"Best model by recall: {best['model']} (recall={best['recall']})")
    with open(METRICS_DIR / "best_model.json", "w") as f:
        json.dump(best, f, indent=2)

    logger.info("Stage 4 complete.")
```

---

## 05_predict.py

```python
"""
Stage 5: Prediction on new CSV input.
Used by the dashboard to classify uploaded traffic data.
"""
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

from config import MODELS_DIR, METRICS_DIR

def load_artifacts():
    """Load scaler, selected features, and all trained models."""
    scaler = joblib.load(MODELS_DIR / "scaler.joblib")
    with open(METRICS_DIR / "selected_features.json") as f:
        selected_features = json.load(f)
    models = {
        "Logistic Regression": joblib.load(MODELS_DIR / "logistic_regression.joblib"),
        "Random Forest": joblib.load(MODELS_DIR / "random_forest.joblib"),
        "Gradient Boosting": joblib.load(MODELS_DIR / "gradient_boosting.joblib"),
    }
    return scaler, selected_features, models


def preprocess_input(df: pd.DataFrame, scaler: MinMaxScaler, selected_features: list) -> pd.DataFrame:
    """Apply same preprocessing steps used during training."""
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(df.mean(numeric_only=True))
    df = df.select_dtypes(include=[np.number])
    
    # Keep only selected features (handle missing ones gracefully)
    available = [f for f in selected_features if f in df.columns]
    missing = [f for f in selected_features if f not in df.columns]
    if missing:
        for m in missing:
            df[m] = 0.0  # Fill missing features with 0
    
    df = df[selected_features]
    df_scaled = pd.DataFrame(scaler.transform(df), columns=selected_features)
    return df_scaled


def predict(df: pd.DataFrame, model_name: str = "Random Forest") -> pd.DataFrame:
    """Run prediction and return results DataFrame."""
    scaler, selected_features, models = load_artifacts()
    X = preprocess_input(df, scaler, selected_features)
    model = models[model_name]
    
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]
    
    results = df.copy()
    results["Prediction"] = ["ATTACK" if p == 1 else "NORMAL" for p in predictions]
    results["Confidence"] = (probabilities * 100).round(2)
    results["Threat_Score"] = (probabilities * 100).round(1)
    return results
```

---

## dashboard/app.py

```python
"""
Streamlit Dashboard — Smart Cybersecurity Threat Prediction Platform
Primary interface for SOC analysts at Keystone Bank.

Displays: system status, model metrics, confusion matrices,
feature importance, and on-demand prediction for uploaded traffic data.
"""
import json
import joblib
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CyberShield | Keystone Bank",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

ROOT = Path(__file__).parent.parent
MODELS_DIR = ROOT / "models"
FIGURES_DIR = ROOT / "outputs" / "figures"
METRICS_DIR = ROOT / "outputs" / "metrics"


# ── Resource loaders (cached) ─────────────────────────────────────────────────
@st.cache_resource
def load_models():
    return {
        "Logistic Regression": joblib.load(MODELS_DIR / "logistic_regression.joblib"),
        "Random Forest": joblib.load(MODELS_DIR / "random_forest.joblib"),
        "Gradient Boosting": joblib.load(MODELS_DIR / "gradient_boosting.joblib"),
    }

@st.cache_resource
def load_scaler():
    return joblib.load(MODELS_DIR / "scaler.joblib")

@st.cache_data
def load_metrics():
    with open(METRICS_DIR / "metrics_summary.json") as f:
        return json.load(f)

@st.cache_data
def load_selected_features():
    with open(METRICS_DIR / "selected_features.json") as f:
        return json.load(f)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Keystone_Bank_logo.png/200px-Keystone_Bank_logo.png",
             use_column_width=True)
    st.title("CyberShield Platform")
    st.markdown("**Smart Cybersecurity Threat Prediction**")
    st.markdown("---")
    selected_model = st.selectbox(
        "Active Classification Model",
        ["Random Forest", "Gradient Boosting", "Logistic Regression"],
        index=0
    )
    st.markdown("---")
    st.markdown("**Project Info**")
    st.caption("Nwankwo Chibuike Chidobem")
    st.caption("VUG/CSC/22/7490")
    st.caption("Veritas University, Abuja")
    st.caption("Supervisor: Mr. Victor Omopariola")


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🛡️ Smart Cybersecurity Threat Prediction Platform")
st.markdown("*AI-Powered Threat Detection for Keystone Bank Nigeria — SOC Analyst Dashboard*")
st.markdown("---")


# ── Load assets ───────────────────────────────────────────────────────────────
try:
    models = load_models()
    scaler = load_scaler()
    metrics_data = load_metrics()
    selected_features = load_selected_features()
    assets_loaded = True
except Exception as e:
    st.error(f"⚠️ Failed to load model assets: {e}")
    st.info("Run the pipeline scripts first: 01_ingest → 02_preprocess → 03_train → 04_evaluate")
    assets_loaded = False
    st.stop()


# ── Metrics summary ───────────────────────────────────────────────────────────
metrics_df = pd.DataFrame(metrics_data)
active_metrics = metrics_df[metrics_df["model"].str.contains(selected_model.split()[0])].iloc[0]

# Status banner
overall_status = "SYSTEM OPERATIONAL"
st.success(f"✅ {overall_status} — Active Model: **{selected_model}**")

# KPI cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Accuracy", f"{active_metrics['accuracy']*100:.1f}%")
col2.metric("Precision", f"{active_metrics['precision']*100:.1f}%")
col3.metric("Recall", f"{active_metrics['recall']*100:.1f}%", help="Primary metric — false negatives are most costly")
col4.metric("F1-Score", f"{active_metrics['f1_score']*100:.1f}%")

st.markdown("---")


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Model Comparison",
    "🔲 Confusion Matrices",
    "📈 Feature Importance",
    "🔍 Upload & Predict"
])


# Tab 1: Model Comparison
with tab1:
    st.subheader("Performance Comparison — All Models")
    display_df = metrics_df[["model", "accuracy", "precision", "recall", "f1_score", "roc_auc"]].copy()
    display_df.columns = ["Model", "Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]
    for col in ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]:
        display_df[col] = display_df[col].apply(lambda x: f"{x*100:.2f}%" if x else "N/A")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("""
    **Note on primary metric:** Recall is prioritized in this platform. A missed attack 
    (false negative) in a banking environment causes more damage than a false alarm. 
    The model with the highest recall is recommended as the primary classifier.
    """)


# Tab 2: Confusion Matrices
with tab2:
    st.subheader("Confusion Matrices")
    model_keys = ["logistic_regression", "random_forest", "gradient_boosting"]
    display_labels = ["Logistic Regression", "Random Forest", "Gradient Boosting"]
    cols = st.columns(3)
    for i, (key, label) in enumerate(zip(model_keys, display_labels)):
        img_path = FIGURES_DIR / f"confusion_matrix_{key}.png"
        if img_path.exists():
            cols[i].image(str(img_path), caption=label, use_column_width=True)
        else:
            cols[i].warning(f"Image not found: {img_path.name}")


# Tab 3: Feature Importance
with tab3:
    st.subheader("Feature Importance — Random Forest")
    fi_path = FIGURES_DIR / "feature_importance_rf.png"
    if fi_path.exists():
        st.image(str(fi_path), use_column_width=True)
    else:
        st.warning("Feature importance chart not found. Run 04_evaluate.py first.")
    st.markdown("""
    The chart above shows which network traffic features have the most predictive 
    power for detecting cyber threats. This supports explainability and auditability 
    requirements under the CBN Cybersecurity Framework.
    """)


# Tab 4: Upload & Predict
with tab4:
    st.subheader("Upload Network Traffic Data for Prediction")
    st.markdown("""
    Upload a CSV file containing network traffic features. The system will classify 
    each record as **NORMAL** or **ATTACK** using the selected model.
    """)

    uploaded_file = st.file_uploader("Upload traffic CSV", type=["csv"])

    if uploaded_file:
        try:
            df_input = pd.read_csv(uploaded_file, low_memory=False)
            st.info(f"Loaded {len(df_input)} records, {len(df_input.columns)} columns")

            # Preprocess
            df_proc = df_input.replace([np.inf, -np.inf], np.nan)
            df_proc = df_proc.fillna(df_proc.mean(numeric_only=True))
            df_num = df_proc.select_dtypes(include=[np.number])

            available = [f for f in selected_features if f in df_num.columns]
            for missing in [f for f in selected_features if f not in df_num.columns]:
                df_num[missing] = 0.0
            df_sel = df_num[selected_features]
            df_scaled = pd.DataFrame(scaler.transform(df_sel), columns=selected_features)

            # Predict
            model = models[selected_model]
            preds = model.predict(df_scaled)
            probs = model.predict_proba(df_scaled)[:, 1]

            df_results = df_input.copy()
            df_results["Prediction"] = ["🔴 ATTACK" if p == 1 else "🟢 NORMAL" for p in preds]
            df_results["Confidence (%)"] = (probs * 100).round(2)

            # Summary
            attack_count = (preds == 1).sum()
            normal_count = (preds == 0).sum()
            
            if attack_count > 0:
                st.error(f"⚠️ THREAT DETECTED — {attack_count} malicious records found out of {len(preds)}")
            else:
                st.success(f"✅ SAFE — All {len(preds)} records classified as normal traffic")

            col_a, col_b = st.columns(2)
            col_a.metric("Normal Records", normal_count)
            col_b.metric("Attack Records", attack_count)

            st.dataframe(
                df_results[["Prediction", "Confidence (%)"]].head(500),
                use_container_width=True,
                hide_index=False
            )

            # Download
            csv_out = df_results.to_csv(index=False).encode()
            st.download_button("Download Results CSV", csv_out, "predictions.csv", "text/csv")

        except Exception as e:
            st.error(f"Error processing file: {e}")
            st.exception(e)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Smart Cybersecurity Threat Prediction Platform | Keystone Bank Nigeria | "
    "Veritas University, Abuja — BSc Computer Science Final Year Project 2026"
)
```

---

## README.md

```markdown
# Smart Cybersecurity Threat Prediction Platform
### Keystone Bank Nigeria — Final Year Project

**Author:** Nwankwo Chibuike Chidobem (VUG/CSC/22/7490)  
**Supervisor:** Mr. Victor Omopariola  
**Institution:** Veritas University, Abuja

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get the dataset
Download CICIDS2017 from: https://www.unb.ca/cic/datasets/ids-2017.html  
Place all day CSV files in `data/raw/`

### 3. Run the pipeline
```bash
python scripts/01_ingest.py
python scripts/02_preprocess.py
python scripts/03_train.py
python scripts/04_evaluate.py
```

Or all at once:
```bash
bash run_pipeline.sh
```

### 4. Launch dashboard
```bash
streamlit run dashboard/app.py
```

---

## Architecture

```
CSV Data → Preprocessing → ML Engine → Streamlit Dashboard
```

**Models:** Logistic Regression, Random Forest, Gradient Boosting  
**Primary dataset:** CICIDS2017  
**Primary metric:** Recall (false negatives most costly in banking)
```
