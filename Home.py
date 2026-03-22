import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_data, render_upload_widget

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Tenders Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}
[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: #60a5fa !important;
}
[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
}
.main { background-color: #0d1117; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar branding ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 10px'>
        <div style='font-size:2.5rem'>📊</div>
        <div style='font-size:1.3rem; font-weight:700; color:#f1f5f9; margin-top:4px'>Tenders Intelligence</div>
    </div>
    <hr style='border-color:#334155; margin: 10px 0 20px'>
    """, unsafe_allow_html=True)

# Data upload widget (shown in sidebar on every page)
render_upload_widget()

df_tenders, df_proposals = load_data()

st.markdown("## 🏠 Welcome to Tenders Intelligence")
st.markdown("<p style='color:#94a3b8'>KSA Procurement Analytics & Market Insights</p>", unsafe_allow_html=True)

# Active data source banner
if st.session_state.get("uploaded_raw") is not None:
    fname = st.session_state.get("uploaded_filename", "custom file")
    st.success(f"📂 Viewing custom dataset: **{fname}**")

# ── KPI Cards ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
total_spend = df_proposals[df_proposals["is_winner"]]["awarding_value"].sum()

with c1: st.metric("📋 Total Tenders", f"{len(df_tenders):,}")
with c2: st.metric("✅ Awarded", f"{int(df_tenders['is_awarded'].sum()):,}")
with c3: st.metric("🏢 Unique Vendors", f"{df_proposals['vendor_name'].nunique():,}")
with c4: st.metric("💰 Total Awarded", f"SAR {total_spend/1_000_000:.1f}M")
with c5: st.metric("⚔️ Avg Bidders", f"{df_tenders['num_proposals'].mean():.1f}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Row ──────────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### 📂 Tenders by Sector")
    sec_counts = df_tenders["sector_en"].value_counts().head(8).reset_index()
    fig = px.bar(sec_counts, x="count", y="sector_en", orientation="h", color="count", color_continuous_scale="Blues", template="plotly_dark")
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=False, height=300, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.markdown("### 🗺️ Tenders by Region")
    reg_counts = df_tenders["region_en"].value_counts().head(8).reset_index()
    fig2 = px.pie(reg_counts, names="region_en", values="count", hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r, template="plotly_dark")
    fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300)
    st.plotly_chart(fig2, use_container_width=True)

# ── Top Market Players ──────────────────────────────────────────────────────────
st.markdown("---")
col_x, col_y = st.columns(2)

with col_x:
    st.markdown("### 🏛️ Top Spending Agencies")
    top_ag = df_tenders[df_tenders["is_awarded"]].groupby("agency_name_en")["winning_bid"].sum().sort_values(ascending=False).head(5).reset_index()
    top_ag.columns = ["Agency", "Awarded Value (SAR)"]
    st.dataframe(top_ag, use_container_width=True, hide_index=True, column_config={"Awarded Value (SAR)": st.column_config.NumberColumn(format="SAR %,.0f")})

with col_y:
    st.markdown("### 🏅 Top Winning Vendors")
    top_vn = df_proposals[df_proposals["is_winner"]].groupby("vendor_name")["proposal_id"].count().sort_values(ascending=False).head(5).reset_index()
    top_vn.columns = ["Vendor", "Total Wins"]
    st.dataframe(top_vn, use_container_width=True, hide_index=True)

st.markdown("<br>", unsafe_allow_html=True)
st.info("👈 Use the sidebar to explore detailed Tenders, Companies, and Market Insights.")
