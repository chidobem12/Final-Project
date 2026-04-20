"""Palantir-style military cyber threat dashboard."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st
from config import BEST_MODEL_PATH, METRICS_SUMMARY_PATH, OUTPUTS_FIGURES_DIR
from scripts.predictor import predict_from_csv

st.set_page_config(
    page_title="GOTHAM | Cyber Threat Operations",
    layout="wide",
    page_icon="🛡️"
)

COLORS = {
    "bg_primary": "#0a0a0a",
    "bg_secondary": "#111111",
    "bg_tertiary": "#1a1a1a",
    "border": "#2a2a2a",
    "text_primary": "#e0e0e0",
    "text_secondary": "#888888",
    "accent_cyan": "#00d4aa",
    "accent_red": "#ff3b3b",
    "accent_yellow": "#ffb300",
    "accent_blue": "#4dabf7",
    "success": "#00ff88",
    "danger": "#ff3333",
    "warning": "#ffaa00",
}

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    * {{
        font-family: 'JetBrains Mono', 'Space Grotesk', monospace;
    }}

    .stApp {{
        background-color: {COLORS['bg_primary']};
    }}

    .stHeader {{
        background-color: {COLORS['bg_primary']} !important;
        border-bottom: 1px solid {COLORS['border']};
    }}

    .stSidebar {{
        background-color: {COLORS['bg_secondary']};
        border-right: 1px solid {COLORS['border']};
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: {COLORS['text_primary']} !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600;
    }}

    .title-brand {{
        font-size: 1.4rem;
        font-weight: 700;
        color: {COLORS['accent_cyan']} !important;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }}

    .tactical-box {{
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid {COLORS['accent_cyan']};
    }}

    .status-indicator {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0.75rem;
        border-radius: 2px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }}

    .status-online {{
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid {COLORS['success']};
        color: {COLORS['success']};
    }}

    .status-offline {{
        background: rgba(255, 59, 59, 0.1);
        border: 1px solid {COLORS['danger']};
        color: {COLORS['danger']};
    }}

    .status-warning {{
        background: rgba(255, 179, 0, 0.1);
        border: 1px solid {COLORS['warning']};
        color: {COLORS['warning']};
    }}

    .metric-card {{
        background: {COLORS['bg_tertiary']};
        border: 1px solid {COLORS['border']};
        padding: 1rem;
        text-align: center;
    }}

    .metric-value {{
        font-size: 1.75rem;
        font-weight: 700;
        color: {COLORS['accent_cyan']};
        font-family: 'JetBrains Mono', monospace;
    }}

    .metric-label {{
        font-size: 0.7rem;
        color: {COLORS['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.25rem;
    }}

    .data-table {{
        border: 1px solid {COLORS['border']};
    }}

    .stDataFrame {{
        border: 1px solid {COLORS['border']};
    }}

    div[data-testid="stDataFrame"] table {{
        border: 1px solid {COLORS['border']};
    }}

    div[data-testid="stDataFrame"] thead {{
        background: {COLORS['bg_tertiary']};
    }}

    div[data-testid="stDataFrame"] th {{
        color: {COLORS['text_secondary']};
        border-bottom: 1px solid {COLORS['border']};
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    div[data-testid="stDataFrame"] td {{
        color: {COLORS['text_primary']};
        border-bottom: 1px solid {COLORS['border']};
    }}

    .stSelectbox label, .stFileUploader label, .stTabs [data-testid="stMarkdownContainer"] {{
        color: {COLORS['text_secondary']} !important;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    .stSelectbox > div > div {{
        background: {COLORS['bg_tertiary']};
        border: 1px solid {COLORS['border']};
        color: {COLORS['text_primary']};
    }}

    .stTabs [data-testid="stTabbedContent"] {{
        border: 1px solid {COLORS['border']};
        background: {COLORS['bg_secondary']};
    }}

    .stTabs [data-baseweb="tab"] {{
        background: {COLORS['bg_tertiary']};
        border: 1px solid {COLORS['border']};
        color: {COLORS['text_secondary']};
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }}

    .stTabs [aria-selected="true"] {{
        background: {COLORS['bg_secondary']} !important;
        border-bottom: 2px solid {COLORS['accent_cyan']};
        color: {COLORS['accent_cyan']} !important;
    }}

    .stButton > button {{
        background: {COLORS['bg_tertiary']};
        border: 1px solid {COLORS['accent_cyan']};
        color: {COLORS['accent_cyan']};
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }}

    .stButton > button:hover {{
        background: {COLORS['accent_cyan']};
        color: {COLORS['bg_primary']};
    }}

    .stDownloadButton > button {{
        background: {COLORS['accent_cyan']};
        color: {COLORS['bg_primary']};
    }}

    .pulse-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: {COLORS['success']};
        animation: pulse 2s infinite;
    }}

    @keyframes pulse {{
        0% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.5; transform: scale(1.2); }}
        100% {{ opacity: 1; transform: scale(1); }}
    }}

    .section-header {{
        color: {COLORS['text_secondary']};
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 0.5rem;
        padding-bottom: 0.25rem;
        border-bottom: 1px solid {COLORS['border']};
    }}

    .divider {{
        height: 1px;
        background: {COLORS['border']};
        margin: 1rem 0;
    }}

    .timestamp {{
        color: {COLORS['text_secondary']};
        font-size: 0.65rem;
        font-family: 'JetBrains Mono', monospace;
    }}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_metrics() -> dict:
    with METRICS_SUMMARY_PATH.open("r", encoding="utf-8") as fp:
        return json.load(fp)


@st.cache_data
def load_best_model() -> dict:
    with BEST_MODEL_PATH.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def render_header():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; border-bottom: 1px solid {COLORS['border']};">
        <div>
            <span class="title-brand">GOTHAM</span>
            <span style="color: {COLORS['text_secondary']}; margin-left: 1rem; font-size: 0.8rem;">// CYBER THREAT OPERATIONS PLATFORM</span>
        </div>
        <div style="display: flex; align-items: center; gap: 1.5rem;">
            <span class="timestamp">SYS.TIME: {current_time}</span>
            <span class="status-indicator status-online">
                <span class="pulse-dot"></span>
                SYSTEM ACTIVE
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div class="section-header">// OPERATIONAL STATUS</div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="tactical-box">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: {COLORS['text_secondary']}; font-size: 0.7rem;">ML ENGINE</span>
                <span class="status-indicator status-online">ONLINE</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: {COLORS['text_secondary']}; font-size: 0.7rem;">DATABASE</span>
                <span class="status-indicator status-online">CONNECTED</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: {COLORS['text_secondary']}; font-size: 0.7rem;">INFERENCE</span>
                <span class="status-indicator status-online">READY</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="divider"></div>', unsafe_allow_html=True)

        selected_model = st.selectbox("SELECT ACTIVE MODEL", options=model_names)

        best_model = best_model_info.get('best_model', 'N/A')
        is_best = "(OPTIMAL)" if selected_model == best_model else ""

        st.markdown(f"""
        <div class="tactical-box" style="border-left-color: {COLORS['accent_yellow']};">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.7rem; margin-bottom: 0.25rem;">BEST MODEL (RECALL)</div>
            <div style="color: {COLORS['accent_yellow']}; font-weight: 600; font-size: 0.9rem;">
                {best_model.upper()} {is_best}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="divider"></div>', unsafe_allow_html=True)

        st.markdown(f'<div class="section-header">// MODEL STATISTICS</div>', unsafe_allow_html=True)

        return selected_model


def render_metrics_grid(metrics: dict):
    cols = st.columns(5)
    metric_items = [
        ("Accuracy", metrics.get('accuracy', 0), COLORS['accent_cyan']),
        ("Precision", metrics.get('precision', 0), COLORS['accent_blue']),
        ("Recall", metrics.get('recall', 0), COLORS['accent_yellow']),
        ("F1 Score", metrics.get('f1', 0), COLORS['accent_cyan']),
        ("ROC-AUC", metrics.get('roc_auc', 0), COLORS['accent_cyan']),
    ]

    for col, (label, value, color) in zip(cols, metric_items):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {color};">{value:.4f}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def render_model_comparison(metrics_data: dict):
    st.markdown(f'<div class="section-header">// MODEL PERFORMANCE MATRIX</div>', unsafe_allow_html=True)

    df_metrics = pd.DataFrame(metrics_data).T.reset_index().rename(columns={"index": "MODEL"})
    df_metrics = df_metrics.round(4)

    st.dataframe(
        df_metrics,
        use_container_width=True,
        hide_index=True
    )


def render_confusion_matrices(model_names: list):
    st.markdown(f'<div class="section-header">// CONFUSION MATRICES</div>', unsafe_allow_html=True)

    cols = st.columns(len(model_names))
    for idx, model_name in enumerate(model_names):
        cm_path = OUTPUTS_FIGURES_DIR / f"confusion_matrix_{model_name}.png"
        with cols[idx]:
            if cm_path.exists():
                st.markdown(f"**{model_name.upper()}**")
                st.image(str(cm_path), use_container_width=True)
            else:
                st.warning(f"Matrix unavailable: {model_name}")


def render_feature_importance():
    st.markdown(f'<div class="section-header">// FEATURE IMPORTANCE (RF)</div>', unsafe_allow_html=True)

    fi_path = OUTPUTS_FIGURES_DIR / "feature_importance_rf.png"
    if fi_path.exists():
        st.image(str(fi_path), use_container_width=True)
    else:
        st.warning("Feature importance data unavailable.")


def render_prediction_tab(model_names: list, default_model: str):
    st.markdown(f'<div class="section-header">// THREAT PREDICTION ENGINE</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        upload = st.file_uploader("UPLOAD THREAT DATA", type=["csv"])

    with col2:
        run_model = st.selectbox(
            "SELECT MODEL",
            options=model_names,
            index=model_names.index(default_model)
        )

    if upload is not None:
        st.markdown(f'<div class="divider"></div>', unsafe_allow_html=True)

        temp_path = Path("/tmp") / upload.name
        temp_path.write_bytes(upload.getvalue())

        with st.spinner("EXECUTING PREDICTION ENGINE..."):
            results = predict_from_csv(temp_path, model_name=run_model)

        threat_count = (results['Prediction'] == 1).sum()
        benign_count = (results['Prediction'] == 0).sum()
        total = len(results)

        st.markdown(f"""
        <div style="display: flex; gap: 1rem; margin: 1rem 0;">
            <div class="tactical-box" style="flex: 1; border-left-color: {COLORS['danger']};">
                <div style="color: {COLORS['text_secondary']}; font-size: 0.65rem;">DETECTED THREATS</div>
                <div style="color: {COLORS['danger']}; font-size: 1.5rem; font-weight: 700;">{threat_count}</div>
            </div>
            <div class="tactical-box" style="flex: 1; border-left-color: {COLORS['success']};">
                <div style="color: {COLORS['text_secondary']}; font-size: 0.65rem;">BENIGN TRAFFIC</div>
                <div style="color: {COLORS['success']}; font-size: 1.5rem; font-weight: 700;">{benign_count}</div>
            </div>
            <div class="tactical-box" style="flex: 1; border-left-color: {COLORS['accent_cyan']};">
                <div style="color: {COLORS['text_secondary']}; font-size: 0.65rem;">TOTAL RECORDS</div>
                <div style="color: {COLORS['accent_cyan']}; font-size: 1.5rem; font-weight: 700;">{total}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**PREDICTION RESULTS**")
        st.dataframe(results.head(200), use_container_width=True, hide_index=True)

        csv_bytes = results.to_csv(index=False).encode("utf-8")
        st.download_button(
            "EXPORT RESULTS",
            data=csv_bytes,
            file_name=f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


artifacts_ready = METRICS_SUMMARY_PATH.exists() and BEST_MODEL_PATH.exists()

render_header()

if not artifacts_ready:
    st.markdown(f"""
    <div class="tactical-box" style="border-left-color: {COLORS['danger']};">
        <div style="color: {COLORS['danger']}; font-weight: 600;">// CRITICAL ERROR</div>
        <div style="color: {COLORS['text_secondary']}; margin-top: 0.5rem;">
            Model artifacts not found. Execute pipeline scripts 01 → 04 before accessing the dashboard.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

metrics_data = load_metrics()
best_model_info = load_best_model()
model_names = list(metrics_data.keys())

selected_model = render_sidebar()

selected_metrics = metrics_data[selected_model]

render_metrics_grid(selected_metrics)

st.markdown(f'<div class="divider"></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "MODEL COMPARISON",
    "CONFUSION MATRICES",
    "FEATURE IMPORTANCE",
    "PREDICTION ENGINE"
])

with tab1:
    render_model_comparison(metrics_data)

with tab2:
    render_confusion_matrices(model_names)

with tab3:
    render_feature_importance()

with tab4:
    render_prediction_tab(model_names, selected_model)