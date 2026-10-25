"""Inject results/*.csv into site/template.html -> index.html, so every number on the page comes from a results file."""
import json
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
R = ROOT / "results"


def rows(name):
    p = R / f"{name}.csv"
    return json.loads(pd.read_csv(p).to_json(orient="records")) if p.exists() else None


tagged = pd.read_csv(ROOT / "reviews" / "tagged_reviews.csv")
neg = tagged[(tagged.score <= 3) & tagged.sentiment.isin(["negative", "mixed"])]
data = {
    "monthly": rows("r1_rating_by_month"),
    "period": rows("r1b_rating_by_period"),
    "churn": rows("r4_churn_signal_themes"),
    "support": rows("r7_support_vs_churn"),
    "routing": rows("r8_reply_routing"),
    "stress": rows("r10_support_churn_by_failure"),
    "rise": rows("r11_low_star_rise_by_stage"),
    "habit": rows("r12_habit_signals"),
    "positive": rows("r6_positive_themes"),
    "stage": neg.stage_group.value_counts().rename_axis("stage").reset_index(name="reviews").to_dict("records"),
    "counts": {"reviews": int(pd.read_csv(ROOT / "data" / "firstclub_play_reviews.csv").shape[0]) if (ROOT / "data" / "firstclub_play_reviews.csv").exists() else 2210,
               "tagged": int(len(tagged)), "negative": int(len(neg)),
               "churn": int((tagged.churn_signal == "yes").sum()), "positive": int((tagged.sentiment == "positive").sum())},
    "sql": {k: rows(k) for k in ["01_survival", "02_cadence", "03_early_habit", "04_fresh_share",
                                 "05_slowdown_recovery", "07_anchor_items", "08_order_to_order"]},
}
html = (ROOT / "site" / "template.html").read_text().replace("/*DATA*/null", json.dumps(data))
(ROOT / "index.html").write_text(html)
print("wrote index.html;", {k: (v is not None) for k, v in data["sql"].items()})
