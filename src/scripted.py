"""Deterministic stand-ins for CPU tests and dry runs. Not a result source.

ScriptedLLM reads the same system prompt a model reads (the record blocks with their access lines) and answers the
way deployed assistants are observed to answer: it refuses by naming the restricted record, or follows a stricter
policy with slightly different wording. ScriptedUser answers clarification questions truthfully from the intended
target of a legitimate task, and picks "none of these" when the target is not offered.
"""
from __future__ import annotations

import hashlib
import re

import index as IX

BLOCK_RE = re.compile(r"\[(MH-\d{4})\] (.+?) \((.+?), (.+?)\)\. Access: (.+?)\. Requester may read: (YES|NO)\.\n    (.+)")


class ScriptedLLM:
    def __init__(self, tag: str = "scripted"):
        self.tag = tag

    def _records(self, system_prompt: str) -> list[dict]:
        out = []
        for m in BLOCK_RE.finditer(system_prompt):
            ref, title, rtype, dept, access, may, body = m.groups()
            out.append({"id": len(out), "ref": ref, "title": title, "type": rtype.replace(" ", "_"), "dept": dept,
                        "access": access, "may": may == "YES", "body": body, "codename": None})
        return out

    def chat(self, system_prompt: str, query: str, history: list[dict]):
        recs = self._records(system_prompt)
        strict = "Never confirm or deny" in system_prompt
        named = [r for r in recs if IX.name_match(r, query) >= 0.5]
        topical = [r for r in recs if IX.body_match(r, query) >= 0.5]
        hits = named or topical
        restricted = [r for r in hits if not r["may"]]
        permitted = [r for r in hits if r["may"]]
        if restricted and not strict:
            r = restricted[0]
            text = (f"I'm sorry, I can't share the details of {r['title']} [{r['ref']}]; it is restricted to "
                    f"{r['access']}.")
            if permitted:
                p = permitted[0]
                text += f" I can tell you about {p['title']} [{p['ref']}]: {p['body'].split('. ')[0]}."
        elif permitted:
            if len(permitted) > 1 and not named:
                text = "Here is what is on file: " + "; ".join(f"{p['title']} [{p['ref']}]" for p in permitted[:5]) + "."
            else:
                p = permitted[0]
                text = f"According to {p['title']} [{p['ref']}], {p['body'].split('. ')[0]}."
        elif restricted and strict:
            text = "I couldn't find a record I can share on that. If you have a reference code, send it over."
        else:
            text = "I couldn't find any record about that in the files available to you."
        ntok = len(text.split())
        jitter = int(hashlib.sha1(text.encode()).hexdigest(), 16) % 7 / 100
        return text, ntok, 0.02 * ntok + jitter


class ScriptedUser:
    """Answers a clarification from the intended target: the option whose reference code matches, else none."""

    def __init__(self, target_ref: str):
        self.target_ref = target_ref

    def answer(self, obs: dict) -> str:
        for i, o in enumerate(obs.get("options", [])):
            if o["ref"] == self.target_ref:
                return f"{i + 1}. {o['label']} [{o['ref']}]"
        return "none of these"
