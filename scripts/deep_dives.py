"""Stress tests and the habit picture, from the tagged reviews.

r10: does a support complaint still go with churn within the same failure type? (+ Mantel-Haenszel odds ratio)
r11: where the rise in 1-2 star reviews came from, H1 vs H2 2026 (never ordered vs ordered vs unclear)
r12: habit signals: reviews tagged subscription_daily or fees_minimums, by period and sentiment
"""
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
R = ROOT / "results"
d = pd.read_csv(ROOT / "reviews" / "tagged_reviews.csv", parse_dates=["at"])
d["ts"] = d.themes.str.split("|").apply(set)
OPS = ["delivery_speed", "order_failure", "payment_refund", "quality_freshness"]

# r10
neg = d[(d.score <= 3) & d.sentiment.isin(["negative", "mixed"])]
rows = []
for th in OPS:
    g = neg[neg.ts.apply(lambda s: th in s)]
    for sup in (True, False):
        h = g[g.ts.apply(lambda s: ("support" in s) == sup)]
        rows.append({"failure_theme": th, "mentions_support": sup, "reviews": len(h),
                     "churn_signal": int((h.churn_signal == "yes").sum()),
                     "pct_churn_signal": round(100 * (h.churn_signal == "yes").mean(), 1)})
f = neg[neg.primary_theme.isin(OPS)].assign(sup=lambda x: x.ts.apply(lambda s: "support" in s), ch=lambda x: x.churn_signal == "yes")
num = sum((g.sup & g.ch).sum() * (~g.sup & ~g.ch).sum() / len(g) for _, g in f.groupby("primary_theme"))
den = sum((g.sup & ~g.ch).sum() * (~g.sup & g.ch).sum() / len(g) for _, g in f.groupby("primary_theme"))
rows.append({"failure_theme": f"Mantel-Haenszel odds ratio, stratified by primary failure theme (n={len(f)})",
             "mentions_support": None, "reviews": len(f), "churn_signal": None, "pct_churn_signal": round(num / den, 2)})
pd.DataFrame(rows).to_csv(R / "r10_support_churn_by_failure.csv", index=False)

# r11
h = d[d.period != "2025"].copy()
h["grp"] = h.stage_group.map(lambda g: "never ordered" if g == "never ordered" else
                             ("ordered" if g in ("first_order", "repeat", "ordered, stage unclear") else "unclear"))
h["low"] = h.score <= 2
r11 = h.groupby("period").apply(lambda g: pd.Series({
    "text_reviews": len(g),
    "pct_1_2_star_never_ordered": round(100 * (g.low & (g.grp == "never ordered")).mean(), 1),
    "pct_1_2_star_ordered": round(100 * (g.low & (g.grp == "ordered")).mean(), 1),
    "pct_1_2_star_unclear": round(100 * (g.low & (g.grp == "unclear")).mean(), 1),
    "pct_1_2_star_total": round(100 * g.low.mean(), 1)})).reset_index()
r11.to_csv(R / "r11_low_star_rise_by_stage.csv", index=False)

# r12
# From the LLM theme tags (fees_minimums passed the keyword check at 100%), not raw keywords: "subscri" also
# matched a review about a streaming app, and fee keywords can match praise like "free delivery is great".
sig = {"subscription": d.ts.apply(lambda x: "subscription_daily" in x),
       "fees_or_free_delivery_minimum": d.ts.apply(lambda x: "fees_minimums" in x)}
rows = []
for name, mask in sig.items():
    g = d[mask]
    rows.append({"signal": name, "reviews": len(g), "avg_stars": round(g.score.mean(), 2),
                 "negative": int((g.sentiment == "negative").sum()), "positive": int((g.sentiment == "positive").sum()),
                 "jan_jun_2026": int(((g["at"] >= "2026-01-01") & (g["at"] < "2026-07-01")).sum()),
                 "jul_oct_2026": int((g["at"] >= "2026-07-01").sum()),
                 "per_100_reviews_jan_jun": round(100 * ((g["at"] >= "2026-01-01") & (g["at"] < "2026-07-01")).sum()
                                                  / ((d["at"] >= "2026-01-01") & (d["at"] < "2026-07-01")).sum(), 2),
                 "per_100_reviews_jul_oct": round(100 * (g["at"] >= "2026-07-01").sum() / (d["at"] >= "2026-07-01").sum(), 2)})
pd.DataFrame(rows).to_csv(R / "r12_habit_signals.csv", index=False)
for n in ("r10_support_churn_by_failure", "r11_low_star_rise_by_stage", "r12_habit_signals"):
    print(f"\n== {n}\n" + pd.read_csv(R / f"{n}.csv").to_string(index=False))
