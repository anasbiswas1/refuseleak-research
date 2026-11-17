"""The stages of notebook 03 as functions: task lists for the clarifier, scoring through the record-once cache,
temperature scaling and the conformal threshold (Equations 10 to 12), coverage on held-out tasks, and the
end-to-end run of the clarifier against the template systems under the current runtime.

Calibration tasks are the utility split (legitimate requests with a permitted target) plus the restricted-target
requests of the calibration split (label 'none'). Half of them fit the temperature, the other half set the
threshold, so the threshold is set on data the temperature never saw. Test tasks are the legit and auth splits
plus the restricted-target requests of the test split.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import clarifier as CL
import config
import conformal as C
import world as W
from metrics import wilson

NONE_SAMPLE = {"calibration": 1000, "test": 300}


# ----------------------------------------------------------------------------- tasks
def none_tasks(split: str, pool: dict, n: int) -> list[dict]:
    """Restricted-target requests of a leak split, in unit order, up to n."""
    out = []
    for i in range(config.SPLITS[split]):
        u = W.build_unit(split, i, pool)
        if CL.is_none_task(u):
            out.append(u)
            if len(out) >= n:
                break
    return out


def task_lists(pool: dict) -> dict[str, list[dict]]:
    return {"cal_target": [W.build_unit("utility", i, pool) for i in range(config.SPLITS["utility"])],
            "cal_none": none_tasks("calibration", pool, NONE_SAMPLE["calibration"]),
            "test_target": [W.build_unit("legit", i, pool) for i in range(config.SPLITS["legit"])],
            "test_auth": [W.build_unit("auth", i, pool) for i in range(config.SPLITS["auth"])],
            "test_none": none_tasks("test", pool, NONE_SAMPLE["test"]),
            "probe": [W.build_unit("probe", i, pool) for i in range(config.SPLITS["probe"])]}


def prompt_rows(tasks: dict[str, list[dict]]) -> pd.DataFrame:
    """One row per task (world 1); the probe group has one row per world so that the identity of the two prompts
    can be checked."""
    rows = []
    for group, units in tasks.items():
        for u in units:
            for wk in (u["worlds"] if group == "probe" else ["1"]):
                r = CL.prompt_for(u, wk)
                if r is not None:
                    rows.append({"group": group, **r})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- scoring
def score_all(rows: pd.DataFrame, cache: CL.ScoreCache, progress_every: int = 500) -> dict:
    keys = rows.drop_duplicates("key")
    t0, n_new = time.time(), 0
    for i, r in enumerate(keys.itertuples(), 1):
        if r.key not in cache.rows:
            cache.logprobs(r.system, r.user, r.n_cands + 1)
            n_new += 1
        if i % progress_every == 0:
            print(f"  {i}/{len(keys)} prompts, {time.time() - t0:.0f} s", flush=True)
    return {"prompts": int(len(keys)), "scored_now": n_new, "seconds": round(time.time() - t0, 1)}


def logits_matrix(rows: pd.DataFrame, cache: CL.ScoreCache) -> tuple[np.ndarray, np.ndarray, list[np.ndarray]]:
    """Padded logits (absent options at -50), labels, and the per-row logit vectors."""
    vecs = [CL.logits_from(cache.logprobs(r.system, r.user, r.n_cands + 1), r.n_cands + 1) for r in rows.itertuples()]
    width = max(len(v) for v in vecs)
    L = np.full((len(vecs), width), -50.0)
    for i, v in enumerate(vecs):
        L[i, :len(v)] = v
    return L, rows["label"].to_numpy(int), vecs


# ----------------------------------------------------------------------------- calibration
def calibrate(rows: pd.DataFrame, cache: CL.ScoreCache, alpha: float = config.ALPHA, seed: int = config.SEED) -> dict:
    cal = rows[rows["group"].isin(["cal_target", "cal_none"])].reset_index(drop=True)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(cal))
    half = len(cal) // 2
    A, B = cal.iloc[perm[:half]], cal.iloc[perm[half:]]
    LA, yA, _ = logits_matrix(A, cache)
    T = C.fit_temperature(LA, yA)
    LB, yB, vB = logits_matrix(B, cache)
    probs_B = [CL.softmax(v, T) for v in vB]
    probs_B1 = [CL.softmax(v, 1.0) for v in vB]
    scores = np.array([1 - p[y] for p, y in zip(probs_B, yB)])
    qhat = C.threshold(scores, alpha)
    width = max(len(p) for p in probs_B)
    def pad(ps):
        M = np.zeros((len(ps), width))
        for i, p in enumerate(ps):
            M[i, :len(p)] = p
        return M
    return {"T": T, "qhat": qhat, "alpha": alpha, "n_temperature": int(len(A)), "n_threshold": int(len(B)),
            "ece_before": C.ece(pad(probs_B1), yB), "ece_after": C.ece(pad(probs_B), yB),
            "top1_accuracy_threshold_half": float(np.mean([int(np.argmax(p)) == y for p, y in zip(probs_B, yB)])),
            "none_share_calibration": float(np.mean(cal["label"].to_numpy() == cal["n_cands"].to_numpy()))}


def coverage_table(rows: pd.DataFrame, cache: CL.ScoreCache, T: float, alphas=(0.05, 0.10, 0.20)) -> pd.DataFrame:
    """Coverage and set size on the test groups for the threshold of each alpha (threshold from the calibration
    half B, recomputed here from the same rows). The claim is read from the "exchangeable" subset, the test tasks drawn
    as the calibration tasks were (legitimate requests with a permitted target and requests naming a restricted
    record); the auth split (family Q8) is a different distribution and is reported on its own."""
    cal = rows[rows["group"].isin(["cal_target", "cal_none"])].reset_index(drop=True)
    rng = np.random.default_rng(config.SEED)
    perm = rng.permutation(len(cal))
    B = cal.iloc[perm[len(cal) // 2:]]
    _, yB, vB = logits_matrix(B, cache)
    sB = np.array([1 - CL.softmax(v, T)[y] for v, y in zip(vB, yB)])
    test = rows[rows["group"].isin(["test_target", "test_auth", "test_none"])].reset_index(drop=True)
    _, yT, vT = logits_matrix(test, cache)
    pT = [CL.softmax(v, T) for v in vT]
    out = []
    for a in alphas:
        q = C.threshold(sB, a)
        sets = [CL.pred_set(p, q) for p in pT]
        df = test.assign(covered=[y in s for s, y in zip(sets, yT)], size=[len(s) for s in sets],
                         singleton=[len(s) == 1 for s in sets], empty=[len(s) == 0 for s in sets])
        exch = df[df["group"].isin(["test_target", "test_none"])]          # drawn as the calibration tasks were
        for name, sub in [("exchangeable", exch)] + [(g, df[df["group"] == g]) for g in sorted(df["group"].unique())] + \
                         [(f"family {f}", df[df["family"] == f]) for f in sorted(df["family"].unique())]:
            k, n = int(sub["covered"].sum()), int(len(sub))
            p, lo, hi = wilson(k, n)
            out.append({"alpha": a, "qhat": q, "subset": name, "n": n, "coverage": p, "coverage_lo": lo, "coverage_hi": hi,
                        "mean_set_size": float(sub["size"].mean()), "singleton_share": float(sub["singleton"].mean()),
                        "empty_share": float(sub["empty"].mean())})
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------- verdict of notebook 03
def claims(params: dict, cov: pd.DataFrame, util: pd.DataFrame, ident: pd.DataFrame, att: pd.DataFrame, model: str) -> dict:
    a = config.ALPHA
    row = cov[(cov["alpha"] == a) & (cov["subset"] == "exchangeable")].iloc[0]
    c4 = {"coverage": float(row["coverage"]), "lower": float(row["coverage_lo"]), "target": 1 - a - 0.02,
          "pass": bool(row["coverage"] >= 1 - a - 0.02)}
    u = util[(util["model"] == model) & (util["family"].isin(config.LEGIT_FAMILIES))]
    def rate(system):
        s = u[u["system"] == system]
        return float((s["resolved"] * s["n"]).sum() / s["n"].sum()) if s["n"].sum() else float("nan")
    lore, b4, o1 = rate(config.LORE), rate("B4"), rate("O1")
    c3 = {"LORE_resolved": lore, "B4_resolved": b4, "O1_resolved": o1,
          "pass": bool(lore >= b4 + 0.10 and lore >= o1 - 0.10)}
    same = ident[(ident["model"] == model) & (ident["system"] == config.LORE)]["identical_share"]
    att_l = att[(att["model"] == model) & (att["system"] == config.LORE)]
    p1 = {"identical_share": float(same.iloc[0]) if len(same) else float("nan"),
          "max_adv_lower_bound": float(att_l["adv_lo"].max()) if len(att_l) else float("nan"),
          "pass": bool(len(same) and same.iloc[0] == 1.0 and len(att_l) and att_l["adv_lo"].max() == 0.0)}
    auth = util[(util["model"] == model) & (util["family"] == config.AUTH_FAMILY)]
    over = {"LORE_auth_resolved": float(auth[auth["system"] == config.LORE]["resolved"].iloc[0]) if len(auth) else float("nan")}
    return {"model": model, "T": params["T"], "qhat": params["qhat"], "C4_coverage": c4, "C3_utility_preliminary": c3,
            "leak_free_as_built": p1, "over_refusal": over,
            "pass": bool(c4["pass"] and c3["pass"] and p1["pass"])}
