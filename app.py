import streamlit as st
import pandas as pd
import io
from od_analysis import compute_teu, group_by_country, top13

# ─── PAGE CONFIG ─────────────────────────────────────────────
st.set_page_config(
    page_title="JICT OD Analyzer",
    page_icon="🚢",
    layout="wide",
)

# ─── CUSTOM CSS ──────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 18px;
        text-align: center;
    }
    .metric-label { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 24px; font-weight: 700; color: #1e293b; margin: 4px 0 2px; }
    .metric-sub   { font-size: 11px; color: #94a3b8; }
    .section-title { font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; }
    div[data-testid="stDataFrame"] { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
    .stTabs [data-baseweb="tab"] { font-size: 13px; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── HEADER ──────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("## 🚢")
with col_title:
    st.markdown("### JICT OD Analyzer")
    st.caption("Origin & Destination Analysis · Business Development & Marketing Intelligence")

st.divider()

# ─── SIDEBAR ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Upload File")
    uploaded_file = st.file_uploader(
        "Upload raw data Excel / CSV",
        type=["xlsx", "xls", "csv"],
        help="File must contain the standard JICT container columns"
    )
    st.divider()
    st.markdown("### ⚙️ Configuration")

    top_n = st.slider(
        "Top N Countries",
        min_value=13,
        max_value=100,
        value=13,
        step=1,
        help="Number of top countries to show in the ranking"
    )

    exclude_indonesia = st.toggle(
        "Exclude Indonesia",
        value=True,
        help="Remove Indonesia from the ranking (domestic traffic, not O/D)"
    )

    st.markdown("""
    | Parameter | Value |
    |---|---|
    | TEU weight 20ft | × 1.0 |
    | TEU weight 40ft | × 2.0 |
    | TEU weight 45ft | × 2.25 |
    """)
    st.divider()
    st.caption("JICT BDMI Division · v1.0")


# ─── MAIN CONTENT ────────────────────────────────────────────
if uploaded_file is None:
    st.info("👈 Upload your Excel file from the sidebar to get started.")
    st.stop()

# ─── READ FILE ───────────────────────────────────────────────
try:
    if uploaded_file.name.endswith(".csv"):
        df_raw = pd.read_csv(uploaded_file)
    else:
        df_raw = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Failed to read file: {e}")
    st.stop()

st.success(f"✅ Loaded **{uploaded_file.name}** — {len(df_raw):,} rows")

# ─── PROCESS ─────────────────────────────────────────────────
with st.spinner("Processing data..."):
    try:
        df = compute_teu(df_raw.copy())
        grouped, total_import, total_export = group_by_country(df)

        result_export = top13(grouped, "%EXPORT", top_n=top_n, exclude_indonesia=exclude_indonesia)
        result_import = top13(grouped, "%IMPORT", top_n=top_n, exclude_indonesia=exclude_indonesia)

        export_cols = ["COUNTRY_NAME", "FULL_EXPORT", "EMPTY_EXPORT", "TOTAL_EXPORT", "%EXPORT"]
        import_cols = ["COUNTRY_NAME", "FULL_IMPORT", "EMPTY_IMPORT", "TOTAL_IMPORT", "%IMPORT"]

        result_export = result_export[export_cols].reset_index(drop=True)
        result_import = result_import[import_cols].reset_index(drop=True)

        # Add NO column
        result_export.insert(0, "NO", list(range(1, len(result_export))) + ["—"])
        result_import.insert(0, "NO", list(range(1, len(result_import))) + ["—"])

    except Exception as e:
        st.error(f"Analysis error: {e}")
        st.stop()

# ─── TABS ────────────────────────────────────────────────────
tab_export, tab_import, tab_raw = st.tabs(["📤 Top 13 Export", "📥 Top 13 Import", "🗂️ Raw Preview"])

# ── EXPORT TAB ───────────────────────────────────────────────
with tab_export:
    top_exp = result_export.iloc[0]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Total Export TEU</div>
            <div class="metric-value">{total_export:,.0f}</div>
            <div class="metric-sub">All countries</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Top Country</div>
            <div class="metric-value" style="font-size:18px">{top_exp['COUNTRY_NAME']}</div>
            <div class="metric-sub">{top_exp['%EXPORT']:.2f}% share</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Countries (Top 13)</div>
            <div class="metric-value">{len(result_export) - 1}</div>
            <div class="metric-sub">+ Others group</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    display_exp = result_export.copy()
    display_exp["%EXPORT"] = display_exp["%EXPORT"].apply(lambda x: f"{x:.2f}%" if isinstance(x, float) else x)
    st.dataframe(
        display_exp,
        use_container_width=True,
        hide_index=True,
        column_config={
            "NO":           st.column_config.TextColumn("No", width=50),
            "COUNTRY_NAME": st.column_config.TextColumn("Country"),
            "FULL_EXPORT":  st.column_config.NumberColumn("Full Export", format="%.2f"),
            "EMPTY_EXPORT": st.column_config.NumberColumn("Empty Export", format="%.2f"),
            "TOTAL_EXPORT": st.column_config.NumberColumn("Total Export", format="%.2f"),
            "%EXPORT":      st.column_config.TextColumn("% Share"),
        }
    )

# ── IMPORT TAB ───────────────────────────────────────────────
with tab_import:
    top_imp = result_import.iloc[0]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Total Import TEU</div>
            <div class="metric-value">{total_import:,.0f}</div>
            <div class="metric-sub">All countries</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Top Country</div>
            <div class="metric-value" style="font-size:18px">{top_imp['COUNTRY_NAME']}</div>
            <div class="metric-sub">{top_imp['%IMPORT']:.2f}% share</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Countries (Top 13)</div>
            <div class="metric-value">{len(result_import) - 1}</div>
            <div class="metric-sub">+ Others group</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    display_imp = result_import.copy()
    display_imp["%IMPORT"] = display_imp["%IMPORT"].apply(lambda x: f"{x:.2f}%" if isinstance(x, float) else x)
    st.dataframe(
        display_imp,
        use_container_width=True,
        hide_index=True,
        column_config={
            "NO":           st.column_config.TextColumn("No", width=50),
            "COUNTRY_NAME": st.column_config.TextColumn("Country"),
            "FULL_IMPORT":  st.column_config.NumberColumn("Full Import", format="%.2f"),
            "EMPTY_IMPORT": st.column_config.NumberColumn("Empty Import", format="%.2f"),
            "TOTAL_IMPORT": st.column_config.NumberColumn("Total Import", format="%.2f"),
            "%IMPORT":      st.column_config.TextColumn("% Share"),
        }
    )

# ── RAW PREVIEW TAB ──────────────────────────────────────────
with tab_raw:
    st.caption(f"Showing first 100 rows of {len(df_raw):,} total")
    st.dataframe(df_raw.head(100), use_container_width=True, hide_index=True)

# ─── EXPORT BUTTON ───────────────────────────────────────────
st.divider()
st.markdown("### ⬇️ Export Results")

export_cols_clean = ["NO", "COUNTRY_NAME", "FULL_EXPORT", "EMPTY_EXPORT", "TOTAL_EXPORT", "%EXPORT"]
import_cols_clean = ["NO", "COUNTRY_NAME", "FULL_IMPORT", "EMPTY_IMPORT", "TOTAL_IMPORT", "%IMPORT"]

output = io.BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    result_export.to_excel(writer, sheet_name="Top13_Export", index=False)
    result_import.to_excel(writer, sheet_name="Top13_Import", index=False)
output.seek(0)

st.download_button(
    label="Download Results as Excel (.xlsx)",
    data=output,
    file_name="JICT_OD_Results.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
