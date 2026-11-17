"""The low-view conformal clarifier (plan v1, Section 6.5, Equations 9 to 14, Proposition 2).

Everything the requester sees is computed from the permitted view: the candidate records come from an index built
over the records the requester may read, the model scores only those candidates (as a multiple-choice question whose
options are the candidates plus "none of these"), the probabilities are temperature-scaled, and a split conformal
threshold turns them into a prediction set. One record in the set: answer. Only "none" in the set: the universal
reply. Several: ask, listing the set when it is short and otherwise asking first for the attribute (type,
department, owner) that best splits the set. The same prompt gives the same scores in both worlds by construction,
because scores are cached by prompt and the prompt holds only permitted records (Proposition 1).

The scorer is any object with choice_logprobs(system_prompt, user_prompt, letters) -> {letter: logprob}; the vLLM
client implements it from the first generated token, the scripted stand-in deterministically.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

import acl
import config
import index as IX
from baselines import (NONE_OPTION, UNIVERSAL, _aggregate, _user_choice, observation, template_answer, template_list)

LETTERS = "ABCDEFGHIJ"
ATTRIBUTE_LABEL = {"type": "record type", "dept": "department", "owner": "owner"}
TYPE_LABEL = {"project_brief": "project brief", "investigation": "investigation", "hr_case": "people case",
              "acquisition_memo": "transaction memo", "vendor_contract": "vendor contract", "support_ticket": "support ticket"}
SCORER_SYSTEM = ("You match a staff member's request to the record it refers to. Answer with a single letter: the "
                 "option that the request is about, or the last option if none of the records is the one meant.")


# ----------------------------------------------------------------------------- candidates and prompt
def candidate_set(world: dict, pid: int, query: str, m: int = config.CANDIDATES_M) -> list[dict]:
    """Permitted candidates: records whose name matches the request, else the best permitted matches by content."""
    view = acl.permitted_view(world, pid)
    ex = IX.people_tokens(world)
    cands = IX.candidates(view, query, m, exclude=ex)
    if not cands:
        cands = [r for r, _ in IX.search(view, query, m, exclude=ex)]
    return cands[:m]


def option_line(letter: str, rec: dict) -> str:
    return f"{letter}) {rec['title']} [{rec['ref']}] ({TYPE_LABEL[rec['type']]}, {rec['dept']})"


def mc_prompt(requester: dict, query: str, cands: list[dict]) -> tuple[str, str]:
    lines = [option_line(LETTERS[i], r) for i, r in enumerate(cands)]
    lines.append(f"{LETTERS[len(cands)]}) None of these")
    user = (f"Requester: {requester['name']} ({requester['dept']}).\nRequest: {query}\n\n"
            f"Records the requester may read:\n" + "\n".join(lines) + "\n\nAnswer with the letter only.")
    return SCORER_SYSTEM, user


def prompt_key(system: str, user: str) -> str:
    return hashlib.sha1((system + "\n---\n" + user).encode()).hexdigest()


# ----------------------------------------------------------------------------- scorer with a record-once cache
class ScoreCache:
    """Letter log-probabilities keyed by prompt. Reads a JSON-lines file, appends new scores, never re-scores."""

    def __init__(self, path: Path, scorer=None):
        self.path, self.scorer = Path(path), scorer
        self.rows: dict[str, dict] = {}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    self.rows[r["key"]] = r
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def logprobs(self, system: str, user: str, n_options: int) -> dict[str, float]:
        key = prompt_key(system, user)
        if key in self.rows:
            return self.rows[key]["logprobs"]
        if self.scorer is None:
            raise KeyError(f"prompt not scored and no scorer attached: {key}")
        letters = LETTERS[:n_options]
        lp = self.scorer.choice_logprobs(system, user, letters)
        row = {"key": key, "n_options": n_options, "logprobs": {l: float(lp.get(l, float("nan"))) for l in letters}}
        with open(self.path, "a") as fh:
            fh.write(json.dumps(row) + "\n")
        self.rows[key] = row
        return row["logprobs"]


def logits_from(lp: dict[str, float], n_options: int) -> np.ndarray:
    """Letters absent from the model's top log-probabilities get the smallest seen value minus a margin."""
    vals = [lp.get(LETTERS[i], float("nan")) for i in range(n_options)]
    seen = [v for v in vals if not math.isnan(v)]
    floor = (min(seen) - 5.0) if seen else 0.0
    return np.array([floor if math.isnan(v) else v for v in vals], dtype=float)


def pred_set(probs: np.ndarray, qhat: float) -> list[int]:
    """Equation 12: options whose nonconformity 1 - p is at most the threshold."""
    return [int(i) for i in np.where(1 - probs <= qhat + 1e-12)[0]]


def softmax(z: np.ndarray, T: float = 1.0) -> np.ndarray:
    z = z / T
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


# ----------------------------------------------------------------------------- information-gain question (Equation 14)
def entropy(p: np.ndarray) -> float:
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def best_question(set_recs: list[dict], probs: np.ndarray) -> tuple[str, float] | None:
    """The attribute whose answer most reduces the entropy over the set; None when no attribute splits the set."""
    prior = probs / probs.sum()
    h = entropy(prior)
    best = None
    for attr in config.CLARIFIER_ATTRIBUTES:
        groups: dict[str, float] = {}
        for r, p in zip(set_recs, prior):
            groups[str(r[attr])] = groups.get(str(r[attr]), 0.0) + float(p)
        if len(groups) < 2:
            continue
        cond = 0.0
        for val, mass in groups.items():
            sub = np.array([p for r, p in zip(set_recs, prior) if str(r[attr]) == val])
            cond += mass * entropy(sub / sub.sum())
        gain = h - cond
        if best is None or gain > best[1] + 1e-9:
            best = (attr, gain)
    return best


def attribute_value_label(rec: dict, attr: str, world: dict) -> str:
    if attr == "type":
        return TYPE_LABEL[rec["type"]]
    if attr == "owner":
        return world["people"][rec["owner"]]["name"]
    return str(rec[attr])


# ----------------------------------------------------------------------------- the system
class ConformalClarifier:
    """LORE at disclosure level L1: universal reply, single answer, or a clarification over the permitted candidates."""

    def __init__(self, cache: ScoreCache, T: float = 1.0, qhat: float = 1.0, name: str = config.LORE):
        self.cache, self.T, self.qhat, self.name = cache, float(T), float(qhat), name

    # --- scores
    def scores(self, requester: dict, query: str, cands: list[dict]) -> np.ndarray:
        system, user = mc_prompt(requester, query, cands)
        lp = self.cache.logprobs(system, user, len(cands) + 1)
        return softmax(logits_from(lp, len(cands) + 1), self.T)

    def prediction_set(self, probs: np.ndarray) -> list[int]:
        return pred_set(probs, self.qhat)

    # --- turns
    def respond(self, ctx: dict) -> dict:
        world, req, q = ctx["world"], ctx["requester"], ctx["query"]
        pid = req["pid"]
        view = acl.permitted_view(world, pid)
        ex = IX.people_tokens(world)
        if not [t for t in IX.query_name_tokens(q) if t not in ex]:          # aggregate or person request: list by content
            agg = _aggregate(view, q)
            return observation(template_list(agg), "answer") if agg else observation(UNIVERSAL, "none")
        cands = candidate_set(world, pid, q)
        if not cands:
            return observation(UNIVERSAL, "none")
        answer = _user_choice(ctx)
        if answer is not None:
            return self.after_answer(ctx, cands, answer)
        probs = self.scores(req, q, cands)
        none_i = len(cands)
        S = self.prediction_set(probs)
        if not S:                                   # no option within the threshold: ask over the likeliest records
            order = [int(i) for i in np.argsort(-probs) if int(i) != none_i]
            return self.ask_list([cands[i] for i in order[:config.MAX_LIST_OPTIONS]])
        if S == [none_i]:
            return observation(UNIVERSAL, "none")
        recs = [cands[i] for i in S if i != none_i]
        if len(S) == 1:
            return observation(template_answer(recs[0]), "answer", resolved=recs[0]["ref"])
        if len(recs) <= config.MAX_LIST_OPTIONS:
            return self.ask_list(recs)
        qbest = best_question(recs, np.array([probs[i] for i in S if i != none_i]))
        if qbest is None:
            return self.ask_list(recs[:config.MAX_LIST_OPTIONS])
        attr = qbest[0]
        values = sorted({attribute_value_label(r, attr, world) for r in recs})
        text = f"Which {ATTRIBUTE_LABEL[attr]} is it?\n" + "\n".join(f"{i + 1}. {v}" for i, v in enumerate(values))
        text += f"\n{len(values) + 1}. {NONE_OPTION}"
        obs = observation(text, "ask", options=[])
        obs["question"] = {"attribute": attr, "values": values, "set": [r["ref"] for r in recs]}
        return obs

    def ask_list(self, recs: list[dict]) -> dict:
        options = [{"ref": r["ref"], "label": r["title"]} for r in recs]
        text = "Which one do you mean?\n" + "\n".join(f"{i + 1}. {o['label']} [{o['ref']}]" for i, o in enumerate(options))
        text += f"\n{len(options) + 1}. {NONE_OPTION}"
        return observation(text, "ask", options=options)

    def after_answer(self, ctx: dict, cands: list[dict], answer: str) -> dict:
        world = ctx["world"]
        last_q = next((h for h in reversed(ctx["history"]) if h["role"] == "assistant"), None)
        if NONE_OPTION in answer:
            return observation(UNIVERSAL, "none")
        picked = [r for r in cands if r["ref"] in answer]
        if picked:
            return observation(template_answer(picked[0]), "answer", resolved=picked[0]["ref"])
        # an attribute answer: keep the candidates with that value, then list them
        if last_q is not None and last_q.get("question"):
            attr = last_q["question"]["attribute"]
            keep = [r for r in cands if r["ref"] in last_q["question"]["set"]
                    and attribute_value_label(r, attr, world).lower() == answer.strip().lower()]
            if len(keep) == 1:
                return observation(template_answer(keep[0]), "answer", resolved=keep[0]["ref"])
            if keep:
                return self.ask_list(keep[:config.MAX_LIST_OPTIONS])
        return observation(UNIVERSAL, "none")


# ----------------------------------------------------------------------------- scorer v2: permitted-view evidence
TYPE_WORDS = {"project_brief": ["project", "brief"], "investigation": ["investigation", "case"],
              "hr_case": ["people", "case", "hr"], "acquisition_memo": ["transaction", "memo", "acquisition"],
              "vendor_contract": ["vendor", "contract", "agreement", "supply"], "support_ticket": ["ticket", "support"]}
EVIDENCE_NAMES = ["name_match", "body_match", "type_cue", "best_name", "none", "none_minus_best_name", "none_minus_type_cue"]
FEATURE_NAMES = EVIDENCE_NAMES + ["model_logit"]
SCORERS = {"evidence": list(range(7)), "llm": [7], "combined": list(range(8))}


def type_cue(rec: dict, query: str) -> float:
    q = query.lower()
    return 1.0 if any(w in q for w in TYPE_WORDS[rec["type"]]) else 0.0


def any_type_word(query: str) -> bool:
    q = query.lower()
    return any(w in q for ws in TYPE_WORDS.values() for w in ws)


def evidence(world: dict, query: str, cands: list[dict]) -> np.ndarray:
    """Equation 15: per-option evidence from the permitted view alone. Rows are the candidates then 'none of these'."""
    ex = IX.people_tokens(world)
    nm = np.array([IX.name_match(c, query, ex) for c in cands], dtype=float)
    bm = np.array([IX.body_match(c, query) for c in cands], dtype=float)
    tc = np.array([type_cue(c, query) for c in cands], dtype=float)
    n = len(cands) + 1
    X = np.zeros((n, len(EVIDENCE_NAMES)))
    if cands:
        X[:-1, 0], X[:-1, 1], X[:-1, 2] = nm, bm, tc
        X[:-1, 3] = (nm == nm.max()).astype(float)
        X[-1, 5] = -nm.max()
        X[-1, 6] = -(tc.max() if any_type_word(query) else 0.5)
    X[-1, 4] = 1.0
    return X


def tie_size(world: dict, query: str, cands: list[dict]) -> int:
    """Number of candidates sharing the best name match, capped at config.TIE_STRATA (0 without candidates)."""
    if not cands:
        return 0
    ex = IX.people_tokens(world)
    nm = np.array([IX.name_match(c, query, ex) for c in cands])
    return int(min(config.TIE_STRATA, (nm == nm.max()).sum()))


def design(world: dict, query: str, cands: list[dict], llm_logits: np.ndarray | None) -> np.ndarray:
    """Evidence columns plus the model's centred option log-probabilities (zeros when no model score is used)."""
    E = evidence(world, query, cands)
    z = np.zeros(len(cands) + 1) if llm_logits is None else (np.asarray(llm_logits, dtype=float) - np.max(llm_logits))
    return np.column_stack([E, z])


def option_probs(X: np.ndarray, weights: np.ndarray, cols: list[int]) -> np.ndarray:
    """Equation 16: conditional-logit probabilities over the options."""
    z = X[:, cols] @ np.asarray(weights, dtype=float)
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


def fit_weights(Xs: list[np.ndarray], ys: list[int], cols: list[int], l2: float = 1e-3) -> np.ndarray:
    """Maximum-likelihood conditional logit (ridge l2) on labelled option matrices."""
    from scipy.optimize import minimize

    def nll(w):
        total, grad = 0.0, np.zeros(len(cols))
        for X, y in zip(Xs, ys):
            F = X[:, cols]
            z = F @ w
            z = z - z.max()
            e = np.exp(z)
            p = e / e.sum()
            total -= math.log(max(p[y], 1e-300))
            grad += F.T @ p - F[y]
        n = len(Xs)
        return total / n + l2 * float(w @ w), grad / n + 2 * l2 * w

    res = minimize(nll, np.zeros(len(cols)), jac=True, method="L-BFGS-B")
    return res.x


def list_question(recs: list[dict]) -> dict:
    options = [{"ref": r["ref"], "label": r["title"]} for r in recs]
    text = "Which one do you mean?\n" + "\n".join(f"{i + 1}. {o['label']} [{o['ref']}]" for i, o in enumerate(options))
    text += f"\n{len(options) + 1}. {NONE_OPTION}"
    obs = observation(text, "ask", options=options)
    obs["question"] = {"kind": "list", "offered": [r["ref"] for r in recs]}
    return obs


class EvidenceClarifier:
    """LORE with the v2 score: conditional logit over permitted-view evidence (and, in the combined scorer, the
    model's option log-probability), a conformal threshold per tie-size stratum, and follow-through: a requester
    who answers 'none of these' is asked over the candidates not yet offered before the universal reply."""

    def __init__(self, params: dict, cache: ScoreCache | None = None, name: str = config.LORE):
        self.name = name
        self.cols = list(params["cols"])
        self.weights = np.asarray(params["weights"], dtype=float)
        self.qhat_by_k = {int(k): float(v) for k, v in params["qhat_by_k"].items()}
        self.qhat_pooled = float(params["qhat_pooled"])
        self.uses_llm = (len(FEATURE_NAMES) - 1) in self.cols
        self.cache = cache
        if self.uses_llm and cache is None:
            raise ValueError("this scorer uses the model's log-probabilities: a score cache is required")

    def threshold(self, k: int) -> float:
        return self.qhat_by_k.get(int(k), self.qhat_pooled)

    def scores(self, world: dict, requester: dict, query: str, cands: list[dict]) -> np.ndarray:
        z = None
        if self.uses_llm:
            system, user = mc_prompt(requester, query, cands)
            z = logits_from(self.cache.logprobs(system, user, len(cands) + 1), len(cands) + 1)
        return option_probs(design(world, query, cands, z), self.weights, self.cols)

    def prediction_set(self, probs: np.ndarray, k: int) -> list[int]:
        return pred_set(probs, self.threshold(k))

    def respond(self, ctx: dict) -> dict:
        world, req, q = ctx["world"], ctx["requester"], ctx["query"]
        pid = req["pid"]
        view = acl.permitted_view(world, pid)
        ex = IX.people_tokens(world)
        if not [t for t in IX.query_name_tokens(q) if t not in ex]:          # aggregate or person request: list by content
            agg = _aggregate(view, q)
            return observation(template_list(agg), "answer") if agg else observation(UNIVERSAL, "none")
        cands = candidate_set(world, pid, q)
        if not cands:
            return observation(UNIVERSAL, "none")
        probs = self.scores(world, req, q, cands)
        answer = _user_choice(ctx)
        if answer is not None:
            return self.after_answer(ctx, cands, probs, answer)
        none_i = len(cands)
        S = self.prediction_set(probs, tie_size(world, q, cands))
        if not S:                                   # no option within the threshold: ask over the likeliest records
            order = [int(i) for i in np.argsort(-probs) if int(i) != none_i]
            return list_question([cands[i] for i in order[:config.MAX_LIST_OPTIONS]])
        if S == [none_i]:
            return observation(UNIVERSAL, "none")
        recs = [cands[i] for i in S if i != none_i]
        if len(S) == 1:
            return observation(template_answer(recs[0]), "answer", resolved=recs[0]["ref"])
        if len(recs) <= config.MAX_LIST_OPTIONS:
            return list_question(recs)
        qbest = best_question(recs, np.array([probs[i] for i in S if i != none_i]))
        if qbest is None:
            return list_question(recs[:config.MAX_LIST_OPTIONS])
        attr = qbest[0]
        values = sorted({attribute_value_label(r, attr, world) for r in recs})
        text = f"Which {ATTRIBUTE_LABEL[attr]} is it?\n" + "\n".join(f"{i + 1}. {v}" for i, v in enumerate(values))
        text += f"\n{len(values) + 1}. {NONE_OPTION}"
        obs = observation(text, "ask", options=[])
        obs["question"] = {"kind": "attribute", "attribute": attr, "values": values, "set": [r["ref"] for r in recs]}
        return obs

    def after_answer(self, ctx: dict, cands: list[dict], probs: np.ndarray, answer: str) -> dict:
        world = ctx["world"]
        asked = [h for h in ctx["history"] if h["role"] == "assistant" and h.get("question")]
        last_q = asked[-1]["question"] if asked else None
        if NONE_OPTION in answer:
            offered: set[str] = set()
            for h in asked:
                qd = h["question"]
                offered |= set(qd.get("offered", [])) | set(qd.get("set", []))
            order = [int(i) for i in np.argsort(-probs) if int(i) != len(cands)]
            rest = [cands[i] for i in order if cands[i]["ref"] not in offered]
            if rest:
                return list_question(rest[:config.MAX_LIST_OPTIONS])
            return observation(UNIVERSAL, "none")
        picked = [r for r in cands if r["ref"] in answer]
        if picked:
            return observation(template_answer(picked[0]), "answer", resolved=picked[0]["ref"])
        if last_q is not None and last_q.get("attribute"):
            attr = last_q["attribute"]
            keep = [r for r in cands if r["ref"] in last_q["set"]
                    and attribute_value_label(r, attr, world).lower() == answer.strip().lower()]
            if len(keep) == 1:
                return observation(template_answer(keep[0]), "answer", resolved=keep[0]["ref"])
            if keep:
                return list_question(keep[:config.MAX_LIST_OPTIONS])
        return observation(UNIVERSAL, "none")


# ----------------------------------------------------------------------------- calibration helpers
def intended_option(unit: dict, world_key: str, cands: list[dict]) -> int:
    """Index of the intended record among the candidates, or the 'none' index when the intended record is not a
    permitted candidate (restricted, or not retrieved)."""
    for i, r in enumerate(cands):
        if r["ref"] == unit["target_ref"]:
            return i
    return len(cands)


def needs_scoring(world: dict, pid: int, query: str) -> bool:
    """The clarifier scores only named-record requests with at least one permitted candidate."""
    ex = IX.people_tokens(world)
    if not [t for t in IX.query_name_tokens(query) if t not in ex]:
        return False
    return bool(candidate_set(world, pid, query))


def prompt_for(unit: dict, world_key: str = "1") -> dict | None:
    """Prompt, key and label of a unit in one world, or None when the clarifier would not call the scorer. The
    label is the intended option: the permitted target of a legitimate task, 'none' when the intended record is not
    among the permitted candidates (restricted, or not retrieved)."""
    world = unit["worlds"][world_key]
    req = acl.person(world, unit["requester"])
    if not needs_scoring(world, req["pid"], unit["query"]):
        return None
    cands = candidate_set(world, req["pid"], unit["query"])
    system, user = mc_prompt(req, unit["query"], cands)
    return {"uid": unit["uid"], "world": world_key, "family": unit["family"], "kind": unit["kind"],
            "secret": unit.get("secret"), "n_cands": len(cands), "label": intended_option(unit, world_key, cands),
            "system": system, "user": user, "key": prompt_key(system, user)}


labelled_task = prompt_for


NONE_FAMILIES = {"Q1", "Q4", "Q7", "Q1a"}   # the request names the restricted record itself: the intended option is 'none'


def is_none_task(unit: dict) -> bool:
    return unit["kind"] == "leak" and unit["family"] in NONE_FAMILIES
