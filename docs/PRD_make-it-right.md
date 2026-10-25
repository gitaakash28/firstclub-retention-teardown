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
| App walkthrough, 26 Oct 2026 ([screenshots](https://gitaakash28.github.io/firstclub-retention-teardown/prototype/)) | Fresh Android install, no past orders | Help = FAQs plus an AI assistant; "I want a refund" gets a clarifying question. Signup asks for phone, age and food preferences (each skippable) before showing whether they deliver. |

**In customers' own words:**
- "First two orders were smooth and quality excellent… From the third one, it has been an ordeal… items missing." (1★, May 2026)
- "If a packet of milk is not delivered and we try to raise it over chat, your team keeps us engaged for 30 minutes or more." (1★, Jun 2026)
- "Good experience on my first delivery… I have seen many cases where things start going wrong after the first couple of deliveries. Only time will tell." (5★, May 2026)

**Supporting evidence from public grocery data (Instacart, US, 3.4M orders, `sql/`):** early orders show about twice the drop-off of later ones (the history ends at order 4 for 11.6% of customers vs 5.9% at order 20), and fresh-heavy first baskets go with longer histories (29.6% vs 20.6% reach 20+ orders). This is correlational, with no churn label, so I use it for direction only.

**Takeaway:** quality earns the first order; a slow, effortful fix loses the customer, and the first few orders are where that matters most. These are review counts, not cohorts, which is why the bet ends in an A/B test.

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
