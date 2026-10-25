-- Q (the PRD baseline): after an issue in a customer's first 5 orders, what share order again within 14 days,
-- and does that depend on how fast the issue was resolved?
WITH ranked AS (
  SELECT order_id, customer_id, created_at,
         ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at) AS order_n
  FROM orders WHERE status = 'delivered'
), early_issues AS (
  SELECT DISTINCT ON (i.customer_id) i.*, r.order_n
  FROM issues i JOIN ranked r USING (order_id)
  WHERE r.order_n <= 5
  ORDER BY i.customer_id, i.created_at          -- first early issue per customer
)
SELECT CASE WHEN e.resolved_at IS NULL                                    THEN '4 unresolved'
            WHEN e.resolved_at <= e.created_at + INTERVAL '1 hour'        THEN '1 under 1 hour'
            WHEN e.resolved_at <= e.created_at + INTERVAL '24 hours'      THEN '2 1-24 hours'
            ELSE '3 over 24 hours' END                                     AS resolution_time,
       COUNT(*)                                                            AS customers,
       ROUND(100.0 * AVG(CASE WHEN EXISTS (
               SELECT 1 FROM orders o
               WHERE o.customer_id = e.customer_id AND o.status = 'delivered'
                 AND o.created_at > e.created_at AND o.created_at <= e.created_at + INTERVAL '14 days')
             THEN 1 ELSE 0 END), 1)                                        AS pct_reorder_within_14d
FROM early_issues e
GROUP BY 1
ORDER BY 1;
