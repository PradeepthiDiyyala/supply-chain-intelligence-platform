# Dataset inventory

Source: Olist Brazilian E-Commerce Public Dataset (2016–2018), anonymised commercial orders.

| File | Grain | Important fields |
|---|---|---|
| orders | order | status and purchase/approval/carrier/delivery/estimated timestamps |
| customers | order-customer key | customer ID, unique customer ID, city/state/ZIP |
| order_items | order item | product, seller, price, freight, shipping limit |
| order_payments | payment transaction | payment type, installments, value |
| order_reviews | review | score, comments, timestamps |
| products | product | category, weight, dimensions |
| sellers | seller | city, state, ZIP |
| geolocation | coordinate point | ZIP prefix, latitude, longitude |
| category translation | category | Portuguese and English category labels |

See the Kaggle dataset card for full schema.
