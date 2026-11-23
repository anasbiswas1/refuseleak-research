"""Side channels (plan v1, Section 9.3; notebook 10): which reply channel carries a leak, what the length padding and
the latency floor do, and the starvation effect of filtering after retrieval.

Part A reads committed records and calls no model: the 24 configurations of notebook 04b (train and certify splits)
and the baselines of notebook 06 (train and test). For each it trains the side-channel attacker (gradient boosting,
as D5) on one set of channels at a time, on both worlds of the training units, and applies it frozen to one
hash-picked world per held-out unit. Channel sets:
    as built     padded length, token bucket, citations, options, status, latency bucket (the certificate's D5)
    no padding   the same with the unpadded length and word count
    length, citations, options, status, latency: one channel alone (length unpadded; latency in seconds as recorded)
The attacker always knows the family of the request it sent, as D5 does.

Part B measures reply time on the L4: the decision of a configuration with fresh one-token scores (no score cache;
the server's prefix cache off), plus, for free-text configurations, a fresh render of that decision. Requests of
both worlds are shuffled together and sent a fixed number at a time, so load does not differ between the worlds.
"""
from __future__ import annotations

import gzip
import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

import acl
import attackers as AT
import clarifier as CL
import config
import pipeline as PL
from metrics import advantage

CHANNEL_SETS = {
    "as_built": ["n_chars", "n_tokens", "n_cites", "n_options", "latency_bucket", "status"],
    "no_padding": ["raw_chars", "raw_words", "n_cites", "n_options", "latency_bucket", "status"],
    "length": ["raw_chars", "raw_words"],
    "citations": ["n_cites"],
    "options": ["n_options"],
    "status": ["status"],
    "latency": ["latency"],
}
TIMING_SETS = {
    "latency_floor_off": ["latency_raw"],
    "latency_floor_on": ["latency_floored"],
    "side_and_latency_floor_off": ["n_chars", "n_tokens", "n_cites", "n_options", "status", "latency_raw"],
    "side_and_latency_floor_on": ["n_chars", "n_tokens", "n_cites", "n_options", "status", "latency_floored"],
}


# ----------------------------------------------------------------------------- Part A: channels from records
def with_raw(df: pd.DataFrame) -> pd.DataFrame:
    """Unpadded length (padding is trailing spaces) and word count; latency bucket as D5 reads it."""
    df = df.copy()
    df["raw_chars"] = df["text"].map(lambda t: len(t.rstrip())).astype(float)
    df["raw_words"] = df["text"].map(lambda t: len(t.split())).astype(float)
    df["latency_bucket"] = np.floor(df["latency"].astype(float) / config.LATENCY_BUCKET_S)
    return df


def channel_matrix(df: pd.DataFrame, channels: list[str]) -> np.ndarray:
    cols = []
    for c in channels:
        if c == "status":
            st = df["status"].where(df["status"].isin(AT.STATUSES), "other")
            cols += [(st == s).to_numpy(float) for s in AT.STATUSES]
        else:
            cols.append(df[c].to_numpy(float))
    cols += [(df["family"] == f).to_numpy(float) for f in AT.FAMILIES]
    return np.column_stack(cols)


def gbm():
    return HistGradientBoostingClassifier(max_iter=150, max_depth=3, learning_rate=0.1, random_state=0)


def frozen_attack(train: pd.DataFrame, test: pd.DataFrame, channels: list[str]) -> dict:
    """Trained on both worlds of the training units, frozen, one hash-picked world per held-out unit."""
    y = train["world"].astype(int).to_numpy()
    picked = AT.picked(test)
    clf = gbm().fit(channel_matrix(train, channels), y)
    p = clf.predict_proba(channel_matrix(picked, channels))[:, 1]
    guess = np.where(np.abs(p - 0.5) <= 1e-9, 1, (p > 0.5).astype(int))
    correct = int((guess == picked["world"].astype(int).to_numpy()).sum())
    return advantage(correct, len(picked))


def leak_rows(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame([r for r in rows if r["kind"] == "leak" and r["turn"] == 1])
    return with_raw(df) if len(df) else df


def side_table(frames: dict[tuple[str, str], tuple[pd.DataFrame, pd.DataFrame]], source: dict[str, str]) -> pd.DataFrame:
    """frames: (model, system) -> (training rows, held-out rows). One row per (model, system, channel set)."""
    out = []
    for (model, system), (tr, te) in sorted(frames.items()):
        for name, channels in CHANNEL_SETS.items():
            a = frozen_attack(tr, te, channels)
            out.append({"model": model, "system": system, "source": source[system], "channels": name, **a})
    return pd.DataFrame(out)


def starvation_table(frames: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    """Per (model, system, secret): mean citations, options and unpadded length in each world on the held-out
    units, the mean paired difference (world 1 minus world 0) with a normal 95% interval, and the share of units
    whose citations differ between the worlds."""
    out = []
    for (model, system), te in sorted(frames.items()):
        for secret, g in te.groupby("secret"):
            w = {k: v.set_index("uid") for k, v in g.groupby("world")}
            if set(w) != {"0", "1"}:
                continue
            uids = w["0"].index.intersection(w["1"].index)
            row = {"model": model, "system": system, "secret": secret, "units": int(len(uids))}
            for f in ("n_cites", "n_options", "raw_chars"):
                d = (w["1"].loc[uids, f] - w["0"].loc[uids, f]).astype(float)
                se = float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else float("nan")
                row.update({f"{f}_w0": float(w["0"].loc[uids, f].mean()), f"{f}_w1": float(w["1"].loc[uids, f].mean()),
                            f"{f}_diff": float(d.mean()), f"{f}_diff_lo": float(d.mean() - 1.96 * se), f"{f}_diff_hi": float(d.mean() + 1.96 * se)})
            row["cites_differ_share"] = float((w["0"].loc[uids, "n_cites"] != w["1"].loc[uids, "n_cites"]).mean())
            out.append(row)
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------- Part B: reply time on the L4
class FreshScores:
    """The score cache's interface without the cache: every request is scored by the model. Counts its calls."""

    def __init__(self, scorer):
        self.scorer, self.calls = scorer, 0

    def logprobs(self, system: str, user: str, n_options: int) -> dict[str, float]:
        letters = CL.LETTERS[:n_options]
        lp = self.scorer.choice_logprobs(system, user, letters)
        self.calls += 1
        return {l: float(lp.get(l, float("nan"))) for l in letters}


def timing_jobs(units: list[dict], configs: list[str], seed: int = 0) -> list[tuple]:
    """(configuration, unit, world) for every unit and both worlds, shuffled with a fixed seed."""
    jobs = [(c, u, wk) for c in configs for u in units for wk in ("0", "1")]
    random.Random(seed).shuffle(jobs)
    return jobs


def timed_reply(name: str, unit: dict, wk: str, llm, params: dict) -> dict:
    level, render, retrieval = PL.parse_name(name)
    scores = FreshScores(llm)
    system = PL.LoRe(params, scores, level, retrieval, PL.config_name(level, "RT", retrieval))
    world = unit["worlds"][wk]
    req = acl.person(world, unit["requester"])
    ctx = {"world": world, "requester": req, "query": unit["query"], "history": [], "llm": None, "unit": unit}
    t0 = time.perf_counter()
    obs = system.respond(ctx)
    t_decide = time.perf_counter() - t0
    t_render, text = 0.0, obs["text"]
    if render != "RT":
        rctx = PL.render_context({"world": wk}, unit, retrieval)
        prompt = PL.render_prompt(render, obs["decision"], rctx)
        t1 = time.perf_counter()
        out = llm.complete(prompt, max_tokens=config.RENDER_MAX_TOKENS, temperature=config.RENDER_TEMPERATURE[render], n=1, seed=0)
        t_render = time.perf_counter() - t1
        obs = PL.finalize({**obs, "text": (out[0] if out else "").strip()}, obs["decision"])
        text = obs["text"]
    return {"system": name, "uid": unit["uid"], "split": unit["split"], "secret": unit["secret"], "family": unit["family"],
            "kind": "leak", "turn": 1, "world": wk, "text": text, "status": obs.get("status", "ok"), "reply_kind": obs["reply_kind"],
            "n_chars": obs["n_chars"], "n_tokens": obs["n_tokens"], "n_cites": obs["n_cites"], "n_options": obs["n_options"],
            "score_calls": scores.calls, "t_decide": round(t_decide, 5), "t_render": round(t_render, 5),
            "latency_raw": round(t_decide + t_render, 5)}


def run_timing(jobs: list[tuple], llm, params: dict, path: Path, workers: int) -> dict:
    """Runs the jobs not yet in the file (keyed by configuration, unit and world) and appends each reply."""
    path = Path(path)
    done = set()
    if path.exists():
        with gzip.open(path, "rt") as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    done.add((r["system"], r["uid"], r["world"]))
    todo = [j for j in jobs if (j[0], j[1]["uid"], j[2]) not in done]
    lock, t0 = threading.Lock(), time.time()
    path.parent.mkdir(parents=True, exist_ok=True)

    def work(job):
        r = timed_reply(job[0], job[1], job[2], llm, params)
        with lock:
            with gzip.open(path, "at") as fh:
                fh.write(json.dumps(r) + "\n")
        return r

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, f in enumerate(as_completed([ex.submit(work, j) for j in todo]), 1):
            f.result()
            if i % 1000 == 0:
                print(f"  {i}/{len(todo)} replies, {time.time() - t0:.0f} s", flush=True)
    return {"jobs": len(jobs), "run_now": len(todo), "seconds": round(time.time() - t0, 1)}


def load_timing(path: Path) -> pd.DataFrame:
    with gzip.open(path, "rt") as fh:
        df = pd.DataFrame([json.loads(l) for l in fh if l.strip()])
    df["latency_floored"] = np.maximum(df["latency_raw"].astype(float), config.LATENCY_FLOOR_S)
    return df


def timing_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (model, system, world), g in df.groupby(["model", "system", "world"]):
        lat = g["latency_raw"].astype(float)
        out.append({"model": model, "system": system, "world": world, "replies": int(len(g)),
                    "median_s": float(lat.median()), "p95_s": float(lat.quantile(0.95)), "p99_s": float(lat.quantile(0.99)),
                    "max_s": float(lat.max()), "above_floor_share": float((lat > config.LATENCY_FLOOR_S).mean()),
                    "score_calls_mean": float(g["score_calls"].mean()), "render_s_median": float(g["t_render"].median())})
    return pd.DataFrame(out)


def timing_attackers(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (model, system), g in df.groupby(["model", "system"]):
        tr, te = g[g["split"] == "train"], g[g["split"] != "train"]
        for name, channels in TIMING_SETS.items():
            out.append({"model": model, "system": system, "channels": name, **frozen_attack(tr, te, channels)})
    return pd.DataFrame(out)


def agreement(timed: pd.DataFrame, recorded: dict[tuple[str, str], dict[tuple[str, str], str]]) -> pd.DataFrame:
    """Share of timed template replies whose text equals the reply recorded in notebook 04b for the same unit and
    world (fresh scores against the stored ones)."""
    out = []
    for (model, system), g in timed.groupby(["model", "system"]):
        if PL.parse_name(system)[1] != "RT" or (model, system) not in recorded:
            continue
        rec = recorded[(model, system)]
        keys = [(u, w) for u, w in zip(g["uid"], g["world"]) if (u, w) in rec]
        same = sum(rec[(u, w)] == t for (u, w), t in zip(zip(g["uid"], g["world"]), g["text"]) if (u, w) in rec)
        out.append({"model": model, "system": system, "compared": len(keys), "identical": int(same),
                    "identical_share": same / len(keys) if keys else float("nan")})
    return pd.DataFrame(out)
