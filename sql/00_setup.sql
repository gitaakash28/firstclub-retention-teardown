-- Load the Kaggle Instacart CSVs as views. {DATA} is replaced by run_queries.py.
CREATE OR REPLACE VIEW orders      AS SELECT * FROM read_csv_auto('{DATA}/orders.csv');
CREATE OR REPLACE VIEW order_items AS SELECT * FROM read_csv_auto('{DATA}/order_products__prior.csv');
CREATE OR REPLACE VIEW products    AS SELECT * FROM read_csv_auto('{DATA}/products.csv');
CREATE OR REPLACE VIEW departments AS SELECT * FROM read_csv_auto('{DATA}/departments.csv');

-- One row per customer: lifetime orders and tenure (days_since_prior is capped at 30 in the source).
CREATE OR REPLACE TABLE users AS
SELECT user_id,
       MAX(order_number)                              AS total_orders,
       SUM(COALESCE(days_since_prior_order, 0))       AS tenure_days,
       MEDIAN(days_since_prior_order)                 AS median_gap_days
FROM orders
GROUP BY user_id;

-- Item-level history with department, prior orders only (the last order per customer has no items).
CREATE OR REPLACE TABLE items AS
SELECT o.user_id, o.order_number, oi.product_id, oi.reordered, p.department_id, d.department
FROM order_items oi
JOIN orders o      USING (order_id)
JOIN products p    USING (product_id)
JOIN departments d USING (department_id);
