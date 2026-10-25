-- Early habit: share of items in orders 2-3 that repeat an earlier purchase, by quartile,
-- vs long-run outcome. Correlational: it shows which early behaviour to target, not causation.
WITH early AS (
  SELECT user_id, AVG(reordered) AS early_reorder_share
  FROM items
  WHERE order_number BETWEEN 2 AND 3
  GROUP BY user_id
), q AS (
  SELECT e.*, u.total_orders, NTILE(4) OVER (ORDER BY early_reorder_share) AS quartile
  FROM early e JOIN users u USING (user_id)
)
SELECT quartile,
       ROUND(MIN(early_reorder_share), 2)                       AS min_share,
       ROUND(MAX(early_reorder_share), 2)                       AS max_share,
       COUNT(*)                                                 AS customers,
       MEDIAN(total_orders)                                     AS median_lifetime_orders,
       ROUND(100.0 * AVG((total_orders >= 10)::INT), 1)         AS pct_reaching_10_orders,
       ROUND(100.0 * AVG((total_orders >= 20)::INT), 1)         AS pct_reaching_20_orders
FROM q
GROUP BY quartile
ORDER BY quartile;
