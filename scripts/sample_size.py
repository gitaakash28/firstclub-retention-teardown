"""Customers per arm for a two-proportion test (two-sided alpha 0.05, power 0.8).

Baselines are assumptions, not FirstClub data: the real baseline comes from a SQL pull in week 1.
"""
from math import ceil, sqrt
from statistics import NormalDist

Z_A, Z_B = NormalDist().inv_cdf(0.975), NormalDist().inv_cdf(0.80)


def n_per_arm(p1, p2):
    pbar = (p1 + p2) / 2
    num = Z_A * sqrt(2 * pbar * (1 - pbar)) + Z_B * sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    return ceil(num ** 2 / (p2 - p1) ** 2)


if __name__ == "__main__":
    print("baseline,lift_pp,n_per_arm,n_total")
    for base in (0.30, 0.40, 0.50):
        for lift in (0.05, 0.08, 0.10):
            n = n_per_arm(base, base + lift)
            print(f"{base:.2f},{lift*100:.0f},{n},{2*n}")

    # Intent-to-treat design: every new customer is randomized at their first order, but only the share who hit
    # an issue in orders 1-5 can be affected, so the overall lift is diluted. Saved to results/e2_sample_size_itt.csv.
    import csv, pathlib
    rows = []
    for issue_share in (0.15, 0.25):
        for lift in (0.08, 0.10):
            d = issue_share * lift
            n = n_per_arm(0.40, 0.40 + d)
            rows.append({"baseline": 0.40, "issue_share": issue_share, "lift_among_affected_pp": lift * 100,
                         "overall_lift_pp": round(d * 100, 2), "n_per_arm": n, "n_total": 2 * n})
    out = pathlib.Path(__file__).resolve().parent.parent / "results" / "e2_sample_size_itt.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print("\nITT:", *[f"{r['issue_share']:.0%} affected, +{r['lift_among_affected_pp']:.0f}pp -> {r['n_per_arm']:,}/arm" for r in rows], sep="\n  ")
