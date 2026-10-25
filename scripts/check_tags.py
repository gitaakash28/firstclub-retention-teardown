"""Sanity-check that LLM tags line up with review text: keyword hits should usually carry the matching theme."""
import glob
import re
import pandas as pd

CHECKS = {
    "serviceability": r"servic(?:e|ea)ble|pincode|pin code|not available in|not deliver(?:ing)? (?:to|in) my",
    "app_bugs": r"\botp\b|login|log in|crash|blank screen",
    "fees_minimums": r"handling (?:fee|charge)|delivery (?:fee|charge)|free delivery",
    "quality_freshness": r"fresh|rotten|mould|mold|fungus|spoil|expired",
}

pooled = {k: [0, 0] for k in CHECKS}
for f in sorted(glob.glob("reviews/tags_batch_*.csv")):
    n = re.search(r"(\d)", f).group(1)
    t = pd.read_csv(f)
    b = pd.read_csv(f"data/batches/batch_{n}.txt", sep="\t", header=None, quoting=3,
                    names=["reviewId", "score", "date", "content"])
    m = b.merge(t, on="reviewId", how="left")
    out = [f"batch {n}: rows {len(t)}/{len(b)} missing {m['themes'].isna().sum()}"]
    for theme, pat in CHECKS.items():
        hit = m[m.content.str.lower().str.contains(pat, regex=True, na=False)]
        agree = hit.themes.fillna("").str.contains(theme).mean() if len(hit) else float("nan")
        pooled[theme][0] += int(hit.themes.fillna("").str.contains(theme).sum()); pooled[theme][1] += len(hit)
        out.append(f"{theme} {agree:.0%} of {len(hit)}")
    print(" | ".join(out))

print("pooled agreement (themes only; stage, sentiment and churn tags were checked by reading churn-signal reviews):")
for theme, (ok, n) in pooled.items():
    print(f"  {theme}: {ok}/{n} = {ok / n:.0%}")
