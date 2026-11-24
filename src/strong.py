"""Notebook 13: a stronger declared attacker (D7) and the certificate's sensitivity to the number of certify units.

D7 is the entailment model of D3 fine-tuned end to end on one system's training observations. Its input is the
requester's request and the reply as the premise and the statement of the protected fact as the hypothesis; the
probability of world 1 is the softmax of the pretrained head's entailment logit against the log-sum-exp of the other
two logits, so training starts from the zero-shot entailment judgement and sharpens it. Like D1, D2, D3 and D5 it
trains on both worlds of every training unit, is frozen, and guesses one hash-picked world per certify or test unit.
It is not stacked into D6: that would need five more fine-tunes per system for out-of-fold scores.

The D1 to D6 scores of every system were stored per unit by notebooks 04b, 06, 07c, 07d and 08b. D7 is scored on
exactly those rows and merged in, and every table that used the declared family is recomputed with seven attackers.
The six-attacker tables are recomputed from the same stored scores first and must equal the committed ones.

With REFUSELEAK_DRY_RUN=1, D7 is a deterministic stand-in (hashed words and logistic regression; not a result source).
"""
from __future__ import annotations

import copy
import contextlib
import gzip
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom
from sklearn.linear_model import LogisticRegression

import attackers as AT
import config
import gate as G
from metrics import advantage
from serving import DRY_RUN

D7_HP = {"epochs": 3, "lr": 2e-5, "batch": 32, "max_len": 256, "warmup": 0.1, "weight_decay": 0.01, "clip": 1.0, "group": 50}
ATT6 = ["D1", "D2", "D3", "D4", "D5", "D6"]
ATT7 = ATT6 + ["D7"]
EPS_GRID = np.round(np.arange(0.01, 1.0001, 0.01), 2)


# ----------------------------------------------------------------------------- D7 inputs
def premise(query: str, text: str) -> str:
    return f"Request: {str(query).strip()}\nReply: {str(text).strip()}"


def d7_pairs(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    return [premise(q, t) for q, t in zip(df["query"], df["text"])], [str(h) for h in df["hypothesis"]]


def job_key(train: pd.DataFrame, test: pd.DataFrame, model_id: str, hp: dict) -> str:
    """Content hash of a fit: identical training and test inputs give the same key, the same seed and the same
    predictions, so a fit is never run twice (template systems give the same replies under both model tags)."""
    tp, th = d7_pairs(train)
    sp, sh = d7_pairs(test)
    payload = json.dumps([model_id, hp, tp, th, train["world"].astype(int).tolist(), sp, sh])
    return hashlib.sha1(payload.encode()).hexdigest()


# ----------------------------------------------------------------------------- D7: the fine-tuned entailment model
class FineTunedEntailment:
    """D7 on a GPU. The base model and tokenizer are loaded once; every fit starts from a fresh copy of the base."""

    def __init__(self, model_id: str = config.NLI_MODEL, device: str = "cuda", **hp):
        self.model_id, self.device, self.hp = model_id, device, {**D7_HP, **hp}
        self.tok = self.base = None
        self.entail, self.others = None, None

    def _load(self):
        if self.base is None:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            self.tok = AutoTokenizer.from_pretrained(self.model_id)
            self.base = AutoModelForSequenceClassification.from_pretrained(self.model_id).float().eval()   # fp32 master weights
            labels = {int(i): str(l).lower() for i, l in self.base.config.id2label.items()}
            self.entail = next(i for i, l in labels.items() if l.startswith("entail"))
            self.others = [i for i in sorted(labels) if i != self.entail]

    def _encode(self, prem: list[str], hyp: list[str]) -> list[dict]:
        enc = self.tok(prem, hyp, truncation="only_first", max_length=self.hp["max_len"])
        keys = [k for k in ("input_ids", "token_type_ids", "attention_mask") if k in enc]
        return [{k: enc[k][i] for k in keys} for i in range(len(prem))]

    def _batches(self, rng, lens: np.ndarray) -> list[np.ndarray]:
        """One epoch of training batches: a random order, sorted by length within groups of `group` batches (less
        padding), then the batches shuffled."""
        b, g = self.hp["batch"], max(1, int(self.hp["group"]))
        perm = rng.permutation(len(lens))
        out = []
        for c in range(0, len(perm), b * g):
            idx = perm[c:c + b * g]
            idx = idx[np.argsort(lens[idx], kind="stable")]
            out += [idx[s:s + b] for s in range(0, len(idx), b)]
        return [out[i] for i in rng.permutation(len(out))]

    def _two_class(self, logits):
        import torch
        return torch.stack([torch.logsumexp(logits[:, self.others], dim=1), logits[:, self.entail]], dim=1)

    def _autocast(self):
        import torch
        if str(self.device).startswith("cuda") and torch.cuda.is_available() and torch.cuda.is_bf16_supported():
            return torch.autocast("cuda", dtype=torch.bfloat16)
        return contextlib.nullcontext()

    def _probs(self, model, feats: list[dict], batch: int = 128) -> np.ndarray:
        import torch
        order = np.argsort([len(f["input_ids"]) for f in feats], kind="stable")
        out = np.zeros(len(feats))
        model.eval()
        with torch.no_grad():
            for s in range(0, len(order), batch):
                idx = order[s:s + batch]
                enc = self.tok.pad([feats[i] for i in idx], return_tensors="pt").to(self.device)
                with self._autocast():
                    logits = model(**enc).logits
                out[idx] = torch.softmax(self._two_class(logits.float()), dim=1)[:, 1].cpu().numpy()
        return out

    def fit_predict(self, train: pd.DataFrame, test: pd.DataFrame, seed: int = 0) -> tuple[np.ndarray, dict]:
        import torch
        import torch.nn.functional as F
        self._load()
        t0 = time.time()
        torch.manual_seed(seed)
        rng = np.random.default_rng(seed)
        hp = self.hp
        ftr, fte = self._encode(*d7_pairs(train)), self._encode(*d7_pairs(test))
        y = torch.tensor(train["world"].astype(int).to_numpy(), dtype=torch.long)
        model = copy.deepcopy(self.base).to(self.device)
        decay = [p for n, p in model.named_parameters() if not any(k in n for k in ("bias", "LayerNorm", "layernorm"))]
        no_decay = [p for n, p in model.named_parameters() if any(k in n for k in ("bias", "LayerNorm", "layernorm"))]
        opt = torch.optim.AdamW([{"params": decay, "weight_decay": hp["weight_decay"]}, {"params": no_decay, "weight_decay": 0.0}], lr=hp["lr"])
        lens = np.array([len(f["input_ids"]) for f in ftr])
        epochs = [self._batches(rng, lens) for _ in range(hp["epochs"])]
        steps = sum(len(b) for b in epochs)
        warm = max(1, int(hp["warmup"] * steps))
        sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (s + 1) / warm if s < warm else max(0.0, (steps - s) / max(1, steps - warm)))
        losses = []
        model.train()
        for batches in epochs:
            tot = 0.0
            for idx in batches:
                enc = self.tok.pad([ftr[i] for i in idx], return_tensors="pt").to(self.device)
                with self._autocast():
                    logits = model(**enc).logits
                loss = F.cross_entropy(self._two_class(logits.float()), y[idx].to(self.device))
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), hp["clip"])
                opt.step()
                sched.step()
                tot += float(loss.detach()) * len(idx)
            losses.append(tot / len(ftr))
        p = self._probs(model, fte)
        del model, opt
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return p, {"seconds": round(time.time() - t0, 1), "steps": steps, "loss_by_epoch": [round(v, 4) for v in losses],
                   "n_train": len(ftr), "n_test": len(fte)}


class StubD7:
    """Dry-run stand-in: hashed words of premise and hypothesis, logistic regression. Not a result source."""

    model_id = "stand-in"
    hp = {"stand_in": True}

    def fit_predict(self, train: pd.DataFrame, test: pd.DataFrame, seed: int = 0) -> tuple[np.ndarray, dict]:
        t0 = time.time()
        emb = AT.HashEmbedder(256)
        Xtr = emb.encode([a + " || " + b for a, b in zip(*d7_pairs(train))])
        Xte = emb.encode([a + " || " + b for a, b in zip(*d7_pairs(test))])
        clf = LogisticRegression(max_iter=1000).fit(Xtr, train["world"].astype(int).to_numpy())
        return clf.predict_proba(Xte)[:, 1], {"seconds": round(time.time() - t0, 2), "stand_in": True, "n_train": len(train), "n_test": len(test)}


def make_d7(device: str = "cuda"):
    return StubD7() if DRY_RUN else FineTunedEntailment(device=device)


# ----------------------------------------------------------------------------- the store of D7 predictions (resumable)
class D7Store:
    """One CSV per (group, model, system) with uid, world and p_D7, and an index line per finished fit."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "index.jsonl"
        self.index: dict[tuple, dict] = {}
        if self.index_path.exists():
            for line in self.index_path.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    self.index[(r["group"], r["model"], r["system"])] = r

    def path(self, group: str, model: str, system: str) -> Path:
        return self.root / group / model / f"{system}.csv.gz"

    def done(self, group: str, model: str, system: str, key: str) -> bool:
        r = self.index.get((group, model, system))
        return bool(r and r["key"] == key and self.path(group, model, system).exists())

    def by_key(self, key: str) -> Path | None:
        for (g, m, s), r in self.index.items():
            if r["key"] == key and self.path(g, m, s).exists():
                return self.path(g, m, s)
        return None

    def put(self, group: str, model: str, system: str, key: str, frame: pd.DataFrame, info: dict):
        p = self.path(group, model, system)
        p.parent.mkdir(parents=True, exist_ok=True)
        frame[["uid", "world", "p_D7"]].to_csv(p, index=False)
        r = {"group": group, "model": model, "system": system, "key": key, **info}
        self.index[(group, model, system)] = r
        with open(self.index_path, "a") as fh:
            fh.write(json.dumps(r) + "\n")

    def load(self, group: str, model: str, system: str) -> pd.DataFrame:
        d = pd.read_csv(self.path(group, model, system))
        return d.assign(world=d["world"].astype(str))


def run_job(store: D7Store, d7, job: dict) -> dict:
    """Fits D7 for one job unless its predictions exist; reuses the predictions of an identical fit."""
    g, m, s, tr, te = job["group"], job["model"], job["system"], job["train"], job["test"]
    key = job_key(tr, te, getattr(d7, "model_id", "?"), getattr(d7, "hp", {}))
    if store.done(g, m, s, key):
        return {"status": "done before", **store.index[(g, m, s)]}
    src = store.by_key(key)
    if src is not None:
        prev = pd.read_csv(src).assign(world=lambda d: d["world"].astype(str))
        frame = te[["uid", "world"]].merge(prev, on=["uid", "world"], how="left", validate="one_to_one")
        assert frame["p_D7"].notna().all(), (g, m, s, "reused predictions do not cover the test rows")
        info = {"reused_from": str(src.relative_to(store.root)), "n_train": len(tr), "n_test": len(te), "seconds": 0.0}
    else:
        p, info = d7.fit_predict(tr, te, seed=int(key[:8], 16))
        frame = te[["uid", "world"]].assign(p_D7=p)
    store.put(g, m, s, key, frame, info)
    return {"status": "fitted" if src is None else "reused", **info}


# ----------------------------------------------------------------------------- jobs: training and test rows of every system
def read_jsonl(path: Path) -> list[dict]:
    if not Path(path).exists():
        return []
    with gzip.open(path, "rt") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def leak_frame(rows: list[dict], hyp: dict[str, str]) -> pd.DataFrame:
    """First-turn rows of leak units with the unit's hypothesis (as attackers.prepare, from a hypothesis map)."""
    df = pd.DataFrame([r for r in rows if r.get("kind") == "leak" and int(r.get("turn", 0)) == 1])
    if df.empty:
        return df
    df["world"] = df["world"].astype(str)
    df["hypothesis"] = df["uid"].map(hyp)
    assert df["hypothesis"].notna().all(), "a leak row without a hypothesis"
    return df


def scored_rows(score_file: Path) -> pd.DataFrame:
    s = pd.read_csv(score_file)
    return s.assign(world=s["world"].astype(str), uid=s["uid"].astype(str))


def make_job(group: str, model: str, system: str, frame: pd.DataFrame, train_mask, test_split: str, score_file: Path,
             expect_train: int | None = None) -> dict:
    """Training rows: both worlds of the training units. Test rows: exactly the rows the stored D1 to D6 scores cover
    (one hash-picked world per unit)."""
    keep = ["uid", "world", "split", "query", "text", "hypothesis"]
    tr = frame.loc[train_mask, keep].reset_index(drop=True)
    sc = scored_rows(score_file)
    te = frame.loc[frame["split"] == test_split, keep].merge(sc[["uid", "world"]], on=["uid", "world"], how="inner").reset_index(drop=True)
    assert len(te) == len(sc), (group, model, system, "test rows", len(te), "stored scores", len(sc))
    assert set(tr["world"]) == {"0", "1"} and tr.groupby("uid").size().eq(2).all(), (group, model, system, "training units need both worlds")
    if expect_train is not None:
        assert len(tr) == expect_train, (group, model, system, "training rows", len(tr), expect_train)
    return {"group": group, "model": model, "system": system, "train": tr, "test": te, "score_file": score_file}


def certificate_jobs(group: str, rec_root: Path, score_root: Path, models, configs, hyp: dict, train_units: int):
    for model in models:
        for cfg in configs:
            f = leak_frame([r for r in read_jsonl(rec_root / model / f"{cfg}.jsonl.gz") if r["split"] in ("train", "certify")], hyp)
            yield make_job(group, model, cfg, f, f["split"] == "train", "certify", score_root / model / f"{cfg}.csv.gz", 2 * train_units)


def heldout_jobs(group: str, base_root: Path, base_scores: Path, lam_root: Path, lam_scores: Path, models, systems, lam: str,
                 hyp: dict, train_uids: set):
    for model in models:
        for system in systems + [lam]:
            root, scores = (lam_root, lam_scores) if system == lam else (base_root, base_scores)
            rows = [r for r in read_jsonl(root / model / f"{system}.jsonl.gz") if r["split"] == "test" or (r["split"] == "train" and r["uid"] in train_uids)]
            f = leak_frame(rows, hyp)
            yield make_job(group, model, system, f, f["split"] == "train", "test", scores / model / f"{system}.csv.gz", 2 * len(train_uids))


def agent_jobs(group: str, rec_root: Path, score_root: Path, models, arms, hyp: dict, train_units: int):
    for model in models:
        rows = read_jsonl(rec_root / f"{model}.jsonl.gz")
        for arm in arms:
            f = leak_frame([r for r in rows if r["system"] == arm and r["split"] in ("train", "test")], hyp)
            yield make_job(group, model, arm, f, f["split"] == "train", "test", score_root / model / f"{arm}.csv.gz", 2 * train_units)


def agent_hypotheses(manifest_rows: list[dict]) -> dict[str, str]:
    """The agent's protected statements from the committed manifests (the file name and its owner), as in notebook 08b."""
    out = {}
    for r in manifest_rows:
        if r["kind"] == "leak":
            out[r["uid"]] = AT.hypothesis({"domain": "agent", "secret": r["secret"], "codename": r["target"], "values": r["values"]})
    return out


# ----------------------------------------------------------------------------- recomputed tables
def merged(score_file: Path, d7: pd.DataFrame | None) -> pd.DataFrame:
    s = scored_rows(score_file)
    return s if d7 is None else merge_frame(s, d7, str(score_file))


def merge_frame(scored: pd.DataFrame, d7: pd.DataFrame, label: str = "") -> pd.DataFrame:
    """The stored D1 to D6 scores with D7's probability on the same rows (every row must be covered)."""
    s = scored.assign(world=scored["world"].astype(str), uid=scored["uid"].astype(str))
    m = s.merge(d7[["uid", "world", "p_D7"]].assign(world=lambda d: d["world"].astype(str)), on=["uid", "world"], how="left", validate="one_to_one")
    assert m["p_D7"].notna().all(), (label, "D7 does not cover every stored row")
    return m


def frame_job(group: str, model: str, system: str, train: pd.DataFrame, scored: pd.DataFrame) -> dict:
    """A D7 job from in-memory frames: both worlds of the training units, and the scored (picked) test rows."""
    keep = ["uid", "world", "split", "query", "text", "hypothesis"]
    tr = train[keep].assign(world=train["world"].astype(str)).reset_index(drop=True)
    te = scored[keep].assign(world=scored["world"].astype(str)).reset_index(drop=True)
    assert set(tr["world"]) == {"0", "1"} and tr.groupby("uid").size().eq(2).all(), (group, model, system, "training units need both worlds")
    assert te["uid"].is_unique and (te["world"] == te["uid"].map(AT.world_pick)).all(), (group, model, system, "test rows must be the picked rows")
    return {"group": group, "model": model, "system": system, "train": tr, "test": te}


def counts(frame: pd.DataFrame, attackers: list[str]) -> dict[str, tuple[int, int]]:
    return AT.counts_from_scores(frame, attackers)


def certificate(all_counts: dict[str, dict], eps: float, delta: float, model: str) -> pd.DataFrame:
    return G.certificate_table(all_counts, eps, delta).assign(model=model)


def select(all_counts: dict[str, dict], utility: dict[str, float], eps: float, delta: float, fallback: str = "L0-RT-pre") -> tuple[str, dict]:
    cert = G.certify(all_counts, eps, delta)
    return G.select(cert, utility, fallback), cert


def attacker_rows(model: str, system: str, c: dict[str, tuple[int, int]], eps: float, delta: float) -> list[dict]:
    """As heldout.frozen_attacker_table: single tests at delta."""
    p_sys, eps_hat = G.config_p_value(c, eps), G.certified_bound(c, delta)
    out = []
    for d, (k, n) in c.items():
        a = advantage(k, n)
        out.append({"model": model, "system": system, "attacker": d, "k": k, "n": n, "acc": a["acc"], "adv": a["adv"], "adv_lo": a["adv_lo"],
                    "adv_hi": a["adv_hi"], "p_attacker": G.p_value(k, n, eps), "p_system": p_sys, "bound_at_delta": eps_hat,
                    "within_eps": bool(a["adv_hi"] <= eps)})
    return out


def main_with(main: pd.DataFrame, att: pd.DataFrame, cols=("max_adv", "max_adv_hi", "worst_attacker", "bound_at_delta")) -> pd.DataFrame:
    """A committed main table with its attacker columns replaced by those of a new attacker table. The strongest
    attacker is named only when it is the only one at the largest advantage; otherwise it is "tie" (the six-attacker
    tables named one of the tied attackers arbitrarily), and attackers_at_max says how many share it."""
    out = main.copy().astype({c: object for c in cols if c in main.columns})
    out["attackers_at_max"] = 0
    for i, r in out.iterrows():
        a = att[(att["model"] == r["model"]) & (att["system"] == r["system"])]
        if not len(a):
            continue
        top = a[np.isclose(a["adv"], a["adv"].max(), rtol=0, atol=1e-12)]
        vals = {"max_adv": float(a["adv"].max()), "max_adv_lo": float(a["adv_lo"].max()), "max_adv_hi": float(a["adv_hi"].max()),
                "worst_attacker": top["attacker"].iloc[0] if len(top) == 1 else "tie", "bound_at_delta": float(a["bound_at_delta"].iloc[0])}
        for c in cols:
            out.at[i, c] = vals[c]
        out.at[i, "attackers_at_max"] = int(len(top))
    return out


def same_counts(new: pd.DataFrame, old: pd.DataFrame, keys: list[str]) -> dict:
    """Rows of a committed table reproduced by the recomputation (k and n)."""
    m = old.merge(new, on=keys, how="left", suffixes=("_old", ""))
    ok = (m["k"] == m["k_old"]) & (m["n"] == m["n_old"])
    return {"rows": int(len(m)), "identical": int(ok.sum())}


# ----------------------------------------------------------------------------- sensitivity of the certificate to n
def correct_matrix(frame: pd.DataFrame, attackers: list[str]) -> tuple[np.ndarray, list[str]]:
    """Per picked unit (sorted by uid) and attacker: whether the frozen attacker's guess was right."""
    f = AT.picked(frame).sort_values("uid")
    truth = f["world"].astype(int).to_numpy()
    C = np.column_stack([((f[f"p_{a}"].to_numpy() >= 0.5).astype(int) == truth) for a in attackers])
    return C, f["uid"].tolist()


def eps_hat_vec(K: np.ndarray, n: int, delta_m: float, grid: np.ndarray = EPS_GRID) -> float:
    """Equation 18 for counts K (one per attacker), vectorised over the grid; equals gate.certified_bound."""
    K = np.asarray(K)[:, None]
    hi = binom.cdf(K, n, (1 + grid[None, :]) / 2)
    lo = binom.sf(K - 1, n, (1 - grid[None, :]) / 2)
    pmax = np.maximum(hi, lo).max(axis=0)
    ok = np.nonzero(pmax <= delta_m)[0]
    return float(grid[ok[0]]) if len(ok) else 1.0


def p_config_vec(K: np.ndarray, n: int, eps: float) -> float:
    K = np.asarray(K)
    return float(np.maximum(binom.cdf(K, n, (1 + eps) / 2), binom.sf(K - 1, n, (1 - eps) / 2)).max())


def config_class(cfg: str) -> str:
    level, _, retrieval = cfg.split("-")
    if level == "L3":
        return "L3"
    return "pre" if retrieval == "pre" else "post"


def sensitivity(mats: dict[str, np.ndarray], n_grid: list[int], reps: int, eps: float, delta_m: float, seed: int = 0) -> pd.DataFrame:
    """For each n, `reps` random subsets of n certify units (the same subsets for every configuration of a model):
    the certified bound and whether the configuration is certified at eps with the domain's Bonferroni share."""
    n_full = next(iter(mats.values())).shape[0]
    rows = []
    for n in n_grid:
        r_n = 1 if n >= n_full else reps
        rng = np.random.default_rng(seed + n)
        for rep in range(r_n):
            idx = np.arange(n_full) if n >= n_full else rng.choice(n_full, size=n, replace=False)
            for cfg, C in mats.items():
                K = C[idx].sum(axis=0)
                m = len(idx)
                rows.append({"config": cfg, "class": config_class(cfg), "n": m, "rep": rep, "eps_hat": eps_hat_vec(K, m, delta_m),
                             "certified": bool(p_config_vec(K, m, eps) <= delta_m)})
    return pd.DataFrame(rows)
