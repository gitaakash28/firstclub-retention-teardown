"""Pull public Google Play reviews for the FirstClub app (com.firstclub.app)."""
import sys
import pandas as pd
from google_play_scraper import app, reviews, Sort

APP_ID = "com.firstclub.app"
OUT = sys.argv[1] if len(sys.argv) > 1 else "data/firstclub_play_reviews.csv"

meta = app(APP_ID, lang="en", country="in")
print(f"{meta['title']} | rating {meta['score']:.2f} | ratings {meta['ratings']} | reviews {meta['reviews']} | installs {meta['installs']} | released {meta.get('released')}")

rows, token = [], None
while True:
    batch, token = reviews(APP_ID, lang="en", country="in", sort=Sort.NEWEST, count=200, continuation_token=token)
    rows.extend(batch)
    if not token or not batch:
        break

df = pd.DataFrame(rows)[["reviewId", "at", "score", "content", "thumbsUpCount", "appVersion"]  # reply text dropped: it holds support contacts]
df = df.drop_duplicates("reviewId")
df.to_csv(OUT, index=False)
print(f"saved {len(df)} reviews to {OUT}; date range {df['at'].min()} -> {df['at'].max()}")
print(df["score"].value_counts().sort_index().to_string())
print("with text >= 20 chars:", (df["content"].fillna("").str.len() >= 20).sum())
