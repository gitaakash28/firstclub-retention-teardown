"""Synthetic FirstClub-shaped data, ONLY to prove the day-1 queries run end to end.

Every behaviour here is random noise: churn, issues and resolution times are independent by design,
so the outputs carry no insight. Do not read the numbers in sample_output/ as findings.
"""
import pathlib
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
OUT = pathlib.Path(__file__).parent / "synthetic"
OUT.mkdir(exist_ok=True)
START, END = pd.Timestamp("2026-06-01"), pd.Timestamp("2026-10-25")
PINCODES = [f"5600{n:02d}" for n in range(1, 21)] + [f"5000{n:02d}" for n in range(1, 11)]
SERVICEABLE = set(rng.choice(PINCODES, 20, replace=False))
CATS = ["fruits_veg", "dairy", "bakery", "staples", "snacks", "home"]

events, customers, orders, items, issues = [], [], [], [], []
oid = iid = 0
for cid in range(1, 12001):
    pin = rng.choice(PINCODES)
    t = START + pd.Timedelta(minutes=int(rng.integers(0, int((END - START).total_seconds() // 60))))
    events.append((cid, "install", t, pin, None))
    if rng.random() < 0.85:
        events.append((cid, "otp_verified", t + pd.Timedelta(minutes=2), pin, None))
        events.append((cid, "location_set", t + pd.Timedelta(minutes=3), pin, None))
        ok = pin in SERVICEABLE
        events.append((cid, "serviceability_result", t + pd.Timedelta(minutes=3), pin, ok))
        if ok and rng.random() < 0.6:
            customers.append((cid, t, "Bengaluru" if pin.startswith("560") else "Hyderabad", pin))
            cadence = rng.uniform(4, 20)
            ot = t + pd.Timedelta(minutes=10)
            first = True
            while ot < END:
                oid += 1
                if first:
                    events.append((cid, "first_order", ot, pin, None))
                    first = False
                promised = ot + pd.Timedelta(minutes=int(rng.integers(15, 35)))
                delivered = promised + pd.Timedelta(minutes=int(rng.normal(0, 12)))
                gmv = round(float(rng.gamma(4, 180)), 2)
                orders.append((oid, cid, int(rng.integers(1, 9)), ot, promised, delivered, "delivered", gmv, 30.0 if gmv < 299 else 0.0, 9.0,
                               int(rng.random() < 0.05)))
                for _ in range(int(rng.integers(2, 9))):
                    items.append((oid, int(rng.integers(1, 2000)), rng.choice(CATS), int(rng.integers(1, 4)), round(float(rng.uniform(20, 400)), 2)))
                if rng.random() < 0.07:
                    iid += 1
                    created = delivered + pd.Timedelta(minutes=int(rng.integers(5, 600)))
                    hours = float(rng.lognormal(1.2, 1.3))
                    resolved = None if rng.random() < 0.08 else created + pd.Timedelta(hours=hours)
                    issues.append((iid, oid, cid, created, rng.choice(["missing", "damaged", "quality", "expired", "wrong_item", "late"]),
                                   rng.choice(["chat", "call", "email"], p=[0.7, 0.2, 0.1]), resolved,
                                   "none" if resolved is None else rng.choice(["refund", "credit", "replacement"]),
                                   0.0 if resolved is None else round(float(rng.uniform(30, 250)), 2)))
                if rng.random() < 0.10:      # random churn, independent of everything above
                    break
                ot = ot + pd.Timedelta(hours=float(rng.exponential(cadence * 24)))

cols = {
    "app_events": ["customer_id", "event_name", "event_at", "pincode", "is_serviceable"],
    "customers": ["customer_id", "signup_at", "city", "pincode"],
    "orders": ["order_id", "customer_id", "store_id", "created_at", "promised_at", "delivered_at", "status", "gmv", "delivery_fee", "handling_fee", "short_picked_items"],
    "order_items": ["order_id", "sku_id", "category", "qty", "unit_price"],
    "issues": ["issue_id", "order_id", "customer_id", "created_at", "reason", "channel", "resolved_at", "resolution", "credit_amount"],
}
data = {"app_events": events, "customers": customers, "orders": orders, "order_items": items, "issues": issues}
for name, rows in data.items():
    pd.DataFrame(rows, columns=cols[name]).to_parquet(OUT / f"{name}.parquet", index=False)

# Subscriptions: ~15% of customers subscribe to a daily item; misses and cancellations are independent noise.
subs, sub_del = [], []
cust = pd.DataFrame(customers, columns=cols["customers"])
for sid, row in enumerate(cust.sample(frac=0.15, random_state=7).itertuples(), start=1):
    start = (row.signup_at + pd.Timedelta(days=int(rng.integers(1, 20)))).normalize()
    cancel = None
    day = start
    while day < END:
        status = "skipped_by_customer" if rng.random() < 0.08 else ("missed" if rng.random() < 0.04 else "delivered")
        sub_del.append((sid, day.date(), status))
        if rng.random() < 0.006:
            cancel = day + pd.Timedelta(hours=20)
            break
        day += pd.Timedelta(days=1)
    subs.append((sid, row.customer_id, int(rng.integers(1, 50)), start, cancel))
pd.DataFrame(subs, columns=["subscription_id", "customer_id", "sku_id", "started_at", "cancelled_at"]).to_parquet(OUT / "subscriptions.parquet", index=False)
pd.DataFrame(sub_del, columns=["subscription_id", "delivery_date", "status"]).to_parquet(OUT / "subscription_deliveries.parquet", index=False)

# Experiment: every new customer randomised 50/50 at their first order (intent to treat).
o = pd.DataFrame(orders, columns=cols["orders"]).sort_values("created_at")
first = o.groupby("customer_id").head(1)
assign = pd.DataFrame({"customer_id": first.customer_id, "experiment": "make_it_right_v1",
                       "variant": rng.choice(["control", "treatment"], len(first)), "assigned_at": first.created_at})
assign.to_parquet(OUT / "experiment_assignments.parquet", index=False)
print({k: len(v) for k, v in data.items()}, "assignments", len(assign))
