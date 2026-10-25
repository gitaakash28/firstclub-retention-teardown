-- Q: Which active customers are overdue right now? Days since last order vs their own median gap.
-- Feeds a win-back list (and the cadence-nudge idea in the PRD). psql: \set as_of '2026-10-25'.
WITH gaps AS (
  SELECT customer_id, created_at,
         EXTRACT(EPOCH FROM (created_at - LAG(created_at) OVER (PARTITION BY customer_id ORDER BY created_at))) / 86400 AS gap_days
  FROM orders WHERE status = 'delivered'
), per_customer AS (
  SELECT customer_id,
         COUNT(*)                                                       AS orders,
         MAX(created_at)                                                AS last_order_at,
         GREATEST(percentile_cont(0.5) WITHIN GROUP (ORDER BY gap_days), 1) AS median_gap_days   -- same-day repeats floor at 1 day
  FROM gaps
  GROUP BY customer_id
  HAVING COUNT(*) >= 4                                                  -- needs a rhythm to break
)
SELECT customer_id, orders,
       ROUND(median_gap_days::numeric, 1)                                                  AS median_gap_days,
       ROUND((EXTRACT(EPOCH FROM (CAST(:'as_of' AS TIMESTAMP) - last_order_at)) / 86400)::numeric, 1) AS days_since_last,
       ROUND((EXTRACT(EPOCH FROM (CAST(:'as_of' AS TIMESTAMP) - last_order_at)) / 86400 / NULLIF(median_gap_days, 0))::numeric, 1) AS overdue_ratio
FROM per_customer
WHERE EXTRACT(EPOCH FROM (CAST(:'as_of' AS TIMESTAMP) - last_order_at)) / 86400 >= 2 * median_gap_days
  AND EXTRACT(EPOCH FROM (CAST(:'as_of' AS TIMESTAMP) - last_order_at)) / 86400 >= 7
ORDER BY overdue_ratio DESC
LIMIT 500;
