# PRD: Make it right in one tap

**Protecting a customer's first five orders: prevent the bad ones, fix the rest in one tap**

**Author:** Aakash Mishra · **Status:** Proposal (outside-in, built on public data and an app walkthrough) · **Project area:** Customer retention · **Date:** October 2026

## Problem (in 3 sentences)
FirstClub wins customers on quality: freshness comes up in 66% of its 1,149 positive Play Store reviews. When an order goes wrong (a missing milk packet, a stale loaf, a late slot), fixing it means a support conversation, and a failure review that also complains about support signals the customer is leaving 3.4x as often as one that doesn't (24.2% vs 7.2%). As FirstClub scaled, the average rating of new written reviews fell from 4.37 (Jan–May 2026) to 3.92 (Jun–Oct 2026), so every slow fix costs more.

## Evidence
| Signal | Source | Number |
|---|---|---|
| Average rating of new written reviews, Jan–May → Jun–Oct 2026 (the overall store rating is still 4.7 across 10,862 ratings) | 2,210 Play Store reviews (`results/r1b_rating_by_period.csv`) | 4.37 → 3.92 |
| Share of new reviews rated 1–2★, same periods | same | 13.8% → 24.9% |
| Failure reviews (order, delivery, payment, quality) that signal churn, **with** a support complaint | 62 reviews (`results/r7_support_vs_churn.csv`) | 24.2% (15) |
| Same, **without** a support complaint | 167 reviews | 7.2% (12) |
| First-order reviews that mention quality or freshness | 76 first-order reviews (`results/r5_first_order_reviews.csv`) | 33 |
| Positive reviews that mention quality or freshness | 1,149 positive reviews (`results/r6_positive_themes.csv`) | 66% |
| FirstClub replies to 1–2★ reviews sending the customer to email (Aug–Oct 2026); replies mentioning a self-serve credit | 223 replies (`results/r8_reply_routing.csv`) | 72% (161); 0 |
| "Not serviceable" complaints from people who never ordered: from cities FirstClub doesn't serve; explicitly found out only after entering details | 81 reviews (`results/r9_serviceability_split.csv`) | 25; 24 |
| Support–churn link **within the same failure type** (Mantel-Haenszel odds ratio, stratified) | 136 failure reviews (`results/r10_support_churn_by_failure.csv`) | 4.1; late delivery 38.9% vs 5.6%, missing order 30.4% vs 11.5%, bad quality 10.0% vs 7.2% |
| Rise in 1–2★ share of text reviews, Jan–May → Jun–Oct 2026, by stage | 1,529 text reviews (`results/r11_low_star_rise_by_stage.csv`) | 16.0% → 29.0%: customers who ordered +6.5 pts, never ordered +4.2, unclear +2.3 |
| App walkthrough, 26 Oct 2026 ([screenshots](https://gitaakash28.github.io/firstclub-retention-teardown/prototype/)) | Fresh Android install, no past orders | Help = FAQs plus an AI assistant; "I want a refund" gets a clarifying question. Signup asks for phone, age and food preferences (each skippable) before showing whether they deliver. |

**In customers' own words:**
- "First two orders were smooth and quality excellent… From the third one, it has been an ordeal… items missing." (1★, May 2026)
- "If a packet of milk is not delivered and we try to raise it over chat, your team keeps us engaged for 30 minutes or more." (1★, Jun 2026)
- "Good experience on my first delivery… I have seen many cases where things start going wrong after the first couple of deliveries. Only time will tell." (5★, May 2026)

**Supporting evidence from public grocery data (Instacart, US, 3.4M orders, `sql/`):** early orders show about twice the drop-off of later ones (the history ends at order 4 for 11.6% of customers vs 5.9% at order 20), and fresh-heavy first baskets go with longer histories (29.6% vs 20.6% reach 20+ orders). This is correlational, with no churn label, so I use it for direction only.

**Takeaway:** quality earns the first order; a slow, effortful fix loses the customer, and the first few orders are where that matters most. These are review counts, not cohorts, which is why the bet ends in an A/B test.

**What the stress test changed:**
- The support–churn link survives stratifying by failure type (odds ratio 4.1), so severity across failure types doesn't explain it away.
- It's strongest for **late and missing orders** (7 of 18 vs 2 of 36, and 7 of 23 vs 3 of 26). For **bad quality** the gap is small and rests on very few churn signals (2 of 20 vs 5 of 69), so it only suggests a direction. The design splits accordingly:
  - **recovery** (fast, one-tap fixes) for late and missing orders;
  - **prevention** (the quality lane) for quality, where a fast refund doesn't buy back trust.

## Where this sits: the retention map
| Stage | What the evidence says | Lever | Owner / next step |
|---|---|---|---|
| **Find the right customers** | 25 serviceability complaints from cities FirstClub doesn't serve; never-ordered complaints added 4.2 pts to the 1–2★ share | Say where you deliver (C) | Marketing and the store listing; no test needed |
| **First five orders** | About half the rise in 1–2★ reviews (+6.5 of 13 pts from customers who ordered); quality in 33 of 76 first-order reviews; support–churn odds ratio 4.1 | **Prevent (A) + recover (B): this PRD** | Product, ops and support |
| **Habit** | Subscriptions: 22 reviews averaging 2.91★, split 10 positive and 10 negative (pause and resume broken, delivery timing, and one report of a 25% overnight price rise), though these halved per review from Jan–Jun to Jul–Oct, so some may already be fixed. Fees and free-delivery minimums: 21 reviews averaging 2.00★, about twice as common per review since July 2026 (0.78 → 1.57 per 100; `results/r12_habit_signals.csv`) | Fix subscription reliability; test whether the free-delivery minimum pushes small top-ups elsewhere | Confirm which subscription bugs remain, then hand them to engineering. Fees: `day1_sql/09` and `10` first |
| **Win back** | 46% of customers slow down at least once (Instacart, directional) | Overdue-customer watchlist and nudges | `day1_sql/06`; later |

**Why the first five orders come first:**
- **Reach:** every new customer passes through them, and customers who ordered account for about half the rise in 1–2★ reviews.
- **Leverage:** before a habit forms, one bad experience is the whole relationship.
- **Easier wins elsewhere:** the subscription problems are mostly **bugs** (pause and resume, delivery windows), so they're tickets for engineering, not a product bet.
- **Unproven:** the fee hypothesis rests on 21 reviews and needs data (`day1_sql/10`) before anyone touches pricing.

## Design principles
1. **Prevent before you compensate.** The best fix is the bad item that never ships.
2. **Never hold a refund hostage.** For a trust brand, the customer chooses where the money goes, and credits never expire. Two reviewers say they'll leave once their wallet balance runs out, and one calls wallet expiry a "market strategy to make people use more often".
3. **Trust the customer, verify with your own data.** Approve instantly when pick, pack or delivery data agrees with the claim; ask for a photo only when it doesn't.
4. **Give the existing AI a button.** FirstClub already runs an AI assistant. A structured entry point beats a blank chat box.

## Solution
**A. Prevent: a first-orders quality lane** (ops change, in every dark store)
- Orders 1–3 for a customer are flagged to the packer: best-in-crate produce, and dairy and bakery must meet a **minimum remaining shelf life** (e.g. 3+ days on milk and bread).
- The minimum shelf life is shown on product pages ("At least 3 days to best-before, guaranteed") to make the quality promise visible.

**B. Recover: "Something not right?" on the order card** (product change)
1. For 48 hours after delivery on a customer's first 5 orders, the order card shows **Something not right?** The customer picks the items and a reason (missing, damaged, poor quality, expired).
2. **Instant approval when FirstClub's own data agrees.** If the item was short-picked or substituted, approve immediately. Otherwise the customer adds one photo, which takes seconds, and approval is still immediate under the value cap.
3. **The customer chooses the remedy:**
   - **refund to the original payment method**, labelled honestly as 2–3 days;
   - **instant credit that never expires**;
   - **free replacement** in the next order.
4. **Late delivery:** if delivery misses the promised ETA by 15+ minutes, that order's **delivery and handling fee is refunded automatically**. The cost is bounded and it speaks directly to the fee complaints.
5. **Repeat claimers (4th in 30 days)** go to the existing **AI assistant with the order and items already attached**, and a person calls back. The customer never re-explains, and the copy never tells them they've been flagged.
6. **Close the loop.** Every claim is logged by SKU, batch and dark store for the quality team, and the customer later hears what changed ("We pulled that batch of bread from your store").

**C. Say where you deliver, early** (communications, plus a small onboarding change)
- The Play Store listing and ads name the cities served, and a **city waitlist** captures demand elsewhere (25 of the 81 serviceability complaints came from cities FirstClub doesn't serve).
- In-city: check the pincode **before** asking for a phone number, with "notify me" for unserved pincodes.

**Prototype:** [clickable concept](https://gitaakash28.github.io/firstclub-retention-teardown/prototype/), built next to screenshots of today's app.

## Goal and metrics
- **Primary (intent to treat):** **early-habit rate**, the share of *all* new customers with 3+ delivered orders within 30 days of their first.
- **Pre-registered triggered readout:** among customers whose orders 1–5 include an **ops-detected** failure (late by 15+ minutes against the promised ETA, or a short-picked item), the share who reorder within 14 days. These triggers fire the same way in both arms, so the groups are comparable. Bad produce can't be detected this way, so its effect shows up only in the primary metric.
- **Secondary:** time from report to resolution, post-fix rating, support contact rate.
- **Guardrails:**
  - credit and refund cost as a percentage of GMV;
  - claims per 100 orders;
  - share of claims from accounts under 7 days old, since the ₹100 welcome offer plus easy credits is an abuse risk;
  - **promised ETAs must not creep up**, so the late-fee refund doesn't lead ops to pad estimates;
  - support contact rate must not rise.

## Experiment design
- **Why customers are randomized at their first order:** the button itself changes who reports issues. Randomizing only customers who report would compare different kinds of people across the two arms.
- **Unit:** each new customer, 50/50 at their first order. **Control:** today's help flow. **Treatment:** B (one-tap recovery and the late-fee refund).
- **Sample size** (`scripts/sample_size.py` → `results/e2_sample_size_itt.csv`; 40% baseline assumed, α = 0.05, power 0.8): if 15–25% of new customers hit an issue in their first 5 orders and recovery lifts them by 8–10 points, the overall lift is 1.2–2.5 points. That needs **6,086–26,289 new customers per arm**. The triggered readout needs far fewer (about 600 per arm for +8 points), so it reads earlier but can't settle the question alone.
- **Duration:** until the sample is reached, and at least 4 full weeks, since the metric has a 30-day window. Look only at the planned end.
- **A (prevention) is tested separately, by dark store:** it's an ops process, so roll it out store by store (a staggered rollout) and compare complaint rates on orders 1–3 before and after, against stores not yet switched.
- **Decision rule:**
  - **Ship** if the primary metric improves significantly and no guardrail breaches its threshold.
  - **Triggered readout up but primary flat:** the effect is real but too small to show across all new customers. Keep the late-fee refund and the assistant hand-off, and look at cost.
  - **Both flat:** kill the credits, but keep the one-tap entry as a better route into support.

## Prioritization (RICE, outside-in estimates)
Reach is relative (1–10) because FirstClub's volumes aren't public. Impact uses the standard 0.25–3 scale, and effort is in weeks.

| Idea | Reach | Impact | Confidence | Effort | RICE | Why |
|---|---|---|---|---|---|---|
| A. First-orders quality lane | 7 | 2 | 60% | 2 | **4.2** | Every new customer's first 3 orders; prevents the most common first-order complaint (quality in 33 of 76 first-order reviews) |
| C. Say where you deliver, early | 5 | 1 | 80% | 1 | **4.0** | Cheap; 25 complaints from other cities, 24 from finding out late. The skippable signup screens already soften it |
| B. One-tap make-it-right | 6 | 2 | 70% | 3 | **2.8** | Targets the moment reviewers say they leave; needs the A/B test |

**Call:** ship A and C now (an ops process and a communications change, each measured by its own simple before-and-after), and A/B test B, the product bet.

## Edge cases
| Case | Handling |
|---|---|
| Discounted order (e.g. WELCOME100) | Refund what the customer paid for the item: its price minus a pro-rated share of the discount, never the full MRP. |
| Cash on delivery (if offered; two reviews say it isn't) | No source to refund to, so offer the never-expiring credit or a replacement, or a UPI refund once the customer adds an ID. |
| Item already refunded at packing (short-pick auto-refund) | Hide it from the picker so it can't be claimed twice. |
| Several claims on one order | Allowed until the 48-hour window closes; each item can be claimed once. |
| Café and freshly prepared items | Same flow; "poor quality" needs a photo, because preparation varies. |
| Subscription deliveries | Out of scope for v1. Handled by the subscription reliability fixes in the retention map. |
| Late refund when delivery was already free | Refund the handling fee only. |
| Customer offline when the order lands | The button stays available for 48 hours from delivery, not from app open. |

## Tracking plan
| Event | Key properties | Used for |
|---|---|---|
| `order_issue_entry_viewed` | order_id, order_n, hours_since_delivery | Discoverability (seen → tapped) |
| `order_issue_started` | order_id, entry_point (order card / help / assistant) | Funnel start |
| `order_issue_items_selected` | item_ids, reasons, claim_value | Mix of reasons; value distribution |
| `order_issue_verified` | method (pack_data / photo / manual), approved | Share auto-approved by data, fraud checks |
| `order_issue_remedy_chosen` | remedy (refund / credit / replacement), amount | Remedy preference; cost |
| `order_issue_escalated` | reason (repeat_claimer / over_cap), assistant_session_id | Load on support |
| `late_fee_refunded` | order_id, minutes_late, amount | Late-refund cost; ETA-creep guardrail |
| `quality_lane_flagged` (ops) | order_id, store_id, checks_passed | Prevention coverage per store |

Experiment assignment is logged once per customer at their first order (`experiment_assignments`), and every metric query joins on it.

## Rollout
1. **Week 0:** run the day-1 SQL for baselines (issue rate on orders 1–5, fix time, triggered-group size) and confirm the sample size.
2. **Weeks 1–2:** start the quality lane in 2–3 dark stores, as a staggered rollout. Ship "say where you deliver".
3. **Weeks 2–3:** build B behind a feature flag, and run an internal dogfood pass with ops verifying pack-data matches.
4. **Weeks 4–8+:** run the A/B test at 50/50 for new customers, until the planned sample is reached and at least 4 weeks have passed.
5. **Readout:** primary, triggered and guardrails, then a ship / iterate / kill call using the decision rule above.

## Out of scope (v1)
- Customers beyond order 5 (phase 2 if the test wins).
- Rebuilding the AI assistant; this only gives it a structured entry point.
- Milk subscription delivery windows: a separate problem and a separate spec.

## Open questions for the team
1. What's the real 14-day reorder rate after an early-order issue, and does fix time change it? ([`day1_sql/03`](../day1_sql/03_repeat_after_issue_by_resolution.sql))
2. How long does a fix take today, by channel? ([`day1_sql/05`](../day1_sql/05_resolution_time_by_channel.sql))
3. What share of new customers hit an issue in their first 5 orders? This sets the A/B sample size. ([`day1_sql/04`](../day1_sql/04_issue_rate_by_order_number.sql))
4. Does pack data reliably flag short-picks and substitutions? Instant approval depends on it.
5. Does a delivered order already have a report-an-issue path? My walkthrough had no past orders, so I couldn't test it.
