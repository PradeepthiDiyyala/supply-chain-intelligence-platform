"""Forecasting, seller scorecards and anomaly detection over historical Olist data."""
import json
import numpy as np
import pandas as pd
import duckdb
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from .common import setup, logger, path

def _read():
    db=path("warehouse")
    if not db.exists(): raise FileNotFoundError("Run the core pipeline first.")
    con=duckdb.connect(str(db),read_only=True)
    try:
        orders=con.execute("SELECT * FROM fact_orders").df()
        items=con.execute("SELECT * FROM fact_order_items").df()
    finally: con.close()
    orders["order_purchase_timestamp"]=pd.to_datetime(orders.order_purchase_timestamp,utc=True)
    for c in ["order_delivered_customer_date","shipping_limit_date"]:
        if c in items: items[c]=pd.to_datetime(items[c],utc=True)
    return orders,items

def demand_forecast(horizon=8):
    """Weekly category-level order-item demand; recursive lag-feature RF forecast."""
    _,items=_read()
    items["order_purchase_timestamp"]=pd.to_datetime(items["order_purchase_timestamp"],errors="coerce",utc=True).dt.tz_convert(None)
    items=items.dropna(subset=["order_purchase_timestamp","category"])
    items["week"]=items["order_purchase_timestamp"].dt.to_period("W").dt.start_time
    top=items.category.value_counts().head(8).index.tolist()
    rows=[]
    for category in top:
        y=(items[items.category==category].groupby("week").size().sort_index())
        if len(y)<20: continue
        idx=pd.date_range(y.index.min(),y.index.max(),freq="W-MON")
        y=y.reindex(idx,fill_value=0).astype(float)
        frame=pd.DataFrame({"y":y})
        for lag in [1,2,3,4,8,12]:
            frame[f"lag_{lag}"]=frame.y.shift(lag)
        frame["roll4"]=frame.y.shift(1).rolling(4).mean()
        frame["weekofyear"]=frame.index.isocalendar().week.astype(int)
        train=frame.dropna()
        if len(train)<12: continue
        X=train.drop(columns="y"); model=RandomForestRegressor(n_estimators=250,min_samples_leaf=2,random_state=42)
        model.fit(X,train.y)
        hist=list(y.values); last=idx[-1]
        for step in range(1,horizon+1):
            dt=last+pd.Timedelta(weeks=step)
            feats={f"lag_{lag}":hist[-lag] if len(hist)>=lag else float(np.mean(hist)) for lag in [1,2,3,4,8,12]}
            feats["roll4"]=float(np.mean(hist[-4:]))
            feats["weekofyear"]=int(dt.isocalendar().week)
            pred=max(0.0,float(model.predict(pd.DataFrame([feats]))[0]))
            hist.append(pred); rows.append({"category":category,"week":dt,"forecast_items":pred})
    result=pd.DataFrame(rows)
    setup(); result.to_csv(path("artifacts")/"weekly_demand_forecast.csv",index=False)
    return result

def seller_scorecard():
    _,items=_read()
    g=items.groupby("seller_id",dropna=False).agg(
      orders=("order_id","nunique"),items=("order_id","size"),
      late_rate=("late_delivery","mean"),avg_freight=("freight_value","mean"),
      avg_item_value=("price","mean")).reset_index()
    g["performance_score"]=(100*(1-g.late_rate.clip(0,1))).round(1)
    g["risk_band"]=pd.cut(g.performance_score,[-1,60,80,100.1],labels=["High risk","Watch","Good"]).astype(str)
    g=g.sort_values(["performance_score","orders"],ascending=[True,False])
    g.to_csv(path("artifacts")/"seller_scorecard.csv",index=False)
    return g

def detect_anomalies(contamination=0.02):
    _,items=_read()
    cols=["price","freight_value"]
    x=items[cols].replace([np.inf,-np.inf],np.nan).dropna()
    if len(x)<20: return pd.DataFrame()
    model=IsolationForest(n_estimators=250,contamination=contamination,random_state=42)
    labels=model.fit_predict(x)
    out=items.loc[x.index,["order_id","seller_id","product_id","category"]+cols].copy()
    out["anomaly"]=labels==-1; out["anomaly_score"]=-model.score_samples(x)
    out=out.sort_values("anomaly_score",ascending=False)
    out.to_csv(path("artifacts")/"order_item_anomalies.csv",index=False)
    return out

def run():
    setup(); log=logger("advanced_analytics")
    f=demand_forecast(); s=seller_scorecard(); a=detect_anomalies()
    log.info("Advanced analytics complete: forecast=%d seller_rows=%d anomalies=%d",len(f),len(s),int(a.anomaly.sum()) if len(a) else 0)
    return {"forecast_rows":len(f),"seller_rows":len(s),"anomaly_rows":int(a.anomaly.sum()) if len(a) else 0}
