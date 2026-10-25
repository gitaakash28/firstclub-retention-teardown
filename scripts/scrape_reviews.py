"""Pull public Google Play reviews for the FirstClub app (com.firstclub.app) and merge them into a CSV.

Reply text is dropped because it holds support contact details. New reviews are merged into the existing
file, so a partial or blocked fetch (Google sometimes throttles cloud runners) never loses data.
"""
import pathlib
import sys
import time
import pandas as pd
from google_play_scraper import app, reviews, Sort

APP_ID = "com.firstclub.app"
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "data/firstclub_play_reviews.csv")
COLS = ["reviewId", "at", "score", "content", "thumbsUpCount", "appVersion"]


def fetch_all():
    rows, token = [], None
    while True:
        for attempt in range(3):
            try:
                batch, token = reviews(APP_ID, lang="en", country="in", sort=Sort.NEWEST, count=200, continuation_token=token)
                break
            except Exception as e:  # network hiccup or throttling: back off and retry
                print(f"fetch attempt {attempt + 1} failed: {e}", file=sys.stderr)
                time.sleep(5 * (attempt + 1))
        else:
            break
        rows.extend(batch)
        if not token or not batch:
            break
    return rows


try:
    meta = app(APP_ID, lang="en", country="in")
    print(f"{meta['title']} | rating {meta['score']:.2f} | ratings {meta['ratings']} | reviews {meta['reviews']} | installs {meta['installs']}")
except Exception as e:
    print(f"app metadata unavailable: {e}", file=sys.stderr)

rows = fetch_all()
fresh = pd.DataFrame(rows, columns=None)
if fresh.empty or "reviewId" not in fresh:
    print("No reviews fetched (likely throttled); keeping the existing file unchanged.")
    sys.exit(0)
fresh = fresh[COLS]

old = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame(columns=COLS)
merged = pd.concat([old, fresh.astype({"at": str})]).drop_duplicates("reviewId", keep="last")
merged = merged.sort_values("at", ascending=False)
OUT.parent.mkdir(parents=True, exist_ok=True)
merged.to_csv(OUT, index=False)
print(f"fetched {len(fresh)}, {len(merged) - len(old)} new; saved {len(merged)} reviews to {OUT}; latest {merged['at'].max()}")
