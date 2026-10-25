-- When do customers shop? Share of orders by hour of day (all days), to time nudges.
SELECT order_hour_of_day::INT AS hour,
       COUNT(*) AS orders,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_orders
FROM orders
GROUP BY 1
ORDER BY 1;
