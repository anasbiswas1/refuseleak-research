"""Tests of the scale check (notebook 14): model ids, the judge of each responder, D7 jobs from in-memory frames,
the scale table."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import attackers as AT  # noqa: E402
import config  # noqa: E402
import judge as J  # noqa: E402
import paper_figures as F  # noqa: E402
import serving  # noqa: E402
import strong as S  # noqa: E402


def test_model_ids_and_judges():
    assert serving.hf_id("qwen25_7b") == config.MODELS["qwen25_7b"]
    assert serving.hf_id("qwen25_14b") == "Qwen/Qwen2.5-14B-Instruct-AWQ"
    assert "qwen25_14b" not in config.MODELS                        # the main grid is unchanged
    assert J.other_model("qwen25_7b") == "llama31_8b" and J.other_model("llama31_8b") == "qwen25_7b"
    assert J.other_model("qwen25_14b") == "llama31_8b"
    with pytest.raises(KeyError):
        serving.hf_id("unknown")


def _frames(n_units=6):
    tr, te = [], []
    for i in range(n_units):
        uid = f"test-{i:05d}"
        for w in ("0", "1"):
            tr.append({"uid": f"train-{i:05d}", "world": w, "split": "train", "query": "q", "text": f"t{w}", "hypothesis": "h"})
            row = {"uid": uid, "world": w, "split": "test", "query": "q", "text": f"t{w}", "hypothesis": "h"}
            if w == AT.world_pick(uid):
                te.append({**row, **{f"p_D{k}": 0.5 for k in range(1, 7)}})
    return pd.DataFrame(tr), pd.DataFrame(te)


def test_frame_job_and_merge(tmp_path):
    tr, scored = _frames()
    job = S.frame_job("scale", "qwen25_14b", "B0", tr, scored)
    assert len(job["train"]) == 12 and len(job["test"]) == 6
    store = S.D7Store(tmp_path / "d7")
    assert S.run_job(store, S.StubD7(), job)["status"] == "fitted"
    m = S.merge_frame(scored, store.load("scale", "qwen25_14b", "B0"))
    c = S.counts(m, S.ATT7)
    assert set(c) == set(S.ATT7) and all(n == 6 for _, n in c.values())
    with pytest.raises(AssertionError):           # test rows must be the picked rows
        flip = scored.assign(world=scored["world"].map({"0": "1", "1": "0"}))
        S.frame_job("scale", "qwen25_14b", "B0", tr, flip)


def test_scale_table(tmp_path):
    base = pd.DataFrame([{"model": m, "system": s, "max_adv": 0.3 if s == "B0" else 0.02, "resolved_legit": 0.9}
                         for m in config.MODELS for s in ("B0", "L2-RT-pre")])
    new = pd.DataFrame([{"model": "qwen25_14b", "system": s, "max_adv": 0.25 if s == "B0" else 0.01, "resolved_legit": 0.95} for s in ("B0", "L2-RT-pre")])
    base.to_csv(tmp_path / "13_main_meridian.csv", index=False)
    new.to_csv(tmp_path / "14_main.csv", index=False)
    t = F.scale_table(tmp_path)
    assert list(t["System"]) == ["B0 Privileged agent", "LoRe (selected)"]
    assert t.loc[0, "Qwen2.5-14B-Instruct (4-bit): largest attacker advantage"] == 0.25
    assert not [c for c in t.columns if F.CODE_KEY.search(c)]
    assert np.isclose(t.loc[1, "Qwen2.5-7B-Instruct: resolved"], 0.9)
