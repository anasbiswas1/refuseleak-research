"""CPU tests of the agent setting (notebook 08): the units satisfy Equation 2, projection makes every tool output a
function of the requester's view, raw and trimmed errors depend on the hidden file, generic errors are constant, and
the full agent loop (AgentDojo pipeline with the stand-in model) gives identical transcripts across worlds under
projection while completing the same legitimate tasks as raw errors."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

pytest.importorskip("agentdojo")

import agent as AG  # noqa: E402
import serving  # noqa: E402

BASE = AG.base_files()
LEAK = [AG.build_unit("train", i, BASE) for i in range(60)]
LEGIT = [AG.build_unit("legit", i, BASE) for i in range(30)] + [AG.build_unit("auth", i, BASE) for i in range(10)]


def outputs(unit, world, arm):
    d = AG.Drive(AG.drive_files(BASE, unit, world), arm)
    stem = unit["target_ref"].split("-")[0]
    out = []
    for call in (lambda: d.open(unit["target_ref"]), lambda: d.search_name(stem), lambda: d.search_content("reference"),
                 lambda: [AG._meta(f) for f in d.listing()], lambda: d.get(str(len(AG.view(d.files)))), lambda: d.get("999")):
        try:
            out.append(("ok", call()))
        except Exception as e:            # noqa: BLE001
            out.append((type(e).__name__, str(e)))
    return out


def test_units_are_deterministic_and_low_equivalent():
    again = [AG.build_unit("train", i, BASE) for i in range(60)]
    assert [AG.manifest_row(u) for u in LEAK] == [AG.manifest_row(u) for u in again]
    assert all(AG.low_equivalent(u, BASE) for u in LEAK)
    assert {u["secret"] for u in LEAK} == {"S1", "S3"}
    targets = {u["target_ref"] for u in LEAK}
    assert not targets & {f["filename"] for f in BASE}


def test_projection_outputs_are_a_function_of_the_view():
    for u in LEAK:
        assert outputs(u, "0", "projection") == outputs(u, "1", "projection"), u["uid"]


def test_raw_and_trimmed_errors_depend_on_the_hidden_file():
    for arm in ("raw", "trimmed"):
        assert all(outputs(u, "0", arm)[0] != outputs(u, "1", arm)[0] for u in LEAK), arm


def test_generic_errors_are_constant():
    for u in LEAK:
        for w in u["worlds"]:
            kind, msg = outputs(u, w, "generic")[0]
            assert kind == "OperationFailed" and msg == "The operation failed."


def test_listing_is_privileged_only_in_raw_and_generic():
    u = next(x for x in LEAK if x["secret"] == "S1")
    for arm in AG.ARMS:
        names = {f["filename"] for f in AG.Drive(AG.drive_files(BASE, u, "1"), arm).listing()}
        assert (u["target_ref"] in names) == AG.PRIVILEGED_LISTING[arm], arm


def test_target_names_are_unique_across_units_and_splits():
    units = LEAK + [AG.build_unit("test", i, BASE) for i in range(60)] + LEGIT
    names = [u["target_ref"] for u in units if u["kind"] != "legit"]
    assert len(names) == len(set(names))
    for u in units:
        for w in u["worlds"].values():
            fns = [f["filename"] for f in w["files"]]
            assert len(fns) == len(set(fns)), u["uid"]


def test_parse_call_reads_the_forms_models_write():
    assert AG.parse_call('x <function=open_file>{"filename": "a.docx"}</function>') == ("open_file", {"filename": "a.docx"})
    assert AG.parse_call('<function=open_file>{"filename": "a.docx"}') == ("open_file", {"filename": "a.docx"})
    assert AG.parse_call('<function=open_file>{"filename": "a.docx"}<function>') == ("open_file", {"filename": "a.docx"})
    assert AG.parse_call("<function=list_files></function>") == ("list_files", {})
    assert AG.parse_call('<function=search_files>{"query": "a {b} \\"c\\""}</function>') == ("search_files", {"query": 'a {b} "c"'})
    assert AG.parse_call("The reference code is ABC-1234.") is None
    assert AG.parse_call('<function=open_file>{"filename": "a.do') is None


def test_call_cache_shares_one_call_between_threads():
    import threading
    import time

    class Slow:
        n = 0

        def messages(self, messages, max_tokens=0, temperature=0.0, stop=None):
            Slow.n += 1
            time.sleep(0.05)
            return f"answer {Slow.n}"

    cache = AG.CallCache(Path(tempfile.mkdtemp()) / "c.jsonl.gz", "m", Slow())
    out = []
    ts = [threading.Thread(target=lambda: out.append(cache.text([{"role": "user", "content": "same"}]))) for _ in range(8)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert Slow.n == 1 and len(set(out)) == 1 and len(out) == 8


def test_filename_search_finds_variant_and_typo_names():
    found = 0
    for u in [x for x in LEGIT if x["family"] in ("A-legit-variant", "A-legit-typo")]:
        named = u["query"]
        for t in AG.TEMPLATES:
            pre, post = t.split("{fn}")
            if named.startswith(pre) and named.endswith(post):
                named = named[len(pre):len(named) - len(post)]
                break
        hits = AG.Drive(AG.drive_files(BASE, u, "0"), "projection").search_name(named)
        found += bool(hits) and hits[0]["filename"] == u["target_ref"]
    assert found >= 18, found


def test_agent_loop_identical_under_projection_and_completion_kept():
    cache = AG.CallCache(Path(tempfile.mkdtemp()) / "c.jsonl.gz", "qwen25_7b", serving.make_llm("qwen25_7b"))
    pipe, rt = AG.make_pipeline(cache), AG.make_runtime()
    for u in LEAK[:20]:
        a, b = (AG.run_episode(pipe, rt, u, w, "projection", BASE, "m") for w in ("0", "1"))
        assert (a["text"], a["latency"]) == (b["text"], b["latency"]), u["uid"]
    raw = [AG.run_episode(pipe, rt, u, "0", "raw", BASE, "m")["success"] for u in LEGIT]
    proj = [AG.run_episode(pipe, rt, u, "0", "projection", BASE, "m")["success"] for u in LEGIT]
    assert raw == proj and sum(proj) >= 0.8 * len(proj)
    assert any(AG.run_episode(pipe, rt, u, "1", "raw", BASE, "m")["disclosed"] for u in LEAK[:10])
