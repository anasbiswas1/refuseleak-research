"""CPU tests of the ablations (notebook 11): the full variant is the certified configuration, each change does what
its name says, and every variant gives the same replies in both worlds."""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

import ablation as AB  # noqa: E402
import acl  # noqa: E402
import clarifier as CL  # noqa: E402
import config  # noqa: E402
import harness as H  # noqa: E402
import pipeline as PL  # noqa: E402
import world as W  # noqa: E402
from scripted import ScriptedLLM  # noqa: E402

POOL = W.load_pool()
PARAMS = ROOT / "reports" / "03b_params.json"


@pytest.fixture(scope="module")
def systems(tmp_path_factory):
    if not PARAMS.exists():
        pytest.skip("03b_params.json not in this checkout")
    params = json.load(open(PARAMS))["qwen25_7b"]
    cache = CL.ScoreCache(tmp_path_factory.mktemp("s") / "scores.jsonl", scorer=ScriptedLLM("qwen25_7b"))
    reg = {}
    AB.register(params, cache, lambda n, f: reg.__setitem__(n, f))
    reg["L2-RT-pre"] = lambda: PL.LoRe(params["combined"], cache, "L2", "pre", "L2-RT-pre")
    return {n: f() for n, f in reg.items()}


def units(split, n):
    return [W.build_unit(split, i, POOL) for i in range(n)]


def replies(system, u, wk):
    world = u["worlds"][wk]
    ctx = {"world": world, "requester": acl.person(world, u["requester"]), "query": u["query"], "history": [], "llm": None, "unit": u}
    o = system.respond(ctx)
    return {k: o.get(k) for k in ("text", "reply_kind", "status", "n_cites", "n_options", "private")}


def test_full_variant_is_the_certified_configuration(systems):
    for u in units("certify", 30) + units("utility", 20):
        for wk in u["worlds"]:
            assert replies(systems["A-full"], u, wk) == replies(systems["L2-RT-pre"], u, wk)


def test_each_change_does_what_its_name_says_and_stays_world_independent(systems):
    asked = {n: 0 for n in systems}
    for u in units("certify", 60) + units("utility", 60):
        wks = sorted(u["worlds"])
        for name, s in systems.items():
            r0, r1 = (replies(s, u, wk) for wk in (wks[0], wks[-1]))
            assert {k: v for k, v in r0.items() if k != "private"} == {k: v for k, v in r1.items() if k != "private"}, (name, u["uid"])
            asked[name] += r0["reply_kind"] == "ask"
            if name == "A-set-argmax":
                assert r0["reply_kind"] != "ask"
            if name == "A-no-private-action":
                assert not (r1["private"] or {}).get("access_request") and CL.UNIVERSAL + " " + PL.NOTICE not in r0["text"]
    assert asked["A-set-always-ask"] >= asked["A-full"] >= asked["A-set-argmax"] == 0


def test_top_list_never_asks_an_attribute_question(systems):
    attr = {"A-set-always-ask": 0, "A-always-ask-top-list": 0, "A-question-top-list": 0}
    for u in units("utility", 200):
        world = next(iter(u["worlds"].values()))
        ctx = {"world": world, "requester": acl.person(world, u["requester"]), "query": u["query"], "history": [], "llm": None, "unit": u}
        for name in attr:
            o = systems[name].respond(ctx)
            attr[name] += (o.get("question") or {}).get("kind") == "attribute"
            if name == "A-always-ask-top-list" and IXN(world, u["query"]):
                assert o["reply_kind"] == "ask" or o["reply_kind"] == "none"
    assert attr["A-question-top-list"] == attr["A-always-ask-top-list"] == 0 < attr["A-set-always-ask"]


def IXN(world, q):
    import index as IX
    return IX.has_name(world, q)
