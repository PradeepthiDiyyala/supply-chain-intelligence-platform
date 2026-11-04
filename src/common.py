from pathlib import Path
import logging, yaml

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "orders":"olist_orders_dataset.csv", "customers":"olist_customers_dataset.csv",
    "items":"olist_order_items_dataset.csv", "payments":"olist_order_payments_dataset.csv",
    "reviews":"olist_order_reviews_dataset.csv", "products":"olist_products_dataset.csv",
    "sellers":"olist_sellers_dataset.csv", "geolocation":"olist_geolocation_dataset.csv",
    "category_translation":"product_category_name_translation.csv"
}
def settings():
    return yaml.safe_load((ROOT/"config/settings.yaml").read_text())
def path(key):
    return ROOT/settings()["paths"][key]
def setup():
    for k in ("raw","bronze","silver","gold","artifacts","logs"):
        path(k).mkdir(parents=True, exist_ok=True)
    (ROOT/"warehouse").mkdir(exist_ok=True)
def logger(name):
    setup(); x=logging.getLogger(name)
    if not x.handlers:
        x.setLevel(logging.INFO)
        fmt=logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        for h in (logging.FileHandler(path("logs")/"pipeline.log"), logging.StreamHandler()):
            h.setFormatter(fmt); x.addHandler(h)
    return x
def raw_files():
    missing=[v for v in FILES.values() if not (path("raw")/v).exists()]
    if missing:
        raise FileNotFoundError("Missing CSVs in data/raw: "+", ".join(missing)+
          ". Download https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce")
    return {k:path("raw")/v for k,v in FILES.items()}
