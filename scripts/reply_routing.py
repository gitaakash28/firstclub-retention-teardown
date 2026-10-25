"""How does FirstClub route complaints today? Counts where its developer replies to 1-2 star reviews send people.

Reply text holds support contact details, so it's fetched fresh and never written to disk; only counts are saved.
"""
import pathlib
import pandas as pd
from google_play_scraper import reviews, Sort

ROOT = pathlib.Path(__file__).resolve().parent.parent
rows, token = [], None
while True:
    batch, token = reviews("com.firstclub.app", lang="en", country="in", sort=Sort.NEWEST, count=200, continuation_token=token)
    rows.extend(batch)
    if not token or not batch:
        break
d = pd.DataFrame(rows)
neg = d[(d.score <= 2) & d.replyContent.notna() & (d["at"] >= "2026-08-01") & (d["at"] < "2026-10-25")]
text = neg.replyContent.str.lower()
routes = {
    "email ('write to us at ...')": r"e-?mail|@|write to us|drop us",
    "call": r"\bcall",
    "chat": r"\bchat",
    "self-serve / in-app credit or refund": r"in[- ]app (refund|credit)|instant (refund|credit)|self[- ]serve|tap .{0,20}(refund|report)",
}
out = pd.DataFrame([{"route": k, "replies": int(text.str.contains(p, regex=True).sum()),
                     "pct": round(100 * text.str.contains(p, regex=True).mean(), 1)} for k, p in routes.items()])
out.loc[len(out)] = {"route": "total 1-2 star reviews with a reply, Aug 1 - Oct 24 2026", "replies": len(neg), "pct": 100.0}
out.to_csv(ROOT / "results" / "r8_reply_routing.csv", index=False)
print(out.to_string(index=False))
