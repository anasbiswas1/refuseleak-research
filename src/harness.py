"""Runs a unit through a system and records what the requester sees (plan v1, Section 6.2), once per
(runtime, model, system, unit, world). Leak units are single-turn: the attacker's observation is the first reply.
Legitimate and authorised units run the clarification loop with the scripted user, up to config.MAX_TURNS, and
success means the final reply cites the intended record.

Records are gzipped JSON lines per (model, system) under reports/02_records/<model>/, keyed by what produced them,
so an interrupted session resumes and nothing is generated twice. Records made under an older RUNTIME_VERSION are
ignored and re-run.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import acl
import baselines as B
import config
from scripted import ScriptedUser


def obs_key(model: str, system: str, unit: dict, world_key: str) -> str:
    blob = "|".join([config.RUNTIME_VERSION, model, system, unit["uid"], world_key, unit["pool_hash"]])
    return hashlib.sha1(blob.encode()).hexdigest()


def disclosed(text: str, unit: dict) -> list[str]:
    low = text.lower()
    return [s for s in unit.get("secret_strings", []) if s.lower() in low]


def run_task(system, unit: dict, world_key: str, llm, shared: dict | None = None) -> list[dict]:
    """All turns of one task. Returns one row per assistant turn."""
    world = unit["worlds"][world_key]
    requester = acl.person(world, unit["requester"])
    history: list[dict] = []
    user = None
    if unit["kind"] in ("legit", "auth"):
        target = next((r for r in world["records"] if r["ref"] == unit["target_ref"]), None)
        user = ScriptedUser(unit["target_ref"], target, world)
    rows = []
    ctx = {"world": world, "requester": requester, "query": unit["query"], "history": history, "llm": llm, "unit": unit}
    if shared and "b0" in shared:
        ctx["b0"] = shared["b0"]
    for turn in range(1, config.MAX_TURNS + 1):
        obs = system.respond(ctx)
        rows.append({"system": system.name, "uid": unit["uid"], "split": unit["split"], "kind": unit["kind"],
                     "secret": unit.get("secret"), "family": unit["family"], "world": world_key, "turn": turn,
                     "target_ref": unit["target_ref"], "query": unit["query"], **obs,
                     "disclosed": disclosed(obs["text"], unit)})
        if obs["reply_kind"] != "ask" or user is None:
            break
        history.append({"role": "assistant", "text": obs["text"], "question": obs.get("question")})
        history.append({"role": "user", "text": user.answer(obs)})
    final = rows[-1]
    listed = final["reply_kind"] == "answer" and unit["target_ref"] in final["cites"]
    resolved = listed and final["n_cites"] == 1          # one record answered about, and it is the intended one
    for r in rows:
        r["turns"] = len(rows)
        r["success"] = bool(resolved)
        r["success_listed"] = bool(listed)
    return rows


SYSTEMS: dict = {}          # systems registered by name beyond the baselines (the clarifier with its cache and parameters)


def register_system(name: str, factory) -> None:
    SYSTEMS[name] = factory


def make_system(name: str):
    return SYSTEMS[name]() if name in SYSTEMS else B.make_system(name)


def run_unit(unit: dict, world_key: str, systems: list[str], llm, model: str, shared: dict | None = None) -> list[dict]:
    rows = []
    shared = dict(shared or {})
    order = sorted(systems, key=lambda s: (s != "B0", s))        # B0 first: B2 reuses its generation
    for name in order:
        sysobj = make_system(name)
        task_rows = run_task(sysobj, unit, world_key, llm, shared)
        if name == "B0":
            shared["b0"] = {k: task_rows[0][k] for k in ("text", "status", "latency")}
        for r in task_rows:
            r["model"] = model
            r["key"] = obs_key(model, name, unit, world_key)
            r["runtime"] = config.RUNTIME_VERSION
        rows.extend(task_rows)
    return rows


# ----------------------------------------------------------------------------- store
class Store:
    def __init__(self, root: Path, model: str):
        self.dir = root / model
        self.dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.rows: dict[str, list[dict]] = {}
        for f in sorted(self.dir.glob("*.jsonl.gz")):
            with gzip.open(f, "rt") as fh:
                for line in fh:
                    r = json.loads(line)
                    if r.get("runtime") == config.RUNTIME_VERSION:
                        self.rows.setdefault(r["key"], []).append(r)

    def has(self, key: str) -> bool:
        return key in self.rows

    def add(self, rows: list[dict]):
        by_system: dict[str, list[dict]] = {}
        for r in rows:
            by_system.setdefault(r["system"], []).append(r)
        with self.lock:
            for system, rs in by_system.items():
                with gzip.open(self.dir / f"{system}.jsonl.gz", "at") as fh:
                    for r in rs:
                        fh.write(json.dumps(r) + "\n")
                        self.rows.setdefault(r["key"], []).append(r)

    def all_rows(self) -> list[dict]:
        return [r for rs in self.rows.values() for r in rs]

    def compact(self) -> dict:
        """Rewrites every record file as one gzip stream. Appends during recording create one gzip member per
        append, which compresses poorly; a compacted file is five to ten times smaller and reads the same."""
        sizes = {}
        with self.lock:
            for f in sorted(self.dir.glob("*.jsonl.gz")):
                lines = [l for l in gzip.open(f, "rt") if l.strip()]
                tmp = f.with_suffix(".tmp.gz")
                with gzip.open(tmp, "wt", compresslevel=9) as fh:
                    fh.writelines(lines)
                tmp.replace(f)
                sizes[f.name] = f.stat().st_size
        return sizes


def record_grid(units: list[dict], systems: list[str], llm, model: str, store: Store, workers: int = config.WORKERS,
                progress_every: int = 200) -> dict:
    """Runs every missing (unit, world, system) and appends to the store. Returns counts."""
    jobs = []
    for u in units:
        for wk in u["worlds"]:
            missing = [s for s in systems if not store.has(obs_key(model, s, u, wk))]
            if missing:
                jobs.append((u, wk, missing))
    done, t0 = 0, time.time()
    llm_jobs = [j for j in jobs if any(s in config.LLM_SYSTEMS for s in j[2])]
    plain = [j for j in jobs if j not in llm_jobs]

    def work(job):
        u, wk, missing = job
        shared = {}
        if "B2" in missing and "B0" not in missing:          # B2 reuses B0's stored generation
            b0 = store.rows[obs_key(model, "B0", u, wk)][0]
            shared["b0"] = {k: b0[k] for k in ("text", "status", "latency")}
        return run_unit(u, wk, missing, llm, model, shared)

    for job in plain:
        store.add(work(job))
        done += 1
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(work, j) for j in llm_jobs]
        for f in as_completed(futs):
            store.add(f.result())
            done += 1
            if done % progress_every == 0:
                print(f"  {done}/{len(jobs)} tasks, {time.time() - t0:.0f} s", flush=True)
    return {"tasks_run": len(jobs), "rows_total": len(store.all_rows()), "seconds": round(time.time() - t0, 1)}
