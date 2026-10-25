# Day-1 SQL pack

These are the queries I'd run in my first week on FirstClub's retention project. They're written in Postgres against an **assumed** schema ([`schema.sql`](schema.sql)), and mapping them to the real tables should take an hour.

| # | Question | Why it matters |
|---|---|---|
| [01](01_weekly_cohort_retention.sql) | Of each weekly first-order cohort, what share orders again in weeks 1, 2, 4 and 8? | The retention curve the project is judged on |
| [02](02_first_order_experience.sql) | Does a late or complained-about first order lower the chance of a second order within 14 days? | Tests "quality wins the first order" with real orders |
| [03](03_repeat_after_issue_by_resolution.sql) | After an early-order issue, does how fast it's fixed change the 14-day reorder rate? | **The PRD's baseline and core hypothesis** |
| [04](04_issue_rate_by_order_number.sql) | Are early orders more likely to go wrong? Issues per 100 orders, by order number | Sizes the problem |
| [05](05_resolution_time_by_channel.sql) | How long does a fix take today, by channel (median, p90, unresolved)? | The "slow fix" the reviews describe |
| [06](06_slowdown_watchlist.sql) | Which customers are overdue against their own rhythm right now? | Win-back list and the cadence nudge |
| [07](07_signup_funnel_by_pincode.sql) | How many verified signups hit "not serviceable", by pincode? | Sizes the location-first onboarding fix |
| [08](08_ab_readout.sql) | Make-it-right A/B readout: 14-day reorder lift with a 95% CI, plus credit-cost and claim-rate guardrails | Hypothesis-to-readout, end to end |

## Tested, not analysed
FirstClub's data isn't public, so [`make_synthetic.py`](make_synthetic.py) generates FirstClub-shaped data whose behaviour is **pure random noise**: churn, issues and fix times are independent by design. The only purpose is to prove every query runs end to end. [`run_day1.py`](run_day1.py) runs them in DuckDB, and every query also parses as valid Postgres.

**Don't read [`sample_output/`](sample_output/) as findings.** It's test output on synthetic data.

```bash
python day1_sql/make_synthetic.py && python day1_sql/run_day1.py
```
