"""CPU tests of the side-channel analysis (notebook 10): unpadded length, the frozen side-channel attacker (a planted
channel is found; identical channels give ties), the starvation table, and the timed reply path with fresh scores."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

import attackers as AT  # noqa: E402
import config  # noqa: E402
import pipeline as PL  # noqa: E402
import side as SD  # noqa: E402
import world as W  # noqa: E402
from scripted import ScriptedLLM  # noqa: E402

POOL = W.load_pool()


def test_unpadded_length_undoes_the_bucket():
    for t in ["No accessible record matched.", "x" * 170, "Which one?\n1. a [MH-1]\n2. none of these"]:
        df = SD.with_raw(pd.DataFrame([{"text": PL.bucket(t), "latency": 1.0}]))
        assert df["raw_chars"].iloc[0] == len(t) and df["raw_words"].iloc[0] == len(t.split())


def frame(n, split, planted, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        for w in ("0", "1"):
            cites = 2 - (1 if planted and w == "1" and rng.random() < 0.8 else 0)
            rows.append({"uid": f"{split}-{i:05d}", "world": w, "secret": "S1", "family": AT.FAMILIES[i % len(AT.FAMILIES)],
                         "text": PL.bucket("reply " * (3 + cites)), "status": "ok", "n_chars": 160.0, "n_tokens": 32.0,
                         "n_cites": float(cites), "n_options": 0.0, "latency": 1.0})
    return SD.with_raw(pd.DataFrame(rows))


def test_frozen_attacker_finds_a_planted_channel_and_ties_otherwise():
    tr, te = frame(200, "train", True), frame(400, "certify", True, seed=1)
    assert SD.frozen_attack(tr, te, SD.CHANNEL_SETS["citations"])["acc"] > 0.8
    assert SD.frozen_attack(tr, te, SD.CHANNEL_SETS["as_built"])["acc"] > 0.8
    a = SD.frozen_attack(tr, te, SD.CHANNEL_SETS["latency"])                  # latency is constant: a tie, world 1 guessed
    share = float((AT.picked(te)["world"] == "1").mean())
    assert abs(a["acc"] - share) < 1e-12


def test_starvation_table_reports_the_paired_difference():
    te = frame(300, "certify", True)
    t = SD.starvation_table({("m", "B5"): te})
    r = t.iloc[0]
    assert r["n_cites_w0"] == 2.0 and r["n_cites_diff"] < -0.6 and r["n_cites_diff_hi"] < 0
    assert 0.6 < r["cites_differ_share"] < 1.0


def test_fresh_scores_never_cache():
    class Count:
        n = 0

        def choice_logprobs(self, s, u, letters):
            Count.n += 1
            return {l: -1.0 for l in letters}

    f = SD.FreshScores(Count())
    assert f.logprobs("s", "u", 3) == {"A": -1.0, "B": -1.0, "C": -1.0}
    f.logprobs("s", "u", 3)
    assert Count.n == 2 and f.calls == 2


def test_timed_replies_pre_filter_identical_in_both_worlds():
    import json
    params = json.load(open(ROOT / "reports" / "03b_params.json"))["qwen25_7b"][config.SCORER] if (ROOT / "reports" / "03b_params.json").exists() else None
    if params is None:
        import pytest
        pytest.skip("03b_params.json not in this checkout")
    llm = ScriptedLLM("qwen25_7b")
    units = [W.build_unit("certify", i, POOL) for i in range(9)]
    for name in ("L2-RT-pre", "L2-RF-pre"):
        for u in units:
            r0, r1 = (SD.timed_reply(name, u, wk, llm, params) for wk in ("0", "1"))
            for k in ("text", "n_chars", "n_tokens", "n_cites", "n_options", "status", "score_calls"):
                assert r0[k] == r1[k], (name, u["uid"], k)
            assert r0["latency_raw"] >= r0["t_render"] >= 0
            assert (r0["t_render"] > 0) == (name.split("-")[1] == "RF")
    jobs = SD.timing_jobs(units, ["L2-RT-pre", "L2-RT-post"])
    assert len(jobs) == 36 and len({(c, u["uid"], w) for c, u, w in jobs}) == 36
