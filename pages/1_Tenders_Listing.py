import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data_loader import load_data

st.set_page_config(page_title="Tenders Listing", page_icon="📋", layout="wide")

# ── Header & Search ────────────────────────────────────────────────────────────
st.markdown("## 📋 Tenders Listing")
st.markdown("<p style='color:#94a3b8'>Browse and filter all procurement opportunities.</p>", unsafe_allow_html=True)

df_tenders, _ = load_data()

# ── True Cross-Filtering (Bidirectional Smart Filters) ────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filters")
    if st.button("🔄 Clear All Filters"):
        st.session_state.clear()
        st.rerun()

    # To calculate options for filter X, we apply all filters Y != X
    # This allows a truly "smart" bidirectional experience.

    # 1. Available Agencies (filtered by Sector, Region, City)
    df_ag = df_tenders.copy()
    if st.session_state.get("smart_sec"): df_ag = df_ag[df_ag["sector_en"].isin(st.session_state["smart_sec"])]
    if st.session_state.get("smart_reg"): df_ag = df_ag[df_ag["region_en"].isin(st.session_state["smart_reg"])]
    if st.session_state.get("smart_city"): df_ag = df_ag[df_ag["city_en"].isin(st.session_state["smart_city"])]
    available_agencies = sorted(df_ag["agency_name_en"].dropna().unique().tolist())
    sel_agency = st.multiselect("Agency", available_agencies, key="smart_ag")

    # 2. Available Sectors (filtered by Agency, Region, City)
    df_sec = df_tenders.copy()
    if st.session_state.get("smart_ag"): df_sec = df_sec[df_sec["agency_name_en"].isin(st.session_state["smart_ag"])]
    if st.session_state.get("smart_reg"): df_sec = df_sec[df_sec["region_en"].isin(st.session_state["smart_reg"])]
    if st.session_state.get("smart_city"): df_sec = df_sec[df_sec["city_en"].isin(st.session_state["smart_city"])]
    available_sectors = sorted(df_sec["sector_en"].dropna().unique().tolist())
    sel_sector = st.multiselect("Sector / Activity", available_sectors, key="smart_sec")

    # 3. Available Regions (filtered by Agency, Sector, City)
    df_reg = df_tenders.copy()
    if st.session_state.get("smart_ag"): df_reg = df_reg[df_reg["agency_name_en"].isin(st.session_state["smart_ag"])]
    if st.session_state.get("smart_sec"): df_reg = df_reg[df_reg["sector_en"].isin(st.session_state["smart_sec"])]
    if st.session_state.get("smart_city"): df_reg = df_reg[df_reg["city_en"].isin(st.session_state["smart_city"])]
    available_regions = sorted(df_reg["region_en"].dropna().unique().tolist())
    sel_region = st.multiselect("Region", available_regions, key="smart_reg")

    # 4. Available Cities (filtered by Agency, Sector, Region)
    df_city = df_tenders.copy()
    if st.session_state.get("smart_ag"): df_city = df_city[df_city["agency_name_en"].isin(st.session_state["smart_ag"])]
    if st.session_state.get("smart_sec"): df_city = df_city[df_city["sector_en"].isin(st.session_state["smart_sec"])]
    if st.session_state.get("smart_reg"): df_city = df_city[df_city["region_en"].isin(st.session_state["smart_reg"])]
    available_cities = sorted(df_city["city_en"].dropna().unique().tolist())
    sel_city = st.multiselect("City", available_cities, key="smart_city")

    # (Removed Winning Bid Range as per request)

# ── Search & Quick Filters (Top Row) ──────────────────────────────────────────
c1, c2 = st.columns([3, 1])
with c1:
    # Use multiselect for "Smart Search" with suggestions
    search_options = sorted(df_tenders["tenderName"].dropna().unique().tolist())
    # Add IDs as well
    search_options += [f"ID: {tid}" for tid in df_tenders["id"].dropna().unique()]
    
    sel_search = st.multiselect(
        "🔍 Smart Search", 
        search_options, 
        placeholder="Search and pick specific tenders...", 
        label_visibility="collapsed"
    )
with c2:
    status_options = ["All", "Active", "Awarded", "Expired/Other"]
    sel_status_bucket = st.selectbox("Status Filter", status_options, label_visibility="collapsed")

# ── Apply Filters ──────────────────────────────────────────────────────────────
filtered = df_tenders.copy()

# 1. Smart Search filter
if sel_search:
    ids_to_find = []
    names_to_find = []
    for s in sel_search:
        if s.startswith("ID: "):
            ids_to_find.append(s.replace("ID: ", ""))
        else:
            names_to_find.append(s)
    
    filtered = filtered[
        filtered["tenderName"].isin(names_to_find) |
        filtered["id"].astype(str).isin(ids_to_find)
    ]

# 2. Sidebar filters (Agency, Sector, Region, City)
if sel_agency:  filtered = filtered[filtered["agency_name_en"].isin(sel_agency)]
if sel_sector:  filtered = filtered[filtered["sector_en"].isin(sel_sector)]
if sel_region:  filtered = filtered[filtered["region_en"].isin(sel_region)]
if sel_city:    filtered = filtered[filtered["city_en"].isin(sel_city)]

# 3. Status Bucket filter
if sel_status_bucket != "All":
    filtered = filtered[filtered["status_bucket"] == sel_status_bucket]

# 4. Bid Range filter removed

# ── Summary Metrics ─────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Opportunities", f"{len(filtered):,}")
m2.metric("Total Awarded", f"SAR {filtered['winning_bid'].sum()/1_000_000:.1f}M")
m3.metric("Med. Bid", f"SAR {filtered['winning_bid'].median():,.0f}" if not filtered.empty else "—")
m4.metric("Avg Bids", f"{filtered['num_proposals'].mean():.1f}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Table Selection Logic ─────────────────────────────────────────────────────
display_cols = {
    "id": "ID",
    "tenderName": "Tender Name",
    "agency_name_en": "Agency",
    "sector_en": "Sector",
    "region_en": "Region",
    "city_en": "City",
    "status_bucket": "Status",
    "winning_bid": "Winner (SAR)",
    "lastOfferPresentationDate": "Deadline",
}

show_df = filtered[list(display_cols.keys())].rename(columns=display_cols).reset_index(drop=True)

if not show_df.empty:
    st.info("💡 **Tip:** Click on a row in the table below, then click **View Details**.")
    
    # New Streamlit 1.35+ feature: selection_mode
    event_dict = st.dataframe(
        show_df,
        use_container_width=True,
        height=550,
        column_config={
            "Tender Name": st.column_config.TextColumn(width="large"),
            "Winner (SAR)": st.column_config.NumberColumn(format="SAR %,.0f"),
            "Deadline": st.column_config.DatetimeColumn(format="YYYY-MM-DD"),
        },
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    # Handle Selection
    selected_rows = event_dict.get("selection", {}).get("rows", [])
    if selected_rows:
        row_idx = selected_rows[0]
        selected_id = filtered.iloc[row_idx]["id"]
        st.session_state["selected_tender_id"] = selected_id
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"🔍 View Details for Tender #{selected_id}", type="primary", use_container_width=True):
            st.switch_page("pages/2_Opportunity_Detail.py")
else:
    st.error("No tenders found matching your search and filters.")

