import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data_loader import load_data

st.set_page_config(page_title="Market Insights", page_icon="💡", layout="wide")

st.markdown("## 💡 Market Insights")
st.markdown(
    "<p style='color:#94a3b8'>Data-driven insight derived directly from the procurement dataset.</p>",
    unsafe_allow_html=True,
)

df_tenders, df_proposals = load_data()

if df_proposals.empty:
    st.warning("No data available.")
    st.stop()

st.markdown("### 🗂️ Vendor Specialization Map")
st.markdown(
    "<p style='color:#94a3b8'>"
    "Which vendors dominate specific sectors or regions? "
    "A concentration ≥80% means a vendor wins almost exclusively in one area — "
    "flagging either deep expertise or narrow market access."
    "</p>",
    unsafe_allow_html=True,
)

winner_props = df_proposals[df_proposals["is_winner"]].copy()

if winner_props.empty:
    st.info("No winner data available.")
    st.stop()

# ── Sector Specialization ────────────────────────────────────────────────────
vendor_sector_wins = (
    winner_props.groupby(["vendor_name", "sector_en"])["proposal_id"]
    .count().reset_index()
    .rename(columns={"proposal_id": "sector_wins"})
)
vendor_total_wins = vendor_sector_wins.groupby("vendor_name")["sector_wins"].sum().reset_index()
vendor_total_wins.columns = ["vendor_name", "total_wins"]

merged = vendor_sector_wins.merge(vendor_total_wins, on="vendor_name")
merged["concentration_pct"] = (merged["sector_wins"] / merged["total_wins"] * 100).round(1)

min_wins = st.number_input(
    "Minimum total wins to include a vendor",
    min_value=1, max_value=50, value=2, step=1,
)

specialized = merged[
    (merged["concentration_pct"] >= 80) & (merged["total_wins"] >= min_wins)
].sort_values(["total_wins", "vendor_name"], ascending=[False, True])

# ── Top Specialist per Sector ────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### 🥇 Top Specialist per Sector")
st.markdown("<p style='color:#94a3b8'>The #1 most concentrated vendor for each sector (ties broken by total wins, then name).</p>", unsafe_allow_html=True)

if not specialized.empty:
    # Keep only the top vendor per sector (duplicate-safe)
    top_per_sector = (
        specialized
        .sort_values(["sector_en", "concentration_pct", "total_wins", "vendor_name"],
                     ascending=[True, False, False, True])
        .drop_duplicates(subset="sector_en", keep="first")
        .sort_values("total_wins", ascending=False)
        .reset_index(drop=True)
    )
    top_per_sector.index += 1

    st.dataframe(
        top_per_sector[["sector_en", "vendor_name", "sector_wins", "total_wins", "concentration_pct"]].rename(columns={
            "sector_en": "Sector",
            "vendor_name": "Top Vendor",
            "sector_wins": "Wins in Sector",
            "total_wins": "Total Wins",
            "concentration_pct": "Concentration %",
        }),
        use_container_width=True,
        column_config={
            "Concentration %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
            "Wins in Sector": st.column_config.NumberColumn(width="small"),
            "Total Wins": st.column_config.NumberColumn(width="small"),
        },
    )
else:
    st.info(f"No vendors with ≥{min_wins} wins and ≥80% concentration found.")
st.markdown("---")

# ── Treemap: Who wins where ──────────────────────────────────────────────────
st.markdown("#### 🗺️ Where Does Each Vendor Win?")
top_vendor_list = vendor_total_wins.nlargest(40, "total_wins")["vendor_name"].tolist()
treemap_data = vendor_sector_wins[vendor_sector_wins["vendor_name"].isin(top_vendor_list)]

if not treemap_data.empty:
    fig_tree = px.treemap(
        treemap_data,
        path=["sector_en", "vendor_name"],
        values="sector_wins",
        color="sector_wins",
        color_continuous_scale="Blues",
        template="plotly_dark",
    )
    fig_tree.update_traces(textinfo="label+value")
    fig_tree.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        height=460,
        margin=dict(t=10, l=0, r=0, b=0),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_tree)

# ── Sector Specialization Table ──────────────────────────────────────────────
st.markdown("#### 📋 Full Specialist List (≥80% Concentration)")
if not specialized.empty:
    st.dataframe(
        specialized[["vendor_name", "sector_en", "sector_wins", "total_wins", "concentration_pct"]].rename(columns={
            "vendor_name": "Vendor",
            "sector_en": "Dominant Sector",
            "sector_wins": "Wins in Sector",
            "total_wins": "Total Wins",
            "concentration_pct": "Concentration %",
        }),
        use_container_width=True, hide_index=True,
        column_config={
            "Concentration %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
            "Wins in Sector": st.column_config.NumberColumn(width="small"),
            "Total Wins": st.column_config.NumberColumn(width="small"),
        },
    )
else:
    st.info(f"No vendors with ≥{min_wins} wins and ≥80% sector concentration found.")

# ── Region Specialization Table ──────────────────────────────────────────────
st.markdown("---")
st.markdown("#### 🌍 Region Specialists (≥90% Concentration)")
vendor_region_wins = (
    winner_props.groupby(["vendor_name", "region_en"])["proposal_id"]
    .count().reset_index()
    .rename(columns={"proposal_id": "region_wins"})
)
vendor_region_wins = vendor_region_wins.merge(vendor_total_wins, on="vendor_name")
vendor_region_wins["region_concentration"] = (vendor_region_wins["region_wins"] / vendor_region_wins["total_wins"] * 100).round(1)
reg_specialized = vendor_region_wins[
    (vendor_region_wins["region_concentration"] >= 90) & (vendor_region_wins["total_wins"] >= min_wins)
].sort_values("total_wins", ascending=False).head(20)

if not reg_specialized.empty:
    st.dataframe(
        reg_specialized[["vendor_name", "region_en", "region_wins", "total_wins", "region_concentration"]].rename(columns={
            "vendor_name": "Vendor",
            "region_en": "Dominant Region",
            "region_wins": "Wins in Region",
            "total_wins": "Total Wins",
            "region_concentration": "Concentration %",
        }),
        use_container_width=True, hide_index=True,
        column_config={
            "Concentration %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
        },
    )
else:
    st.info(f"No vendors with ≥{min_wins} wins and ≥90% region concentration found.")
