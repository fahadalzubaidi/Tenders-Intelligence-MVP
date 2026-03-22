import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data_loader import load_data

st.set_page_config(page_title="Company Intelligence", page_icon="🏢", layout="wide")

st.markdown("## 🏢 Company Intelligence")
st.markdown("<p style='color:#94a3b8'>Analyse vendor performance, win rates, and bidding behaviour.</p>", unsafe_allow_html=True)

_, df_proposals = load_data()

if df_proposals.empty:
    st.warning("No proposals data found.")
    st.stop()

# ── Compute vendor stats ────────────────────────────────────────────────────────
df_proposals["rank"] = df_proposals.groupby("tender_id")["price"].rank(method="min", ascending=True)

vendor_stats = (
    df_proposals.groupby("vendor_name")
    .agg(
        participations=("proposal_id", "count"),
        wins=("is_winner", "sum"),
        avg_bid=("price", "mean"),
        avg_rank=("rank", "mean"),
        total_awarded=("awarding_value", lambda x: x[df_proposals.loc[x.index, "is_winner"]].sum()),
        last_activity=("created_at", "max"),
        sectors=("sector_en", lambda x: ", ".join(x.dropna().unique()[:3])),
        regions=("region_en", lambda x: ", ".join(x.dropna().unique()[:3])),
    )
    .reset_index()
)
vendor_stats["win_rate"] = (vendor_stats["wins"] / vendor_stats["participations"] * 100).round(1)
vendor_stats = vendor_stats.sort_values("participations", ascending=False)

# ── Smart Filter Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏢 Find Vendor")
    
    # Smart Bidirectional Filters
    df_f_ag = df_proposals.copy()
    if st.session_state.get("v_ag"): df_f_ag = df_f_ag[df_f_ag["agency_name_en"].isin(st.session_state["v_ag"])]
    avail_sectors = sorted(df_f_ag["sector_en"].dropna().unique().tolist())
    sel_sector = st.multiselect("Filter by Sector", avail_sectors, key="v_sec")

    df_f_sec = df_proposals.copy()
    if st.session_state.get("v_sec"): df_f_sec = df_f_sec[df_f_sec["sector_en"].isin(st.session_state["v_sec"])]
    avail_agencies = sorted(df_f_sec["agency_name_en"].dropna().unique().tolist())
    sel_agency = st.multiselect("Filter by Agency", avail_agencies, key="v_ag")

    # Filtered Vendor list
    df_final = df_proposals.copy()
    if sel_sector: df_final = df_final[df_final["sector_en"].isin(sel_sector)]
    if sel_agency: df_final = df_final[df_final["agency_name_en"].isin(sel_agency)]
    available_vendors = sorted(df_final["vendor_name"].unique().tolist())

    st.markdown("---")
    if not available_vendors:
        st.warning("No vendors found.")
        st.stop()
        
    selected_vendor = st.selectbox(
        "🔍 Smart Search & Pick Vendor", 
        available_vendors, 
        placeholder="Type to search...",
    )
    if not selected_vendor:
        st.info("Choose a vendor.")
        st.stop()

# ── Vendor Display ─────────────────────────────────────────────────────────────
v = vendor_stats[vendor_stats["vendor_name"] == selected_vendor].iloc[0]

st.markdown(f"### {selected_vendor}")
st.markdown("<p style='color:#94a3b8'>Comprehensive vendor analysis and procurement history.</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1: st.metric("📨 Bids", f"{int(v['participations']):,}")
with col2: st.metric("🏆 Wins", f"{int(v['wins']):,}")
with col3: st.metric("📈 Win Rate", f"{v['win_rate']:.1f}%")
with col4: st.metric("💰 Avg Bid", f"SAR {v['avg_bid']:,.0f}" if pd.notna(v["avg_bid"]) else "—")
with col5: st.metric("🏅 Avg Rank", f"{v['avg_rank']:.1f}", help="Price position (1.0 = Cheapest)")
with col6: st.metric("📅 Last Activity", v["last_activity"].strftime("%Y-%m-%d") if pd.notna(v["last_activity"]) else "—")

st.caption(f"**Sectors:** {v['sectors'] or '—'} &nbsp;|&nbsp; **Regions:** {v['regions'] or '—'}")
st.markdown("---")

# ── Charts Row ──────────────────────────────────────────────────────────────────
vendor_proposals = df_proposals[df_proposals["vendor_name"] == selected_vendor].copy()
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("#### 🎯 Wins vs Losses")
    pie_data = pd.DataFrame({"Outcome": ["Wins", "Losses"], "Count": [int(v["wins"]), int(v["participations"] - v["wins"])]})
    fig_pie = px.pie(pie_data, names="Outcome", values="Count", color="Outcome", color_discrete_map={"Wins": "#4ade80", "Losses": "#f87171"}, hole=0.5, template="plotly_dark")
    fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=280, margin=dict(t=10, b=0))
    st.plotly_chart(fig_pie)

with col_b:
    st.markdown("#### 💵 Bid Values")
    bid_data = vendor_proposals.dropna(subset=["price"])
    if len(bid_data) > 0:
        fig_hist = px.histogram(bid_data, x="price", nbins=20, color_discrete_sequence=["#60a5fa"], template="plotly_dark")
        fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=280, margin=dict(t=10, b=0), showlegend=False)
        st.plotly_chart(fig_hist)

# ── Leaderboard ─────────────────────────────────────────────────────────────────
st.markdown("### 🏅 Vendor Leaderboard (Top 20 by Participations)")
lb = vendor_stats.head(20)[["vendor_name", "participations", "wins", "win_rate", "avg_bid"]].copy()
lb.columns = ["Vendor", "Participations", "Wins", "Win Rate (%)", "Avg Bid (SAR)"]
st.dataframe(lb, use_container_width=True, hide_index=True, column_config={
    "Win Rate (%)": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
    "Avg Bid (SAR)": st.column_config.NumberColumn(format="SAR %,.0f"),
})
