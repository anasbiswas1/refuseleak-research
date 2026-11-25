"""Tests of src/session.py (notebook 15): session counts, the session certificate, the check against notebook 09's
table, and the leak by query family."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import attackers as AT  # noqa: E402
import gate as G  # noqa: E402
import paper_figures as F  # noqa: E402
import session as SE  # noqa: E402


def _scores(tmp: Path):
    rng = np.random.default_rng(0)
    root = tmp / "09_scores"
    for model in ("qwen25_7b", "llama31_8b"):
        (root / model).mkdir(parents=True)
        for system, policies in (("L2-RT-pre", ("A1", "A2")), ("B1", ("A1",))):
            for pol in policies:
                rows = []
                pools = ("S1", "S3") if pol == "A2" else ("S3",)
                for pool in pools:
                    for i in range(400):
                        w = int(rng.integers(2))
                        if system == "L2-RT-pre":
                            ps = dict(p_bow=0.5, p_nli=0.5, p_side=0.5, p_stack=0.5)            # identical transcripts: ties
                        else:
                            ps = {k: (0.9 if w else 0.1) if rng.random() < 0.8 else 0.5 for k in ("p_bow", "p_nli", "p_side", "p_stack")}
                        rows.append({"uid": f"test-{i:05d}", "world": w, "secret": pool, **ps})
                pd.DataFrame(rows).to_csv(root / model / f"{system}_{pol}.csv.gz", index=False)
    return root


def test_session_counts_and_certificate(tmp_path):
    root = _scores(tmp_path)
    c = SE.session_counts(root)
    assert len(c) == 2 * (3 * 4 + 1 * 4)                       # per model: SameView A1 (1 pool) + A2 (2 pools), B1 A1; 4 learners each
    att, cert = SE.session_certificate(c, 0.10, 0.05, {"qwen25_7b": "L2-RT-pre", "llama31_8b": "L2-RT-pre"})
    assert set(cert["role"]) == {"deployed", "control"} and len(cert) == 4
    dep = cert[cert.role == "deployed"]
    assert (dep["attackers"] == 12).all() and (dep["sessions"] == 1200).all()
    ctl = cert[cert.role == "control"]
    assert (ctl["eps_hat"] > 0.3).all() and not ctl["certified"].any()
    # the deployed configuration's family p-value is the gate's value on the same counts
    g = c[(c.model == "qwen25_7b") & (c.system == "L2-RT-pre")]
    fam = {f"{r.policy}-{r.pool}-{r.learner}": (int(r.correct), int(r.n)) for r in g.itertuples()}
    assert dep[dep.model == "qwen25_7b"].eps_hat.iloc[0] == G.certified_bound(fam, 0.05)
    assert att["p_attacker"].between(0, 1).all() and (att["adv_hi"] >= att["adv"]).all()


def test_check_against_09_table(tmp_path):
    root = _scores(tmp_path)
    c = SE.session_counts(root)
    a09 = c.rename(columns={"policy": "attacker", "pool": "secret"}).assign(k=3)
    a09 = pd.concat([a09.assign(k=1, correct=0), a09], ignore_index=True)    # an earlier turn with other counts
    chk = SE.check_against_09(c, a09)
    assert chk["rows"] == len(c) == chk["identical"]


def test_family_table_and_figure(tmp_path):
    rng = np.random.default_rng(1)
    rows = []
    for i in range(600):
        uid = f"test-{i:05d}"
        for w in ("0", "1"):
            fam = ["Q1", "Q6", "Q7"][i % 3]
            leak = 0.95 if (fam == "Q7" and w == "1") else (0.05 if fam == "Q7" else 0.5)
            rows.append({"uid": uid, "world": w, "family": fam, "secret": "S1", **{f"p_D{k}": 0.5 for k in range(1, 7)}, "p_D7": leak})
    df = pd.DataFrame(rows)
    df.drop(columns=["p_D7"]).to_csv(tmp_path / "s.csv.gz", index=False)
    d7 = df[df.world == df.uid.map(AT.world_pick)][["uid", "world", "p_D7"]]
    t = pd.DataFrame(SE.family_table(tmp_path / "s.csv.gz", d7, "qwen25_7b", "B1", ["D1", "D2", "D3", "D4", "D5", "D6", "D7"]))
    assert set(t["family"]) == {"Q1", "Q6", "Q7"} and t["n"].sum() == 600
    assert t[t.family == "Q7"].adv.iloc[0] > 0.9 and (t.attacker == "D7").all()      # the strongest attacker is chosen once
    assert (t[t.family != "Q7"].adv_lo == 0).all()
    fam = pd.concat([t.assign(system=s_, model=m) for s_ in ("B0", "B1", "L2-RT-pre") for m in F.MODELS], ignore_index=True)
    r = F.figure10(tmp_path, fam)
    assert r["code_keys"] == [] and r["png_pixels"][0] == round(F.FULL_W * F.DPI)


def test_session_table_names(tmp_path):
    pd.DataFrame([{"model": "qwen25_7b", "system": "L2-RT-pre", "role": "deployed", "attackers": 24, "sessions": 12000, "max_adv": 0.039,
                   "max_adv_hi": 0.08, "p_system": 0.001, "eps_hat": 0.08, "certified": True},
                  {"model": "qwen25_7b", "system": "B1", "role": "control", "attackers": 8, "sessions": 600, "max_adv": 0.9,
                   "max_adv_hi": 0.95, "p_system": 1.0, "eps_hat": 0.95, "certified": False}]).to_csv(tmp_path / "15_session_certificate.csv", index=False)
    t = F.session_table(tmp_path)
    assert list(t["System"]) == ["SameView (selected)", "B1 Privacy prompt"] and list(t["Certified at 0.10"]) == ["yes", "no"]
    assert not [c for c in t.columns if F.CODE_KEY.search(c)]
