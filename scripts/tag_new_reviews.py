"""Tag reviews that don't have tags yet, using the taxonomy in reviews/tagging_prompt.md.

Runs in the weekly GitHub Action. Needs GROQ_API_KEY (OpenAI-compatible Groq API); without it, it exits
quietly and the pulse page shows ratings only. Labels are validated; anything off-taxonomy is dropped.
"""
import json
import os
import pathlib
import sys
import urllib.request
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
REVIEWS = ROOT / "data" / "live" / "reviews.csv"
TAGS = ROOT / "reviews" / "live_tags.csv"
MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
STAGES = {"pre_order", "first_order", "repeat", "unclear"}
THEMES = {"quality_freshness", "price_value", "fees_minimums", "delivery_speed", "order_failure", "payment_refund",
          "serviceability", "app_bugs", "ads_comms", "support", "assortment_stock", "packaging_sustainability",
          "subscription_daily", "trust_brand", "general_praise", "other"}
SENTIMENTS = {"positive", "negative", "mixed"}


def call_llm(prompt, batch):
    lines = "\n".join(f"{r.reviewId}\t{r.score}\t{str(r.at)[:10]}\t{r.content}" for r in batch.itertuples())
    body = {
        "model": MODEL, "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": prompt + '\n\nReturn JSON: {"rows": [{"reviewId": ..., "stage": ..., "themes": "a|b", '
                                                   '"sentiment": ..., "churn_signal": "yes|no", "first_order": "yes|no"}]}'},
            {"role": "user", "content": lines},
        ],
    }
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(json.loads(resp.read())["choices"][0]["message"]["content"])["rows"]


def valid(row):
    themes = [t for t in str(row.get("themes", "")).split("|") if t]
    return (row.get("stage") in STAGES and row.get("sentiment") in SENTIMENTS and themes and len(themes) <= 3
            and all(t in THEMES for t in themes) and row.get("churn_signal") in {"yes", "no"} and row.get("first_order") in {"yes", "no"})


def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("GROQ_API_KEY not set; skipping tagging")
        return
    reviews = pd.read_csv(REVIEWS)
    reviews = reviews[reviews.content.fillna("").str.len() >= 20]
    done = set(pd.read_csv(TAGS).reviewId) if TAGS.exists() else set()
    todo = reviews[~reviews.reviewId.isin(done)]
    print(f"{len(todo)} new reviews to tag")
    prompt = (ROOT / "reviews" / "tagging_prompt.md").read_text()
    out = []
    for start in range(0, len(todo), 25):
        batch = todo.iloc[start:start + 25]
        try:
            rows = call_llm(prompt, batch)
        except Exception as e:  # one bad batch shouldn't kill the weekly run
            print(f"batch {start}: {e}", file=sys.stderr)
            continue
        ids = set(batch.reviewId)
        out += [r for r in rows if r.get("reviewId") in ids and valid(r)]
    if out:
        new = pd.DataFrame(out)[["reviewId", "stage", "themes", "sentiment", "churn_signal", "first_order"]]
        new.to_csv(TAGS, mode="a", header=not TAGS.exists(), index=False)
    print(f"tagged {len(out)} of {len(todo)}")


if __name__ == "__main__":
    main()
