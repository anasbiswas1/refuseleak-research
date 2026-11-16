"""Shared statistics: Wilson intervals, attacker advantage (Equations 5 to 7) and min-entropy leakage (Equation 8)."""
from __future__ import annotations

import math


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float, float]:
    """Point estimate and 95% Wilson interval of a share, as (p, lo, hi)."""
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def fmt_share(k: int, n: int) -> str:
    p, lo, hi = wilson(k, n)
    return f"{100 * p:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}] ({k}/{n})"


def advantage(correct: int, n: int) -> dict:
    """Advantage |2 acc - 1| of a distinguisher on balanced worlds, with the interval implied by the Wilson interval
    of its accuracy. The lower bound is 0 whenever the accuracy interval contains one half."""
    acc, lo, hi = wilson(correct, n)
    adv = abs(2 * acc - 1) if n else float("nan")
    if lo > 0.5:
        a_lo, a_hi = 2 * lo - 1, 2 * hi - 1
    elif hi < 0.5:
        a_lo, a_hi = 1 - 2 * hi, 1 - 2 * lo
    else:
        a_lo, a_hi = 0.0, max(2 * hi - 1, 1 - 2 * lo)
    return {"n": n, "correct": correct, "acc": acc, "acc_lo": lo, "acc_hi": hi, "adv": adv, "adv_lo": a_lo, "adv_hi": a_hi}


def min_entropy_leakage(acc: float) -> float:
    """Equation 8 with a uniform prior over one bit: log2(V_post / V_prior) with V_post = max(acc, 1 - acc)."""
    v_post = max(acc, 1 - acc)
    return math.log2(v_post / 0.5)
