SELECT purchase_month,COUNT(*) delivered_orders,
       AVG(late_delivery::DOUBLE) late_rate,AVG(delivery_days) avg_delivery_days
FROM fact_orders WHERE delivery_status!='not_delivered'
GROUP BY purchase_month ORDER BY purchase_month;

SELECT seller_id,COUNT(DISTINCT order_id) orders,AVG(late_delivery::DOUBLE) late_rate
FROM fact_order_items GROUP BY seller_id HAVING COUNT(DISTINCT order_id)>=30
ORDER BY late_rate DESC LIMIT 25;

SELECT category,SUM(freight_value) freight_brl,SUM(price) gmv_brl,
       SUM(freight_value)/NULLIF(SUM(price),0) freight_to_gmv
FROM fact_order_items GROUP BY category ORDER BY freight_to_gmv DESC;
