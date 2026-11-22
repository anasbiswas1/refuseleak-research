"""Deterministic stand-ins for CPU tests and dry runs. Not a result source.

ScriptedLLM reads the same system prompt a model reads (the record blocks with their access lines) and answers the
way deployed assistants are observed to answer: it refuses by naming the restricted record, or follows a stricter
policy with slightly different wording. ScriptedUser answers clarification questions truthfully from the intended
target of a legitimate task, and picks "none of these" when the target is not offered.
"""
from __future__ import annotations

import hashlib
import math
import re

import index as IX

TYPE_KEY = {"project brief": "project_brief", "investigation": "investigation", "people case": "hr_case",
            "transaction memo": "acquisition_memo", "vendor contract": "vendor_contract", "support ticket": "support_ticket"}
BLOCK_RE = re.compile(r"\[((?:MH|EN)-\d{4})\] (.+) \((.+?), (.+?)\)\. Access: (.+?)\. Requester may read: (YES|NO)\.\n    (.+)")
# the title is greedy: real email subjects can contain parentheses, and the type and department are the last parenthesis before "Access"


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

    def messages(self, messages: list[dict], max_tokens: int = 300, temperature: float = 0.0) -> str:
        """Stand-in agent for notebook 08: opens the file the request names, follows a suggested name once, and
        reports the reference code or repeats the error it got."""
        import json as _json
        import re as _re
        import agent as AG
        last = messages[-1]
        tried = sum(1 for m in messages if m["role"] == "assistant")
        if last["role"] == "user":
            q, name = last["content"], None
            for t in AG.TEMPLATES:
                pre, post = t.split("{fn}")
                if q.startswith(pre) and q.endswith(post):
                    name = q[len(pre):len(q) - len(post)] if post else q[len(pre):]
                    break
            name = name or q
            return '<function=open_file>' + _json.dumps({"filename": name}) + '</function>'
        if last["role"] == "tool":
            d = _json.loads(last["content"])
            if "error" in d:
                m = _re.search(r"similar names you can open: '([^']+)'", d["error"])
                if m and tried < 2:
                    return '<function=open_file>' + _json.dumps({"filename": m.group(1)}) + '</function>'
                if tried < 2 and "operation failed" in d["error"].lower():
                    q = next(x["content"] for x in messages if x["role"] == "user")
                    word = max(_re.findall(r"[a-z]{5,}", q.lower()), key=len, default="file")
                    return '<function=search_files_by_filename>' + _json.dumps({"filename": word}) + '</function>'
                return "I could not open that file. " + d["error"].split(": ", 1)[-1]
            res = str(d.get("result", ""))
            if res.startswith("[") and tried < 3:
                hits = _re.findall(r'"filename": "([^"]+)"', res)
                if len(hits) == 1:
                    return '<function=open_file>' + _json.dumps({"filename": hits[0]}) + '</function>'
                return "I found these files: " + ", ".join(hits[:5]) + "." if hits else "I found no matching file."
            m = _re.search(r"Reference code: ([A-Z]{3}-[0-9]{4})", res)
            return f"The reference code is {m.group(1)}." if m else "I opened the file but found no reference code."
        return "Done."

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


    # --- multiple-choice scoring for the clarifier (deterministic stand-in for the model's letter log-probabilities)
    OPTION_RE = re.compile(r"^([A-J])\) (.+?) \[((?:MH|EN)-\d{4})\] \((.+?), (.+?)\)$", re.M)

    def complete(self, prompt: str, max_tokens: int = 120, temperature: float = 0.7, n: int = 1, seed: int = 0) -> list[str]:
        """Deterministic stand-in for a rendered reply: echoes the slot lines of the prompt in a fixed wording."""
        marker = next((m for m in ("SLOTS\n", "FACTS\n") if m in prompt), None)
        body = prompt.split(marker, 1)[1] if marker else prompt
        lines = [l.strip(" -") for l in body.splitlines() if l.strip()]
        text = "Here is what I can tell you. " + " ".join(lines)
        return [text[: max_tokens * 4]] * n

    def choice_logprobs(self, system_prompt: str, user_prompt: str, letters: str) -> dict:
        if "Statement:" in user_prompt:                      # the judge attacker (notebook 05): a deterministic stand-in
            reply = user_prompt.split("Reply:", 1)[1].split("Statement:", 1)[0]
            statement = user_prompt.split("Statement:", 1)[1]
            caps = [w.strip(".,;") for w in statement.split() if w[:1].isupper() and len(w) > 3]
            hit = any(w in reply for w in caps[1:])          # skip the first word of the sentence
            jitter = (int(hashlib.sha1(user_prompt.encode()).hexdigest(), 16) % 100) / 500
            pa = min(0.95, max(0.05, (0.7 if hit else 0.3) + jitter))
            return {"A": math.log(pa), "B": math.log(1 - pa)}
        request = user_prompt.split("Request: ", 1)[1].split("\n", 1)[0]
        opts = self.OPTION_RE.findall(user_prompt)
        scores = {}
        best = 0.0
        for letter, title, ref, rtype, dept in opts:
            rec = {"title": title, "codename": None, "type": TYPE_KEY.get(rtype, "project_brief"), "body": "", "id": 0}
            nm = IX.name_match(rec, request)
            tw = 1.0 if any(w in request.lower() for w in rtype.lower().split()) else 0.0
            jitter = (int(hashlib.sha1((request + ref).encode()).hexdigest(), 16) % 100) / 400
            scores[letter] = 4.0 * nm + 2.0 * tw + jitter
            best = max(best, nm)
        none_letter = letters[len(opts)]
        scores[none_letter] = 3.0 if best < 0.95 else 1.0      # no exact name among the options: lean to 'none'
        z = {k: v for k, v in scores.items()}
        m = max(z.values())
        lse = m + math.log(sum(math.exp(v - m) for v in z.values()))
        return {k: v - lse for k, v in z.items()}


class ScriptedUser:
    """Answers a clarification from the intended target: the listed option whose reference code matches, the
    target's value for an attribute question, else "none of these"."""

    def __init__(self, target_ref: str, target: dict | None = None, world: dict | None = None):
        self.target_ref, self.target, self.world = target_ref, target, world

    def answer(self, obs: dict) -> str:
        if obs.get("question") and obs["question"].get("attribute") and self.target is not None:
            from clarifier import attribute_value_label
            value = attribute_value_label(self.target, obs["question"]["attribute"], self.world)
            if self.target_ref in obs["question"]["set"]:
                return value
            return "none of these"
        for i, o in enumerate(obs.get("options", [])):
            if o["ref"] == self.target_ref:
                return f"{i + 1}. {o['label']} [{o['ref']}]"
        return "none of these"
