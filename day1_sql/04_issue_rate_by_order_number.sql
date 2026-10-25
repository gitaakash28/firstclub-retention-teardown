-- Q: Are early orders more likely to go wrong? Complaints per 100 delivered orders, by order number and reason.
WITH ranked AS (
  SELECT order_id, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at) AS order_n
  FROM orders WHERE status = 'delivered'
)
SELECT LEAST(r.order_n, 6)                                                         AS order_n_capped,   -- 6 = 6th and later
       COUNT(DISTINCT r.order_id)                                                  AS orders,
       ROUND(100.0 * COUNT(i.issue_id) / COUNT(DISTINCT r.order_id), 2)            AS issues_per_100_orders,
       ROUND(100.0 * COUNT(i.issue_id) FILTER (WHERE i.reason IN ('missing','wrong_item')) / COUNT(DISTINCT r.order_id), 2) AS picking_per_100,
       ROUND(100.0 * COUNT(i.issue_id) FILTER (WHERE i.reason IN ('quality','expired','damaged')) / COUNT(DISTINCT r.order_id), 2) AS quality_per_100
FROM ranked r
LEFT JOIN issues i ON i.order_id = r.order_id
GROUP BY 1
ORDER BY 1;
