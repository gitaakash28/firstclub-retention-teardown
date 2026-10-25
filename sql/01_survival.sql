-- Order-number survival: of customers who placed order 4 (everyone in the dataset), what share reach order N?
-- Instacart only includes customers with 4-100 orders, so 1->2 and 2->3 drop-off cannot be measured here.
WITH n AS (SELECT UNNEST([4,5,6,8,10,15,20,30,50,100]) AS order_n)
SELECT order_n,
       COUNT(*) FILTER (WHERE u.total_orders >= order_n)                                   AS customers,
       ROUND(100.0 * COUNT(*) FILTER (WHERE u.total_orders >= order_n) / COUNT(*), 1)      AS pct_reaching
FROM n CROSS JOIN users u
GROUP BY order_n
ORDER BY order_n;
