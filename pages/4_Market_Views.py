import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data_loader import load_data

st.set_page_config(page_title="Market Views", page_icon="📊", layout="wide")

st.markdown("## 📊 Market & Competitive Views")
st.markdown("<p style='color:#94a3b8'>In-depth competitive analytics and pricing intelligence across Saudi procurement.</p>", unsafe_allow_html=True)

df_tenders, df_proposals = load_data()

tab1, tab2, tab3 = st.tabs(["🏆 Top Performing Companies", "⚔️ Competitive Density", "💰 Pricing Analysis"])


# ─── TAB 1: Top Performing Companies ──────────────────────────────────────────
with tab1:
    st.markdown("### 🏆 Top Performing Companies")
    st.markdown("<p style='color:#94a3b8'>Ranked by number of contract wins. Use smart filters to narrow by sector or agency.</p>", unsafe_allow_html=True)

    # Smart Bidirectional Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        # Sector options (filtered by any agency selection)
        df_sec_base = df_proposals.copy()
        if st.session_state.get("t1_ag"):
            df_sec_base = df_sec_base[df_sec_base["agency_name_en"].isin(st.session_state["t1_ag"])]
        avail_secs = sorted(df_sec_base["sector_en"].dropna().unique().tolist())
        sel_sec = st.multiselect("Filter by Sector", avail_secs, key="t1_sec")

    with col_f2:
        # Agency options (filtered by any sector selection)
        df_ag_base = df_proposals.copy()
        if st.session_state.get("t1_sec"):
            df_ag_base = df_ag_base[df_ag_base["sector_en"].isin(st.session_state["t1_sec"])]
        avail_ags = sorted(df_ag_base["agency_name_en"].dropna().unique().tolist())
        sel_ag = st.multiselect("Filter by Agency", avail_ags, key="t1_ag")

    # Apply filters
    prop_f = df_proposals.copy()
    if sel_sec: prop_f = prop_f[prop_f["sector_en"].isin(sel_sec)]
    if sel_ag:  prop_f = prop_f[prop_f["agency_name_en"].isin(sel_ag)]

    top_companies = (
        prop_f.groupby("vendor_name")
        .agg(wins=("is_winner", "sum"), participations=("proposal_id", "count"), avg_bid=("price", "mean"))
        .reset_index()
        .assign(win_rate=lambda d: (d["wins"] / d["participations"] * 100).round(1))
        .sort_values("wins", ascending=False)
        .head(25)
    )

    if top_companies.empty or top_companies["wins"].sum() == 0:
        st.info("No winner data available for the selected filters.")
    else:
        # Horizontal bar chart — wins, coloured by win rate
        fig = px.bar(
            top_companies, x="wins", y="vendor_name", orientation="h",
            color="win_rate", color_continuous_scale="Teal",
            labels={"vendor_name": "Vendor", "wins": "Total Wins", "win_rate": "Win Rate (%)"},
            custom_data=["participations", "win_rate", "avg_bid"],
            template="plotly_dark",
        )
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Wins: %{x}<br>Win Rate: %{customdata[1]}%<br>Bids: %{customdata[0]}<extra></extra>")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=540, margin=dict(l=0, r=0, t=10, b=0),
            yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
        )
        st.plotly_chart(fig)

        # Table
        st.dataframe(
            top_companies[["vendor_name", "wins", "participations", "win_rate", "avg_bid"]].rename(columns={
                "vendor_name": "Vendor", "wins": "Wins", "participations": "Bids",
                "win_rate": "Win Rate (%)", "avg_bid": "Avg Bid (SAR)"
            }),
            use_container_width=True, hide_index=True,
            column_config={
                "Win Rate (%)": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                "Avg Bid (SAR)": st.column_config.NumberColumn(format="SAR %,.0f"),
            },
        )


# ─── TAB 2: Competitive Density ───────────────────────────────────────────────
with tab2:
    st.markdown("### ⚔️ Competitive Density")
    st.markdown("<p style='color:#94a3b8'>Tenders ranked by number of bidders — identify highly competitive vs low-competition opportunities.</p>", unsafe_allow_html=True)

    density = df_tenders[df_tenders["num_proposals"] > 0].copy()

    # Competition label
    def label_competition(n):
        if n >= 5: return "🔥 High"
        if n >= 3: return "🟡 Medium"
        if n == 2: return "🟠 Low"
        return "🧊 Single"

    density["Competition"] = density["num_proposals"].apply(label_competition)

    high_count  = (density["num_proposals"] >= 5).sum()
    med_count   = ((density["num_proposals"] >= 3) & (density["num_proposals"] < 5)).sum()
    low_count   = (density["num_proposals"] == 2).sum()
    single_count = (density["num_proposals"] == 1).sum()

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔥 High Competition (5+ bids)", f"{high_count:,}")
    c2.metric("🟡 Medium Competition (3-4)", f"{med_count:,}")
    c3.metric("🟠 Low Competition (2 bids)", f"{low_count:,}")
    c4.metric("🧊 Single-Bidder", f"{single_count:,} ({single_count/len(density)*100:.0f}%)")

    st.markdown("<br>", unsafe_allow_html=True)

    # Filters for the table
    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        comp_filter = st.selectbox("Competition Level", ["All", "🔥 High", "🟡 Medium", "🟠 Low", "🧊 Single"], key="dens_comp")
    with cf2:
        sec_f = sorted(density["sector_en"].dropna().unique().tolist())
        sel_sec_d = st.multiselect("Sector", sec_f, key="dens_sec")
    with cf3:
        ag_f_base = density.copy()
        if sel_sec_d: ag_f_base = ag_f_base[ag_f_base["sector_en"].isin(sel_sec_d)]
        ag_f = sorted(ag_f_base["agency_name_en"].dropna().unique().tolist())
        sel_ag_d = st.multiselect("Agency", ag_f, key="dens_ag")

    # Apply filters
    d_table = density.copy()
    if comp_filter != "All":    d_table = d_table[d_table["Competition"] == comp_filter]
    if sel_sec_d:               d_table = d_table[d_table["sector_en"].isin(sel_sec_d)]
    if sel_ag_d:                d_table = d_table[d_table["agency_name_en"].isin(sel_ag_d)]

    d_table = d_table[[
        "tenderName", "agency_name_en", "sector_en", "region_en",
        "num_proposals", "Competition", "winning_bid", "status_bucket"
    ]].sort_values("num_proposals", ascending=False).reset_index(drop=True)
    d_table.index += 1

    st.markdown(f"#### 📋 Ranked by Competitive Pressure ({len(d_table):,} tenders)")
    st.dataframe(
        d_table.rename(columns={
            "tenderName": "Tender", "agency_name_en": "Agency", "sector_en": "Sector",
            "region_en": "Region", "num_proposals": "# Bidders",
            "winning_bid": "Winning Bid (SAR)", "status_bucket": "Status"
        }),
        use_container_width=True, height=550,
        column_config={
            "Winning Bid (SAR)": st.column_config.NumberColumn(format="SAR %,.0f"),
            "# Bidders": st.column_config.NumberColumn(width="small"),
        },
        hide_index=False,
    )


# ─── TAB 3: Pricing Analysis ───────────────────────────────────────────────────
with tab3:
    st.markdown("### 💰 Pricing Analysis")
    st.markdown("<p style='color:#94a3b8'>Awarded contract values and bid spread analysis across all tenders.</p>", unsafe_allow_html=True)

    pricing = df_tenders.dropna(subset=["min_bid"]).copy()
    pricing["bid_spread"] = (pricing["max_bid"].fillna(pricing["min_bid"]) - pricing["min_bid"]).fillna(0)

    # Summary KPIs — only show what is genuinely different and informative
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tenders with Price Data", f"{len(pricing):,}")
    c2.metric("Total Awarded Value", f"SAR {pricing['winning_bid'].sum()/1_000_000:.1f}M" if pd.notna(pricing['winning_bid'].sum()) else "—")
    c3.metric("Lowest Awarded Contract", f"SAR {pricing['winning_bid'].min():,.0f}" if pd.notna(pricing['winning_bid'].min()) else "—")
    c4.metric("Highest Awarded Contract", f"SAR {pricing['winning_bid'].max():,.0f}" if pd.notna(pricing['winning_bid'].max()) else "—")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Per-Tender Pricing Table (CORE REQUIREMENT) ──────────────────────────────


    # Filter controls
    cf1, cf2 = st.columns(2)
    with cf1:
        sec_opts = sorted(pricing["sector_en"].dropna().unique().tolist())
        sel_sec_p = st.multiselect("Filter by Sector", sec_opts, key="p_sec")
    with cf2:
        ag_opts = sorted(pricing["agency_name_en"].dropna().unique().tolist())
        if sel_sec_p:
            ag_opts = sorted(pricing[pricing["sector_en"].isin(sel_sec_p)]["agency_name_en"].dropna().unique().tolist())
        sel_ag_p = st.multiselect("Filter by Agency", ag_opts, key="p_ag")

    p_table = pricing.copy()
    if sel_sec_p: p_table = p_table[p_table["sector_en"].isin(sel_sec_p)]
    if sel_ag_p:  p_table = p_table[p_table["agency_name_en"].isin(sel_ag_p)]

    price_display = p_table[[
        "tenderName", "agency_name_en", "sector_en",
        "min_bid", "max_bid", "winning_bid", "bid_spread"
    ]].rename(columns={
        "tenderName": "Tender",
        "agency_name_en": "Agency",
        "sector_en": "Sector",
        "min_bid": "Min Bid (SAR)",
        "max_bid": "Max Bid (SAR)",
        "winning_bid": "Winning Bid (SAR)",
        "bid_spread": "Spread (SAR)",
    }).sort_values("Spread (SAR)", ascending=False).reset_index(drop=True)

    st.dataframe(
        price_display,
        use_container_width=True, height=520, hide_index=True,
        column_config={
            "Min Bid (SAR)":     st.column_config.NumberColumn(format="SAR %,.0f"),
            "Max Bid (SAR)":     st.column_config.NumberColumn(format="SAR %,.0f"),
            "Winning Bid (SAR)": st.column_config.NumberColumn(format="SAR %,.0f"),
            "Spread (SAR)":      st.column_config.NumberColumn(format="SAR %,.0f"),
        }
    )

    # ── Winning Bid by Sector (only if there is useful spread data) ───────────────
    sector_pricing = p_table.groupby("sector_en").agg(
        avg_min=("min_bid", "mean"),
        avg_winning=("winning_bid", "mean"),
        avg_spread=("bid_spread", "mean"),
        count=("id", "count"),
    ).dropna(subset=["avg_winning"]).sort_values("avg_winning", ascending=False).reset_index()

    if not sector_pricing.empty and sector_pricing["avg_winning"].notna().any():
        st.markdown("---")
        st.markdown("#### 📊 Average Winning Bid by Sector")
        fig_bar = px.bar(
            sector_pricing.head(12), x="sector_en", y="avg_winning",
            color="avg_spread", color_continuous_scale="RdYlGn_r",
            labels={"sector_en": "Sector", "avg_winning": "Avg Winning Bid (SAR)", "avg_spread": "Avg Spread"},
            template="plotly_dark",
        )
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               height=360, margin=dict(t=10, b=0), xaxis_tickangle=-30,
                               coloraxis_showscale=False)
        st.plotly_chart(fig_bar)
