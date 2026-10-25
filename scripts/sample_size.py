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
