-- Cadence segments: a customer's typical gap between orders vs how many orders they end up placing.
SELECT CASE WHEN median_gap_days <= 7  THEN '1 weekly (<=7d)'
            WHEN median_gap_days <= 14 THEN '2 fortnightly (8-14d)'
            WHEN median_gap_days < 30  THEN '3 monthly (15-29d)'
            ELSE '4 lapsing (30d+, capped)' END                           AS cadence,
       COUNT(*)                                                           AS customers,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)                 AS pct_customers,
       MEDIAN(total_orders)                                               AS median_lifetime_orders,
       ROUND(100.0 * AVG((total_orders >= 20)::INT), 1)                   AS pct_reaching_20_orders
FROM users
GROUP BY 1
ORDER BY 1;
