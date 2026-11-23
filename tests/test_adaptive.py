"""CPU tests of the adaptive attackers (notebook 09): fresh units with Equation 2, world-independent probes, identical
transcripts for low-view systems under every attacker, the follow-through of A4, the generation memo (one call per
input, latency replayed) and the learners (a planted leak is found; identical transcripts give ties)."""
import os
import sys
import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

import acl  # noqa: E402
import adaptive as AD  # noqa: E402
import attackers as AT  # noqa: E402
import baselines as B  # noqa: E402
import config  # noqa: E402
import world as W  # noqa: E402
from scripted import ScriptedLLM  # noqa: E402

POOL = W.load_pool()


def units_of(secret, n=6, split="test"):
    first, count = config.ADAPTIVE_UNITS[split]
    return [W.build_unit(split, i, POOL) for i in AD.unit_indices(first, count, secret)[:n]]


def test_fresh_units_carry_their_secret_and_never_overlap_earlier_splits():
    for split, (first, count) in config.ADAPTIVE_UNITS.items():
        assert first >= config.SPLITS[split]                     # indices after every unit used before notebook 09
        for s in config.SECRET_TYPES:
            idx = AD.unit_indices(first, count, s)
            assert len(idx) == count // 3
            assert all(W.build_unit(split, i, POOL)["secret"] == s for i in idx[:3])


def test_equation_2_holds_on_adaptive_units():
    for s in config.SECRET_TYPES:
        for u in units_of(s, 4):
            assert acl.low_equivalent(u["worlds"]["0"], u["worlds"]["1"], u["requester"])


def test_probes_are_world_independent_text_about_the_protected_record():
    for s in config.SECRET_TYPES:
        for u in units_of(s, 4):
            rec = AD.anchor(u)
            for a in AD.attackers_for(s):
                plan = AD.probe_plan(u, a)
                assert plan and all(isinstance(q, str) and q.strip() for q in plan)
                if a == "A1" or (a == "A2" and s != "S2"):
                    assert all(rec["codename"] in q for q in plan if "Which" not in q)
                if a == "A4":
                    assert [t in q for t, q in zip(AD.typos(rec, u["uid"]), plan)] == [True] * 3
                if a == "A1":
                    _, values = W.S3_ATTRIBUTE[rec["type"]]
                    assert all(any(v in q for q in plan) for v in values)        # both values asked
                if a == "A2" and s == "S2":
                    assert any(u["person_name"] in q for q in plan)


def test_typos_are_distinct_misspellings():
    for u in units_of("S1", 8):
        rec = AD.anchor(u)
        t = AD.typos(rec, u["uid"])
        assert len(t) == 3 and len({x.lower() for x in t}) == 3
        assert all(x.lower() != rec["codename"].lower() for x in t)
        assert t == AD.typos(rec, u["uid"])                                # fixed by the unit


def strip(rows):
    return [{k: v for k, v in r.items() if k not in ("world", "key")} for r in rows]


@pytest.mark.parametrize("system", ["B4", "B6"])
def test_low_view_systems_give_identical_transcripts_under_every_attacker(system):
    sysobj = B.make_system(system)
    for s in config.SECRET_TYPES:
        for u in units_of(s, 5):
            for a in AD.attackers_for(s):
                r0 = AD.run_session(sysobj, u, "0", None, a, "m")
                r1 = AD.run_session(sysobj, u, "1", None, a, "m")
                assert strip(r0) == strip(r1)
                assert [r["turn"] for r in r0] == list(range(1, AD.ATTACKERS[a]["turns"] + 1))


def test_triggered_refusal_is_told_apart_by_the_typo_attacker():
    sysobj, llm = B.make_system("B3"), ScriptedLLM("m")
    differ = 0
    for u in units_of("S1", 12):
        r0 = AD.run_session(sysobj, u, "0", llm, "A4", "m")
        r1 = AD.run_session(sysobj, u, "1", llm, "A4", "m")
        differ += strip(r0) != strip(r1)
    assert differ >= 6


def test_follow_through_answers_none_of_these_after_a_list_question():
    class AskOnce:
        name = "ask-once"

        def respond(self, ctx):
            if not ctx["history"]:
                return {**B.observation("Which one?\n1. x\n2. none of these", "ask"), "question": {"kind": "list", "offered": []}}
            assert ctx["history"][-1] == {"role": "user", "text": B.NONE_OPTION}
            return B.observation(B.UNIVERSAL, "none")

    u = units_of("S1", 1)[0]
    rows = AD.run_session(AskOnce(), u, "1", None, "A4", "m")
    assert all(r["n_replies"] == 2 and r["final_kind"] == "none" for r in rows)
    rows = AD.run_session(AskOnce(), u, "1", None, "A2", "m")          # only A4 follows through
    assert all(r["n_replies"] == 1 for r in rows)


def test_chat_memo_shares_one_call_and_replays_latency(tmp_path):
    calls = []

    class Slow:
        def chat(self, s, q, h):
            calls.append(q)
            time.sleep(0.05)
            return "reply to " + q, 3, 1.234

    memo = AD.ChatMemo(tmp_path / "m.jsonl.gz", "m", Slow())
    out = []
    ts = [threading.Thread(target=lambda: out.append(memo.chat("sys", "q", []))) for _ in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(calls) == 1 and len(set(out)) == 1 and out[0] == ("reply to q", 3, 1.234)
    memo.compact()
    again = AD.ChatMemo(tmp_path / "m.jsonl.gz", "m", None)
    assert again.chat("sys", "q", []) == ("reply to q", 3, 1.234)
    with pytest.raises(KeyError):
        again.chat("sys", "other", [])


def fake_rows(n_units, leak, k=3, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_units):
        uid = f"test-{i:05d}" if seed else f"train-{i:05d}"
        for w in ("0", "1"):
            for t in range(1, k + 1):
                word = ("restricted match" if (leak and w == "1" and rng.random() < 0.8) else "nothing found")
                text = f"reply {t}: {word} for item {i % 7}"
                rows.append({"model": "m", "system": "s", "attacker": "A3", "uid": uid, "split": "test" if seed else "train",
                             "secret": "S1", "world": w, "turn": t, "query": f"q{t}", "text": text, "reply_kind": "none",
                             "final_kind": "none", "status": "ok", "n_chars": len(text), "n_tokens": len(text.split()),
                             "cites": [], "n_cites": 0, "n_options": 0, "latency": 1.0, "n_replies": 1, "llm_calls": 0,
                             "disclosed": []})
    return pd.DataFrame(rows)


def test_learners_find_a_planted_leak_and_tie_on_identical_transcripts():
    nli = AT.MemoNLI(AT.StubNLI())
    for leak in (True, False):
        tr, te = fake_rows(120, leak, seed=0), fake_rows(300, leak, seed=1)
        hyp = {u: "There is a restricted record." for u in pd.concat([tr, te])["uid"].unique()}
        k = 3
        ftr = AD.add_nli(AD.session_frame(tr, k, k, hyp), k, nli)
        fte = AD.add_nli(AT.picked(AD.session_frame(te, k, k, hyp)), k, nli)
        sc = AD.score_sessions(ftr, fte, k)
        c = AD.counts(sc)
        if leak:
            assert c["bow"][0] / c["bow"][1] > 0.8 and c["stack"][0] / c["stack"][1] > 0.8
        else:
            for name in AD.LEARNERS:
                assert np.allclose(sc[f"p_{name}"], 0.5, atol=1e-6)
            share = float((fte["world"] == "1").mean())                   # every learner ties: the guess is world 1
            assert all(abs(c[n][0] / c[n][1] - share) < 1e-12 for n in AD.LEARNERS)


def test_session_frame_marks_turns_beyond_the_end():
    rows = fake_rows(4, False, k=2)
    hyp = {u: "h" for u in rows["uid"].unique()}
    f = AD.session_frame(rows, 3, 3, hyp)
    assert len(f) == 8 and (f["present_3"] == 0).all() and (f["present_1"] == 1).all()
    assert f["text_3"].str.endswith("noturn").all()
