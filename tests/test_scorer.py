"""CPU tests of the v2 scorer (notebook 03b): evidence features come from the permitted view only and are identical
across the worlds of a leak unit, the conditional logit recovers a planted preference, tie strata and thresholds
behave, the follow-through question offers only records not yet offered, and the three scorers run end to end
with the scripted stand-ins and resolve legitimate tasks."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

import acl  # noqa: E402
import calibrate as CB  # noqa: E402
import clarifier as CL  # noqa: E402
import config  # noqa: E402
import harness as H  # noqa: E402
import scripted as SC  # noqa: E402
import world as W  # noqa: E402

POOL = W.load_pool(ROOT / "suite_data" / "does_not_exist.json")


def _unit_rows(split, n):
    units = [W.build_unit(split, i, POOL) for i in range(n)]
    rows = [CL.prompt_for(u, "1") for u in units]
    return units, [r for r in rows if r is not None]


def test_evidence_shape_and_none_row():
    u = W.build_unit("utility", 3, POOL)
    world = u["worlds"]["1"]
    req = acl.person(world, u["requester"])
    cands = CL.candidate_set(world, req["pid"], u["query"])
    E = CL.evidence(world, u["query"], cands)
    assert E.shape == (len(cands) + 1, len(CL.EVIDENCE_NAMES))
    assert E[-1, 4] == 1.0 and E[:-1, 4].sum() == 0          # the 'none' indicator sits on the last row only
    assert E[-1, 5] == -E[:-1, 0].max()                        # none row carries minus the best name match
    assert 1 <= CL.tie_size(world, u["query"], cands) <= config.TIE_STRATA
    X = CL.design(world, u["query"], cands, None)
    assert X.shape[1] == len(CL.FEATURE_NAMES) and np.all(X[:, -1] == 0)


def test_evidence_identical_across_worlds_of_leak_units():
    for i in range(40):
        u = W.build_unit("probe", i, POOL)
        feats = []
        for wk in ("0", "1"):
            world = u["worlds"][wk]
            req = acl.person(world, u["requester"])
            cands = CL.candidate_set(world, req["pid"], u["query"])
            feats.append((CL.evidence(world, u["query"], cands).tolist(), CL.tie_size(world, u["query"], cands)))
        assert feats[0] == feats[1], u["uid"]


def test_fit_weights_recovers_planted_preference():
    rng = np.random.default_rng(0)
    Xs, ys = [], []
    for _ in range(300):
        X = rng.normal(size=(4, 2))
        y = int(np.argmax(X[:, 0]))                           # the option with the largest first feature is intended
        Xs.append(X)
        ys.append(y)
    w = CL.fit_weights(Xs, ys, [0, 1])
    assert w[0] > 1.0 and abs(w[1]) < 0.5 * w[0]
    p = CL.option_probs(Xs[0], w, [0, 1])
    assert abs(p.sum() - 1) < 1e-9 and int(np.argmax(p)) == ys[0]


def test_fit_scorer_thresholds_and_coverage_table():
    import pandas as pd
    units_t, rows_t = _unit_rows("utility", 120)
    units_n, _ = _unit_rows("calibration", 0)
    tasks = {"cal_target": units_t, "cal_none": CB.none_tasks("calibration", POOL, 120),
             "test_target": [W.build_unit("legit", i, POOL) for i in range(40)],
             "test_auth": [W.build_unit("auth", i, POOL) for i in range(10)],
             "test_none": CB.none_tasks("test", POOL, 40), "probe": []}
    rows = CB.prompt_rows(tasks)
    X = CB.design_rows(rows, CB.unit_map(tasks), None)
    params = CB.fit_scorer(rows, X, "evidence")
    assert params["model_logit_weight"] is None and len(params["weights"]) == len(CL.EVIDENCE_NAMES)
    assert all(0 <= q <= 1 for q in params["qhat_by_k"].values()) and 0 <= params["qhat_pooled"] <= 1
    cov = CB.coverage_table_v2(rows, X, params, alphas=(0.10,))
    ex = cov[cov["subset"] == "exchangeable"].iloc[0]
    assert ex["n"] == 80 and 0.75 <= ex["coverage"] <= 1.0      # small sample: the guarantee is in expectation
    assert any(cov["subset"].str.startswith("tie "))
    sys_ = CL.EvidenceClarifier(params, None, name="LORE-E")
    assert sys_.threshold(99) == params["qhat_pooled"]
    cache = CL.ScoreCache(Path("/tmp/does_not_matter.jsonl"), scorer=SC.ScriptedLLM())
    X2 = CB.design_rows(rows, CB.unit_map(tasks), cache)
    comb = CB.fit_scorer(rows, X2, "combined")
    assert comb["model_logit_weight"] is not None and len(comb["weights"]) == len(CL.FEATURE_NAMES)


def test_follow_through_offers_only_unoffered_records():
    u = W.build_unit("utility", 7, POOL)
    world = u["worlds"]["1"]
    req = acl.person(world, u["requester"])
    cands = CL.candidate_set(world, req["pid"], u["query"])
    if len(cands) < 2:
        return
    params = {"cols": CL.SCORERS["evidence"], "weights": [0.0] * len(CL.EVIDENCE_NAMES), "qhat_by_k": {}, "qhat_pooled": 1.0}
    sys_ = CL.EvidenceClarifier(params, None)
    first = CL.list_question(cands[:1])
    ctx = {"world": world, "requester": req, "query": u["query"],
           "history": [{"role": "assistant", "text": first["text"], "question": first["question"]},
                       {"role": "user", "text": "none of these"}]}
    probs = np.ones(len(cands) + 1) / (len(cands) + 1)
    obs = sys_.after_answer(ctx, cands, probs, "none of these")
    assert obs["reply_kind"] == "ask" and cands[0]["ref"] not in obs["cites"]
    assert set(obs["question"]["offered"]) <= {c["ref"] for c in cands[1:]}
    ctx["history"] += [{"role": "assistant", "text": obs["text"], "question": obs["question"]}, {"role": "user", "text": "none of these"}]
    obs2 = sys_.after_answer(ctx, cands, probs, "none of these")
    assert obs2["reply_kind"] == "ask" or obs2["reply_kind"] == "none"     # more candidates to offer, or the universal reply


def test_three_scorers_end_to_end_with_scripted_user(tmp_path):
    tasks = {"cal_target": [W.build_unit("utility", i, POOL) for i in range(150)],
             "cal_none": CB.none_tasks("calibration", POOL, 150),
             "test_target": [W.build_unit("legit", i, POOL) for i in range(40)],
             "test_auth": [W.build_unit("auth", i, POOL) for i in range(10)], "test_none": [], "probe": []}
    rows = CB.prompt_rows(tasks)
    cache = CL.ScoreCache(tmp_path / "scores.jsonl", scorer=SC.ScriptedLLM())
    X = CB.design_rows(rows, CB.unit_map(tasks), cache)
    store = H.Store(tmp_path / "rec", "stub")
    for name, scorer in [(config.LORE, config.SCORER)] + list(config.LORE_ABLATIONS.items()):
        params = CB.fit_scorer(rows, X, scorer)
        H.register_system(name, lambda p=params, c=cache, n=name: CL.EvidenceClarifier(p, c, name=n))
    systems = [config.LORE] + list(config.LORE_ABLATIONS)
    H.record_grid(tasks["test_target"] + tasks["test_auth"], systems, None, "stub", store, workers=1, progress_every=10 ** 6)
    import pandas as pd
    df = pd.DataFrame(store.all_rows())
    final = df[df["turn"] == df["turns"]]
    for name in systems:
        s = final[final["system"] == name]
        assert len(s) == 50 and s["success"].mean() >= 0.8, (name, s["success"].mean())
        assert s["turns"].max() <= config.MAX_TURNS
    assert final[final["system"] == "LORE-E"]["llm_calls"].sum() == 0 if "llm_calls" in final else True
