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
