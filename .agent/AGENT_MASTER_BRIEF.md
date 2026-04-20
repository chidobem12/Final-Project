# AGENT MASTER BRIEF
## Smart Cybersecurity Threat Prediction Platform
### Keystone Bank Nigeria — Final Year Project (BSc Computer Science, Veritas University)

---

## 0. HONEST CONTEXT (READ FIRST)

This is a **proof-of-concept prototype**, not a production system. The project is graded on:
- Working code that matches what was written in the proposal
- A functional Streamlit dashboard
- Trained ML models with reported metrics
- Clean, documented code structure

You are building exactly what the document says — no more, no less. Do not over-engineer. Do not add features not mentioned. The examiner will run the dashboard and look at the code.

---

## 1. PROJECT SUMMARY

**What it is:** A Python-based ML pipeline that ingests network traffic data (CSV), preprocesses it, trains 3 classifiers, evaluates them, and displays results through a Streamlit web dashboard for SOC analysts.

**What it is NOT:**
- Not a real-time network packet sniffer
- Not connected to any live bank infrastructure
- Not a production-ready security tool
- Not a deep learning system

**Primary dataset:** CICIDS2017 (the one the document commits to most heavily)
**Secondary datasets:** UNSW-NB15 and KDD Cup 1999 (for benchmarking/comparison — can be lighter treatment)

---

## 2. SYSTEM ARCHITECTURE (4-Stage Pipeline)

```
[CSV Input] → [Preprocessing Layer] → [ML Engine] → [Streamlit Dashboard]
```

### Stage 1: Data Ingestion Layer
- Load CICIDS2017 CSV files using pandas
- Validate required columns exist
- Handle multi-file loading (CICIDS2017 comes in multiple day-files)
- Pass clean DataFrame downstream

### Stage 2: Preprocessing & Feature Engineering Layer
- Remove duplicates
- Drop irrelevant columns (e.g., IPs, timestamps after feature extraction)
- Handle infinite values (replace with 0 or column mean)
- Handle null/NaN values
- Label encode categorical target column (attack label → numeric)
- Min-Max normalize all continuous features to [0, 1]
- Apply SMOTE to handle class imbalance on training set ONLY
- Train/test split: 80/20, stratified
- Feature selection using Random Forest importance scores (keep top N features)
- Save scaler and selected feature list for dashboard reuse

### Stage 3: Machine Learning Engine
Three independent classifiers, all from scikit-learn:
1. **Logistic Regression** — baseline, interpretable
2. **Random Forest** — ensemble, primary classifier
3. **Gradient Boosting** (GradientBoostingClassifier or XGBClassifier) — best performing

Each model:
- Trains on preprocessed training set
- Predicts on test set
- Outputs: predicted label, confidence score (predict_proba)
- Computes: Accuracy, Precision, Recall, F1-score, ROC-AUC
- Generates: Confusion matrix
- Saves trained model to disk (joblib/pickle)

Primary classifier for dashboard: the best-performing one (expected: Random Forest or Gradient Boosting)

### Stage 4: Streamlit Dashboard
Single-page dashboard showing:
- System status banner: "SAFE" (green) or "THREAT DETECTED" (red)
- Best model prediction + confidence score
- Attack type predicted
- Model comparison table (all 3 models, all metrics)
- Confusion matrices for each model (matplotlib embedded)
- Feature importance bar chart (top 15 features)
- Upload interface: analyst can upload a CSV and get predictions
- About section referencing the project

---

## 3. ACTORS / USERS

| Actor | Role | Interaction |
|-------|------|-------------|
| SOC Analyst | Primary user | Views dashboard, uploads traffic data, reads predictions |
| Security Manager | Secondary | Reviews model metrics and reports |
| System (automated) | Background | Runs pipeline, loads models |

No authentication required for the prototype. The dashboard is local/internal-use only.

---

## 4. FUNCTIONAL REQUIREMENTS (from the document)

| ID | Requirement |
|----|-------------|
| FR-01 | Ingest network traffic data in CSV format |
| FR-02 | Remove duplicates, nulls, irrelevant features |
| FR-03 | Classify each record as Normal or Malicious using LR, RF, and GB |
| FR-04 | Display accuracy, precision, recall, F1-score per model |
| FR-05 | Interactive Streamlit dashboard for analysts |
| FR-06 | Test against CICIDS2017 (DDoS, brute force, phishing, intrusion) |

## 5. NON-FUNCTIONAL REQUIREMENTS

| ID | Requirement |
|----|-------------|
| NFR-01 | Modular code — one Python script per pipeline stage |
| NFR-02 | Usable by non-programmers via the Streamlit UI |
| NFR-03 | Scalable — adding a new model should not require full rewrite |
| NFR-04 | Compliant in spirit with CBN Framework (interpretable, auditable) |
| NFR-05 | Runs on standard laptop hardware (no GPU required) |

---

## 5. TECH STACK

| Layer | Technology | Version / Notes |
|-------|-----------|-----------------|
| Language | Python | 3.10+ |
| Data handling | pandas, numpy | Latest stable |
| ML models | scikit-learn | Latest stable |
| Gradient Boosting | scikit-learn GradientBoostingClassifier OR xgboost | Either works |
| Class balancing | imbalanced-learn (SMOTE) | Latest stable |
| Explainability | shap | For feature importance (optional, can use RF built-in) |
| Dashboard | streamlit | Latest stable |
| Visualization | matplotlib, seaborn | Embedded in streamlit |
| Model persistence | joblib | Save/load trained models |
| Dimensionality reduction | scikit-learn (PCA optional) | Mentioned in doc but optional |

**No web framework needed. No database needed. No Docker needed. No API needed.**

---

## 6. FILE STRUCTURE

```
project/
├── data/
│   ├── raw/                    # CICIDS2017 CSVs go here (not committed)
│   └── processed/              # Preprocessed outputs
├── models/
│   ├── logistic_regression.joblib
│   ├── random_forest.joblib
│   ├── gradient_boosting.joblib
│   └── scaler.joblib           # MinMaxScaler
├── scripts/
│   ├── 01_ingest.py            # Stage 1: Data loading
│   ├── 02_preprocess.py        # Stage 2: Cleaning, encoding, SMOTE
│   ├── 03_train.py             # Stage 3: Train all 3 models
│   ├── 04_evaluate.py          # Stage 4: Metrics, confusion matrices
│   └── 05_predict.py           # Prediction on new CSV input
├── dashboard/
│   └── app.py                  # Streamlit app (main entry point)
├── outputs/
│   ├── metrics/                # JSON/CSV metrics per model
│   └── figures/                # Confusion matrix PNGs, feature importance
├── tests/
│   ├── test_ingest.py
│   ├── test_preprocess.py
│   └── test_models.py
├── requirements.txt
├── README.md
└── run_pipeline.sh             # One-command pipeline runner
```

---

## 7. DATASET NOTES

**CICIDS2017** — Primary. Download from: https://www.unb.ca/cic/datasets/ids-2017.html
- Files: Monday, Tuesday, Wednesday, Thursday, Friday CSVs
- Key columns: all numeric features + `Label` column (target)
- Label values: BENIGN, DDoS, DoS Hulk, PortScan, Bot, Infiltration, Web Attack, Brute Force, etc.
- Binary classification: BENIGN=0, everything else=1
- Multi-class: keep all label categories

**UNSW-NB15** — Secondary/benchmarking.
- Available from Australian Cyber Security Centre
- 9 attack categories + Normal

**KDD Cup 1999** — Tertiary/benchmarking. Old but standard.
- Available from UCI repository

**For the prototype to work without downloading 3 datasets:**
- Use CICIDS2017 as primary (required)
- Simulate or skip UNSW/KDD if time is short — the dashboard only needs to work

---

## 8. MODEL TRAINING SPECIFICS

### Binary Classification (primary):
- Target: 0 = Normal, 1 = Attack
- SMOTE applied to training set only, never test set

### Multi-class (secondary, optional):
- Target: specific attack type (DDoS, BruteForce, PortScan, etc.)
- Harder, fewer clean predictions — only add if time allows

### Expected metrics (based on literature in the document):
- Random Forest: ~92% accuracy, high recall
- Gradient Boosting: ~92% accuracy, ~94% ROC-AUC
- Logistic Regression: lower (~80-85%) but interpretable

### Hyperparameter tuning:
- Keep it simple: use defaults with light tuning via GridSearchCV on small param grid
- Don't over-tune — this is a proof of concept, not a competition

---

## 9. DASHBOARD SPECIFICS (app.py)

### Layout:
```
[Header: Platform Name + Keystone Bank branding]
[Sidebar: Upload CSV, Select Model, Options]

[Main area]:
  - Row 1: Status banner (SAFE / THREAT DETECTED)
  - Row 2: 3 metric cards (Accuracy | Precision | Recall)
  - Row 3: Tabs
      Tab 1: "Model Comparison" — table of all 3 models
      Tab 2: "Confusion Matrices" — 3 side-by-side plots
      Tab 3: "Feature Importance" — RF importance bar chart
      Tab 4: "Upload & Predict" — upload CSV, get predictions table
  - Footer: Project info, supervisor, university
```

### Streamlit patterns to use:
- `st.file_uploader()` for CSV upload
- `st.tabs()` for tabbed layout
- `st.metric()` for KPI cards
- `st.dataframe()` for results tables
- `st.pyplot()` for matplotlib figures
- `st.selectbox()` for model selection in sidebar
- `st.cache_data` / `st.cache_resource` for loading models

---

## 10. PIPELINE EXECUTION ORDER

Run in this order:
```bash
python scripts/01_ingest.py       # Loads and validates data
python scripts/02_preprocess.py   # Cleans, encodes, splits, SMOTEs
python scripts/03_train.py        # Trains and saves 3 models
python scripts/04_evaluate.py     # Generates metrics and figures
streamlit run dashboard/app.py    # Launches dashboard
```

Or just: `bash run_pipeline.sh`

---

## 11. WHAT THE AGENT MUST PRODUCE

Priority order — do these first:

1. `requirements.txt` — exact pinned versions
2. `scripts/01_ingest.py` — with docstrings, logging, column validation
3. `scripts/02_preprocess.py` — full preprocessing pipeline, saves artifacts
4. `scripts/03_train.py` — trains all 3 models, saves with joblib
5. `scripts/04_evaluate.py` — computes and saves all metrics + figures
6. `scripts/05_predict.py` — prediction on new CSV
7. `dashboard/app.py` — full Streamlit dashboard
8. `tests/` — basic unit tests for each stage
9. `README.md` — setup and run instructions

---

## 12. QUALITY STANDARDS

- Every script must have a `if __name__ == "__main__"` guard
- Every function must have a docstring
- Use Python logging (not print) for pipeline scripts
- Streamlit app can use print/st.write freely
- No hardcoded paths — use `pathlib.Path` and a `config.py` or constants at top of each file
- Handle missing data gracefully — don't let NaN/inf crash the pipeline silently
- Comments in code must reference what the project document says (e.g., `# SMOTE applied per methodology section 3.14`)

---

## 13. THINGS TO AVOID

- Do not add authentication — not in scope
- Do not use Flask/FastAPI — Streamlit only
- Do not build a real-time packet sniffer — CSV only
- Do not use deep learning (no TensorFlow, no PyTorch) — explicitly excluded in document
- Do not use external APIs or internet connections at runtime
- Do not over-comment obvious code — comment intent, not mechanics
- Do not build a database — flat files (CSV/joblib/JSON) only
