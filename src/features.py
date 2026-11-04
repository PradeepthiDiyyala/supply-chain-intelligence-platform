import pandas as pd
FEATURES=["purchase_hour","purchase_dayofweek","purchase_month_num","estimated_delivery_days",
"item_count","gmv_brl","freight_brl","seller_count","product_count","payment_installments_max",
"payment_type_count","customer_state"]
NUMERIC=[x for x in FEATURES if x!="customer_state"]
CATEGORICAL=["customer_state"]
def build_training_frame(df):
    x=df.copy()
    x["purchase_hour"]=x.order_purchase_timestamp.dt.hour
    x["purchase_dayofweek"]=x.order_purchase_timestamp.dt.dayofweek
    x["purchase_month_num"]=x.order_purchase_timestamp.dt.month
    x["customer_state"]=x.customer_state.fillna("unknown")
    x["target"]=x.late_delivery.astype(int)
    x=x[x.order_delivered_customer_date.notna() & x.order_estimated_delivery_date.notna()]
    return x[FEATURES+["target","order_purchase_timestamp"]].replace([float("inf"),-float("inf")],pd.NA)
def single_frame(payload):
    return pd.DataFrame([{k:payload.get(k) for k in FEATURES}],columns=FEATURES)
