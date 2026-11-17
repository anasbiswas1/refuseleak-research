"""CPU tests of the low-view conformal clarifier with the scripted stand-ins: the scorer sees permitted records
only, its prompt is identical in both worlds of every leak unit, the cache never re-scores, the prediction set and
the question choice behave as Equations 12 to 14 say, labels are the intended option, and the scripted user
answers attribute questions."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

import acl  # noqa: E402
import clarifier as CL  # noqa: E402
import config  # noqa: E402
import harness as H  # noqa: E402
import scripted as SC  # noqa: E402
import world as W  # noqa: E402

POOL = W.load_pool(ROOT / "suite_data" / "does_not_exist.json")
LLM = SC.ScriptedLLM()


def make_system(tmp_path, T=1.0, qhat=0.9):
    cache = CL.ScoreCache(tmp_path / "scores.jsonl", scorer=LLM)
    return CL.ConformalClarifier(cache, T=T, qhat=qhat), cache


def test_prompts_hold_permitted_records_only_and_match_across_worlds():
    for i in range(45):
        u = W.build_unit("probe", i, POOL)
        rows = [CL.prompt_for(u, wk) for wk in ("1", "0")]
        if rows[0] is None:
            assert rows[1] is None
            continue
        assert rows[0]["key"] == rows[1]["key"], u["uid"]
        w1 = u["worlds"]["1"]
        req = acl.person(w1, u["requester"])
        restricted = {r["ref"] for r in acl.restricted_records(w1, req["pid"])}
        assert not any(ref in rows[0]["user"] for ref in restricted)
        assert u["target_ref"] not in rows[0]["user"]


def test_labels_are_the_intended_option():
    for i in range(30):
        u = W.build_unit("legit", i, POOL)
        row = CL.prompt_for(u)
        assert row is not None and row["label"] < row["n_cands"]
    none_tasks = [u for u in (W.build_unit("probe", i, POOL) for i in range(60)) if CL.is_none_task(u)]
    assert none_tasks
    for u in none_tasks:
        row = CL.prompt_for(u)
        assert row is None or row["label"] == row["n_cands"]


def test_cache_scores_each_prompt_once(tmp_path):
    system, cache = make_system(tmp_path)
    u = W.build_unit("legit", 0, POOL)
    row = CL.prompt_for(u)
    a = cache.logprobs(row["system"], row["user"], row["n_cands"] + 1)
    cache.scorer = None                       # a second call must come from the cache
    b = cache.logprobs(row["system"], row["user"], row["n_cands"] + 1)
    assert a == b
    reloaded = CL.ScoreCache(tmp_path / "scores.jsonl")
    assert reloaded.logprobs(row["system"], row["user"], row["n_cands"] + 1) == a


def test_prediction_set_and_decisions(tmp_path):
    system, _ = make_system(tmp_path, qhat=0.5)
    assert system.prediction_set(np.array([0.7, 0.2, 0.1])) == [0]
    assert system.prediction_set(np.array([0.5, 0.5, 0.0])) == [0, 1]
    assert system.prediction_set(np.array([0.4, 0.4, 0.2])) == []     # empty: the system then asks over the likeliest records
    assert system.prediction_set(np.array([0.1, 0.1, 0.8])) == [2]


def test_best_question_prefers_the_attribute_that_splits_the_set():
    recs = [{"type": "project_brief", "dept": "Finance", "owner": 1}, {"type": "vendor_contract", "dept": "Finance", "owner": 2},
            {"type": "support_ticket", "dept": "Finance", "owner": 3}]
    attr, gain = CL.best_question(recs, np.array([0.4, 0.4, 0.2]))
    assert attr in ("type", "owner") and gain > 0
    assert CL.best_question([recs[0], dict(recs[0])], np.array([0.5, 0.5])) is None


def test_end_to_end_resolves_and_is_identical_across_worlds(tmp_path):
    system, _ = make_system(tmp_path, qhat=1.0)      # the widest set: every clarification is a question
    legit = [W.build_unit("legit", i, POOL) for i in range(30)]
    runs = [H.run_task(system, u, "1", LLM) for u in legit]
    assert sum(r[-1]["success"] for r in runs) >= 0.9 * len(runs)
    assert all(r[-1]["turns"] <= config.MAX_TURNS for r in runs)
    for i in range(30):
        u = W.build_unit("probe", i, POOL)
        a, b = H.run_task(system, u, "1", LLM)[0], H.run_task(system, u, "0", LLM)[0]
        for k in ("text", "status", "options", "reply_kind", "cites"):
            assert a[k] == b[k], (u["uid"], k)


def test_scripted_user_answers_attribute_questions():
    w = W.build_world(3, POOL)
    target = w["records"][0]
    user = SC.ScriptedUser(target["ref"], target, w)
    obs = {"question": {"attribute": "dept", "values": [target["dept"], "Other"], "set": [target["ref"], "MH-0000"]}, "options": []}
    assert user.answer(obs) == target["dept"]
    obs["question"]["set"] = ["MH-0000"]
    assert user.answer(obs) == "none of these"
