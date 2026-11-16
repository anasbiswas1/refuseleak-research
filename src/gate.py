"""The as-built certificate (plan v1, Section 6.6, Equations 15 to 19 and Proposition 3).

For a configuration lambda and a frozen attacker d with k correct guesses out of n independent calibration units,
the null hypothesis "advantage above epsilon" is the union of "accuracy >= (1+eps)/2" and "accuracy <= (1-eps)/2";
its intersection-union p-value is the larger of the two one-sided binomial tails. The configuration's p-value is the
maximum over attackers; Bonferroni over the configuration set controls the family-wise error at delta.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.stats import binom, norm


def p_value(k: int, n: int, eps: float) -> float:
    """Equation 15."""
    hi = binom.cdf(k, n, (1 + eps) / 2)          # P[Bin(n, (1+eps)/2) <= k]
    lo = binom.sf(k - 1, n, (1 - eps) / 2)       # P[Bin(n, (1-eps)/2) >= k]
    return float(max(hi, lo))


def config_p_value(counts: dict[str, tuple[int, int]], eps: float) -> float:
    """Equation 16: the maximum over attackers of their p-values. counts[d] = (k, n)."""
    return max(p_value(k, n, eps) for k, n in counts.values())


def certify(all_counts: dict[str, dict[str, tuple[int, int]]], eps: float, delta: float) -> dict[str, dict]:
    """Equation 16 over the configuration set. all_counts[lambda][d] = (k, n)."""
    m = len(all_counts)
    out = {}
    for lam, counts in all_counts.items():
        p = config_p_value(counts, eps)
        out[lam] = {"p": p, "threshold": delta / m, "certified": p <= delta / m}
    return out


def select(cert: dict[str, dict], utility: dict[str, float], fallback: str) -> str:
    """Equation 17: the most useful certified configuration, else the fallback."""
    ok = [lam for lam, c in cert.items() if c["certified"]]
    if not ok:
        return fallback
    return max(ok, key=lambda lam: (utility.get(lam, float("-inf")), lam == fallback, lam))


def certified_bound(counts: dict[str, tuple[int, int]], delta_m: float, grid: np.ndarray | None = None) -> float:
    """Equation 18: the smallest epsilon on the grid at which the configuration is certified."""
    grid = np.round(np.arange(0.01, 1.0001, 0.01), 2) if grid is None else grid
    for e in grid:
        if config_p_value(counts, float(e)) <= delta_m:
            return float(e)
    return 1.0


def sample_size(eps: float, delta_m: float, power: float = 0.8) -> int:
    """Equation 19: units needed to certify a chance-level attacker at epsilon with the given power."""
    z1 = norm.ppf(1 - delta_m)
    z2 = norm.ppf(power)
    return int(math.ceil(((z1 + z2) / eps) ** 2))


def simulate(acc_true: float, n: int, eps: float, delta_m: float, seeds: int = 2000, seed: int = 0) -> float:
    """Share of simulated attackers with true accuracy acc_true that the certificate accepts (p <= delta_m)."""
    rng = np.random.default_rng(seed)
    ks = rng.binomial(n, acc_true, size=seeds)
    return float(np.mean([p_value(int(k), n, eps) <= delta_m for k in ks]))
