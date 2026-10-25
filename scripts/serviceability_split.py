"""Of the 'not serviceable' complaints from people who never ordered: which city, and do they say they found out late?

Keyword-based on the review text (city names, pincode prefixes, 'after entering details' language), so treat as approximate.
"""
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
d = pd.read_csv(ROOT / "reviews" / "tagged_reviews.csv")
s = d[(d.stage_group == "never ordered") & (d.primary_theme == "serviceability") & (d.score <= 3) & d.sentiment.isin(["negative", "mixed"])].copy()
t = s.content.fillna("").str.lower()
OTHER = r"mumbai|pune|delhi|noida|gurgaon|gurugram|kolkata|chennai|ahmedabad|kochi|jaipur|lucknow|thane|navi|chandigarh|indore|vizag|coimbatore|mysore|mysuru|kerala|vikhroli|salt lake|surat|nagpur|bhopal|goa"
HOME = r"bangalore|bengaluru|blr|hyderabad|hyd|secunderabad|whitefield|koramangala|hsr|indiranagar|jayanagar|malleswaram|rajajinagar|yelahanka|electronic city|marathahalli|bellandur|sarjapur|gachibowli|kondapur|madhapur|kukatpally|banjara|jubilee|hebbal|jp nagar|btm|kr puram"
home = t.str.contains(HOME) | t.str.contains(r"\b(?:56|50)\d{4}\b")
other = (t.str.contains(OTHER) | t.str.contains(r"\b(?:4\d{5}|1\d{5}|7\d{5}|6[0-4]\d{4}|3[89]\d{4})\b")) & ~home
s["where"] = "city unclear"
s.loc[home, "where"] = "Bengaluru or Hyderabad"
s.loc[other, "where"] = "a city FirstClub doesn't serve"
s["says_found_out_late"] = t.str.contains(r"after|end|login|log in|details|sign|register|otp|number|wast|first ask|before")
out = s.groupby("where").agg(reviews=("reviewId", "size"), say_found_out_late=("says_found_out_late", "sum")).reset_index()
out.loc[len(out)] = {"where": "total", "reviews": len(s), "say_found_out_late": int(s.says_found_out_late.sum())}
out.to_csv(ROOT / "results" / "r9_serviceability_split.csv", index=False)
print(out.to_string(index=False))
