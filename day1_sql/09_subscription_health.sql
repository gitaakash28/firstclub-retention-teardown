-- Q: Subscriptions are the daily habit. When we miss a delivery, are subscribers more likely to cancel soon after?
-- Compares the 14-day cancellation rate after a week with a missed delivery vs a week without one.
WITH weeks AS (
  SELECT d.subscription_id, s.cancelled_at,
         date_trunc('week', d.delivery_date)                           AS week,
         COUNT(*) FILTER (WHERE d.status = 'missed')                   AS missed
  FROM subscription_deliveries d
  JOIN subscriptions s USING (subscription_id)
  GROUP BY 1, 2, 3
)
SELECT CASE WHEN missed > 0 THEN 'week with a missed delivery' ELSE 'clean week' END                  AS week_type,
       COUNT(*)                                                                                       AS subscription_weeks,
       ROUND(100.0 * AVG(CASE WHEN cancelled_at >= week + INTERVAL '7 days'
                               AND cancelled_at <  week + INTERVAL '21 days' THEN 1 ELSE 0 END), 2)  AS pct_cancelled_within_14d_after
FROM weeks
WHERE cancelled_at IS NULL OR cancelled_at >= week + INTERVAL '7 days'   -- still active at the end of that week
GROUP BY 1
ORDER BY 1;
