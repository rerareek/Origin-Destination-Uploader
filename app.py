import streamlit as st
import pandas as pd
import io
from od_analysis import compute_teu, group_by_country, top13, analyze_russia

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
    div[data-testid="stDataFrame"] { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
    .stTabs [data-baseweb="tab"] { font-size: 13px; }
    .russia-banner {
        background: linear-gradient(90deg, #1e3a5f 0%, #2563eb 100%);
        border-radius: 10px;
        padding: 14px 20px;
        color: white;
        margin-bottom: 1rem;
    }
    .russia-banner h4 { margin: 0 0 4px; font-size: 15px; }
    .russia-banner p  { margin: 0; font-size: 12px; opacity: 0.8; }
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

        result_export.insert(0, "NO", list(range(1, len(result_export))) + ["—"])
        result_import.insert(0, "NO", list(range(1, len(result_import))) + ["—"])

        # Russia analysis
        import_russia, export_russia = analyze_russia(df)

    except Exception as e:
        st.error(f"Analysis error: {e}")
        st.stop()

# ─── TABS ────────────────────────────────────────────────────
tab_export, tab_import, tab_russia, tab_raw = st.tabs([
    "📤 Top N Export",
    "📥 Top N Import",
    "🇷🇺 Russia Detail",
    "🗂️ Raw Preview"
])

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
            <div class="metric-label">Countries Shown</div>
            <div class="metric-value">{len(result_export) - 1}</div>
            <div class="metric-sub">+ Others group</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    display_exp = result_export.copy()
    display_exp["%EXPORT"] = display_exp["%EXPORT"].apply(lambda x: f"{x:.2f}%" if isinstance(x, float) else x)
    st.dataframe(
        display_exp, use_container_width=True, hide_index=True,
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
            <div class="metric-label">Countries Shown</div>
            <div class="metric-value">{len(result_import) - 1}</div>
            <div class="metric-sub">+ Others group</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    display_imp = result_import.copy()
    display_imp["%IMPORT"] = display_imp["%IMPORT"].apply(lambda x: f"{x:.2f}%" if isinstance(x, float) else x)
    st.dataframe(
        display_imp, use_container_width=True, hide_index=True,
        column_config={
            "NO":           st.column_config.TextColumn("No", width=50),
            "COUNTRY_NAME": st.column_config.TextColumn("Country"),
            "FULL_IMPORT":  st.column_config.NumberColumn("Full Import", format="%.2f"),
            "EMPTY_IMPORT": st.column_config.NumberColumn("Empty Import", format="%.2f"),
            "TOTAL_IMPORT": st.column_config.NumberColumn("Total Import", format="%.2f"),
            "%IMPORT":      st.column_config.TextColumn("% Share"),
        }
    )

# ── RUSSIA DETAIL TAB ────────────────────────────────────────
with tab_russia:
    if import_russia.empty and export_russia.empty:
        st.warning("⚠️ No Russia (RU) data found in the uploaded file.")
    else:
        st.markdown("""<div class="russia-banner">
            <h4>🇷🇺 Russia — Port-Level Breakdown</h4>
            <p>Container traffic to/from Russia, grouped by individual port of call.</p>
        </div>""", unsafe_allow_html=True)

        r_imp_total = import_russia["TOTAL_IMPORT"].sum() if not import_russia.empty else 0
        r_exp_total = export_russia["TOTAL_EXPORT"].sum() if not export_russia.empty else 0
        r_ports     = len(import_russia) if not import_russia.empty else len(export_russia)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">Total Import TEU</div>
                <div class="metric-value">{r_imp_total:,.0f}</div>
                <div class="metric-sub">Russia (discharge)</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">Total Export TEU</div>
                <div class="metric-value">{r_exp_total:,.0f}</div>
                <div class="metric-sub">Russia (load)</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">Active Ports</div>
                <div class="metric-value">{r_ports}</div>
                <div class="metric-sub">Unique port codes</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        sub_imp, sub_exp = st.tabs(["📥 Import by Port", "📤 Export by Port"])

        with sub_imp:
            if import_russia.empty:
                st.info("No import data for Russia.")
            else:
                disp = import_russia.copy()
                disp["%IMPORT"] = disp["%IMPORT"].apply(lambda x: f"{x:.2f}%")
                st.dataframe(
                    disp, use_container_width=True, hide_index=True,
                    column_config={
                        "COUNTRY_NAME": st.column_config.TextColumn("Country"),
                        "PORT":         st.column_config.TextColumn("Port Code"),
                        "PORT_NAME":    st.column_config.TextColumn("Port Name"),
                        "FULL_IMPORT":  st.column_config.NumberColumn("Full Import",  format="%.2f"),
                        "EMPTY_IMPORT": st.column_config.NumberColumn("Empty Import", format="%.2f"),
                        "TOTAL_IMPORT": st.column_config.NumberColumn("Total Import", format="%.2f"),
                        "%IMPORT":      st.column_config.TextColumn("% Share"),
                    }
                )

        with sub_exp:
            if export_russia.empty:
                st.info("No export data for Russia.")
            else:
                disp = export_russia.copy()
                disp["%EXPORT"] = disp["%EXPORT"].apply(lambda x: f"{x:.2f}%")
                st.dataframe(
                    disp, use_container_width=True, hide_index=True,
                    column_config={
                        "COUNTRY_NAME": st.column_config.TextColumn("Country"),
                        "PORT":         st.column_config.TextColumn("Port Code"),
                        "PORT_NAME":    st.column_config.TextColumn("Port Name"),
                        "FULL_EXPORT":  st.column_config.NumberColumn("Full Export",  format="%.2f"),
                        "EMPTY_EXPORT": st.column_config.NumberColumn("Empty Export", format="%.2f"),
                        "TOTAL_EXPORT": st.column_config.NumberColumn("Total Export", format="%.2f"),
                        "%EXPORT":      st.column_config.TextColumn("% Share"),
                    }
                )

        # Russia export button
        st.markdown("<br>", unsafe_allow_html=True)
        russia_output = io.BytesIO()
        with pd.ExcelWriter(russia_output, engine="xlsxwriter") as writer:
            if not import_russia.empty:
                import_russia.to_excel(writer, sheet_name="IMPORT", index=False)
            if not export_russia.empty:
                export_russia.to_excel(writer, sheet_name="EXPORT", index=False)
        russia_output.seek(0)
        st.download_button(
            label="⬇️ Download Russia Report (.xlsx)",
            data=russia_output,
            file_name="Russia_Port_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ── RAW PREVIEW TAB ──────────────────────────────────────────
with tab_raw:
    st.caption(f"Showing first 100 rows of {len(df_raw):,} total")
    st.dataframe(df_raw.head(100), use_container_width=True, hide_index=True)

# ─── EXPORT BUTTON ───────────────────────────────────────────
st.divider()
st.markdown("### ⬇️ Export Results")

output = io.BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    result_export.to_excel(writer, sheet_name="Top_Export", index=False)
    result_import.to_excel(writer, sheet_name="Top_Import", index=False)
output.seek(0)

st.download_button(
    label="Download OD Results as Excel (.xlsx)",
    data=output,
    file_name="JICT_OD_Results.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
