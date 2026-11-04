import pandas as pd
from .common import setup, logger, path

DATES={"orders":["order_purchase_timestamp","order_approved_at","order_delivered_carrier_date","order_delivered_customer_date","order_estimated_delivery_date"],
       "items":["shipping_limit_date"],"reviews":["review_creation_date","review_answer_timestamp"]}
NAMES=["orders","customers","items","payments","reviews","products","sellers","geolocation","category_translation"]

def read(name):
    p=path("bronze")/f"{name}.parquet"
    if not p.exists(): raise FileNotFoundError(f"{p} missing; run python -m src.ingest")
    return pd.read_parquet(p).drop(columns=["__source_file","__ingested_at_utc"],errors="ignore")

def run():
    setup(); log=logger("transform"); t={n:read(n) for n in NAMES}
    for n,cols in DATES.items():
        for c in cols: t[n][c]=pd.to_datetime(t[n][c],errors="coerce",utc=True)
    for n,key in [("orders","order_id"),("customers","customer_id"),("items",["order_id","order_item_id"]),
                  ("reviews","review_id"),("products","product_id"),("sellers","seller_id")]:
        t[n]=t[n].drop_duplicates(subset=key,keep="last")
    g=t.pop("geolocation").dropna(subset=["geolocation_zip_code_prefix"]).copy()
    g["geolocation_zip_code_prefix"]=g.geolocation_zip_code_prefix.astype(str).str.zfill(5)
    t["geolocation_zip"]=g.groupby("geolocation_zip_code_prefix",as_index=False).agg(
      latitude=("geolocation_lat","mean"),longitude=("geolocation_lng","mean"),
      geo_city=("geolocation_city","first"),geo_state=("geolocation_state","first"))
    for n,df in t.items():
        df.to_parquet(path("silver")/f"{n}.parquet",index=False); log.info("Silver %s %d",n,len(df))
    item=t["items"].groupby("order_id",as_index=False).agg(item_count=("order_item_id","count"),
      gmv_brl=("price","sum"),freight_brl=("freight_value","sum"),seller_count=("seller_id","nunique"),
      product_count=("product_id","nunique"))
    pay=t["payments"].groupby("order_id",as_index=False).agg(payment_total_brl=("payment_value","sum"),
      payment_installments_max=("payment_installments","max"),payment_type_count=("payment_type","nunique"))
    rev=t["reviews"].groupby("order_id",as_index=False).agg(review_score=("review_score","mean"))
    fact=t["orders"].merge(item,on="order_id",how="left",validate="one_to_one")
    fact=fact.merge(pay,on="order_id",how="left",validate="one_to_one").merge(rev,on="order_id",how="left",validate="one_to_one")
    fact=fact.merge(t["customers"],on="customer_id",how="left",validate="many_to_one")
    fact["purchase_month"]=fact.order_purchase_timestamp.dt.strftime("%Y-%m")
    delivered=fact.order_delivered_customer_date.notna()
    fact["delivery_days"]=(fact.order_delivered_customer_date-fact.order_purchase_timestamp).dt.total_seconds()/86400
    fact["estimated_delivery_days"]=(fact.order_estimated_delivery_date-fact.order_purchase_timestamp).dt.total_seconds()/86400
    fact["late_delivery"]=(delivered & (fact.order_delivered_customer_date>fact.order_estimated_delivery_date)).astype("int8")
    fact["delivery_status"]="not_delivered"
    fact.loc[delivered & (fact.late_delivery==0),"delivery_status"]="on_time_or_early"
    fact.loc[fact.late_delivery==1,"delivery_status"]="late"
    items=t["items"].merge(t["orders"][["order_id","order_purchase_timestamp","order_status","order_delivered_customer_date","order_estimated_delivery_date"]],on="order_id",how="left",validate="many_to_one")
    items=items.merge(t["products"],on="product_id",how="left",validate="many_to_one").merge(t["sellers"],on="seller_id",how="left",validate="many_to_one")
    items=items.merge(t["category_translation"],on="product_category_name",how="left",validate="many_to_one")
    items["category"]=items.product_category_name_english.fillna(items.product_category_name).fillna("unknown")
    items["late_delivery"]=(items.order_delivered_customer_date.notna() & (items.order_delivered_customer_date>items.order_estimated_delivery_date)).astype("int8")
    fact.to_parquet(path("gold")/"fact_orders.parquet",index=False)
    items.to_parquet(path("gold")/"fact_order_items.parquet",index=False)
    for n in ("customers","sellers","products"): t[n].to_parquet(path("gold")/f"dim_{n}.parquet",index=False)
    log.info("Gold built: %d orders, %d items",len(fact),len(items))
    return {"orders":len(fact),"items":len(items)}
if __name__=="__main__": run()
