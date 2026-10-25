-- Q: Did make-it-right work? Primary metric per arm with a 95% CI on the difference, plus guardrails.
-- Primary: share of assigned customers with a delivered order within 14 days of assignment.
WITH a AS (
  SELECT * FROM experiment_assignments WHERE experiment = 'make_it_right_v1'
), per_customer AS (
  SELECT a.customer_id, a.variant,
         MAX(CASE WHEN o.created_at > a.assigned_at AND o.created_at <= a.assigned_at + INTERVAL '14 days' THEN 1 ELSE 0 END) AS reordered_14d,
         COALESCE(SUM(o.gmv) FILTER (WHERE o.created_at > a.assigned_at AND o.created_at <= a.assigned_at + INTERVAL '28 days'), 0) AS gmv_28d,
         COUNT(o.order_id) FILTER (WHERE o.created_at > a.assigned_at AND o.created_at <= a.assigned_at + INTERVAL '28 days')  AS orders_28d
  FROM a LEFT JOIN orders o ON o.customer_id = a.customer_id AND o.status = 'delivered'
  GROUP BY a.customer_id, a.variant
), credits AS (
  -- Credit cost includes the triggering issue (that credit is the treatment); claims count only later issues (abuse check).
  SELECT a.variant,
         SUM(i.credit_amount)                                          AS credit_28d,
         COUNT(i.issue_id) FILTER (WHERE i.created_at > a.assigned_at) AS claims_28d
  FROM a JOIN issues i ON i.customer_id = a.customer_id
                      AND i.created_at >= a.assigned_at AND i.created_at <= a.assigned_at + INTERVAL '28 days'
  GROUP BY a.variant
), arms AS (
  SELECT p.variant, COUNT(*) AS n, AVG(p.reordered_14d) AS p,
         SUM(p.gmv_28d) AS gmv_28d, SUM(p.orders_28d) AS orders_28d
  FROM per_customer p GROUP BY p.variant
)
SELECT t.n AS n_treatment, c.n AS n_control,
       ROUND(100 * t.p, 1)                                                                          AS pct_reorder_14d_treatment,
       ROUND(100 * c.p, 1)                                                                          AS pct_reorder_14d_control,
       ROUND(100 * (t.p - c.p), 1)                                                                  AS lift_pp,
       ROUND(100 * (t.p - c.p - 1.96 * SQRT(t.p * (1 - t.p) / t.n + c.p * (1 - c.p) / c.n)), 1)    AS ci95_low_pp,
       ROUND(100 * (t.p - c.p + 1.96 * SQRT(t.p * (1 - t.p) / t.n + c.p * (1 - c.p) / c.n)), 1)    AS ci95_high_pp,
       ROUND(100.0 * ct.credit_28d / NULLIF(t.gmv_28d, 0), 2)                                       AS guardrail_credit_pct_gmv_treatment,
       ROUND(100.0 * cc.credit_28d / NULLIF(c.gmv_28d, 0), 2)                                       AS guardrail_credit_pct_gmv_control,
       ROUND(100.0 * ct.claims_28d / NULLIF(t.orders_28d, 0), 1)                                    AS guardrail_claims_per_100_orders_treatment,
       ROUND(100.0 * cc.claims_28d / NULLIF(c.orders_28d, 0), 1)                                    AS guardrail_claims_per_100_orders_control
FROM arms t, arms c, credits ct, credits cc
WHERE t.variant = 'treatment' AND c.variant = 'control' AND ct.variant = 'treatment' AND cc.variant = 'control';
