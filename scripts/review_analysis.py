"""Combine tagged FirstClub reviews and summarise themes by lifecycle stage, period and churn intent."""
import glob
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
raw = pd.read_csv(ROOT / "data" / "firstclub_play_reviews.csv", parse_dates=["at"])
tags = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(str(ROOT / "reviews" / "tags_batch_*.csv"))))
df = raw.drop(columns=["replyContent"], errors="ignore").merge(tags, on="reviewId", how="inner")
df["month"] = df["at"].dt.to_period("M").astype(str)
df["period"] = df["at"].apply(lambda t: "H1: Jan-May 2026" if pd.Timestamp("2026-01-01") <= t < pd.Timestamp("2026-06-01")
                              else ("H2: Jun-Oct 2026" if t >= pd.Timestamp("2026-06-01") else "2025"))
ORDER_THEMES = {"quality_freshness", "delivery_speed", "order_failure", "packaging_sustainability", "subscription_daily",
                "payment_refund", "fees_minimums"}
df["theme_list"] = df["themes"].str.split("|")
df["primary_theme"] = df["theme_list"].str[0]


def stage_group(r):
    if r.stage == "pre_order":
        return "never ordered"
    if r.stage in ("first_order", "repeat"):
        return r.stage
    return "ordered, stage unclear" if set(r.theme_list) & ORDER_THEMES else "unclear"


df["stage_group"] = df.apply(stage_group, axis=1)
df.drop(columns=["theme_list"]).to_csv(ROOT / "reviews" / "tagged_reviews.csv", index=False)
neg = df[df.sentiment.isin(["negative", "mixed"]) & (df.score <= 3)]
out = ROOT / "results"
out.mkdir(exist_ok=True)

# 1. Ratings over time (all reviews, including those without text)
raw["month"] = raw["at"].dt.to_period("M").astype(str)
m = raw.groupby("month").agg(reviews=("score", "size"), avg_rating=("score", "mean"),
                             pct_1_2_star=("score", lambda s: 100 * (s <= 2).mean())).round(2)
m.to_csv(out / "r1_rating_by_month.csv")
p = raw.assign(period=raw["at"].apply(lambda t: "H1" if pd.Timestamp("2026-01-01") <= t < pd.Timestamp("2026-06-01")
                                      else ("H2" if t >= pd.Timestamp("2026-06-01") else "2025")))
pp = p.groupby("period").agg(reviews=("score", "size"), avg_rating=("score", "mean"),
                             pct_1_2_star=("score", lambda s: 100 * (s <= 2).mean())).round(2)
pp.to_csv(out / "r1b_rating_by_period.csv")
print(pp, "\n")

# 2. Complaint themes (any mention) among negative reviews, H1 vs H2
ex = neg.explode("theme_list") if "theme_list" in neg else neg.assign(theme_list=neg.themes.str.split("|")).explode("theme_list")
t = (ex.groupby(["theme_list", "period"]).reviewId.nunique().unstack(fill_value=0))
for c in t.columns:
    t[f"pct_{c}"] = (100 * t[c] / neg[neg.period == c].reviewId.nunique()).round(1)
t["total"] = t[[c for c in t.columns if not str(c).startswith("pct_")]].sum(axis=1)
t = t.sort_values("total", ascending=False)
t.to_csv(out / "r2_negative_themes_by_period.csv")
print(f"negative/mixed reviews (<=3 stars): {len(neg)}  by period: {neg.period.value_counts().to_dict()}")
print(t, "\n")

# 3. Primary complaint by lifecycle stage
s = pd.crosstab(neg.primary_theme, neg.stage_group, margins=True).sort_values("All", ascending=False)
s.to_csv(out / "r3_primary_theme_by_stage.csv")
print(s, "\n")

# 4. What do reviewers who say they are leaving complain about?
ch = df[df.churn_signal == "yes"].assign(theme_list=lambda d: d.themes.str.split("|")).explode("theme_list")
c = ch.theme_list.value_counts().rename("churn_reviews_mentioning").to_frame()
c["pct"] = (100 * c.churn_reviews_mentioning / df[df.churn_signal == "yes"].shape[0]).round(1)
c.to_csv(out / "r4_churn_signal_themes.csv")
print("churn-signal reviews:", (df.churn_signal == "yes").sum()); print(c, "\n")

# 5. First-order reviews
fo = df[df.first_order == "yes"]
print("first-order reviews:", len(fo), "avg stars", round(fo.score.mean(), 2), "| negative share",
      round((fo.sentiment == "negative").mean() * 100, 1))
print(fo.assign(theme_list=fo.themes.str.split("|")).explode("theme_list").theme_list.value_counts().head(8), "\n")
fo.to_csv(out / "r5_first_order_reviews.csv", index=False)

# 6. What delights: themes in positive reviews
pos = df[df.sentiment == "positive"].assign(theme_list=lambda d: d.themes.str.split("|")).explode("theme_list")
pv = pos.theme_list.value_counts().rename("positive_reviews").to_frame()
pv["pct"] = (100 * pv.positive_reviews / (df.sentiment == "positive").sum()).round(1)
pv.to_csv(out / "r6_positive_themes.csv")
print("positive reviews:", (df.sentiment == "positive").sum()); print(pv.head(8))

# 7. Among negative reviews that describe an operational failure, does a support complaint go with leaving?
OPS = {"order_failure", "delivery_speed", "payment_refund", "quality_freshness"}
ts = df.themes.str.split("|").apply(set)
fail = df[ts.apply(lambda s: bool(s & OPS)) & df.sentiment.isin(["negative", "mixed"])].copy()
fail["mentions_support"] = fail.themes.str.contains("support")
r7 = fail.groupby("mentions_support").agg(reviews=("reviewId", "size"),
                                         churn_signal=("churn_signal", lambda s: int((s == "yes").sum())))
r7["pct_churn_signal"] = (100 * r7.churn_signal / r7.reviews).round(1)
r7.to_csv(out / "r7_support_vs_churn.csv")
print(r7)
