"""Tests of src/mechanism.py (notebook 17): paired world comparison of recorded replies, named features, phrase choice, Figure 11."""
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import mechanism as M  # noqa: E402
import paper_figures as F  # noqa: E402

REFUSAL = "I could not find a matching record you have access to. If you have a link or a reference code, share it and I will look again."
ANSWER = "According to the Indus supply agreement [MH-2966], the contract is managed by Theo Silva (HR)."


def write_records(root: Path, model: str, n_units: int = 40):
    rows = []
    for split in ("train", "test"):
        for i in range(n_units):
            uid = f"{split}-{i:05d}"
            secret = ["S1", "S2", "S3"][i % 3]
            for w in ("0", "1"):
                text = REFUSAL if (w == "1" or i % 4 == 0) else ANSWER                  # world 1 refuses; world 0 answers three times in four
                rows.append({"uid": uid, "split": split, "turn": 1, "world": w, "secret": secret, "system": "B1", "text": text,
                             "n_tokens": 30 if text == REFUSAL else 40, "n_cites": 0 if text == REFUSAL else 1})
    (root / model).mkdir(parents=True)
    with gzip.open(root / model / "B1.jsonl.gz", "wt") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def test_paired_lengths_and_features(tmp_path):
    write_records(tmp_path, "claude_haiku_55")
    df = M.load_records(tmp_path, "claude_haiku_55", "B1", split="test")
    assert len(df) == 80 and set(df["world"]) == {"0", "1"}
    pp = M.paired(df)
    assert len(pp) == 40 and set(pp.columns) >= {"tokens_0", "tokens_1", "cites_0", "cites_1", "text_0", "text_1", "secret"}
    L = pd.DataFrame(M.length_rows(pp, "claude_haiku_55", "B1"))
    a = L[L.secret == "all"].iloc[0]
    assert a["n"] == 40 and abs(a["tokens_diff"] - (-10 * 0.75)) < 1e-9 and abs(a["cites_diff"] + 0.75) < 1e-9
    assert a["tokens_diff_lo"] < a["tokens_diff"] < a["tokens_diff_hi"] and abs(a["share_same_text"] - 0.25) < 1e-9
    assert set(L.secret) == {"all", "S1", "S2", "S3"}
    Fe = pd.DataFrame(M.feature_rows(pp, df, "claude_haiku_55", "B1"))
    assert list(Fe.feature) == list(M.FEATURES) and (Fe.n == 40).all()
    ref = Fe.set_index("feature")
    assert ref.loc["refusal", "share_world1"] == 1.0 and abs(ref.loc["refusal", "share_world0"] - 0.25) < 1e-9
    assert ref.loc["cites", "share_world1"] == 0.0 and abs(ref.loc["cites", "diff"] + 0.75) < 1e-9
    assert ref.loc["access", "share_world1"] == 1.0 and ref.loc["share", "share_world1"] == 0.0
    assert (Fe.diff_lo <= Fe["diff"]).all() and (Fe["diff"] <= Fe.diff_hi).all()


def test_features_patterns():
    f = M.features_of("I can't share that record; it is restricted to named staff.", 0)
    assert f["share"] and f["access"] and not f["refusal"] and not f["cites"]
    f = M.features_of("I couldn't find a matching record. Send a reference code and I will check.", 2)
    assert f["refusal"] and f["code"] and f["cites"] and not f["share"]


def test_phrases_and_choice(tmp_path):
    ph = M.phrases_of("I could not find the record [MH-2966] of the agreement.")
    assert "could not find" in ph and "agreement" in ph and "mh" not in ph and "of the" not in ph
    write_records(tmp_path, "claude_haiku_55")
    train = M.load_records(tmp_path, "claude_haiku_55", "B1", split="train")
    chosen = M.choose_phrases(train, k=4)
    assert 1 <= len(chosen) <= 4 and all(p not in ("the", "of the") for p in chosen)
    assert not any(a != b and (a in b or b in a) for a in chosen for b in chosen)         # no phrase nested in another
    shares = M.phrase_shares(train, chosen)
    assert list(shares.phrase) == chosen and (shares.share_world1_lo <= shares.share_world1).all()
    assert (shares.n_world0 == 40).all() and (shares.n_world1 == 40).all()


def test_mechanism_end_to_end_and_figure(tmp_path):
    for m in ("claude_haiku_55", "claude_sonnet_55"):
        write_records(tmp_path / "records", m)
    L, Fe, P, chosen = M.mechanism(tmp_path / "records", {"claude_haiku_55": "Claude Haiku 5.5", "claude_sonnet_55": "Claude Sonnet 5.5"}, k=5)
    assert set(L.model) == {"claude_haiku_55", "claude_sonnet_55"} and len(Fe) == 2 * len(M.FEATURES) and set(P.model) == set(L.model)
    r = F.figure11(tmp_path, L, Fe)
    assert r["name"] == "figure11_mechanism" and r["code_keys"] == [] and r["png_pixels"][0] == round(F.FULL_W * F.DPI)
    assert (tmp_path / "figure11_mechanism.pdf").exists()
    assert "figure11_mechanism" in F.CAPTIONS and "Figure 11" in (F.write_captions(tmp_path).read_text())
