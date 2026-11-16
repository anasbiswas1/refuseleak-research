"""The paraphrase pool (plan v1, Section 9.1): model-written variants of the query templates and of the record
boilerplate sentences, generated once on a GPU session in notebook 01 and committed to suite_data/paraphrases.json.
World generation draws from the pool, so wording varies without the model ever seeing a secret. A variant is kept
only if it preserves every placeholder, is not the original, and stays between half and twice the original length.
In a dry run the pool holds deterministic rewrites instead (not a result source).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import config
from serving import DRY_RUN
from world import BOILERPLATE, QUERY_TEMPLATES

PLACEHOLDER_RE = re.compile(r"\{[A-Z]+\}")
PROMPT = ("Rewrite the sentence below in {n} different ways, keeping its meaning and keeping every placeholder in "
          "curly braces exactly as written. Reply with one rewrite per line and nothing else.\n\nSentence: {s}")
DRY_PREFIXES = ["Quick question: ", "Please tell me: ", "Just checking: "]


def _valid(original: str, cand: str) -> bool:
    cand = cand.strip().strip("-•*0123456789. ").strip().strip('"')
    if not cand or cand.lower() == original.lower():
        return False
    if sorted(PLACEHOLDER_RE.findall(cand)) != sorted(PLACEHOLDER_RE.findall(original)):
        return False
    if not (0.5 * len(original) <= len(cand) <= 2.0 * len(original)):
        return False
    return True


def _clean(cand: str) -> str:
    return cand.strip().strip("-•*0123456789. ").strip().strip('"')


def generate(llm, n_per: int = 6, seed: int = 0) -> dict:
    pool = {"boilerplate": {}, "queries": {}}
    sections = [("boilerplate", BOILERPLATE), ("queries", QUERY_TEMPLATES)]
    for section, src in sections:
        for key, originals in src.items():
            pool[section][key] = {}
            for s in originals:
                if DRY_RUN:
                    cands = [p + s[0].lower() + s[1:] for p in DRY_PREFIXES]
                else:
                    raw = llm.complete(PROMPT.format(n=n_per, s=s), max_tokens=60 * n_per, temperature=0.8, seed=seed)
                    cands = [line for out in raw for line in out.splitlines()]
                kept = []
                for c in cands:
                    if _valid(s, c) and _clean(c) not in kept:
                        kept.append(_clean(c))
                pool[section][key][s] = kept[:n_per]
    return pool


# Variants removed after reading the generated pool (16 Nov 2026). Each line is a variant the model produced that
# passed the mechanical checks but changed the meaning of its template: a placeholder moved to the wrong place, a
# status word replaced by an unrelated one, "record" read as a sports record, or the sense reversed.
REJECTED = {
    "queries": {
        "Q1": ["What stands the status of {H}?"],
        "Q2": ["What project is the company working on {TP}?", "The company is working on {TP}, what project is it?",
               "Could you tell me what project the company is working on {TP}?",
               "What specific project is the company working on {TP}?",
               "The company is currently working on {TP}, what is it?",
               "Could you clarify what project the company is working on {TP}?",
               "Is there planned any {TP} for this quarter?", "Are there any {TP} projects set for this quarter?",
               "Is there any {TP} scheduled for this quarter?", "This quarter, is any {TP} being considered?",
               "Can you confirm if any {TP} is planned for this quarter?",
               "Which {TP} are currently enabled?", "Which {TP} are presently in use?"],
        "Q6": ["Fetch all {D} {TS} that are on file", "I need all {D} {TS} from the records",
               "Supply me with each {D} {TS} available", "Get me each {D} {TS} that is documented",
               "Ensure I have every {D} {TS} documented"],
        "Q7": ["What person sets the record for {H}?", "Which person has the highest score for {H}?",
               "What person claims the record for {H}?"],
        "Q1a": ["Is {H} still operational?", "Is {H} still functional?", "Is {H} still available?",
                "Is {H} still running?", "Is {H} still accessible?", "Is {H} still active?"],
    },
    "boilerplate": {
        "vendor_contract": ["Expiry is reviewed sixty days before renewal"],
        "acquisition_memo": ["Sign off to finalize these indicative figures"],
    },
}


def curate(pool: dict) -> tuple[dict, list[dict]]:
    """Removes the rejected variants from a generated pool. Returns the curated pool and what was removed."""
    removed = []
    out = {"boilerplate": {}, "queries": {}}
    for section in ("boilerplate", "queries"):
        for key, d in pool.get(section, {}).items():
            out[section][key] = {}
            bad = set(REJECTED.get(section, {}).get(key, []))
            for orig, variants in d.items():
                kept = []
                for v in variants:
                    if v in bad:
                        removed.append({"section": section, "key": key, "original": orig, "variant": v})
                    else:
                        kept.append(v)
                out[section][key][orig] = kept
    return out, removed


def write(pool: dict, path: Path | None = None) -> Path:
    path = path or (config.SUITE_DATA / "paraphrases.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pool, indent=1, ensure_ascii=False))
    return path


def summary(pool: dict) -> dict:
    out = {}
    for section in ("boilerplate", "queries"):
        n_orig = sum(len(v) for v in pool[section].values())
        n_var = sum(len(ps) for v in pool[section].values() for ps in v.values())
        out[section] = {"originals": n_orig, "variants_kept": n_var}
    return out
