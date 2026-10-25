-- Assumed FirstClub schema (Postgres). Table and column names are my guesses at a typical quick-commerce
-- warehouse; on day 1 I'd map these to the real tables, the query logic stays the same.

CREATE TABLE customers (
  customer_id   BIGINT PRIMARY KEY,
  signup_at     TIMESTAMP NOT NULL,
  city          TEXT,            -- 'Bengaluru' | 'Hyderabad'
  pincode       TEXT
);

CREATE TABLE app_events (          -- onboarding funnel events, one row per event
  customer_id   BIGINT,
  event_name    TEXT,            -- 'install' | 'otp_verified' | 'location_set' | 'serviceability_result' | 'first_order'
  event_at      TIMESTAMP,
  pincode       TEXT,
  is_serviceable BOOLEAN         -- only on serviceability_result
);

CREATE TABLE orders (
  order_id      BIGINT PRIMARY KEY,
  customer_id   BIGINT REFERENCES customers,
  store_id      INT,             -- dark store
  created_at    TIMESTAMP NOT NULL,
  promised_at   TIMESTAMP,       -- ETA shown at checkout
  delivered_at  TIMESTAMP,
  status        TEXT,            -- 'delivered' | 'cancelled'
  gmv           NUMERIC(10,2),
  delivery_fee  NUMERIC(10,2),
  handling_fee  NUMERIC(10,2)
);

CREATE TABLE order_items (
  order_id      BIGINT REFERENCES orders,
  sku_id        BIGINT,
  category      TEXT,            -- 'fruits_veg' | 'dairy' | 'bakery' | 'staples' | 'snacks' | 'home'
  qty           INT,
  unit_price    NUMERIC(10,2)
);

CREATE TABLE issues (              -- one row per customer complaint about an order
  issue_id      BIGINT PRIMARY KEY,
  order_id      BIGINT REFERENCES orders,
  customer_id   BIGINT REFERENCES customers,
  created_at    TIMESTAMP,
  reason        TEXT,            -- 'missing' | 'damaged' | 'quality' | 'expired' | 'wrong_item' | 'late'
  channel       TEXT,            -- 'chat' | 'call' | 'email' | 'one_tap' (after launch)
  resolved_at   TIMESTAMP,       -- NULL = unresolved
  resolution    TEXT,            -- 'refund' | 'credit' | 'replacement' | 'none'
  credit_amount NUMERIC(10,2)
);

CREATE TABLE experiment_assignments (
  customer_id   BIGINT REFERENCES customers,
  experiment    TEXT,            -- e.g. 'make_it_right_v1'
  variant       TEXT,            -- 'control' | 'treatment'
  assigned_at   TIMESTAMP        -- the customer's first early-order issue
);
