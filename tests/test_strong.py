"""Tests of src/strong.py (notebook 13): the vectorised certificate, job alignment, the D7 store, recomputed tables,
the sensitivity analysis, and the fine-tuning loop of D7 on a tiny local model (no download)."""
import gzip
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import attackers as AT  # noqa: E402
import gate as G  # noqa: E402
import strong as S  # noqa: E402


def test_vectorised_certificate_equals_gate():
    rng = np.random.default_rng(0)
    for _ in range(60):
        n = int(rng.integers(200, 3001))
        K = rng.integers(int(0.40 * n), int(0.62 * n), size=7)
        counts = {f"D{i}": (int(k), n) for i, k in enumerate(K, 1)}
        for dm in (0.05 / 24, 0.05 / 10, 0.05):
            assert S.eps_hat_vec(K, n, dm) == G.certified_bound(counts, dm)
        for eps in (0.05, 0.10, 0.2):
            assert S.p_config_vec(K, n, eps) == pytest.approx(G.config_p_value(counts, eps), rel=1e-12, abs=1e-15)


def _write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt") as fh:
        fh.writelines(json.dumps(r) + "\n" for r in rows)


def _fixture(tmp: Path, n_train: int = 6, n_cert: int = 8, leaky: bool = True):
    rows, hyp = [], {}
    for split, n in (("train", n_train), ("certify", n_cert)):
        for i in range(n):
            uid = f"{split}-{i:05d}"
            hyp[uid] = f"There is a restricted record about X{i}."
            for w in ("0", "1"):
                text = ("That record is restricted." if (leaky and w == "1") else "No accessible record matches.")
                rows.append({"uid": uid, "split": split, "kind": "leak", "turn": 1, "world": w, "query": f"Status of X{i}?", "text": text,
                             "family": "Q1", "secret": "S1"})
            rows.append({"uid": uid, "split": split, "kind": "leak", "turn": 2, "world": "1", "query": "x", "text": "y", "family": "Q1", "secret": "S1"})
    _write_jsonl(tmp / "rec" / "m1" / "C1.jsonl.gz", rows)
    picked = [r for r in rows if r["split"] == "certify" and r["turn"] == 1 and r["world"] == AT.world_pick(r["uid"])]
    sc = pd.DataFrame([{"uid": r["uid"], "world": int(r["world"]), "family": "Q1", "secret": "S1",
                        **{f"p_D{i}": 0.5 for i in range(1, 7)}} for r in picked])
    (tmp / "sc" / "m1").mkdir(parents=True, exist_ok=True)
    sc.to_csv(tmp / "sc" / "m1" / "C1.csv.gz", index=False)
    return hyp


def test_jobs_align_with_stored_scores(tmp_path):
    hyp = _fixture(tmp_path)
    jobs = list(S.certificate_jobs("cert", tmp_path / "rec", tmp_path / "sc", ["m1"], ["C1"], hyp, train_units=6))
    j = jobs[0]
    assert len(j["train"]) == 12 and set(j["train"]["world"]) == {"0", "1"}
    assert len(j["test"]) == 8 and (j["test"]["world"] == j["test"]["uid"].map(AT.world_pick)).all()
    assert j["train"]["hypothesis"].notna().all()
    with pytest.raises(AssertionError):           # the stored scores and the records must cover the same rows
        list(S.certificate_jobs("cert", tmp_path / "rec", tmp_path / "sc", ["m1"], ["C1"], hyp, train_units=7))


def test_store_resumes_and_reuses(tmp_path):
    hyp = _fixture(tmp_path)
    job = next(S.certificate_jobs("cert", tmp_path / "rec", tmp_path / "sc", ["m1"], ["C1"], hyp, train_units=6))
    store, d7 = S.D7Store(tmp_path / "d7"), S.StubD7()
    assert S.run_job(store, d7, job)["status"] == "fitted"
    assert S.run_job(store, d7, job)["status"] == "done before"
    twin = {**job, "group": "other"}
    assert S.run_job(store, d7, twin)["status"] == "reused"
    again = S.D7Store(tmp_path / "d7")            # a new session reads the index
    assert again.done("cert", "m1", "C1", S.job_key(job["train"], job["test"], d7.model_id, d7.hp))
    p = again.load("cert", "m1", "C1")
    assert len(p) == 8 and p["p_D7"].between(0, 1).all()


def test_merge_counts_and_tables(tmp_path):
    hyp = _fixture(tmp_path)
    job = next(S.certificate_jobs("cert", tmp_path / "rec", tmp_path / "sc", ["m1"], ["C1"], hyp, train_units=6))
    store = S.D7Store(tmp_path / "d7")
    S.run_job(store, S.StubD7(), job)
    m = S.merged(tmp_path / "sc" / "m1" / "C1.csv.gz", store.load("cert", "m1", "C1"))
    c = S.counts(m, S.ATT7)
    assert set(c) == set(S.ATT7) and all(n == 8 for _, n in c.values())
    t = S.certificate({"C1": c}, 0.10, 0.05, "m1")
    assert set(t["attacker"]) == set(S.ATT7) and t["eps_hat"].nunique() == 1
    rows = pd.DataFrame(S.attacker_rows("m1", "C1", c, 0.10, 0.05))
    assert len(rows) == 7 and rows["bound_at_delta"].nunique() == 1
    with pytest.raises(AssertionError):           # D7 must cover every stored row
        S.merged(tmp_path / "sc" / "m1" / "C1.csv.gz", store.load("cert", "m1", "C1").iloc[:-1])


def test_main_with_replaces_attacker_columns():
    main = pd.DataFrame([{"model": "m", "system": "s", "max_adv": 0.1, "max_adv_hi": 0.2, "worst_attacker": "D1", "bound_at_delta": 0.3, "other": 7}])
    att = pd.DataFrame([{"model": "m", "system": "s", "attacker": a, "adv": v, "adv_lo": 0.0, "adv_hi": v + 0.05, "bound_at_delta": 0.4}
                        for a, v in (("D1", 0.1), ("D7", 0.3))])
    out = S.main_with(main, att)
    assert out.loc[0, "max_adv"] == 0.3 and out.loc[0, "worst_attacker"] == "D7" and out.loc[0, "bound_at_delta"] == 0.4 and out.loc[0, "other"] == 7
    assert out.loc[0, "attackers_at_max"] == 1
    tied = att.assign(adv=0.023)                  # identical replies: every attacker at the same floor
    out = S.main_with(main, tied)
    assert out.loc[0, "worst_attacker"] == "tie" and out.loc[0, "attackers_at_max"] == 2


def test_sensitivity_full_size_equals_full_certificate():
    rng = np.random.default_rng(1)
    n = 400
    mats = {"L2-RT-pre": rng.random((n, 7)) < 0.5, "L2-RT-post": rng.random((n, 7)) < 0.58, "L3-RT-pre": rng.random((n, 7)) < 0.65}
    sens = S.sensitivity(mats, [100, 200, 400], reps=5, eps=0.10, delta_m=0.05 / 3)
    full = sens[sens["n"] == n]
    assert len(full) == 3 and set(full["rep"]) == {0}
    for cfg, C in mats.items():
        K = C.sum(axis=0)
        row = full[full["config"] == cfg].iloc[0]
        assert row["eps_hat"] == G.certified_bound({f"D{i}": (int(k), n) for i, k in enumerate(K)}, 0.05 / 3)
    assert set(sens["class"]) == {"pre", "post", "L3"} and (sens.groupby("n").size() == [15, 15, 3]).all()


def test_agent_hypotheses_from_manifest():
    rows = [{"uid": "ag-test-00000", "kind": "leak", "secret": "S1", "target": "a.pdf", "values": {"0": None, "1": "Tom"}},
            {"uid": "ag-test-00001", "kind": "leak", "secret": "S3", "target": "b.pdf", "values": {"0": "Ann", "1": "Tom"}},
            {"uid": "ag-legit-00000", "kind": "legit", "secret": None, "target": "c.pdf", "values": {}}]
    h = S.agent_hypotheses(rows)
    assert set(h) == {"ag-test-00000", "ag-test-00001"} and "a.pdf" in h["ag-test-00000"] and h["ag-test-00001"].endswith("owned by Tom.")


@pytest.mark.skipif(importlib.util.find_spec("torch") is None or importlib.util.find_spec("transformers") is None,
                    reason="torch and transformers are needed for the fine-tuning loop")
def test_fine_tuning_loop_on_a_tiny_local_model(tmp_path):
    from tokenizers import Tokenizer, models, normalizers, pre_tokenizers, processors
    from transformers import BertConfig, BertForSequenceClassification, PreTrainedTokenizerFast
    words = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "request", "reply", "status", "of", "x", "that", "record", "is", "restricted",
             "no", "accessible", "matches", "there", "a", "about", ":", ".", "?"]
    t = Tokenizer(models.WordLevel({w: i for i, w in enumerate(words)}, unk_token="[UNK]"))
    t.normalizer = normalizers.Lowercase()
    t.pre_tokenizer = pre_tokenizers.BertPreTokenizer()
    t.post_processor = processors.TemplateProcessing(single="[CLS] $A [SEP]", pair="[CLS] $A [SEP] $B:1 [SEP]:1",
                                                     special_tokens=[("[CLS]", 2), ("[SEP]", 3)])
    tok = PreTrainedTokenizerFast(tokenizer_object=t, unk_token="[UNK]", pad_token="[PAD]", cls_token="[CLS]", sep_token="[SEP]", mask_token="[MASK]")
    assert tok("that record")["input_ids"] == [2, 10, 11, 3]
    cfg = BertConfig(vocab_size=len(words), hidden_size=32, num_hidden_layers=2, num_attention_heads=2, intermediate_size=64,
                     max_position_embeddings=64, num_labels=3, id2label={0: "entailment", 1: "neutral", 2: "contradiction"},
                     label2id={"entailment": 0, "neutral": 1, "contradiction": 2}, initializer_range=0.2)
    BertForSequenceClassification(cfg).save_pretrained(tmp_path / "m")
    tok.save_pretrained(tmp_path / "m")
    rows = []
    for i in range(40):
        for w in ("0", "1"):
            rows.append({"uid": f"u{i}", "world": w, "query": "status of x?", "hypothesis": "there is a restricted record about x.",
                         "text": "that record is restricted." if w == "1" else "no accessible record matches."})
    df = pd.DataFrame(rows)
    d7 = S.FineTunedEntailment(model_id=str(tmp_path / "m"), device="cpu", epochs=15, lr=1e-3, batch=8, max_len=48)
    p, info = d7.fit_predict(df, df, seed=3)
    assert p.shape == (80,) and np.all((p >= 0) & (p <= 1))
    assert p[df["world"] == "1"].mean() > p[df["world"] == "0"].mean() + 0.3, info
    assert len(info["loss_by_epoch"]) == 15 and info["loss_by_epoch"][-1] < info["loss_by_epoch"][0]
    p2, _ = d7.fit_predict(df, df, seed=3)
    assert np.allclose(p, p2, atol=1e-5)          # a fit starts from a fresh copy of the base: same seed, same result
