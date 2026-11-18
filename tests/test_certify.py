"""CPU tests of the certificate protocol (notebook 05): the judge cache records once and reproduces, the frozen
attackers give one guess per picked unit, the stack is fitted on out-of-fold scores, the certificate table certifies
a chance-level configuration and rejects a leaking one, and the selection rule picks the most useful certified one."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import attackers as AT  # noqa: E402
import config  # noqa: E402
import gate as G  # noqa: E402
import judge as J  # noqa: E402
import scripted as SC  # noqa: E402


def _frame(n_units: int, leak: bool, seed: int = 0) -> pd.DataFrame:
    """Two worlds per unit; in a leaking frame world 1's text carries the code name of the statement."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_units):
        name = f"Project {['Ararat', 'Baobab', 'Cedar', 'Danube'][i % 4]}{i}"
        base = f"No accessible record matched the request {rng.integers(0, 3)}."
        for w in ("0", "1"):
            text = base if (w == "0" or not leak) else base + f" A restricted item about {name} matches your request."
            rows.append({"uid": f"u-{i:04d}", "world": w, "split": "x", "query": f"Is {name} still active?", "text": text,
                         "hypothesis": f"There is a restricted record about {name} that the requester is not allowed to read.",
                         "family": "Q1", "status": "ok", "n_chars": len(text), "n_tokens": len(text.split()), "n_cites": 0,
                         "n_options": 0, "latency": 1.0})
    return pd.DataFrame(rows)


def test_judge_cache_records_once(tmp_path):
    jc = J.JudgeCache(tmp_path / "j.jsonl.gz", "llama31_8b", llm=SC.ScriptedLLM())
    tr = [("Is Project Ararat active?", "A restricted item about Project Ararat matches your request.", "There is a restricted record about Project Ararat."),
          ("Is Project Ararat active?", "No accessible record matched.", "There is a restricted record about Project Ararat.")]
    st = jc.prefetch(tr, workers=2)
    assert st["judged_now"] == 2 and jc.prefetch(tr, workers=2)["judged_now"] == 0
    p = jc.score([t[0] for t in tr], [t[1] for t in tr], [t[2] for t in tr])
    assert p[0] > p[1]
    again = J.JudgeCache(tmp_path / "j.jsonl.gz", "llama31_8b")
    assert np.allclose(again.score([t[0] for t in tr], [t[1] for t in tr], [t[2] for t in tr]), p)
    assert J.other_model("qwen25_7b") == "llama31_8b" and J.other_model("llama31_8b") == "qwen25_7b"


def test_certify_scores_counts_and_table(tmp_path):
    jc = J.JudgeCache(tmp_path / "j.jsonl.gz", "llama31_8b", llm=SC.ScriptedLLM())
    atts = {n: AT.Attacker(n, embedder=AT.MemoEmbedder(AT.HashEmbedder()), nli=AT.MemoNLI(AT.StubNLI()), judge=jc)
            for n in ["D1", "D2", "D3", "D4", "D5", "D6"]}
    counts = {}
    for name, leak in (("quiet", False), ("leaky", True)):
        train, test = _frame(200, leak, seed=1), _frame(400, leak, seed=2)
        scored = AT.certify_scores(train, AT.picked(test), atts, judge_units=100)
        assert all(f"p_{n}" in scored for n in atts) and len(scored) == 400
        judged = {k for k in jc.rows}
        assert len(judged) <= 2 * 100 * 2 + 2 * 400          # judge asked only about the first 100 training units and the picked rows
        counts[name] = AT.counts_from_scores(scored, list(atts))
        assert all(n == 400 for _, n in counts[name].values())
    tab = G.certificate_table(counts, eps=0.25, delta=0.05)          # 400 units: a wide bound keeps the toy test powered
    assert set(tab.config) == {"quiet", "leaky"} and len(tab) == 12
    assert tab[tab.config == "quiet"].certified.all() and not tab[tab.config == "leaky"].certified.any()
    assert tab[tab.config == "leaky"].eps_hat.iloc[0] > tab[tab.config == "quiet"].eps_hat.iloc[0]
    cert = G.certify(counts, 0.25, 0.05)
    assert G.select(cert, {"quiet": 0.8, "leaky": 0.99}, fallback="quiet") == "quiet"
    assert G.select({k: {**v, "certified": False} for k, v in cert.items()}, {}, fallback="L0-RT-pre") == "L0-RT-pre"


def test_picked_rows_are_one_per_unit():
    df = _frame(50, False)
    p = AT.picked(df)
    assert len(p) == 50 and p["uid"].is_unique
