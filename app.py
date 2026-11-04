import joblib,duckdb,pandas as pd,plotly.express as px,streamlit as st
from src.common import path
from src.features import single_frame
from src.inventory import recommend_replenishment
st.set_page_config(page_title="Supply Chain Intelligence",page_icon="🚚",layout="wide")
st.title("🚚 Supply Chain Intelligence Platform")
st.caption("Historical Olist logistics analytics | Forecasting · Risk · Supplier intelligence · Inventory what-if")
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
t1,t2,t3,t4,t5,t6,t7=st.tabs(["Overview","Logistics","Delivery risk","Demand forecast","Supplier scorecard","Anomaly detection","Inventory simulator"])
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
    f=path("artifacts")/"weekly_demand_forecast.csv"
    if f.exists():
        forecast=pd.read_csv(f); forecast["week"]=pd.to_datetime(forecast.week)
        categories=sorted(forecast.category.unique())
        selected=st.selectbox("Product category",categories)
        view=forecast[forecast.category==selected]
        st.plotly_chart(px.line(view,x="week",y="forecast_items",markers=True,title=f"Weekly demand forecast: {selected}"),use_container_width=True)
        st.dataframe(view,use_container_width=True)
    else: st.warning("Run the full pipeline to generate forecasts.")
    st.caption("Forecasts use historical weekly item counts for the eight largest categories; recursive Random Forest forecasts are estimates, not live demand.")
with t5:
    f=path("artifacts")/"seller_scorecard.csv"
    if f.exists():
        sellers=pd.read_csv(f); st.caption("Performance score is 100 × (1 − historical late-delivery rate); sellers with more history are easier to compare.")
        st.dataframe(sellers,use_container_width=True)
        st.plotly_chart(px.scatter(sellers,x="orders",y="late_rate",size="items",hover_name="seller_id",title="Seller volume vs late-delivery rate"),use_container_width=True)
    else: st.warning("Run the full pipeline to generate seller scores.")
with t6:
    f=path("artifacts")/"order_item_anomalies.csv"
    if f.exists():
        anomalies=pd.read_csv(f); flagged=anomalies[anomalies.anomaly==True]
        st.metric("Flagged unusual order items",len(flagged))
        st.dataframe(flagged.head(100),use_container_width=True)
    else: st.warning("Run the full pipeline to generate anomaly results.")
    st.caption("Isolation Forest flags unusual price/freight combinations. These are investigation candidates, not confirmed fraud.")
with t7:
    st.info("Olist does not provide on-hand inventory. Enter hypothetical inventory and lead-time values; outputs are scenario calculations, not observed stock.")
    x,y,z=st.columns(3)
    stock=x.number_input("Current stock (units)",min_value=0,value=50)
    demand=y.number_input("Average weekly demand (units)",min_value=0.0,value=30.0)
    lead=z.number_input("Supplier lead time (days)",min_value=0,value=14)
    buffer=st.slider("Safety buffer (weeks)",0.0,4.0,1.0,0.25)
    pack=st.number_input("Supplier pack size",min_value=1,value=1)
    if st.button("Calculate replenishment"):
        r=recommend_replenishment(stock,demand,lead,buffer,pack)
        x,y,z=st.columns(3); x.metric("Reorder point",f"{r['reorder_point']:.0f} units")
        y.metric("Suggested order",f"{r['recommended_order_qty']} units"); z.metric("Stockout risk",r["stockout_risk"])
