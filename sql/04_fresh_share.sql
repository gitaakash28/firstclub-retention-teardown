-- Fresh share of the first 3 baskets (produce, dairy & eggs, bakery: FirstClub's core categories)
-- vs long-run outcome.
WITH early AS (
  SELECT user_id,
         AVG((department IN ('produce','dairy eggs','bakery'))::INT) AS fresh_share
  FROM items
  WHERE order_number <= 3
  GROUP BY user_id
), b AS (
  SELECT e.*, u.total_orders,
         CASE WHEN fresh_share < 0.25 THEN '1 <25%'
              WHEN fresh_share < 0.50 THEN '2 25-50%'
              WHEN fresh_share < 0.75 THEN '3 50-75%'
              ELSE '4 75%+' END AS fresh_band
  FROM early e JOIN users u USING (user_id)
)
SELECT fresh_band,
       COUNT(*)                                             AS customers,
       MEDIAN(total_orders)                                 AS median_lifetime_orders,
       ROUND(100.0 * AVG((total_orders >= 10)::INT), 1)     AS pct_reaching_10_orders,
       ROUND(100.0 * AVG((total_orders >= 20)::INT), 1)     AS pct_reaching_20_orders
FROM b
GROUP BY fresh_band
ORDER BY fresh_band;
