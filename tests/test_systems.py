"""CPU tests of the systems, the harness and the record store with the scripted stand-ins: Proposition 1 as built
(low-view systems give byte-identical observations in both worlds), the triggered refusal leaks by its trigger, the
clarifier resolves legitimate ambiguity, success is defined as one cited record that is the intended one, and the
store resumes without repeating work."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

import baselines as B  # noqa: E402
import config  # noqa: E402
import harness as H  # noqa: E402
import serving  # noqa: E402
import world as W  # noqa: E402

POOL = W.load_pool(ROOT / "suite_data" / "does_not_exist.json")
LLM = serving.make_llm("qwen25_7b")
UNITS = [W.build_unit("probe", i, POOL) for i in range(36)]


def first(system, unit, wk):
    return H.run_task(B.make_system(system), unit, wk, LLM)[0]


def test_low_view_systems_are_identical_across_worlds():
    for name in ("B4", "O1"):
        for u in UNITS:
            a, b = first(name, u, "1"), first(name, u, "0")
            for k in ("text", "status", "options", "reply_kind", "cites", "n_chars", "n_tokens"):
                assert a[k] == b[k], (name, u["uid"], k)


def test_triggered_refusal_differs_on_existence_units():
    diff = 0
    for u in UNITS:
        if u["secret"] != "S1" or u["family"] in ("Q2", "Q6"):
            continue
        a, b = first("B3", u, "1"), first("B3", u, "0")
        diff += a["text"] != b["text"]
        assert a["reply_kind"] == "refuse"
    assert diff > 0


def test_redaction_reuses_b0_and_never_cites_restricted():
    import acl
    for u in UNITS[:12]:
        rows = H.run_unit(u, "1", ["B0", "B2"], LLM, "stub")
        b0 = [r for r in rows if r["system"] == "B0"][0]
        b2 = [r for r in rows if r["system"] == "B2"][0]
        assert b2["llm_calls"] == 0 and b2["latency"] == b0["latency"]
        w = u["worlds"]["1"]
        restricted = {r["ref"] for r in acl.restricted_records(w, u["requester"])}
        assert not (set(b2["cites"]) & restricted)


def test_clarifier_resolves_legitimate_ambiguity_and_success_is_single_record():
    legit = [W.build_unit("legit", i, POOL) for i in range(30)]
    q5 = [u for u in legit if u["family"] == "Q5"]
    assert q5
    o2 = [H.run_task(B.make_system("O2"), u, "1", LLM) for u in q5]
    assert all(rows[0]["reply_kind"] == "ask" for rows in o2)
    assert sum(rows[-1]["success"] for rows in o2) >= 0.8 * len(o2)
    assert all(rows[-1]["turns"] <= config.MAX_TURNS for rows in o2)
    b4 = [H.run_task(B.make_system("B4"), u, "1", LLM) for u in q5]
    assert all(rows[-1]["success_listed"] for rows in b4)      # B4 lists every candidate
    assert not any(rows[-1]["success"] for rows in b4)          # a list is not a resolution
    o1 = [H.run_task(B.make_system("O1"), u, "1", LLM) for u in legit]
    assert all(rows[-1]["success"] for rows in o1)


def test_store_resumes_and_keys_by_runtime(tmp_path):
    store = H.Store(tmp_path, "stub")
    units = UNITS[:4]
    r1 = H.record_grid(units, ["B4", "B0", "B2"], LLM, "stub", store, workers=2, progress_every=10 ** 6)
    assert r1["tasks_run"] == 8
    store2 = H.Store(tmp_path, "stub")
    r2 = H.record_grid(units, ["B4", "B0", "B2"], LLM, "stub", store2, workers=2, progress_every=10 ** 6)
    assert r2["tasks_run"] == 0 and r2["rows_total"] == r1["rows_total"]
    rows = store2.all_rows()
    assert {r["system"] for r in rows} == {"B4", "B0", "B2"}
    assert all(r["runtime"] == config.RUNTIME_VERSION for r in rows)
    # a B2-only request reuses the stored B0 generation
    r3 = H.record_grid(units, ["B2"], LLM, "stub", H.Store(tmp_path, "stub"), workers=2, progress_every=10 ** 6)
    assert r3["tasks_run"] == 0


def test_observation_fields_and_disclosure_strings():
    u = next(u for u in UNITS if u["secret"] == "S1" and u["family"] == "Q1")
    a = first("B0", u, "1")
    for k in ("text", "reply_kind", "status", "options", "cites", "n_chars", "n_tokens", "n_cites", "n_options", "latency"):
        assert k in a
    assert u["target_ref"] in a["disclosed"]          # the scripted model names the restricted record, as deployed assistants do
    b = first("B0", u, "0")
    assert b["disclosed"] == []
