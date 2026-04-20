# ARCHITECTURE & DESIGN ARTIFACT
## Smart Cybersecurity Threat Prediction Platform

---

## System Architecture Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DATA SOURCES (Input)                            │
│  CICIDS2017 CSVs  │  UNSW-NB15 CSVs  │  KDD Cup 1999 CSVs          │
│  (Primary)        │  (Benchmarking)  │  (Benchmarking)             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│               STAGE 1: DATA INGESTION LAYER                         │
│  scripts/01_ingest.py                                               │
│  • Load CSV files with pandas                                       │
│  • Validate required columns                                        │
│  • Concatenate multi-day files                                      │
│  • Output: data/processed/raw_combined.csv                          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│         STAGE 2: PREPROCESSING & FEATURE ENGINEERING                │
│  scripts/02_preprocess.py                                           │
│  • Remove duplicates & drop identifier columns                      │
│  • Replace infinite values with column mean                         │
│  • Label encode: BENIGN=0, all attacks=1                            │
│  • Min-Max normalization → features scaled to [0, 1]               │
│  • Feature selection via RF importance (top 20)                     │
│  • SMOTE → balance classes in training set only                     │
│  • 80/20 stratified train/test split                                │
│  Outputs:                                                           │
│    data/processed/X_train.csv, X_test.csv                           │
│    data/processed/y_train.csv, y_test.csv                           │
│    models/scaler.joblib                                             │
│    outputs/metrics/selected_features.json                           │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  STAGE 3: MACHINE LEARNING ENGINE                   │
│  scripts/03_train.py                                                │
│                                                                     │
│  ┌──────────────────┐  ┌─────────────────┐  ┌───────────────────┐  │
│  │ Logistic         │  │ Random Forest   │  │ Gradient          │  │
│  │ Regression       │  │ (100 trees)     │  │ Boosting          │  │
│  │ (Baseline)       │  │ (Primary)       │  │ (100 estimators)  │  │
│  │                  │  │                 │  │                   │  │
│  │ Interpretable    │  │ ~92% accuracy   │  │ ~94% ROC-AUC      │  │
│  │ Auditable        │  │ High recall     │  │ Low false neg.    │  │
│  └──────────────────┘  └─────────────────┘  └───────────────────┘  │
│                                                                     │
│  Each model outputs: predicted label, confidence score              │
│  Saved to: models/*.joblib                                          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  STAGE 4: EVALUATION LAYER                          │
│  scripts/04_evaluate.py                                             │
│  • Accuracy, Precision, Recall, F1-Score, ROC-AUC per model        │
│  • Confusion matrices (PNG) per model                               │
│  • Feature importance bar chart (RF)                                │
│  • Primary model selection by recall                                │
│  Outputs:                                                           │
│    outputs/metrics/metrics_summary.json                             │
│    outputs/metrics/best_model.json                                  │
│    outputs/figures/confusion_matrix_*.png                           │
│    outputs/figures/feature_importance_rf.png                        │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│            STAGE 5: STREAMLIT DASHBOARD (User Interface)            │
│  dashboard/app.py                                                   │
│                                                                     │
│  Sidebar: Model selector, project info                              │
│                                                                     │
│  Main:                                                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  STATUS BANNER: ✅ SAFE / ⚠️ THREAT DETECTED               │    │
│  │  KPI Cards: Accuracy | Precision | Recall | F1              │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │  Tab 1: Model Comparison Table                              │    │
│  │  Tab 2: Confusion Matrices (3 side-by-side)                 │    │
│  │  Tab 3: Feature Importance Chart                            │    │
│  │  Tab 4: Upload CSV → Get Predictions                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Target users: SOC Analysts, Security Managers                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
CICIDS2017 CSV
     │
     ▼
[01_ingest.py] ──→ raw_combined.csv
                         │
                         ▼
              [02_preprocess.py]
                    │         │
              X_train.csv   X_test.csv   ← SMOTE only on X_train
              y_train.csv   y_test.csv
              scaler.joblib
              selected_features.json
                    │
                    ▼
              [03_train.py]
                    │
          ┌─────────┼──────────┐
          │         │          │
         LR.joblib  RF.joblib  GB.joblib
          │         │          │
          └─────────┼──────────┘
                    │
                    ▼
              [04_evaluate.py]
                    │
          metrics_summary.json
          confusion_matrix_*.png
          feature_importance_rf.png
                    │
                    ▼
            [app.py / Streamlit]
                    │
            [SOC Analyst UI]
```

---

## Use Case Diagram

```
              ┌───────────────────────────────────┐
              │   Cybersecurity Threat Prediction  │
              │              System               │
              │                                   │
  SOC ───────►│ View dashboard metrics            │
  Analyst     │ View confusion matrices           │
              │ View feature importance           │
              │ Upload traffic CSV                │
              │ Download prediction results       │
              │ Select active model               │
              │                                   │
  Security ──►│ View model comparison             │
  Manager     │ Review system status              │
              │                                   │
  System ────►│ Load models at startup            │
(automated)   │ Preprocess uploaded CSV           │
              │ Run predictions                   │
              └───────────────────────────────────┘
```

---

## Entity Relationship / Data Structure

```
NetworkTrafficRecord {
  // Raw features from CICIDS2017
  Destination_Port: int
  Flow_Duration: float
  Total_Fwd_Packets: int
  Total_Backward_Packets: int
  Total_Length_of_Fwd_Packets: float
  Total_Length_of_Bwd_Packets: float
  Fwd_Packet_Length_Max: float
  Fwd_Packet_Length_Min: float
  Bwd_Packet_Length_Max: float
  Flow_Bytes_per_s: float
  Flow_Packets_per_s: float
  Flow_IAT_Mean: float
  Flow_IAT_Std: float
  ... (78 total features in CICIDS2017)
  Label: string  // BENIGN, DDoS, DoS Hulk, etc.

  // Added by preprocessing
  label_binary: int  // 0=Normal, 1=Attack
  label_original: string
}

ModelOutput {
  prediction: int        // 0 or 1
  confidence: float      // 0.0 to 1.0 (from predict_proba)
  attack_label: string   // "NORMAL" or "ATTACK"
}

EvaluationMetrics {
  model: string
  accuracy: float
  precision: float
  recall: float
  f1_score: float
  roc_auc: float
}
```

---

## Threat Categories Handled

| Threat Type | Dataset Source | Binary Label |
|-------------|---------------|--------------|
| DDoS | CICIDS2017 | Attack (1) |
| DoS | CICIDS2017 | Attack (1) |
| Brute Force | CICIDS2017 | Attack (1) |
| Port Scan | CICIDS2017 | Attack (1) |
| Web Attack | CICIDS2017 | Attack (1) |
| Botnet | CICIDS2017 | Attack (1) |
| Infiltration | CICIDS2017 | Attack (1) |
| Phishing (proxy via web attack) | CICIDS2017 | Attack (1) |
| Normal Traffic | CICIDS2017 | Normal (0) |

---

## Assumptions & Realistic Limitations

1. **No live data**: This is trained and tested on benchmark CSVs only. It will not connect to any real bank network.

2. **CICIDS2017 is not Nigerian data**: The document acknowledges this in the research gaps section. The models trained on it will not perfectly reflect Keystone Bank's actual traffic patterns.

3. **Gradient Boosting training time**: On the full CICIDS2017 dataset (~2.8M rows), sklearn GradientBoostingClassifier will be slow. Consider sampling or using XGBoost instead.

4. **SMOTE memory**: Full CICIDS2017 + SMOTE may require 8GB+ RAM. Consider chunked processing or sampling to 500k rows for the prototype.

5. **Streamlit is local**: The dashboard is a localhost app, not deployed. For demo purposes this is fine.

6. **No authentication**: Intentionally excluded. Not in scope for the prototype.
