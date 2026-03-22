import json
import io
import pandas as pd
import streamlit as st

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_tenders_data.json")

# ── Required top-level keys for validation ──────────────────────────────────────
REQUIRED_FIELDS = {"id", "tenderName", "proposals", "awarded_proposals"}


def _parse_raw(raw: list) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse a list of tender dicts into (df_tenders, df_proposals)."""
    records = []
    proposals_list = []

    for item in raw:
        if not isinstance(item, dict):
            continue

        agency_name    = item.get("agency", {}) or {}
        city_obj       = item.get("city", {}) or {}
        region_obj     = item.get("region", {}) or {}
        activity_obj   = item.get("activity", {}) or {}
        sub_activity_obj = item.get("sub_activity", {}) or {}
        status_obj     = item.get("tender_status", {}) or {}
        type_obj       = item.get("tender_type", {}) or {}

        proposals  = item.get("proposals", []) or []
        awarded    = item.get("awarded_proposals", []) or []
        awarded_ids = {p.get("id") for p in awarded}

        prices    = [p.get("price") or 0 for p in proposals if p.get("price") is not None]
        min_bid   = min(prices) if prices else None
        max_bid   = max(prices) if prices else None
        winning_bid = None
        for a in awarded:
            if a.get("awarding_value"):
                winning_bid = a.get("awarding_value")
                break

        raw_status_en = (status_obj.get("en", "") or "").lower()
        if "award" in raw_status_en:
            status_bucket = "Awarded"
        elif "active" in raw_status_en or "open" in raw_status_en:
            status_bucket = "Active"
        else:
            status_bucket = "Expired/Other"

        record = {
            "id":             item.get("id"),
            "tenderName":     item.get("tenderName", ""),
            "agency_name":    agency_name.get("name", ""),
            "agency_name_en": agency_name.get("en", ""),
            "sector":         agency_name.get("sector", ""),
            "sector_en":      agency_name.get("sector_en", ""),
            "city":           city_obj.get("name", ""),
            "city_en":        city_obj.get("en", ""),
            "region":         region_obj.get("name", ""),
            "region_en":      region_obj.get("en", ""),
            "activity":       activity_obj.get("name", ""),
            "activity_en":    activity_obj.get("en", ""),
            "sub_activity":   sub_activity_obj.get("name", ""),
            "sub_activity_en": sub_activity_obj.get("en", ""),
            "status":         status_obj.get("name", ""),
            "status_en":      status_obj.get("en", ""),
            "status_bucket":  status_bucket,
            "tender_type":    type_obj.get("name", ""),
            "tender_type_en": type_obj.get("en", ""),
            "lastOfferPresentationDate": pd.to_datetime(
                item.get("lastOfferPresentationDate"), errors="coerce"
            ),
            "contractDays":         item.get("contractDays"),
            "tenderDocsFeesAsIs":   item.get("tenderDocsFeesAsIs"),
            "insuredTender":        item.get("insuredTender", 0),
            "num_proposals":        len(proposals),
            "min_bid":              min_bid,
            "max_bid":              max_bid,
            "winning_bid":          winning_bid,
            "bid_spread": (max_bid - min_bid) if (min_bid is not None and max_bid is not None) else None,
            "is_awarded": len(awarded) > 0,
        }
        records.append(record)

        for p in proposals:
            is_winner = p.get("id") in awarded_ids
            proposals_list.append({
                "tender_id":     item.get("id"),
                "tenderName":    item.get("tenderName", ""),
                "proposal_id":   p.get("id"),
                "vendor_name":   p.get("vendor_name", ""),
                "price":         p.get("price"),
                "awarding_value": p.get("awarding_value"),
                "technical_match": p.get("technical_match"),
                "is_winner":     is_winner,
                "sector_en":     agency_name.get("sector_en", ""),
                "agency_name_en": agency_name.get("en", ""),
                "region_en":     region_obj.get("en", ""),
                "created_at":    pd.to_datetime(p.get("created_at"), errors="coerce"),
            })

    df_tenders   = pd.DataFrame(records)
    df_proposals = pd.DataFrame(proposals_list)
    return df_tenders, df_proposals


def _validate(raw: list) -> list[str]:
    """Return a list of warning strings (empty = valid)."""
    warnings = []
    if not isinstance(raw, list):
        warnings.append("JSON root must be an **array** of tender objects.")
        return warnings
    if len(raw) == 0:
        warnings.append("The JSON file is **empty** (no tender records found).")
        return warnings

    # Sample up to 5 items for field checks
    sample = raw[:5]
    missing = []
    for field in REQUIRED_FIELDS:
        if not any(field in item for item in sample if isinstance(item, dict)):
            missing.append(f"`{field}`")
    if missing:
        warnings.append(
            f"Some expected fields were not found in the first records: {', '.join(missing)}. "
            "The app will still try to display available data, but some views may be incomplete."
        )
    return warnings


@st.cache_data(show_spinner="Loading tenders data...")
def _load_default() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not os.path.exists(DATA_PATH):
        st.error(
            "⚠️ **No default data file found.**\n\n"
            "The file `mock_tenders_data.json` is missing from the project folder.\n\n"
            "👈 Use **📂 Upload Custom Data** in the sidebar to load your own JSON dataset."
        )
        st.stop()
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return _parse_raw(raw)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (df_tenders, df_proposals).
    Uses uploaded file stored in st.session_state['uploaded_raw'] if present,
    otherwise falls back to the default mock data file.
    """
    uploaded_raw = st.session_state.get("uploaded_raw")
    if uploaded_raw is not None:
        return _parse_raw(uploaded_raw)
    return _load_default()


# ── Sidebar upload widget — call this from app.py sidebar block ─────────────────
def render_upload_widget():
    """Render the data-upload expander in the sidebar."""
    with st.sidebar:
        with st.expander("📂 Upload Custom Data", expanded=False):
            uploaded = st.file_uploader(
                "Upload a JSON file", type=["json"],
                help="Must be an array of tender objects in the same format as mock_tenders_data.json",
                key="data_upload",
            )

            if uploaded is not None:
                # Size check (max 50 MB)
                MAX_BYTES = 50 * 1024 * 1024
                uploaded.seek(0, 2)          # seek to end
                size = uploaded.tell()
                uploaded.seek(0)
                if size > MAX_BYTES:
                    st.error(f"File is too large ({size/1024/1024:.1f} MB). Maximum allowed size is 50 MB.")
                    return

                # Parse JSON
                try:
                    raw = json.load(io.TextIOWrapper(uploaded, encoding="utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    st.error(f"❌ Invalid JSON file: {e}")
                    return

                # Validate structure
                warnings = _validate(raw)
                for w in warnings:
                    st.warning(w)

                # If root isn't a list, abort
                if not isinstance(raw, list):
                    return

                # Store in session state and clear cache
                st.session_state["uploaded_raw"] = raw
                st.session_state["uploaded_filename"] = uploaded.name
                st.success(f"✅ Loaded **{uploaded.name}** ({len(raw):,} tenders)")
                st.rerun()

            # Show active data source + clear button
            if st.session_state.get("uploaded_raw") is not None:
                fname = st.session_state.get("uploaded_filename", "custom file")
                st.info(f"📄 Active: **{fname}**")
                if st.button("🔄 Reset to default data", use_container_width=True):
                    st.session_state.pop("uploaded_raw", None)
                    st.session_state.pop("uploaded_filename", None)
                    st.rerun()
            else:
                st.caption("Using default: `mock_tenders_data.json`")
