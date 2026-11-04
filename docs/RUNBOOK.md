# Runbook

1. Download all nine Olist CSVs into `data/raw/`.
2. Install dependencies in a Python 3.10–3.12 virtual environment.
3. Run `python -m src.pipeline --all`.
4. Run `pytest -q`.
5. Launch `streamlit run app.py`.

Re-running ingestion overwrites Bronze snapshots; later stages replace Silver/Gold and DuckDB tables/views. Preserve raw source archives separately for reproducibility.

Missing CSV: check exact names in `src/common.py`. Missing Parquet engine: reinstall pyarrow. Missing warehouse: run pipeline. Missing model artifact: run `python -m src.train`.

Raw data, database, artifacts and logs are gitignored. Never commit customer data or credentials.
