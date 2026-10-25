-- Q: Does a bad first order (late by 15+ minutes, or any complaint) lower the chance of a second order within 14 days?
WITH ranked AS (
  SELECT o.*, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at) AS order_n,
         LEAD(created_at) OVER (PARTITION BY customer_id ORDER BY created_at)  AS next_order_at
  FROM orders o WHERE status = 'delivered'
), first_order AS (
  SELECT r.*,
         (r.delivered_at > r.promised_at + INTERVAL '15 minutes')       AS was_late,
         EXISTS (SELECT 1 FROM issues i WHERE i.order_id = r.order_id)  AS had_issue
  FROM ranked r WHERE order_n = 1
)
SELECT CASE WHEN had_issue THEN 'complaint'
            WHEN was_late  THEN 'late, no complaint'
            ELSE 'smooth' END                                                          AS first_order_experience,
       COUNT(*)                                                                         AS customers,
       ROUND(100.0 * AVG(CASE WHEN next_order_at <= created_at + INTERVAL '14 days' THEN 1 ELSE 0 END), 1) AS pct_order2_within_14d
FROM first_order
GROUP BY 1
ORDER BY 1;
