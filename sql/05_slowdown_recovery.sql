-- Slowdown and recovery: when a customer's gap jumps to at least 2x their own running median (and >= 14 days),
-- how often does the following gap return to their normal rhythm? Needs 3+ earlier gaps for a stable baseline.
WITH g AS (
  SELECT user_id, order_number, days_since_prior_order AS gap,
         MEDIAN(days_since_prior_order) OVER (PARTITION BY user_id ORDER BY order_number
                                              ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS baseline,
         COUNT(days_since_prior_order) OVER (PARTITION BY user_id ORDER BY order_number
                                             ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS n_prior_gaps,
         LEAD(days_since_prior_order) OVER (PARTITION BY user_id ORDER BY order_number) AS next_gap
  FROM orders
), slow AS (
  SELECT * FROM g
  WHERE n_prior_gaps >= 3 AND gap >= 14 AND gap >= 2 * baseline AND next_gap IS NOT NULL
)
SELECT COUNT(*)                                                             AS slowdown_events,
       COUNT(DISTINCT user_id)                                              AS customers_with_slowdown,
       ROUND(100.0 * COUNT(DISTINCT user_id) / (SELECT COUNT(*) FROM users), 1) AS pct_customers_with_slowdown,
       ROUND(100.0 * AVG((next_gap <= 1.25 * baseline)::INT), 1)            AS pct_next_gap_back_to_normal,
       ROUND(100.0 * AVG((next_gap >= 30)::INT), 1)                         AS pct_next_gap_30d_plus
FROM slow;
