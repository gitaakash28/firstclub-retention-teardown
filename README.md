# FirstClub retention teardown

An outside-in look at customer retention for [FirstClub](https://play.google.com/store/apps/details?id=com.firstclub.app), a quality-first quick-commerce grocery app in Bengaluru and Hyderabad. It uses only public data.

**Case study:** https://gitaakash28.github.io/firstclub-retention-teardown/ · **Prototype:** [`/prototype`](https://gitaakash28.github.io/firstclub-retention-teardown/prototype/) · **Live pulse:** [`/pulse`](https://gitaakash28.github.io/firstclub-retention-teardown/pulse/) · **PRD:** [`docs/PRD_make-it-right.md`](docs/PRD_make-it-right.md) · **Day-1 SQL:** [`day1_sql/`](day1_sql/)

## What I found
1. **New reviews turned more critical as FirstClub scaled.** The average rating of new written reviews fell from 4.37 (Jan–May 2026) to 3.92 (Jun–Oct 2026), and 1–2★ reviews rose from 13.8% to 24.9%. The overall store rating is still 4.7 across 10,862 ratings.
2. **Failures start the exit, and support decides it.** Among negative reviews that describe a failed order, late delivery, payment problem or bad produce, 24.2% signal churn when they also complain about support (n=62), vs 7.2% when they don't (n=167).
3. **It survives a stress test.** Within each failure type the link holds (odds ratio 4.1), and it's strongest for late and missing orders and weak for bad quality. So the design uses recovery for late and missing orders and prevention for quality (`r10`).
4. **Quality is the reason customers stay.** 66% of positive reviews mention quality or freshness.
5. **The habit is at risk too.** Subscription reviews average 2.91★, split 10 positive and 10 negative (pause and resume, delivery timing), though they halved per review in Jul–Oct, and fee complaints roughly doubled per review from Jan–Jun to Jul–Oct 2026 (`r12`).
6. **30% of negative reviews come from people who never ordered.** They hit "area not serviceable" after signing up, or OTP and login bugs.
7. **Appendix, US grocery benchmark (not FirstClub data):** in Instacart's public data, the order history ends at order 4 for 11.6% of customers, vs 5.9% at order 20. Fresh-heavy early baskets go with longer histories (29.6% vs 20.6% have 20+ observed orders).

**The bet: protect the first five orders.**
- **Prevent:** an extra quality check on first orders, with a guaranteed minimum shelf life.
- **Recover:** a one-tap "Something not right?" on the order. It checks FirstClub's own packing data, the customer chooses a refund to their original payment method, a credit that never expires or a replacement, and hard cases go to the existing AI assistant.
- **Say where you deliver, early:** name the cities served in the store listing and ads, and check the pincode before asking for a phone number.

The recovery part is A/B tested by randomizing every new customer. Prevention rolls out store by store.

## Repo map
| Path | What |
|---|---|
| `scripts/scrape_reviews.py` | Pulls all public Google Play reviews for `com.firstclub.app` |
| `reviews/tagging_prompt.md` | LLM taxonomy: lifecycle stage × theme, sentiment, churn intent |
| `reviews/tagged_reviews.csv` | 1,714 tagged reviews (reviewer names and developer replies not stored) |
| `scripts/check_tags.py` | Checks LLM theme tags against keyword rules (96–100% pooled agreement on 4 themes) |
| `scripts/review_analysis.py` | Review summaries → `results/r*.csv` |
| `scripts/reply_routing.py`, `scripts/serviceability_split.py` | Where FirstClub's replies send complainants (`r8`); serviceability complaints by city and late discovery (`r9`) |
| `day1_sql/` | 8 Postgres queries for FirstClub's own retention questions, on an assumed schema; tested on synthetic data only |
| `prototype/` | Clickable concept of the one-tap fix flow |
| `.github/workflows/weekly-pulse.yml` | Weekly job: scrape → LLM-tag new reviews → rebuild `pulse/` |
| `scripts/tag_new_reviews.py`, `scripts/build_pulse.py` | The pulse pipeline (needs a `GROQ_API_KEY` repo secret for tagging) |
| `sql/*.sql` | Appendix: benchmark queries on the US Instacart dataset (DuckDB, Postgres-style SQL) |
| `scripts/run_queries.py` | Runs `sql/` → `results/0*.csv` |
| `scripts/sample_size.py` | A/B sample sizes: triggered readout (`e1`) and intent-to-treat (`e2`) |
| `scripts/build_site.py` | Injects `results/` into `site/template.html` → `index.html` |

## Reproduce
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/scrape_reviews.py               # new reviews will change the counts slightly
# Instacart CSVs (Kaggle "Instacart Market Basket Analysis") → data/instacart/
python scripts/run_queries.py
python scripts/review_analysis.py
python scripts/build_site.py
```
The tags in `reviews/` were produced by running `tagging_prompt.md` through an LLM in 4 batches, then checked with `check_tags.py`.

## Limitations
- **Reviews are stated reasons from vocal customers, not observed behaviour.** The first query I'd run inside FirstClub is the real 14-day repeat rate after an early-order issue.
- **LLM tags are judgments.** Theme tags were checked against keyword rules, I read all 54 churn-flagged reviews by hand, and every tag is public here.
- **Instacart is a US dataset** that only includes customers with 4–100 orders, caps gaps at 30 days and has no calendar dates. There's no churn label, so a history that ends may be a newer customer, not a lost one. All findings from it are correlational.

Independent work by [Aakash Mishra](https://www.linkedin.com/in/aakash-mishra-6379a3270/). Not affiliated with or endorsed by FirstClub.
