"""CPU tests of Domain 2 (notebook 07): the archive parser, key words, world schema, paired worlds with identical
permitted views, and the systems running unchanged on email records."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import pytest  # noqa: E402

import acl  # noqa: E402
import baselines as B  # noqa: E402
import clarifier as CL  # noqa: E402
import config  # noqa: E402
import enron as EN  # noqa: E402
import harness as H  # noqa: E402
import pipeline as PL  # noqa: E402
from enron_stub import make_archive  # noqa: E402


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    path = make_archive(tmp_path_factory.mktemp("enron") / "enron_with_categories.tar.gz", n=400)
    c = EN.assign_keys(EN.load_archive(path))
    assert len(c) >= 300
    return c


def test_parse_and_keys(corpus):
    st = EN.corpus_stats(corpus)
    assert st["restricted"] > 30 and st["clusters_available"] >= 8
    r = corpus[0]
    assert r["subject"] and not r["subject"].lower().startswith(("re:", "fw:")) and "quoted text" not in r["body"]
    assert r["sender"].endswith("@enron.com") and r["type"] in EN.EMAIL_TYPES
    assert all(("key" in r) for r in corpus)


def test_world_schema(corpus):
    w = EN.build_world(7, corpus)
    assert len(w["records"]) == EN.RECORDS_PER_WORLD and len(w["people"]) == config.PEOPLE_PER_WORLD
    assert len(w["clusters"]) == 8 and sum(c["confidential"] for c in w["clusters"]) == 4
    for c in w["clusters"]:
        a = w["records"][c["anchor"]]
        assert a["codename"] == c["codename"] and len(c["decoys"]) == config.N_DECOYS
        assert all(c["codename"] in w["records"][d]["title"].lower() for d in c["decoys"])
        assert a["sensitive"] == c["confidential"]
    for r in w["records"]:
        assert r["type"] in EN.EMAIL_TYPES and r["body"].startswith("From: ") and "Priority: " in r["body"]
        if r["sensitive"]:
            assert r["acl"]["depts"] == [] and r["owner"] in r["acl"]["people"]
    assert len({r["title"] for r in w["records"]}) == len(w["records"])


def test_units_are_low_equivalent_and_well_formed(corpus):
    for split, n in (("train", 45), ("legit", 10), ("auth", 4)):
        for i in range(n):
            u = EN.build_unit(split, i, corpus)
            assert u["domain"] == "enron" and u["uid"].startswith("en-")
            if u["kind"] == "leak":
                assert acl.low_equivalent(u["worlds"]["0"], u["worlds"]["1"], u["requester"]), u["uid"]
                a1 = EN.get(u["worlds"]["1"], u["target"])
                assert not acl.can_read(acl.person(u["worlds"]["1"], u["requester"]), a1)
                if u["secret"] == "S1":
                    assert all(r["id"] != u["target"] for r in u["worlds"]["0"]["records"])
                if u["secret"] == "S3":
                    assert EN.get(u["worlds"]["0"], u["target"])["attrs"]["priority"] != a1["attrs"]["priority"]
                assert u["codename"].lower() in u["query"].lower() or u["family"] in ("Q2", "Q3", "Q3b", "Q6", "Q2a", "Q4")
            else:
                t = EN.get(u["worlds"]["1"], u["target"])
                assert acl.can_read(acl.person(u["worlds"]["1"], u["requester"]), t)


def test_systems_run_on_email_records(corpus):
    units = [EN.build_unit("legit", i, corpus) for i in range(16)] + [EN.build_unit("train", i, corpus) for i in range(12)]
    params = {"cols": CL.SCORERS["evidence"], "weights": [-0.8, 3.7, 1.8, 0.9, 2.9, -1.9, 5.7], "qhat_by_k": {1: 0.02, 2: 0.10, 3: 0.75},
              "qhat_pooled": 0.7, "scorer": "evidence"}
    H.register_system("L2-RT-pre", lambda: PL.LoRe(params, None, "L2", "pre", "L2-RT-pre"))
    rows = []
    for u in units:
        for wk in u["worlds"]:
            for name in ("B4", "O1", "O2", "L2-RT-pre"):
                rows.extend(H.run_task(H.make_system(name), u, wk, None))
    legit = [r for r in rows if r["kind"] == "legit" and r["turn"] == r["turns"]]
    o1 = [r for r in legit if r["system"] == "O1"]
    assert all(r["success"] for r in o1)
    lore = [r for r in legit if r["system"] == "L2-RT-pre"]
    assert sum(r["success"] for r in lore) >= 0.6 * len(lore)
    leak = [r for r in rows if r["kind"] == "leak" and r["system"] == "L2-RT-pre"]
    by = {}
    for r in leak:
        by.setdefault(r["uid"], {})[r["world"]] = r["text"]
    assert all(v["0"] == v["1"] for v in by.values())


def test_stub_parses_titles_with_parentheses():
    """The dry-run stand-in reads record blocks back from the system prompt; subjects may contain parentheses."""
    import baselines as B
    import scripted as S
    rec = {"id": 0, "ref": "EN-0007", "title": "TW Gas Sales (Phase 2)", "type": "email_logistics", "dept": "Trading",
           "body": "Body text here.", "acl": {"depts": ["all"], "roles": ["all"], "owner": None}, "owner": None, "codename": "sales"}
    world = {"people": [], "records": [rec]}
    requester = {"pid": 0, "name": "A B", "dept": "Trading", "role": "analyst"}
    block = B.record_block(rec, world, requester)
    parsed = S.ScriptedLLM()._records("x\n" + block + "\n")
    assert len(parsed) == 1 and parsed[0]["type"] == "email_logistics" and parsed[0]["title"] == "TW Gas Sales (Phase 2)", parsed
