"""CPU tests of the clarifier amendment of notebook 07d: a request that names a permitted record is never refused
outright. With the prediction set forced to {none of these}, a request with a permitted name match gets a list
question and a request matched by content only gets the universal reply; with the real decision rule no named
request is refused at the first turn at levels L1 to L3; the pre-filter low-view replies stay identical across worlds."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

import acl  # noqa: E402
import clarifier as CL  # noqa: E402
import config  # noqa: E402
import harness as H  # noqa: E402
import index as IX  # noqa: E402
import pipeline as PL  # noqa: E402
import world as W  # noqa: E402

POOL = W.load_pool(ROOT / "suite_data" / "does_not_exist.json")
PARAMS = {"cols": CL.SCORERS["evidence"], "weights": [-0.8, 3.7, 1.8, 0.9, 2.9, -1.9, 5.7], "qhat_by_k": {1: 0.02, 2: 0.10, 3: 0.75},
          "qhat_pooled": 0.7, "scorer": "evidence"}


class NoneOnly(PL.LoRe):
    """The configuration with its prediction set forced to {none of these}: isolates the amended branch."""

    def prediction_set(self, probs, k):
        return [len(probs) - 1]


def _named_request(unit, wk):
    world = unit["worlds"][wk]
    req = acl.person(world, unit["requester"])
    ex = IX.people_tokens(world)
    has_name = bool([t for t in IX.query_name_tokens(unit["query"]) if t not in ex])
    cands = CL.candidate_set(world, req["pid"], unit["query"])
    return has_name, bool(cands), CL.named_candidates(world, req["pid"], unit["query"])


def test_runtime_version():
    assert config.RUNTIME_VERSION == "3"


def test_set_none_named_request_is_asked_content_request_is_refused():
    sys_ = NoneOnly(PARAMS, None, "L2", "pre", "L2-RT-pre")
    named = content = 0
    for split, n in (("train", 120), ("legit", 60)):
        for i in range(n):
            u = W.build_unit(split, i, POOL)
            for wk in u["worlds"]:
                has_name, has_cands, is_named = _named_request(u, wk)
                if not has_name or not has_cands:
                    continue
                first = H.run_task(sys_, u, wk, None)[0]
                if is_named:
                    assert first["reply_kind"] == "ask", (u["uid"], wk, first["text"])
                    named += 1
                else:
                    assert first["reply_kind"] == "none", (u["uid"], wk, first["text"])
                    content += 1
    assert named > 0 and content > 0, (named, content)


def test_no_named_request_refused_at_first_turn():
    for level in ("L1", "L2", "L3"):
        sys_ = PL.LoRe(PARAMS, None, level, "pre", PL.config_name(level, "RT", "pre"))
        for split, n in (("train", 60), ("legit", 40), ("auth", 30)):
            for i in range(n):
                u = W.build_unit(split, i, POOL)
                for wk in u["worlds"]:
                    first = H.run_task(sys_, u, wk, None)[0]
                    if first["reply_kind"] == "none":
                        assert not _named_request(u, wk)[2], (level, u["uid"], wk)


def test_pre_filter_identical_across_worlds_with_the_amended_branch():
    for level in ("L1", "L2"):
        sys_ = NoneOnly(PARAMS, None, level, "pre", PL.config_name(level, "RT", "pre"))
        by = {}
        for i in range(60):
            u = W.build_unit("train", i, POOL)
            for wk in u["worlds"]:
                for r in H.run_task(sys_, u, wk, None):
                    by.setdefault((u["uid"], r["turn"]), {})[wk] = (r["text"], r["status"], r["options"], r["n_chars"], r["latency"])
        assert all(v["0"] == v["1"] for v in by.values() if len(v) == 2), level
