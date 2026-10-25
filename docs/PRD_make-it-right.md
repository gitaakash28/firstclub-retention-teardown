# PRD: Make it right in one tap

**Author:** Aakash Mishra · **Status:** Proposal (outside-in, built on public data) · **Project area:** Customer retention · **Date:** October 2026

## Problem (in 3 sentences)
FirstClub wins customers on quality: freshness comes up in 66% of its 1,149 positive Play Store reviews. When an order goes wrong (a missing milk packet, a stale loaf, a late slot), fixing it means a support chat, and a failure review that also complains about support signals the customer is leaving 3.4x as often as one that doesn't (24.2% vs 7.2%). As FirstClub scaled, the average rating of new written reviews fell from 4.37 (Jan–May 2026) to 3.92 (Jun–Oct 2026), so the cost of a slow fix is growing.

## Evidence
| Signal | Source | Number |
|---|---|---|
| Average rating of new written reviews, Jan–May 2026 → Jun–Oct 2026 (overall store rating is still 4.7 across 10,862 ratings) | 2,210 Play Store reviews (`results/r1b_rating_by_period.csv`) | 4.37 → 3.92 |
| Share of new reviews rated 1–2★, same periods | same | 13.8% → 24.9% |
| Failure reviews (order, delivery, payment, quality) that signal churn, **with** a support complaint | 62 reviews (`results/r7_support_vs_churn.csv`) | 24.2% (15) |
| Same, **without** a support complaint | 167 reviews | 7.2% (12) |
| Customers who say they're leaving and also complain about support; of those, how many also describe a failure | 54 churn-signal reviews | 19 (35%); 18 of the 19 |
| Positive reviews that mention quality or freshness | 1,149 positive reviews (`results/r6_positive_themes.csv`) | 66% |
| Negative reviews from people who never ordered (serviceability, OTP or login) | 463 negative reviews (`results/r3_primary_theme_by_stage.csv`) | 30% (139) |
| FirstClub replies to 1–2★ reviews that send the customer to email (Aug–Oct 2026); replies mentioning a self-serve credit | 223 replies (`results/r8_reply_routing.csv`) | 72% (161); 0 |

**In customers' own words:**
- "First two orders were smooth and quality excellent… From the third one, it has been an ordeal… items missing." (1★, May 2026)
- "If a packet of milk is not delivered and we try to raise it over chat, your team keeps us engaged for 30 minutes or more." (1★, Jun 2026)
- "Good experience on my first delivery… I have seen many cases where things start going wrong after the first couple of deliveries. Only time will tell." (5★, May 2026)

**Supporting evidence from public grocery data (Instacart, 3.4M orders from 206K customers, `sql/`):**
- **Early orders are the fragile ones.** The order history ends after order 4 for 11.6% of customers, vs 5.9% after order 20 (`08_order_to_order`). Only 53.7% of customers with 4 orders have 10 or more observed orders (`01_survival`).
- **Fresh-heavy first baskets go with longer lives.** 29.6% of customers whose first 3 baskets are 75%+ produce, dairy and bakery have 20+ observed orders, vs 20.6% of those under 25% fresh (`04_fresh_share`). Fresh quality in early orders is the experience to protect.
- **Slowdowns are detectable.** 46.2% of customers stretch to at least 2× their usual gap at some point, and only 47.3% return to their rhythm on the next order (`05_slowdown_recovery`). This is the trigger for the cadence nudge below.
- All of this is correlational and comes from a US dataset limited to customers with 4–100 orders, with no churn label: a history that ends may be a newer customer, not a lost one. I use it for direction, not as a FirstClub benchmark.

**Takeaway:** quality earns the first order. Failures happen at any scale, and what separates the customers who leave is a slow, painful fix. That matters most in the first few orders, before a habit has formed. Caveat: these are review counts, not cohorts. The A/B test below is how to find out whether the link is causal.

## Goal and metric
- **Primary metric:** among customers who report an issue in their first 5 orders, the share who place another order within 14 days of reporting it.
- **Secondary:** median time from report to resolution, post-resolution CSAT, the rating of reviews that mention support.
- **Guardrails:** refund and credit cost as a percentage of GMV, claims per 100 orders, the share of credits going to customers with 3+ claims (abuse), and support contact rate (it must not rise).

## Users and moment
New customers in their first 5 orders (habit not yet formed) who hit a missing, wrong or poor-quality item, or a delivery that's late against its promised ETA.

## Solution
1. **"Something not right?" on the order card** for 48 hours after delivery. The customer picks the items and a reason (missing, damaged, quality, expired) and gets an **instant wallet credit**, with no chat and no photo for fresh items under a value cap. They can also add a free replacement to their next order.
2. **Proactive late-delivery credit.** If delivery misses the promised ETA by more than 15 minutes, a small credit and an apology land automatically. The customer doesn't have to ask.
3. **Closing the loop.** Every claim is tagged by SKU, batch and dark store and feeds the quality team's daily view. A credit is also a supply-chain signal.

**Prototype:** [clickable concept](https://gitaakash28.github.io/firstclub-retention-teardown/prototype/) covering the normal claim, a claim over the cap, a repeat claimer and the automatic late credit.

**Abuse controls:** value cap per order, cap on claims per customer per 30 days, and photo required above the cap or after N claims. Fraud thresholds are set with Ops.

## Out of scope (v1)
- Repeat customers beyond order 5 (phase 2, if the test wins).
- Changes to the support chatbot.
- Subscription (milk) delivery-window issues: separate problem, separate spec.

## Experiment design
- **Hypothesis:** resolving early-order issues in one tap, instead of through chat, raises the 14-day repeat rate of affected customers.
- **Unit:** customer, randomized 50/50 the first time they hit an issue in orders 1–5. Randomizing by customer rather than by order prevents contamination.
- **Control:** current support-chat flow. **Treatment:** one-tap credit plus proactive late credit.
- **Sample size** (`scripts/sample_size.py`, two-sided α = 0.05, power 0.8): if the baseline 14-day repeat rate is 40%, detecting +8 pp needs **604 customers per arm (1,208 total)**; +5 pp needs 1,534 per arm. The baseline is an assumption until a week-1 SQL pull confirms it.
- **Duration:** the time to collect about 1,200 affected customers, with a minimum of 2 full weeks to cover weekly ordering cycles. Look at the result only at the planned end, not daily.
- **Decision rule:** ship if the primary metric improves significantly and no guardrail worsens beyond its threshold (e.g. credit cost stays under an agreed percentage of affected-customer GMV). If the lift is positive but not significant, extend once. If it's flat, keep only the proactive late credit and kill the rest.

## Prioritization (RICE, outside-in estimates)
Reach is on a relative 1–10 scale because I don't have FirstClub's volumes. Impact uses the standard 0.25–3 scale, and effort is engineering weeks.

| Idea | Reach | Impact | Confidence | Effort | RICE | Why |
|---|---|---|---|---|---|---|
| Location-first onboarding (check serviceability before login) | 8 | 1 | 90% | 1 | **7.2** | 30% of negative reviews; cheap; ship without a test and track the install → signup funnel |
| One-tap make-it-right (this PRD) | 6 | 2 | 70% | 3 | **2.8** | Targets the moment reviewers say they leave |
| Restock nudge timed to each customer's cadence | 7 | 1 | 50% | 2 | **1.8** | Habit builder; depends on the Instacart cadence findings |

RICE puts location-first onboarding first, so ship it now as the quick win. It fixes signups, though, not retention. One-tap make-it-right is the **retention** bet, which is why it gets the A/B test.

## Open questions for the team
1. What's the real 14-day repeat rate after an early-order issue, and does it depend on fix time? ([`day1_sql/03`](../day1_sql/03_repeat_after_issue_by_resolution.sql), which is ready to run.)
2. What's today's median time to resolve a missing-item complaint? ([`day1_sql/05`](../day1_sql/05_resolution_time_by_channel.sql))
3. What credit cap per order keeps the unit economics healthy for each category?
4. Confirm in the current app that there's no self-serve credit path. FirstClub's own replies point to email (72%) and none mention one, but I haven't used the app. Location-after-signup complaints continue through September 2026.
