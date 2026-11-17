"""Split conformal prediction over a candidate set (plan v1, Equations 10 to 12 and Proposition 2).

Scores are probabilities over the options of one request (the permitted candidates plus "none"). The
nonconformity of the intended option is one minus its probability; the threshold is the ceil((n+1)(1-alpha))-th
smallest calibration score; the prediction set holds every option whose nonconformity is at most the threshold.
"""
from __future__ import annotations

import math

import numpy as np


def temperature_scale(logits: np.ndarray, T: float) -> np.ndarray:
    z = logits / T
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def fit_temperature(logits: np.ndarray, labels: np.ndarray, grid=None) -> float:
    """Temperature that minimises negative log-likelihood on calibration data (one-dimensional grid search)."""
    grid = np.exp(np.linspace(math.log(0.1), math.log(20.0), 80)) if grid is None else grid
    best, best_nll = 1.0, float("inf")
    for T in grid:
        p = temperature_scale(logits, T)
        nll = -np.mean(np.log(np.clip(p[np.arange(len(labels)), labels], 1e-12, 1)))
        if nll < best_nll:
            best, best_nll = float(T), float(nll)
    return best


def threshold(cal_scores: np.ndarray, alpha: float) -> float:
    """Equation 11: the ceil((n+1)(1-alpha))-th smallest nonconformity score (1 when the index exceeds n)."""
    n = len(cal_scores)
    k = math.ceil((n + 1) * (1 - alpha))
    if k > n:
        return 1.0
    return float(np.sort(cal_scores)[k - 1])


def prediction_set(probs: np.ndarray, qhat: float) -> list[int]:
    """Equation 12: options whose nonconformity 1 - p is at most the threshold."""
    return [int(i) for i in np.where(1 - probs <= qhat + 1e-12)[0]]


def coverage(prob_rows: list[np.ndarray], labels: np.ndarray, qhat: float) -> tuple[float, float]:
    """Empirical coverage and mean set size on test rows."""
    hits, sizes = [], []
    for p, y in zip(prob_rows, labels):
        s = prediction_set(p, qhat)
        hits.append(int(y) in s)
        sizes.append(len(s))
    return float(np.mean(hits)), float(np.mean(sizes))


def ece(probs: np.ndarray, labels: np.ndarray, bins: int = 10) -> float:
    """Expected calibration error of the top option."""
    conf = probs.max(axis=1)
    pred = probs.argmax(axis=1)
    correct = (pred == labels).astype(float)
    edges = np.linspace(0, 1, bins + 1)
    out = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            out += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(out)
