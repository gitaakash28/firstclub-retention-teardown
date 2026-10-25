-- Q: Did make-it-right work? Every new customer is randomized at their first order (intent to treat), because the
-- button itself changes who reports issues; randomizing at the first reported issue would compare different people.
--
-- Part 1, primary: early-habit rate = share of new customers with 3+ delivered orders within 30 days of their first.
-- Part 2, pre-registered triggered readout: customers whose orders 1-5 include an ops-detected failure (late by 15+ min
--         vs the promised ETA, or a short-picked item). These triggers fire the same way in both arms, so the subgroup
--         is comparable. Bad produce can't be detected by ops data, so its effect shows up only in Part 1.
-- Guardrails: credit cost as % of GMV and claims per 100 orders, over each customer's first 30 days.
WITH a AS (
  SELECT * FROM experiment_assignments WHERE experiment = 'make_it_right_v1'
), ranked AS (
  SELECT o.*, ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.created_at) AS order_n
  FROM orders o WHERE o.status = 'delivered'
), per_customer AS (
  SELECT a.customer_id, a.variant,
         CASE WHEN COUNT(r.order_id) FILTER (WHERE r.created_at < a.assigned_at + INTERVAL '30 days') >= 3 THEN 1 ELSE 0 END AS habit_30d,
         COALESCE(SUM(r.gmv) FILTER (WHERE r.created_at < a.assigned_at + INTERVAL '30 days'), 0)                          AS gmv_30d,
         COUNT(r.order_id) FILTER (WHERE r.created_at < a.assigned_at + INTERVAL '30 days')                                 AS orders_30d
  FROM a LEFT JOIN ranked r ON r.customer_id = a.customer_id
  GROUP BY a.customer_id, a.variant
), first_failure AS (                    -- first ops-detected failure in orders 1-5, identical rule in both arms
  SELECT DISTINCT ON (r.customer_id) r.customer_id, r.created_at AS failed_at
  FROM ranked r
  WHERE r.order_n <= 5 AND (r.delivered_at > r.promised_at + INTERVAL '15 minutes' OR r.short_picked_items > 0)
  ORDER BY r.customer_id, r.created_at
), triggered AS (
  SELECT a.variant,
         COUNT(*) AS n,
         AVG(CASE WHEN EXISTS (SELECT 1 FROM ranked r WHERE r.customer_id = f.customer_id
                               AND r.created_at > f.failed_at AND r.created_at <= f.failed_at + INTERVAL '14 days') THEN 1 ELSE 0 END) AS p
  FROM first_failure f JOIN a USING (customer_id)
  GROUP BY a.variant
), credits AS (
  SELECT a.variant, SUM(i.credit_amount) AS credit_30d, COUNT(i.issue_id) AS claims_30d
  FROM a JOIN issues i ON i.customer_id = a.customer_id AND i.created_at < a.assigned_at + INTERVAL '30 days'
  GROUP BY a.variant
), arms AS (
  SELECT variant, COUNT(*) AS n, AVG(habit_30d) AS p, SUM(gmv_30d) AS gmv, SUM(orders_30d) AS orders
  FROM per_customer GROUP BY variant
)
SELECT t.n AS n_treatment, c.n AS n_control,
       ROUND(100 * t.p, 1)                                                                       AS habit_30d_treatment_pct,
       ROUND(100 * c.p, 1)                                                                       AS habit_30d_control_pct,
       ROUND(100 * (t.p - c.p), 2)                                                               AS lift_pp,
       ROUND(100 * (t.p - c.p - 1.96 * SQRT(t.p * (1 - t.p) / t.n + c.p * (1 - c.p) / c.n)), 2) AS ci95_low_pp,
       ROUND(100 * (t.p - c.p + 1.96 * SQRT(t.p * (1 - t.p) / t.n + c.p * (1 - c.p) / c.n)), 2) AS ci95_high_pp,
       tt.n AS triggered_n_treatment, tc.n AS triggered_n_control,
       ROUND(100 * tt.p, 1)                                                                      AS triggered_reorder_14d_treatment_pct,
       ROUND(100 * tc.p, 1)                                                                      AS triggered_reorder_14d_control_pct,
       ROUND(100.0 * ct.credit_30d / NULLIF(t.gmv, 0), 2)                                        AS guardrail_credit_pct_gmv_treatment,
       ROUND(100.0 * cc.credit_30d / NULLIF(c.gmv, 0), 2)                                        AS guardrail_credit_pct_gmv_control,
       ROUND(100.0 * ct.claims_30d / NULLIF(t.orders, 0), 1)                                     AS guardrail_claims_per_100_orders_treatment,
       ROUND(100.0 * cc.claims_30d / NULLIF(c.orders, 0), 1)                                     AS guardrail_claims_per_100_orders_control
FROM arms t, arms c, triggered tt, triggered tc, credits ct, credits cc
WHERE t.variant = 'treatment' AND c.variant = 'control' AND tt.variant = 'treatment' AND tc.variant = 'control'
  AND ct.variant = 'treatment' AND cc.variant = 'control';
