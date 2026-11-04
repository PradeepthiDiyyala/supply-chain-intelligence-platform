import duckdb
from .common import setup, logger, path

TABLES=["fact_orders","fact_order_items","dim_customers","dim_sellers","dim_products"]
def run():
    setup(); log=logger("warehouse"); db=path("warehouse")
    con=duckdb.connect(str(db))
    try:
        for name in TABLES:
            f=(path("gold")/f"{name}.parquet").as_posix().replace("'","''")
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_parquet('{f}')")
            log.info("%s rows=%s",name,con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])
        con.execute("""CREATE OR REPLACE VIEW mart_monthly_logistics AS
          SELECT purchase_month,COUNT(*) orders,SUM(COALESCE(gmv_brl,0)) gmv_brl,
          SUM(COALESCE(freight_brl,0)) freight_brl,
          AVG(CASE WHEN delivery_status!='not_delivered' THEN late_delivery::DOUBLE END) late_rate,
          AVG(delivery_days) avg_delivery_days FROM fact_orders
          WHERE purchase_month IS NOT NULL GROUP BY purchase_month ORDER BY purchase_month""")
        con.execute("""CREATE OR REPLACE VIEW mart_state_performance AS
          SELECT customer_state state,COUNT(*) orders,SUM(COALESCE(gmv_brl,0)) gmv_brl,
          AVG(CASE WHEN delivery_status!='not_delivered' THEN late_delivery::DOUBLE END) late_rate,
          AVG(delivery_days) avg_delivery_days FROM fact_orders
          WHERE customer_state IS NOT NULL GROUP BY customer_state ORDER BY orders DESC""")
        con.execute("""CREATE OR REPLACE VIEW mart_category_performance AS
          SELECT category,COUNT(DISTINCT order_id) orders,SUM(price) gmv_brl,
          SUM(freight_value) freight_brl,AVG(late_delivery::DOUBLE) late_rate
          FROM fact_order_items GROUP BY category ORDER BY gmv_brl DESC""")
    finally: con.close()
    return str(db)
if __name__=="__main__": print(run())
