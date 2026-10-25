-- First-order anchor items: fresh products in a customer's first basket, ranked by how often those
-- customers go on to reach 10+ orders. Minimum 2,000 first-order buyers per product.
WITH first_basket AS (
  SELECT DISTINCT i.user_id, i.product_id
  FROM items i
  WHERE i.order_number = 1 AND i.department IN ('produce','dairy eggs','bakery')
), base AS (SELECT AVG((total_orders >= 10)::INT) AS overall FROM users)
SELECT p.product_name,
       d.department,
       COUNT(*)                                              AS first_order_buyers,
       ROUND(100.0 * AVG((u.total_orders >= 10)::INT), 1)    AS pct_reaching_10_orders,
       ROUND(100.0 * (SELECT overall FROM base), 1)          AS pct_all_customers
FROM first_basket fb
JOIN users u       USING (user_id)
JOIN products p    USING (product_id)
JOIN departments d USING (department_id)
GROUP BY 1, 2
HAVING COUNT(*) >= 2000
ORDER BY pct_reaching_10_orders DESC
LIMIT 15;
