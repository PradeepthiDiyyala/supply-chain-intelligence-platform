import joblib,duckdb,pandas as pd,plotly.express as px,streamlit as st
from src.common import path
from src.features import single_frame
st.set_page_config(page_title="Supply Chain Intelligence",page_icon="🚚",layout="wide")
st.title("🚚 Supply Chain Intelligence Platform")
st.caption("Olist historical logistics analytics | Python · Parquet · DuckDB · scikit-learn")
db=path("warehouse")
if not db.exists():
    st.error("Warehouse missing. Add Olist CSVs to data/raw and run python -m src.pipeline --all."); st.stop()
def q(sql):
    c=duckdb.connect(str(db),read_only=True)
    try:return c.execute(sql).df()
    finally:c.close()
orders=q("SELECT * FROM fact_orders")
deliv=orders[orders.delivery_status!="not_delivered"]
late=deliv.late_delivery.mean() if len(deliv) else 0
a,b,c,d=st.columns(4)
a.metric("Orders",f"{len(orders):,}"); b.metric("GMV (BRL)",f"R$ {orders.gmv_brl.fillna(0).sum():,.0f}")
c.metric("Late delivery",f"{late:.1%}"); d.metric("Avg delivery days",f"{deliv.delivery_days.mean():.1f}" if len(deliv) else "N/A")
t1,t2,t3,t4=st.tabs(["Overview","Logistics","Risk scoring","Data quality"])
with t1:
    m=q("SELECT * FROM mart_monthly_logistics")
    st.plotly_chart(px.line(m,x="purchase_month",y="orders",title="Monthly order volume"),use_container_width=True)
    st.plotly_chart(px.line(m,x="purchase_month",y="gmv_brl",title="Monthly GMV (BRL)"),use_container_width=True)
    st.dataframe(m,use_container_width=True)
with t2:
    s=q("SELECT * FROM mart_state_performance"); cats=q("SELECT * FROM mart_category_performance LIMIT 20")
    x,y=st.columns(2)
    x.plotly_chart(px.bar(s.head(15),x="state",y="late_rate",title="Late rate by state"),use_container_width=True)
    y.plotly_chart(px.bar(cats.head(15),x="category",y="gmv_brl",title="Category GMV"),use_container_width=True)
    st.dataframe(s,use_container_width=True)
with t3:
    mp=path("artifacts")/"delivery_risk_model.joblib"
    if not mp.exists(): st.warning("Train first: python -m src.train")
    else:
        model=joblib.load(mp); st.write("Score a hypothetical order profile. This is not a carrier guarantee.")
        z1,z2,z3=st.columns(3)
        hour=z1.slider("Purchase hour",0,23,12); dow=z1.selectbox("Weekday (Mon=0)",range(7),2)
        month=z1.slider("Month",1,12,6); horizon=z1.number_input("Estimated days",1.,60.,15.)
        count=z2.number_input("Items",1,30,1); gmv=z2.number_input("Order value BRL",1.,10000.,150.)
        freight=z2.number_input("Freight BRL",0.,3000.,25.); sellers=z2.number_input("Sellers",1,10,1)
        products=z3.number_input("Unique products",1,30,1); inst=z3.number_input("Payment installments",1,24,1)
        ptypes=z3.number_input("Payment types",1,5,1); state=z3.text_input("Customer state","SP").upper()[:2]
        if st.button("Score late-delivery risk",type="primary"):
            row={"purchase_hour":hour,"purchase_dayofweek":dow,"purchase_month_num":month,"estimated_delivery_days":horizon,
            "item_count":count,"gmv_brl":gmv,"freight_brl":freight,"seller_count":sellers,"product_count":products,
            "payment_installments_max":inst,"payment_type_count":ptypes,"customer_state":state}
            score=float(model.predict_proba(single_frame(row))[0,1]); st.metric("Estimated late risk",f"{score:.1%}"); st.progress(score)
with t4:
    st.dataframe(pd.DataFrame([{"column":col,"nulls":int(orders[col].isna().sum()),"null_rate":float(orders[col].isna().mean())}
      for col in ["order_id","order_purchase_timestamp","customer_id","order_status","gmv_brl","freight_brl"]]),use_container_width=True)
    st.metric("Duplicate order IDs",int(orders.order_id.duplicated().sum()))
