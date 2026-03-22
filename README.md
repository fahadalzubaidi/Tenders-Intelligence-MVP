# 📊 Tenders Intelligence

A Streamlit multi-page analytics dashboard for Saudi procurement data (Etimad / Monafasat).

## Features

| Page | Description |
|---|---|
| 🏠 Home | KPI overview, top agencies & vendors |
| 📋 Tenders Listing | Smart bidirectional filters, search, click-to-detail |
| 🔍 Opportunity Detail | Per-tender bid breakdown, bid comparison chart |
| 🏢 Company Intelligence | Vendor win rates, avg bid, rank, specialization |
| 📊 Market Views | Top companies, competitive density, pricing analysis |
| 💡 Market Insights | Vendor specialization map by sector & region |

## Getting Started

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Add your data
Place your JSON file (same structure as the Etimad export) in the project root, or use the **📂 Upload Custom Data** button in the sidebar at runtime.

### 3. Run the app
```bash
streamlit run Home.py
```

## Data Format

The app expects a JSON array of tender objects with the following structure:

```json
[
  {
    "id": "...",
    "tenderName": "...",
    "agency": { "name": "...", "en": "...", "sector_en": "..." },
    "region": { "name": "...", "en": "..." },
    "city": { "name": "...", "en": "..." },
    "tender_status": { "name": "...", "en": "..." },
    "proposals": [
      {
        "id": "...",
        "vendor_name": "...",
        "price": 0,
        "awarding_value": 0,
        "is_winner": false
      }
    ],
    "awarded_proposals": [...]
  }
]
```

> ⚠️ The `mock_tenders_data.json` file is excluded from this repo (too large). You must supply your own dataset.

## Tech Stack

- **Python** 3.11+
- **Streamlit** ≥ 1.32
- **Pandas** ≥ 2.0
- **Plotly** ≥ 5.20

## Project Structure

```
Jyad/
├── Home.py                    # Main entry point
├── data_loader.py             # Data parsing & upload widget
├── requirements.txt
├── .streamlit/
│   └── config.toml            # Dark theme config
└── pages/
    ├── 1_Tenders_Listing.py
    ├── 2_Opportunity_Detail.py
    ├── 3_Company_Intelligence.py
    ├── 4_Market_Views.py
    └── 5_Market_Insights.py
```
