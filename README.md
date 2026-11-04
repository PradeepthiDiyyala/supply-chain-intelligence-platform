# Supply Chain Intelligence Platform

Advanced local-first data engineering, analytics and ML project using the Olist Brazilian E-Commerce Public Dataset (2016–2018; ~100k orders).

## Pipeline
Raw Olist CSVs → Bronze Parquet → Silver cleaned/typed Parquet → Gold order/item marts → DuckDB warehouse → scikit-learn delivery-risk model → Streamlit dashboard.

**Dataset is historical, not a live carrier feed.** This project demonstrates repeatable batch ELT and retrospective prediction, not real-time tracking.

## Dataset
Download the nine CSV files from https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce and place them in `data/raw/`. This repository does not redistribute the data. See `docs/DATA_LICENSE.md`.

## Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

Run:
```bash
python -m src.pipeline --all
pytest -q
streamlit run app.py
```

## Stack
Python, pandas, PyArrow/Parquet, DuckDB, SQL, scikit-learn, joblib, Streamlit, Plotly, pytest. No paid cloud subscription required.

## ML
Target: late delivery among delivered orders. Features use order-time characteristics only; actual delivery timestamps/duration and reviews are excluded to prevent target leakage. Evaluation uses a chronological 80/20 holdout. Metrics are written to `artifacts/metrics.json` after training.

## Resume description (only after running and validating)
- Built a multi-stage ELT pipeline over a multi-table public logistics dataset, implementing Bronze/Silver/Gold Parquet layers and a DuckDB analytical warehouse.
- Engineered order- and item-grain marts for delivery performance, freight, seller and category analytics while controlling join fan-out.
- Trained a chronologically evaluated, leakage-aware late-delivery risk model and surfaced operational KPIs through Streamlit.

Historical 2016–2018 dataset; no live carrier feed, streaming bus or cloud SLA. Add measured metrics only after your own successful run.
