# Architecture and grain contracts

Raw CSV → Bronze source-shaped Parquet → Silver typed/deduplicated Parquet → Gold marts → DuckDB → ML + Streamlit.

- `fact_orders`: one row per order.
- `fact_order_items`: one row per item.
- Items, payments and reviews are aggregated independently to order grain before joining the order fact to prevent revenue/order multiplication.
- Geolocation has multiple points per ZIP; aggregate ZIP first before joining.
- `customers` is keyed by `customer_id` (order-specific); use `customer_unique_id` for person-level repeat-purchase analysis.

The classifier excludes actual delivery date/duration, review score/text and all post-outcome fields. Chronological holdout is more realistic than random splitting but is not full rolling-origin validation.
