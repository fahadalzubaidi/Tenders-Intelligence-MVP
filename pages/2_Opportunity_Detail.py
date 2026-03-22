import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data_loader import load_data

st.set_page_config(page_title="Opportunity Detail", page_icon="🔍", layout="wide")

st.markdown("## 🔍 Opportunity Detail")

df_tenders, df_proposals = load_data()

# ── Tender selector ────────────────────────────────────────────────────────────
default_id = st.session_state.get("selected_tender_id", None)
tender_ids = df_tenders["id"].tolist()

if default_id and default_id in tender_ids:
    default_idx = tender_ids.index(default_id)
else:
    default_idx = 0

selected_id = st.selectbox(
    "Select Tender",
    options=tender_ids,
    index=default_idx,
    format_func=lambda x: f"#{x} — {df_tenders[df_tenders['id']==x]['tenderName'].values[0][:90]}",
)
st.session_state["selected_tender_id"] = selected_id

# ── Tender info ─────────────────────────────────────────────────────────────────
tender = df_tenders[df_tenders["id"] == selected_id].iloc[0]

st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f"### {tender['tenderName']}")
    status_color = "#4ade80" if tender["is_awarded"] else "#60a5fa"
    st.markdown(
        f"<span style='background:#1e293b;color:{status_color};padding:4px 14px;"
        f"border-radius:999px;font-size:0.85rem;font-weight:600;border:1px solid {status_color}'>"
        f"{tender['status_en'] or '—'}</span>",
        unsafe_allow_html=True
    )

with col2:
    if tender["winning_bid"]:
        st.metric("🏆 Winning Bid", f"SAR {tender['winning_bid']:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Info cards ─────────────────────────────────────────────────────────────────
agency_full = tender["agency_name_en"] or "—"
sector_full = tender["sector_en"] or "—"
region_full = f"{tender['region_en'] or '—'} / {tender['city_en'] or '—'}"
doc_fees    = f"SAR {tender['tenderDocsFeesAsIs']:,.0f}" if tender["tenderDocsFeesAsIs"] else "—"

col_left, col_right = st.columns(2)
with col_left:
    st.metric("Agency",         agency_full, help=agency_full)
    st.metric("Region / City",  region_full, help=region_full)
    st.metric("Contract Days",  tender["contractDays"] or "—")
with col_right:
    st.metric("Sector",         sector_full, help=sector_full)
    st.metric("Doc Fees",       doc_fees)

if pd.notna(tender["lastOfferPresentationDate"]):
    st.caption(f"📅 Deadline: {tender['lastOfferPresentationDate'].strftime('%Y-%m-%d')}")

st.markdown("---")

# ── Proposals ─────────────────────────────────────────────────────────────────
tender_proposals = df_proposals[df_proposals["tender_id"] == selected_id].copy()

if len(tender_proposals) == 0:
    st.info("No proposals found for this tender.")
else:
    st.markdown(f"### 📨 Submitted Bids ({len(tender_proposals)})")

    # Bid metrics
    bm1, bm2, bm3, bm4 = st.columns(4)
    prices = tender_proposals["price"].dropna()
    with bm1: st.metric("Min Bid", f"SAR {prices.min():,.0f}" if len(prices) > 0 else "—")
    with bm2: st.metric("Max Bid", f"SAR {prices.max():,.0f}" if len(prices) > 0 else "—")
    with bm3: st.metric("Bid Spread", f"SAR {prices.max()-prices.min():,.0f}" if len(prices) > 1 else "—")
    with bm4: st.metric("Avg Bid", f"SAR {prices.mean():,.0f}" if len(prices) > 0 else "—")

    st.markdown("<br>", unsafe_allow_html=True)

    # Table
    props_display = tender_proposals[["vendor_name", "price", "awarding_value", "is_winner", "technical_match"]].copy()
    props_display.columns = ["Vendor", "Bid (SAR)", "Awarded Value (SAR)", "Winner", "Tech Match"]
    props_display = props_display.sort_values("Bid (SAR)")

    st.dataframe(
        props_display,
        use_container_width=True,
        column_config={
            "Bid (SAR)": st.column_config.NumberColumn(format="SAR %,.0f"),
            "Awarded Value (SAR)": st.column_config.NumberColumn(format="SAR %,.0f"),
            "Winner": st.column_config.CheckboxColumn(),
            "Tech Match": st.column_config.CheckboxColumn(),
        },
        hide_index=True,
    )

    # ── Bar chart ─────────────────────────────────────────────────────────────
    if len(tender_proposals) > 1:
        st.markdown("### 📊 Bid Comparison")

        chart_df = tender_proposals[["vendor_name", "price", "is_winner"]].dropna(subset=["price"]).copy()
        chart_df = chart_df.sort_values("price")
        chart_df["color"] = chart_df["is_winner"].map({True: "Winner", False: "Bidder"})

        fig = px.bar(
            chart_df,
            x="vendor_name",
            y="price",
            color="color",
            color_discrete_map={"Winner": "#4ade80", "Bidder": "#60a5fa"},
            labels={"vendor_name": "Vendor", "price": "Bid Amount (SAR)", "color": ""},
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=20, b=0),
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)
