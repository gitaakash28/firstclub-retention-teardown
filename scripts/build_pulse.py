"""Weekly FirstClub review pulse: data/live/reviews.csv (+ reviews/live_tags.csv) -> pulse/index.html.

Separate from the case study, which is a frozen snapshot of reviews through 24 Oct 2026.
"""
import json
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
r = pd.read_csv(ROOT / "data" / "live" / "reviews.csv", parse_dates=["at"])
tags_path = ROOT / "reviews" / "live_tags.csv"
tags = pd.read_csv(tags_path) if tags_path.exists() else pd.DataFrame(columns=["reviewId", "themes", "sentiment", "churn_signal"])
as_of = r["at"].max().normalize()

# Weekly rating trend, last 16 complete-or-current weeks (weeks start Monday)
r["week"] = r["at"].dt.to_period("W-SUN").dt.start_time
weeks = (r[r["week"] >= as_of - pd.Timedelta(weeks=16)]
         .groupby("week").agg(reviews=("score", "size"), avg_rating=("score", "mean"),
                              pct_1_2_star=("score", lambda s: 100 * (s <= 2).mean())).round(2).reset_index())
weeks["week"] = weeks["week"].dt.strftime("%Y-%m-%d")


def window(days_from, days_to):
    return r[(r["at"] > as_of - pd.Timedelta(days=days_from)) & (r["at"] <= as_of - pd.Timedelta(days=days_to))]


last, prev = window(28, -1), window(56, 28)
kpi = {"as_of": as_of.strftime("%d %b %Y"), "total": int(len(r)),
       "last_n": int(len(last)), "last_avg": round(float(last.score.mean()), 2) if len(last) else None,
       "prev_avg": round(float(prev.score.mean()), 2) if len(prev) else None,
       "last_low": round(float(100 * (last.score <= 2).mean()), 1) if len(last) else None,
       "prev_low": round(float(100 * (prev.score <= 2).mean()), 1) if len(prev) else None,
       "tagged": int(r.reviewId.isin(tags.reviewId).sum())}

# Complaint themes in negative reviews: last 28 days vs previous 28 (tagged reviews only)
def themes(df):
    neg = df.merge(tags, on="reviewId")
    neg = neg[neg.sentiment.isin(["negative", "mixed"]) & (neg.score <= 3)]
    ex = neg.assign(theme=neg.themes.str.split("|")).explode("theme")
    return ex.theme.value_counts(), len(neg)


tl, nl = themes(last)
tp, np_ = themes(prev)
theme_rows = [{"theme": t, "last": int(tl.get(t, 0)), "prev": int(tp.get(t, 0)),
               "last_pct": round(100 * tl.get(t, 0) / nl, 1) if nl else 0, "prev_pct": round(100 * tp.get(t, 0) / np_, 1) if np_ else 0}
              for t in tl.index if t not in ("other", "general_praise")][:8]

# No verbatim quotes on the live page: an unattended job can't screen them for staff names or accusations.
data = {"kpi": kpi, "weeks": weeks.to_dict("records"), "themes": theme_rows, "neg_last": nl, "neg_prev": np_}
html = (ROOT / "site" / "pulse_template.html").read_text().replace("/*DATA*/null", json.dumps(data))
(ROOT / "pulse" / "index.html").write_text(html)
print("pulse built as of", kpi["as_of"], {k: v for k, v in kpi.items() if k != "as_of"})
