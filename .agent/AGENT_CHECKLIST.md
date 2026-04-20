# AGENT EXECUTION CHECKLIST
## Build this in exact order. Do not skip ahead.

---

## PHASE 1: Foundation (Do this first, always)

- [ ] Create `requirements.txt` with exact versions
- [ ] Create `config.py` at project root
- [ ] Create directory structure:
  ```
  mkdir -p data/raw data/processed models outputs/figures outputs/metrics scripts tests dashboard
  ```
- [ ] Create `run_pipeline.sh`

---

## PHASE 2: Pipeline Scripts (One at a time, test each)

- [ ] `scripts/01_ingest.py`
  - Must handle multiple CSV files in data/raw/
  - Must validate TARGET_COLUMN exists
  - Must log row counts per file
  - Test: python scripts/01_ingest.py → should create data/processed/raw_combined.csv

- [ ] `scripts/02_preprocess.py`
  - Must do: clean → encode labels → split → normalize → feature select → SMOTE
  - SMOTE ONLY on training set
  - Must save: X_train, X_test, y_train, y_test as CSVs
  - Must save: scaler.joblib, selected_features.json
  - Test: python scripts/02_preprocess.py → check data/processed/ populated

- [ ] `scripts/03_train.py`
  - Must train all 3 models in sequence (LR is fast, GB is slow)
  - Must save each as .joblib
  - Test: python scripts/03_train.py → check models/*.joblib exist

- [ ] `scripts/04_evaluate.py`
  - Must produce metrics_summary.json with all 4 metrics + ROC-AUC
  - Must produce 3 confusion matrix PNGs
  - Must produce feature_importance_rf.png
  - Must produce best_model.json
  - Test: python scripts/04_evaluate.py → check outputs/ populated

- [ ] `scripts/05_predict.py`
  - Must load all 3 artifacts (scaler, features, models)
  - Must handle missing columns gracefully (fill with 0)
  - Test: feed it a sample CSV, confirm it returns a DataFrame with Prediction + Confidence columns

---

## PHASE 3: Dashboard

- [ ] `dashboard/app.py`
  - Must load without errors if models exist
  - Must show error message (not crash) if models don't exist yet
  - Must have 4 tabs: Model Comparison, Confusion Matrices, Feature Importance, Upload & Predict
  - Must have sidebar with model selector
  - KPI metrics must match the selected model
  - Upload tab must return results within a few seconds for CSV < 10k rows
  - Test: `streamlit run dashboard/app.py`

---

## PHASE 4: Tests

- [ ] `tests/test_ingest.py` — test column validation, test multi-file concat
- [ ] `tests/test_preprocess.py` — test cleaning, test label encoding, test SMOTE not applied to test set
- [ ] `tests/test_models.py` — test model files exist, test prediction output shape

---

## PHASE 5: Documentation

- [ ] `README.md` — setup, dataset download link, run instructions
- [ ] Each script has module-level docstring explaining its role in the pipeline
- [ ] Key decisions are commented (e.g., why SMOTE is train-only, why recall is primary metric)

---

## COMMON MISTAKES TO AVOID

1. **SMOTE on test set** — this leaks information and inflates metrics. NEVER.
2. **Fitting scaler on full dataset** — must fit on train only, transform both.
3. **Hardcoded paths** — use pathlib.Path and ROOT constants.
4. **Not stripping whitespace from CICIDS2017 Label column** — it has leading/trailing spaces.
5. **Forgetting to handle infinite values** — CICIDS2017 has inf values from division operations.
6. **Not saving selected_features.json** — the dashboard needs this to match columns at prediction time.
7. **Using st.experimental_cache** — deprecated. Use st.cache_data and st.cache_resource.
8. **Not handling missing columns during prediction** — uploaded CSV may not have all features.

---

## CICIDS2017 QUIRKS (Important)

- The Label column is named `" Label"` with a **leading space** — strip it
- Contains `inf` and `-inf` values that must be replaced before any sklearn processing
- Column names have leading/trailing spaces — use `df.columns.str.strip()` after loading
- File sizes: each day CSV is 150-400MB; combined is ~2.8GB — handle with low_memory=False
- For testing/development: sample 100k rows to keep iteration fast

---

## DATASET DOWNLOAD LINKS

- **CICIDS2017**: https://www.unb.ca/cic/datasets/ids-2017.html (free, requires registration)
- **UNSW-NB15**: https://research.unsw.edu.au/projects/unsw-nb15-dataset
- **KDD Cup 1999**: https://kdd.ics.uci.edu/databases/kddcup99/kddcup99.html

For the prototype to be fully functional, only CICIDS2017 is required.

---

## EXPECTED RUNTIME (on standard laptop, full CICIDS2017)

| Script | Estimated Time |
|--------|---------------|
| 01_ingest.py | 2-5 min (loading ~2.8GB) |
| 02_preprocess.py | 5-15 min (SMOTE on large dataset) |
| 03_train.py (LR) | 2-5 min |
| 03_train.py (RF) | 5-10 min |
| 03_train.py (GB) | 20-40 min |
| 04_evaluate.py | 2-5 min |
| Dashboard startup | < 30 seconds |

**Recommendation for development**: Sample 200k rows from raw_combined.csv during preprocessing.
Add a `SAMPLE_SIZE = 200000` constant in config.py and use `df.sample(n=SAMPLE_SIZE)` in 02_preprocess.py.
This cuts training time dramatically and still produces meaningful results.
