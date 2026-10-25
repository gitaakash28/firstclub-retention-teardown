# Review tagging prompt (lifecycle stage × theme)

Extends the [Weekly Pulse AI Agent](https://github.com/gitaakash28/pm-ai-agent): instead of clustering themes, each review is tagged against a fixed retention taxonomy so the counts can be compared across lifecycle stages and months.

Input: one review per line, `reviewId<TAB>stars<TAB>date<TAB>text`. Reviews may be in English, Hindi, Hinglish or Kannada/Telugu transliteration.

Output: one CSV row per review, `reviewId,stage,themes,sentiment,churn_signal,first_order`.

## Fields

**stage** (pick exactly one; the customer's lifecycle moment the review describes)
- `pre_order`: hasn't ordered yet. Install, signup, OTP or login, serviceability check, browsing.
- `first_order`: describes their first order or first few days ("first order", "tried for the first time", "new user").
- `repeat`: an ongoing customer (multiple orders, subscription, "every time", "since months", "regular", "again").
- `unclear`: can't tell.

**themes** (1–3, pipe-separated, most important first)
- `quality_freshness`: product quality, freshness, spoilage, taste, expiry (positive or negative)
- `price_value`: product prices vs market or other apps, value for money
- `fees_minimums`: delivery fee, handling fee, free-delivery threshold, membership charges
- `delivery_speed`: late delivery, ETA accuracy, slots
- `order_failure`: not delivered, marked delivered but not received, missing, wrong or damaged items, cancellations
- `payment_refund`: payment failed or deducted, refunds, wallet, meal cards, COD
- `serviceability`: area or pincode not serviced, discovered late
- `app_bugs`: crashes, lag, blank screen, OTP or login, search, scrolling, UI friction
- `ads_comms`: ads, notifications, misleading marketing
- `support`: customer care responsiveness and resolution
- `assortment_stock`: availability, out of stock, range
- `packaging_sustainability`: packaging, plastic, bags, cold chain
- `subscription_daily`: milk or daily subscription and early-morning delivery
- `trust_brand`: explicit trust, honesty, "curated", "clean", brand promise
- `general_praise`: generic positive with no specific driver ("nice app", "good")
- `other`

**sentiment**: `positive` | `negative` | `mixed` (judge from the text; stars are a hint, not the answer)

**churn_signal**: `yes` if the reviewer says they uninstalled, stopped ordering, switched, or will leave or not order again; else `no`

**first_order**: `yes` if the review explicitly refers to the first order or first experience; else `no`

## Rules
- Tag what the text says, not what you infer about FirstClub.
- Use only the labels above.
- Don't skip rows. Every input reviewId gets exactly one output row.
