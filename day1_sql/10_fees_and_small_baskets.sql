-- Q: Do delivery fees push small top-up orders elsewhere? Compare new customers whose first order paid a delivery
-- fee with those whose first order didn't, ONLY for first baskets within ±₹50 of the free-delivery minimum, so the
-- fee is the main difference rather than basket size. Still observational: a clean answer needs a test that moves
-- the minimum. psql: \set free_delivery_min 299
WITH ranked AS (
  SELECT o.*, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at) AS order_n
  FROM orders o WHERE status = 'delivered'
), firsts AS (
  SELECT customer_id, created_at AS first_at, gmv AS first_basket, delivery_fee > 0 AS paid_fee
  FROM ranked
  WHERE order_n = 1 AND gmv BETWEEN CAST(:'free_delivery_min' AS NUMERIC) - 50 AND CAST(:'free_delivery_min' AS NUMERIC) + 50
)
SELECT CASE WHEN f.paid_fee THEN 'first order paid a delivery fee' ELSE 'first order had free delivery' END AS first_order,
       COUNT(*)                                                                                             AS customers,
       ROUND(AVG(f.first_basket), 0)                                                                        AS avg_first_basket,
       ROUND(100.0 * AVG(CASE WHEN EXISTS (SELECT 1 FROM ranked r WHERE r.customer_id = f.customer_id
                 AND r.order_n = 2 AND r.created_at <= f.first_at + INTERVAL '14 days') THEN 1 ELSE 0 END), 1) AS pct_second_order_14d,
       ROUND(AVG((SELECT COUNT(*) FROM ranked r WHERE r.customer_id = f.customer_id
                  AND r.created_at < f.first_at + INTERVAL '30 days')), 2)                                  AS avg_orders_first_30d
FROM firsts f
GROUP BY 1
ORDER BY 1;
