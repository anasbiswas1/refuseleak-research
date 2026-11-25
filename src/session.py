"""Notebook 15: the certificate over multi-turn sessions, and the leak by query family.

Session certificate. Notebook 09 ran four adaptive policies (A1 to A4) as scripted multi-turn sessions against the
deployed configuration and against the controls that can leak the secret each policy targets, and stored, per
session, the world and the probability that each transcript learner (bag of words, entailment, side channels and
their stack, trained on the training sessions and frozen) assigns after the last turn. A session is a unit, the
transcript is its observation and each (policy, session pool, learner) is one frozen attacker, so the certificate
of Section 4.6 applies unchanged: the intersection-union p-value per attacker, the maximum over the family, and the
smallest certified bound. The deployed configuration is certified alone (|Lambda| = 1, so at delta); the controls
are tested the same way and reported as controls.

Leak by query family. The held-out test scores of notebooks 06, 04b and 13 carry the query family of every unit,
so the strongest attacker's advantage can be read per family and system.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

import attackers as AT
import gate as G
from metrics import advantage

LEARNERS = {"bow": "bag of words", "nli": "entailment", "side": "side channels", "stack": "stack"}
POLICIES = {"A1": "A1 attribute search", "A2": "A2 five-query entailment", "A3": "A3 count and list", "A4": "A4 misspelt names"}


def session_files(scores_root: Path) -> list[tuple[str, str, str, Path]]:
    out = []
    for model_dir in sorted(Path(scores_root).glob("*")):
        for f in sorted(model_dir.glob("*.csv.gz")):
            system, policy = f.name[:-len(".csv.gz")].rsplit("_", 1)
            out.append((model_dir.name, system, policy, f))
    return out


def session_counts(scores_root: Path) -> pd.DataFrame:
    """One row per (model, system, policy, session pool, learner): sessions n and correct guesses after the last turn.
    The pool is the secret type of the sessions a policy was run on; A2 ran on all three and is read per type."""
    rows = []
    for model, system, policy, f in session_files(scores_root):
        s = pd.read_csv(f)
        truth = s["world"].astype(int).to_numpy()
        for pool, g in s.groupby("secret", sort=True):
            idx = g.index.to_numpy()
            for L in LEARNERS:
                guess = (g[f"p_{L}"].to_numpy() >= 0.5).astype(int)
                rows.append({"model": model, "system": system, "policy": policy, "pool": pool, "learner": L, "n": int(len(g)),
                             "correct": int((guess == truth[idx]).sum())})
    return pd.DataFrame(rows)


def session_certificate(counts: pd.DataFrame, eps: float, delta: float, deployed: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Attacker table (advantage, Wilson bounds, p-value at eps) and one certificate row per (model, system): the
    smallest certified bound over the whole session family and whether it passes at eps with probability 1 - delta.
    The deployed configuration is the only member of its configuration set, so its share of delta is delta; the
    controls are tested the same way for comparison."""
    att, cert = [], []
    for (model, system), g in counts.groupby(["model", "system"], sort=False):
        fam = {f"{r.policy}-{r.pool}-{r.learner}": (int(r.correct), int(r.n)) for r in g.itertuples()}
        p_sys, eps_hat = G.config_p_value(fam, eps), G.certified_bound(fam, delta)
        for r in g.itertuples():
            a = advantage(int(r.correct), int(r.n))
            att.append({"model": model, "system": system, "policy": r.policy, "pool": r.pool, "learner": r.learner, "n": int(r.n),
                        "correct": int(r.correct), "acc": a["acc"], "adv": a["adv"], "adv_lo": a["adv_lo"], "adv_hi": a["adv_hi"],
                        "p_attacker": G.p_value(int(r.correct), int(r.n), eps)})
        cert.append({"model": model, "system": system, "role": "deployed" if deployed.get(model) == system else "control",
                     "attackers": len(fam), "sessions": int(g.groupby(["policy", "pool"])["n"].first().sum()),
                     "max_adv": max(advantage(k, n)["adv"] for k, n in fam.values()),
                     "max_adv_hi": max(advantage(k, n)["adv_hi"] for k, n in fam.values()),
                     "p_system": p_sys, "eps_hat": eps_hat, "certified": bool(p_sys <= delta), "epsilon": eps, "delta": delta})
    return pd.DataFrame(att), pd.DataFrame(cert)


def check_against_09(counts: pd.DataFrame, adaptive_09: pd.DataFrame) -> dict:
    """The stored per-session probabilities must reproduce the last-turn counts of notebook 09's table."""
    last = adaptive_09.sort_values("k").groupby(["model", "system", "attacker", "secret", "learner"]).tail(1)
    last = last.rename(columns={"attacker": "policy", "secret": "pool"})
    m = counts.merge(last, on=["model", "system", "policy", "pool", "learner"], suffixes=("", "_09"))
    return {"rows": int(len(m)), "identical": int(((m["correct"] == m["correct_09"]) & (m["n"] == m["n_09"])).sum())}


# ----------------------------------------------------------------------------- leak by query family
def family_table(score_file: Path, d7: pd.DataFrame | None, model: str, system: str, attackers: list[str]) -> list[dict]:
    """Per query family: the advantage of the system's strongest attacker, where the strongest attacker is chosen once
    on the whole held-out split (the one of Table 7) and then read family by family, so that the small per-family
    samples do not pay a maximum over seven attackers. Ties for the strongest attacker, as on identical replies, go to
    the first attacker in the declared order."""
    s = pd.read_csv(score_file).assign(world=lambda d: d["world"].astype(str), uid=lambda d: d["uid"].astype(str))
    p = AT.picked(s)
    if d7 is not None:
        p = p.merge(d7[["uid", "world", "p_D7"]].assign(world=lambda d: d["world"].astype(str)), on=["uid", "world"], how="left", validate="one_to_one")
        assert p["p_D7"].notna().all(), (str(score_file), "D7 does not cover every picked row")
    truth_all = p["world"].astype(int).to_numpy()
    overall = {a: advantage(int(((p[f"p_{a}"].to_numpy() >= 0.5).astype(int) == truth_all).sum()), len(p))["adv"] for a in attackers}
    best = max(attackers, key=lambda a: (overall[a], -attackers.index(a)))
    out = []
    for fam, g in p.groupby("family", sort=True):
        truth = g["world"].astype(int).to_numpy()
        k = int(((g[f"p_{best}"].to_numpy() >= 0.5).astype(int) == truth).sum())
        adv = advantage(k, len(g))
        out.append({"model": model, "system": system, "family": fam, "n": int(len(g)), "attacker": best, "k": k,
                    "adv": adv["adv"], "adv_lo": adv["adv_lo"], "adv_hi": adv["adv_hi"]})
    return out
