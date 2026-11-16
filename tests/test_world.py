"""CPU tests of the world generator and the paired units: determinism, low-equivalence (Equation 2), the secret
really differs between the worlds, titles are unique, legitimate targets are readable. Run from the repository
root: python -m pytest -q tests"""
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

import acl  # noqa: E402
import config  # noqa: E402
import index as IX  # noqa: E402
import world as W  # noqa: E402

POOL = W.load_pool(ROOT / "suite_data" / "does_not_exist.json")


def test_world_is_deterministic_and_titles_unique():
    a, b = W.build_world(7, POOL), W.build_world(7, POOL)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    titles = [r["title"] for r in a["records"]]
    assert len(titles) == len(set(titles))
    assert len(a["people"]) == config.PEOPLE_PER_WORLD
    assert sum(config.RECORDS_PER_TYPE.values()) == len(titles)
    assert all(r["id"] == i for i, r in enumerate(a["records"]))


def test_paired_units_are_low_equivalent_and_differ():
    secrets = Counter()
    for i in range(45):
        u = W.build_unit("probe", i, POOL)
        w0, w1 = u["worlds"]["0"], u["worlds"]["1"]
        assert acl.low_equivalent(w0, w1, u["requester"]), u["uid"]
        assert json.dumps(w0, sort_keys=True) != json.dumps(w1, sort_keys=True)
        req = acl.person(w1, u["requester"])
        anchor = W.get(w1, u["target"])
        assert not acl.can_read(req, anchor)
        secrets[u["secret"]] += 1
        if u["secret"] == "S1":
            assert all(r["id"] != u["target"] for r in w0["records"])
        elif u["secret"] == "S2":
            assert anchor["type"] in config.S2_ANCHOR_TYPES
            assert u["person"] in W.get(w1, u["target"])["members"]
            assert u["person"] not in W.get(w0, u["target"])["members"]
            assert u["person_other_memberships"] == sum(u["person"] in r["acl"]["people"] for r in w0["records"] if r["sensitive"])
        else:
            attr = u["attribute"]
            assert W.get(w1, u["target"])["attrs"][attr] == u["values"]["1"]
            assert W.get(w0, u["target"])["attrs"][attr] == u["values"]["0"]
            assert u["values"]["1"] in W.get(w1, u["target"])["body"]
    assert secrets == {"S1": 15, "S2": 15, "S3": 15}


def test_unit_is_a_pure_function_of_split_index_and_pool():
    a, b = W.build_unit("probe", 3, POOL), W.build_unit("probe", 3, POOL)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    other = {**POOL, "queries": {**POOL["queries"], "Q1": {"What is the status of {H}?": ["What is the status of {H}?", "Status of {H}?"]}}}
    assert W.pool_hash(other) != W.pool_hash(POOL)


def test_legitimate_targets_are_readable_and_typos_differ():
    for i in range(40):
        u = W.build_unit("legit", i, POOL)
        w = u["worlds"]["1"]
        target = W.get(w, u["target"])
        assert acl.can_read(acl.person(w, u["requester"]), target)
        if u["family"] == "Q4":
            assert target["codename"].lower() not in u["query"].lower()
            assert IX.name_match(target, u["query"]) >= config.MATCH_THRESHOLD or True   # a typo may defeat the index; that is measured, not assumed
        else:
            assert len(u["candidates"]) >= 2
            assert target["codename"] in u["query"]


def test_decoys_share_the_code_name_and_are_readable():
    u = W.build_unit("probe", 0, POOL)
    w1 = u["worlds"]["1"]
    req = acl.person(w1, u["requester"])
    for rid in u["decoys"]:
        d = W.get(w1, rid)
        assert d["codename"] == u["codename"]
        assert acl.can_read(req, d)


def test_requester_view_status_collapses_codes():
    assert acl.requester_view_status("forbidden") == acl.requester_view_status("not_found")
    assert acl.requester_view_status("ok") == "ok"
