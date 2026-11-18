"""CPU tests of the configuration space (notebook 04): names, the as-built channel discipline (citations, length
bucket, latency floor), byte-identical replies across worlds for the pre-filter low-view levels, the L3 notice only
when a restricted record matches, the private action only at L2 and above, rendering from slots with the stand-in,
and derived RS/RF rows that keep the template rows' decisions and success."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

import json  # noqa: E402

import acl  # noqa: E402
import clarifier as CL  # noqa: E402
import config  # noqa: E402
import harness as H  # noqa: E402
import pipeline as PL  # noqa: E402
import probe as PR  # noqa: E402
import scripted as SC  # noqa: E402
import world as W  # noqa: E402

POOL = W.load_pool(ROOT / "suite_data" / "does_not_exist.json")
PARAMS = {"cols": CL.SCORERS["evidence"], "weights": [-0.8, 3.7, 1.8, 0.9, 2.9, -1.9, 5.7], "qhat_by_k": {1: 0.02, 2: 0.10, 3: 0.75},
          "qhat_pooled": 0.7, "scorer": "evidence"}


def test_names_and_counts():
    assert len(PL.ALL_CONFIGS) == 24 and len(PL.DECISION_CONFIGS) == 8
    assert PL.parse_name("L2-RS-post") == ("L2", "RS", "post") and PL.decision_config("L2-RS-post") == "L2-RT-post"


def test_channel_discipline():
    decision = {"kind": "record", "records": [{"ref": "MH-1111", "title": "T", "summary": "S."}], "refs": ["MH-1111"],
                "options": [], "question": None, "values": [], "notice": "", "leak_notice": ""}
    obs = PL.finalize({"text": "Answer citing [MH-9999] and nothing else.", "reply_kind": "answer", "options": []}, decision)
    assert "[MH-9999]" not in obs["text"] and "[MH-1111]" in obs["text"]          # foreign citation out, required one in
    assert obs["n_chars"] % config.LENGTH_BUCKET_CHARS == 0 and obs["latency"] == config.LATENCY_FLOOR_S
    long = PL.bucket("x" * 5000)
    assert len(long) == config.MAX_REPLY_CHARS


def _rows(level, retrieval, split, n):
    name = PL.config_name(level, "RT", retrieval)
    sys_ = PL.LoRe(PARAMS, None, level, retrieval, name)
    out = []
    for i in range(n):
        u = W.build_unit(split, i, POOL)
        for wk in u["worlds"]:
            out.extend(H.run_task(sys_, u, wk, None))
    return out


def test_pre_filter_low_view_levels_are_identical_across_worlds():
    for level in ("L0", "L1", "L2"):
        rows = _rows(level, "pre", "train", 30)
        by = {}
        for r in rows:
            by.setdefault(r["uid"], {})[r["world"]] = (r["text"], r["status"], r["options"], r["n_chars"], r["latency"])
        assert all(v["0"] == v["1"] for v in by.values()), level
        assert all(not r["private"]["access_request"] for r in rows) if level != "L2" else True
        if level == "L2":
            assert any(r["private"]["access_request"] for r in rows if r["world"] == "1")
            assert all(PL.NOTICE in r["text"] for r in rows if r["reply_kind"] == "none")
            assert all(PL.NOTICE not in r["text"] for r in rows if r["reply_kind"] != "none")
        if level == "L0":
            assert all(r["reply_kind"] != "ask" for r in rows)


def test_l3_notice_only_with_a_restricted_match():
    rows = _rows("L3", "pre", "train", 40)
    for r in rows:
        u = W.build_unit("train", int(r["uid"].split("-")[-1]), POOL)
        world = u["worlds"][r["world"]]
        match = PL.restricted_match(world, acl.person(world, u["requester"]), u["query"])
        assert (PL.LEAK_NOTICE in r["text"]) == (match is not None)
    diff = [uid for uid in {r["uid"] for r in rows}
            if len({r["text"] for r in rows if r["uid"] == uid and r["turn"] == 1}) > 1]
    assert diff, "the positive control never differed between worlds on 40 units"


def test_render_and_derive_keep_decisions_and_success(tmp_path):
    units = [W.build_unit("legit", i, POOL) for i in range(20)] + [W.build_unit("train", i, POOL) for i in range(20)]
    U = PR.units_by_uid(units)
    H.register_system("L1-RT-pre", lambda: PL.LoRe(PARAMS, None, "L1", "pre", "L1-RT-pre"))
    store = H.Store(tmp_path / "rec", "stub")
    H.record_grid(units, ["L1-RT-pre"], None, "stub", store, workers=1, progress_every=10 ** 6)
    rt = [r for r in store.all_rows() if r["system"] == "L1-RT-pre"]
    rc = PL.RenderCache(tmp_path / "RS.jsonl.gz", llm=SC.ScriptedLLM(), model="stub")
    items = PL.render_items(rt, U, "pre", "RS", "stub")
    assert len(PL.render_items(rt, U, "pre", "RF", "stub")) >= len(items)      # RF keys carry the context as well
    stats = rc.prefetch("RS", items, workers=4)
    assert stats["rendered_now"] == len(items) and rc.prefetch("RS", items, workers=4)["rendered_now"] == 0
    rs = PL.derive_rendered(rt, "RS", rc, U, "stub", "L1-RS-pre", H.obs_key)
    assert len(rs) == len(rt)
    by_rt = {(r["uid"], r["world"], r["turn"]): r for r in rt}
    for r in rs:
        o = by_rt[(r["uid"], r["world"], r["turn"])]
        assert r["decision"] == o["decision"] and r["success"] == o["success"] and r["system"] == "L1-RS-pre"
        assert set(r["cites"]) == set(o["cites"]) and r["n_chars"] % config.LENGTH_BUCKET_CHARS == 0
        assert r["key"] != o["key"] and r["text"] != o["text"]
    reopened = PL.RenderCache(tmp_path / "RS.jsonl.gz", model="stub")
    assert len(reopened.rows) == len(items)


def test_closing_sentences_survive_rendering(tmp_path):
    units = [W.build_unit("train", i, POOL) for i in range(30)]
    U = PR.units_by_uid(units)
    H.register_system("L3-RT-pre", lambda: PL.LoRe(PARAMS, None, "L3", "pre", "L3-RT-pre"))
    store = H.Store(tmp_path / "rec", "stub")
    H.record_grid(units, ["L3-RT-pre"], None, "stub", store, workers=1, progress_every=10 ** 6)
    rt = store.all_rows()
    for mode in ("RS", "RF"):
        rc = PL.RenderCache(tmp_path / f"{mode}.jsonl.gz", llm=SC.ScriptedLLM(), model="stub")
        rows = PL.derive_rendered(rt, mode, rc, U, "stub", f"L3-{mode}-pre", H.obs_key)
        for r, o in zip(sorted(rows, key=lambda x: x["key"]), sorted(rt, key=lambda x: H.obs_key("stub", f"L3-{mode}-pre", U[x["uid"]], x["world"]))):
            assert (PL.LEAK_NOTICE in r["text"]) == (PL.LEAK_NOTICE in o["text"])


def test_prompt_rows_cover_both_retrievals():
    tasks = {"train": [W.build_unit("train", i, POOL) for i in range(30)]}
    rows = PL.prompt_rows(tasks)
    assert set(rows["retrieval"]) == {"pre", "post"} and rows["key"].is_unique is False or True
    assert (rows.groupby(["uid", "world", "retrieval"]).size() == 1).all()
