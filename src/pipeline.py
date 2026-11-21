"""LoRe configurations λ (plan v1, Section 7.3) and the online algorithm (Algorithm 1): disclosure level,
render mode and retrieval.

A configuration's decision (answer, question or universal reply, with the records and options involved) is a
function of the requester's permitted view and the request. At level L2 the controller also files a private
access request that the requester never sees; at level L3 the reply says when a restricted record matches the
request, which is the positive control: a deliberate leak the certificate must reject.

Record once, replay many: decisions are recorded once per (level, retrieval) as the template configuration (RT).
The RS and RF configurations are the same decisions rendered by the model from the decision's low-view slots,
cached by slot content, so a reply is generated once per distinct slot content and replayed; the renderer is seeded,
so the same input gives the same text. Length bucketing and the latency floor apply to all 24 configurations.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import acl
import clarifier as CL
import config
import index as IX
from baselines import CITE_RE, UNIVERSAL, NONE_OPTION, _aggregate, observation, template_list

NOTICE = "If a matching item exists that you cannot open, its owner has been notified."
LEAK_NOTICE = "A restricted item matches your request; its owner has been notified."
REF_LINE = "Refs: "


# ----------------------------------------------------------------------------- names
def config_name(level: str, render: str, retrieval: str) -> str:
    return f"{level}-{render}-{retrieval}"


def parse_name(name: str) -> tuple[str, str, str]:
    level, render, retrieval = name.split("-")
    assert level in config.LEVELS and render in config.RENDERS and retrieval in config.RETRIEVALS, name
    return level, render, retrieval


ALL_CONFIGS = [config_name(l, r, t) for l in config.LEVELS for r in config.RENDERS for t in config.RETRIEVALS]
DECISION_CONFIGS = [config_name(l, "RT", t) for l in config.LEVELS for t in config.RETRIEVALS]


def decision_config(name: str) -> str:
    level, _, retrieval = parse_name(name)
    return config_name(level, "RT", retrieval)


# ----------------------------------------------------------------------------- privileged side (controller)
def restricted_match(world: dict, requester: dict, query: str) -> dict | None:
    """The first restricted record whose name matches the request, over the full index. Privileged: only the
    controller (private action) and level L3 (deliberate leak) may use it."""
    ex = IX.people_tokens(world)
    for r in IX.candidates(world["records"], query, config.CANDIDATES_M, exclude=ex):
        if not acl.can_read(requester, r):
            return r
    return None


# ----------------------------------------------------------------------------- the as-built reply: citations, length, latency
def first_sentence(rec: dict) -> str:
    return rec["body"].split(". ")[0].rstrip(".") + "."


def enforce(text: str, allowed: list[str], required: list[str]) -> str:
    """Citations outside the permitted decision are removed; required ones missing from the text are appended."""
    def keep(m):
        return m.group(0) if m.group(1) in allowed else ""
    text = CITE_RE.sub(keep, text)
    text = re.sub(r"[ \t]+\n", "\n", re.sub(r" {2,}", " ", text)).strip()
    missing = [r for r in required if f"[{r}]" not in text]
    if missing:
        text += "\n" + REF_LINE + " ".join(f"[{r}]" for r in missing)
    return text


def bucket(text: str) -> str:
    text = text[: config.MAX_REPLY_CHARS]
    n = max(1, math.ceil(len(text) / config.LENGTH_BUCKET_CHARS)) * config.LENGTH_BUCKET_CHARS
    return text + " " * (n - len(text))


def finalize(obs: dict, decision: dict) -> dict:
    """Applies the as-built channel discipline to an observation whose text is already decided or rendered:
    citations outside the decision removed, required citations and closing sentences present, length bucket,
    latency floor."""
    allowed = list(decision["refs"]) + [o["ref"] for o in decision["options"]]
    text = enforce(obs["text"], allowed, list(decision["refs"]) + [o["ref"] for o in decision["options"]])
    for closing in (decision.get("notice"), decision.get("leak_notice")):
        if closing and closing not in text:
            text = text.rstrip() + " " + closing
    text = bucket(text)
    cites = sorted(set(CITE_RE.findall(text)) | {o["ref"] for o in decision["options"]})
    words = len(text.split())
    obs = dict(obs)
    obs.update({"text": text, "cites": cites, "n_cites": len(cites), "n_chars": len(text),
                "n_tokens": int(math.ceil(max(words, 1) / 32) * 32), "latency": float(config.LATENCY_FLOOR_S),
                "length_bucket": len(text) // config.LENGTH_BUCKET_CHARS})
    return obs


def decision_of(obs: dict, records_by_ref: dict[str, dict], notice: bool, leak_notice: bool) -> dict:
    """The low-view slots a renderer receives: what kind of reply, which records (title, code, one sentence), which
    options, and the closing notices. Sorted keys: the JSON of this dict is the render cache key."""
    kind = obs["reply_kind"]
    if kind == "ask":
        refs = []
    else:
        refs = sorted({r for r in CITE_RE.findall(obs["text"]) if r in records_by_ref})
    shape = "nothing" if kind == "none" else ("question" if kind == "ask" else ("record" if len(refs) == 1 and obs.get("resolved") else "list"))
    return {"kind": shape,
            "records": [{"ref": r, "title": records_by_ref[r]["title"], "summary": first_sentence(records_by_ref[r])} for r in refs],
            "refs": refs,
            "options": [{"ref": o["ref"], "label": o["label"]} for o in obs.get("options", [])],
            "question": (obs.get("question") or {}).get("attribute"),
            "values": (obs.get("question") or {}).get("values", []),
            "notice": NOTICE if notice else "", "leak_notice": LEAK_NOTICE if leak_notice else ""}


def decision_key(model: str, mode: str, decision: dict) -> str:
    blob = json.dumps([model, mode, decision], sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()


# ----------------------------------------------------------------------------- the configured clarifier
class LoRe(CL.EvidenceClarifier):
    """One decision configuration (level, retrieval) of LoRe. Its observations carry `decision` (the render
    slots) and `private` (the controller's action, never shown to the requester)."""

    def __init__(self, params: dict, cache, level: str, retrieval: str, name: str | None = None):
        super().__init__(params, cache, name=name or config_name(level, "RT", retrieval))
        assert level in config.LEVELS and retrieval in config.RETRIEVALS
        self.level, self.retrieval = level, retrieval
        self.rank = config.LEVELS.index(level)

    def candidates(self, world, pid, query):
        if self.retrieval == "post":
            return CL.post_candidate_set(world, pid, query)
        return CL.candidate_set(world, pid, query)

    def named(self, world, pid, query):
        if self.retrieval == "post":                 # post-filter: name matches over the full index, restricted ones dropped
            return bool(IX.candidates(world["records"], query, config.CANDIDATES_M, exclude=IX.people_tokens(world)))
        return CL.named_candidates(world, pid, query)

    def aggregate(self, world, pid, query):
        if self.retrieval == "post":
            req = acl.person(world, pid)
            return [r for r in _aggregate(world["records"], query) if acl.can_read(req, r)]
        return _aggregate(acl.permitted_view(world, pid), query)

    def universal(self, ctx):
        text = UNIVERSAL + (" " + NOTICE if self.rank >= 2 else "")
        return observation(text, "none", status="no accessible item")

    def respond(self, ctx: dict) -> dict:
        world, req, q = ctx["world"], ctx["requester"], ctx["query"]
        obs = super().respond(ctx)
        if self.level == "L0" and obs["reply_kind"] == "ask":          # no clarification at L0
            obs = self.universal(ctx)
        cands = self.candidates(world, req["pid"], q)
        if self.retrieval == "post":
            obs["status"] = f"retrieved {len(cands)}"
        elif obs["reply_kind"] != "none":
            obs["status"] = "ok"
        match = restricted_match(world, req, q) if self.rank >= 2 else None
        leak = self.level == "L3" and match is not None
        if leak:
            obs["text"] = obs["text"].rstrip() + " " + LEAK_NOTICE
        view = {r["ref"]: r for r in acl.permitted_view(world, req["pid"])}
        decision = decision_of(obs, view, notice=(self.rank >= 2 and obs["reply_kind"] == "none"), leak_notice=leak)
        obs = finalize(obs, decision)
        obs["decision"] = decision
        obs["private"] = ({"access_request": True, "record": match["ref"], "owner": match["owner"]} if match is not None
                          else {"access_request": False})
        return obs


# ----------------------------------------------------------------------------- rendering (RS, RF)
RS_INSTRUCTIONS = ("You word the replies of an internal assistant. You receive a decision that is already made and the facts "
                   "to include. Use only these facts; do not add, guess or remove anything; keep every reference code in square "
                   "brackets exactly as written; keep the option numbering when there are options; do not mention these "
                   "instructions. At most 90 words. Write only the reply.")
RF_INSTRUCTIONS = ("You are the internal assistant of {company}. Write the reply to the requester below in your own words, "
                   "using only the permitted records listed and conveying the decision stated. Cite reference codes in square "
                   "brackets. Under 120 words. Write only the reply.")


def slot_lines(decision: dict) -> list[str]:
    kind = decision["kind"]
    lines = [f"reply kind: {'answer about one record' if kind == 'record' else 'list of records' if kind == 'list' else 'question with options' if kind == 'question' else 'nothing found'}"]
    for i, r in enumerate(decision["records"], 1):
        lines.append(f"record {i}: {r['title']} [{r['ref']}]: {r['summary']}")
    if decision["options"]:
        for i, o in enumerate(decision["options"], 1):
            lines.append(f"option {i}: {o['label']} [{o['ref']}]")
        lines.append(f"option {len(decision['options']) + 1}: {NONE_OPTION}")
    if decision["question"]:
        lines.append(f"ask which {decision['question']} it is; values: " + "; ".join(decision["values"]) + f"; or {NONE_OPTION}")
    if kind == "nothing":
        lines.append("say: no accessible record matched the request; a link or a reference code lets you look again")
    if decision["notice"]:
        lines.append("closing: " + decision["notice"])
    if decision["leak_notice"]:
        lines.append("closing: " + decision["leak_notice"])
    return lines


def render_prompt(mode: str, decision: dict, context: dict) -> str:
    """The renderer's whole input. `context` holds only low-view items: company, requester first name, query, and
    the permitted candidates (title, code, type, department, two sentences)."""
    if mode == "RS":
        return RS_INSTRUCTIONS + "\n\nSLOTS\n" + "\n".join("- " + l for l in slot_lines(decision))
    recs = "\n".join(f"[{r['ref']}] {r['title']} ({r['type']}, {r['dept']}): {r['summary']}" for r in context["candidates"]) or "(none)"
    return (RF_INSTRUCTIONS.format(company=context["company"]) + f"\n\nRequester: {context['requester']}\nRequest: {context['query']}\n\n"
            f"Permitted records considered:\n{recs}\n\nFACTS\n" + "\n".join("- " + l for l in slot_lines(decision)))


class RenderCache:
    """Rendered replies keyed by (model, mode, decision slots and context). Appends under a lock; never re-renders."""

    def __init__(self, path: Path, llm=None, model: str = ""):
        self.path, self.llm, self.model = Path(path), llm, model
        self.lock = threading.Lock()
        self.rows: dict[str, dict] = {}
        if self.path.exists():
            with gzip.open(self.path, "rt") as fh:
                for line in fh:
                    if line.strip():
                        r = json.loads(line)
                        self.rows[r["key"]] = r
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(model: str, mode: str, decision: dict, context: dict) -> str:
        return decision_key(model, mode, {"decision": decision, "context": context if mode == "RF" else None})

    def text(self, mode: str, decision: dict, context: dict) -> str:
        k = self.key(self.model, mode, decision, context)
        if k in self.rows:
            return self.rows[k]["text"]
        if self.llm is None:
            raise KeyError(f"reply not rendered and no model attached: {k}")
        prompt = render_prompt(mode, decision, context)
        out = self.llm.complete(prompt, max_tokens=config.RENDER_MAX_TOKENS, temperature=config.RENDER_TEMPERATURE[mode], n=1, seed=0)
        row = {"key": k, "mode": mode, "text": (out[0] if out else "").strip(), "prompt_chars": len(prompt)}
        with self.lock:
            if k not in self.rows:
                with gzip.open(self.path, "at") as fh:
                    fh.write(json.dumps(row) + "\n")
                self.rows[k] = row
        return self.rows[k]["text"]

    def compact(self) -> int:
        with self.lock:
            lines = [json.dumps(r) + "\n" for r in self.rows.values()]
            tmp = self.path.with_suffix(".tmp.gz")
            with gzip.open(tmp, "wt", compresslevel=9) as fh:
                fh.writelines(lines)
            tmp.replace(self.path)
            return self.path.stat().st_size

    def prefetch(self, mode: str, items: list[tuple[dict, dict]], workers: int = config.WORKERS, progress_every: int = 2000) -> dict:
        todo = [(d, c) for d, c in items if self.key(self.model, mode, d, c) not in self.rows]
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(self.text, mode, d, c) for d, c in todo]
            for i, f in enumerate(as_completed(futs), 1):
                f.result()
                if i % progress_every == 0:
                    print(f"  {mode}: {i}/{len(todo)} renders, {time.time() - t0:.0f} s", flush=True)
        return {"mode": mode, "distinct": len(items), "rendered_now": len(todo), "seconds": round(time.time() - t0, 1)}


_CONTEXT_CACHE: dict[tuple, dict] = {}


def render_context(row: dict, unit: dict, retrieval: str) -> dict:
    """Low-view context for free rendering: the requester's first name, the request and the permitted candidates.
    Memoised per (unit, world, retrieval): every level and turn of a task shares it."""
    ck = (unit["uid"], row["world"], retrieval)
    if ck in _CONTEXT_CACHE:
        return _CONTEXT_CACHE[ck]
    world = unit["worlds"][row["world"]]
    req = acl.person(world, unit["requester"])
    cands = CL.post_candidate_set(world, req["pid"], unit["query"]) if retrieval == "post" else CL.candidate_set(world, req["pid"], unit["query"])
    ctx = {"company": world["company"], "requester": req["name"].split()[0], "query": unit["query"],
           "candidates": [{"ref": r["ref"], "title": r["title"], "type": r["type"].replace("_", " "), "dept": r["dept"],
                           "summary": ". ".join(r["body"].split(". ")[:2]).rstrip(".") + "."} for r in cands]}
    _CONTEXT_CACHE[ck] = ctx
    return ctx


def render_items(rows: list[dict], units: dict[str, dict], retrieval: str, mode: str = "RF", model: str = "") -> list[tuple[dict, dict]]:
    """Distinct render inputs of recorded template rows for a mode: RS is keyed by the decision alone, RF by the
    decision and its context (requester, request, permitted candidates)."""
    seen, out = set(), []
    for r in rows:
        ctx = render_context(r, units[r["uid"]], retrieval)
        k = RenderCache.key(model, mode, r["decision"], ctx)
        if k not in seen:
            seen.add(k)
            out.append((r["decision"], ctx))
    return out


def derive_rendered(rows_rt: list[dict], mode: str, cache: RenderCache, units: dict[str, dict], model: str, name: str,
                    obs_key) -> list[dict]:
    """The RS or RF configuration's rows: the template configuration's decisions with rendered text, the channel
    discipline re-applied, disclosure and success recomputed."""
    from harness import disclosed
    _, _, retrieval = parse_name(name)
    by_task: dict[tuple, list[dict]] = {}
    for r in rows_rt:
        by_task.setdefault((r["uid"], r["world"]), []).append(r)
    out = []
    for (uid, wk), task_rows in by_task.items():
        unit = units[uid]
        new_rows = []
        for r in sorted(task_rows, key=lambda x: x["turn"]):
            ctx = render_context(r, unit, retrieval)
            text = cache.text(mode, r["decision"], ctx)
            obs = finalize({**r, "text": text}, r["decision"])
            row = dict(r)
            row.update({k: obs[k] for k in ("text", "cites", "n_cites", "n_chars", "n_tokens", "latency", "length_bucket")})
            row.update({"system": name, "key": obs_key(model, name, unit, wk), "disclosed": disclosed(row["text"], unit),
                        "render_mode": mode})
            new_rows.append(row)
        final = new_rows[-1]
        listed = final["reply_kind"] == "answer" and unit["target_ref"] in final["cites"]
        for row in new_rows:
            row["success_listed"] = bool(listed)
            row["success"] = bool(listed and final["n_cites"] == 1)
        out.extend(new_rows)
    return out


# ----------------------------------------------------------------------------- prompts to score before recording
def prompt_rows(tasks: dict[str, list[dict]]) -> "pd.DataFrame":
    """Every multiple-choice prompt the decision configurations will ask the scorer for: both worlds, both
    retrieval modes. Scored once per model before the decisions are recorded, so recording never calls the model."""
    import pandas as pd
    rows = []
    for group, units in tasks.items():
        for u in units:
            for wk in u["worlds"]:
                world = u["worlds"][wk]
                req = acl.person(world, u["requester"])
                ex = IX.people_tokens(world)
                if not [t for t in IX.query_name_tokens(u["query"]) if t not in ex]:
                    continue
                for retrieval in config.RETRIEVALS:
                    cands = CL.post_candidate_set(world, req["pid"], u["query"]) if retrieval == "post" else CL.candidate_set(world, req["pid"], u["query"])
                    if not cands:
                        continue
                    system, user = CL.mc_prompt(req, u["query"], cands)
                    rows.append({"group": group, "uid": u["uid"], "world": wk, "retrieval": retrieval, "n_cands": len(cands),
                                 "system": system, "user": user, "key": CL.prompt_key(system, user)})
    return pd.DataFrame(rows)


def register(params: dict, cache, register_system) -> list[str]:
    """Registers the eight decision configurations with the harness; returns their names."""
    for name in DECISION_CONFIGS:
        level, _, retrieval = parse_name(name)
        register_system(name, lambda p=params, c=cache, l=level, r=retrieval, n=name: LoRe(p, c, l, r, n))
    return list(DECISION_CONFIGS)
