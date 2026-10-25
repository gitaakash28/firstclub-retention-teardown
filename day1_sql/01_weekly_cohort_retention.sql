-- Q: Of customers whose first order was in week W, what share ordered again in each later week?
-- The classic retention triangle; the first chart I'd put on the retention dashboard.
WITH first_orders AS (
  SELECT customer_id, MIN(created_at) AS first_order_at
  FROM orders WHERE status = 'delivered'
  GROUP BY customer_id
), activity AS (
  SELECT f.customer_id,
         date_trunc('week', f.first_order_at)                                        AS cohort_week,
         FLOOR(EXTRACT(EPOCH FROM (o.created_at - f.first_order_at)) / 604800)::INT  AS week_n
  FROM first_orders f
  JOIN orders o ON o.customer_id = f.customer_id AND o.status = 'delivered'
)
SELECT cohort_week,
       COUNT(DISTINCT customer_id)                                                         AS cohort_size,
       ROUND(100.0 * COUNT(DISTINCT customer_id) FILTER (WHERE week_n = 1) / COUNT(DISTINCT customer_id), 1) AS pct_w1,
       ROUND(100.0 * COUNT(DISTINCT customer_id) FILTER (WHERE week_n = 2) / COUNT(DISTINCT customer_id), 1) AS pct_w2,
       ROUND(100.0 * COUNT(DISTINCT customer_id) FILTER (WHERE week_n = 4) / COUNT(DISTINCT customer_id), 1) AS pct_w4,
       ROUND(100.0 * COUNT(DISTINCT customer_id) FILTER (WHERE week_n = 8) / COUNT(DISTINCT customer_id), 1) AS pct_w8
FROM activity
GROUP BY cohort_week
ORDER BY cohort_week;
