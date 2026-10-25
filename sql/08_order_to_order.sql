-- Order-to-order drop-off: of customers who placed order N, what share never placed order N+1?
-- Shows where in the lifecycle each additional order is most at risk.
WITH reach AS (
  SELECT n.order_n, COUNT(*) FILTER (WHERE u.total_orders >= n.order_n) AS reached
  FROM (SELECT UNNEST(range(4, 41)) AS order_n) n CROSS JOIN users u
  GROUP BY n.order_n
)
SELECT order_n,
       reached,
       ROUND(100.0 * (1 - LEAD(reached) OVER (ORDER BY order_n) / reached), 1) AS pct_lost_before_next_order
FROM reach
ORDER BY order_n;
