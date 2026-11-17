"""Lexical retrieval used by every system (plan v1, Section 7.1). Deterministic and model-free, so that pre-filter
and post-filter pipelines differ only in which records the index holds.

Score = 2 * name match + body match. Name match is the best character-bigram Dice coefficient between a query token
and a token of the record's title or code name (typo tolerant: "Cedr" against "Cedar" scores 0.57). Body match is a
length-normalised count of query tokens found in the record's searchable text (title, type words, body), with a
light suffix strip so "transactions" finds "transaction".
"""
from __future__ import annotations

import re

import config
from world import TYPE_WORD

STOP = {"the", "a", "an", "of", "on", "in", "is", "are", "any", "me", "for", "to", "what", "which", "who", "can",
        "give", "send", "do", "we", "have", "with", "at", "this", "that", "and", "or", "it", "all", "about", "still",
        "latest", "status", "update", "news", "document", "item", "record", "pull", "up", "list", "every", "file",
        "moment", "currently", "company", "working", "quarter", "planned", "involved", "part", "assigned", "ask",
        "access", "owns", "details", "summarise", "there", "please", "one", "does", "mean", "you", "your", "i",
        "right", "now", "currently", "presently", "being", "under", "linked", "associated", "included", "subject",
        "anything", "include", "involving", "participating", "responsible", "them", "has", "have", "had", "work",
        "working", "works", "engaged", "task", "tasks", "hand", "specify", "could", "tell", "know", "need", "provide",
        "information", "related", "concerning", "regarding", "kind", "data", "possess", "stands", "state", "update",
        "updates", "news", "developments", "recent", "most", "any", "find", "retrieve", "enumerate", "identify",
        "collect", "pinpoint", "fetch", "get", "listed", "documented", "records", "available", "sent", "would", "mind",
        "getting", "possible", "bring", "should", "inquire", "whom", "person", "individual", "anyone", "authority",
        "privileges", "holder", "holds", "suggest", "overview", "brief", "summary", "condensed", "version", "shall",
        "hand", "over", "share", "pass", "supply", "state"}
# words that describe a record's type or place rather than identify it: never used for name matching
GENERIC = {"project", "projects", "investigation", "investigations", "people", "case", "cases", "transaction",
           "transactions", "memo", "supply", "agreement", "contract", "contracts", "ticket", "tickets", "brief",
           "lane", "street", "house", "meeting", "room", "floor", "kitchen", "depot", "reception", "office", "wing",
           "north", "south", "east", "west", "fault", "offline", "failure", "broken", "leak", "jam", "dropouts",
           "lights", "reader", "desk", "water", "heating", "printer", "projector", "flickering", "badge", "door",
           "standing", "acquisition", "acquisitions", "divestment", "divestments", "open", "closed", "deal", "deals"}
TYPE_HINTS = {"project_brief": "project projects brief initiative", "investigation": "investigation investigations case",
              "hr_case": "people case cases grievance", "acquisition_memo": "transaction transactions deal memo acquisition divestment",
              "vendor_contract": "contract contracts supply agreement vendor supplier", "support_ticket": "ticket tickets issue facilities"}


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP]


def stem(t: str) -> str:
    for suf in ("ations", "ation", "ings", "ing", "ies", "es", "s"):
        if t.endswith(suf) and len(t) - len(suf) >= 4:
            return t[: -len(suf)] + ("y" if suf == "ies" else "")
    return t


def bigrams(t: str) -> set[str]:
    t = f" {t} "
    return {t[i:i + 2] for i in range(len(t) - 1)}


def dice(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if a.isdigit() or b.isdigit():          # numbers identify exactly or not at all
        return 0.0
    ba, bb = bigrams(a), bigrams(b)
    return 2 * len(ba & bb) / (len(ba) + len(bb))


def name_tokens(rec: dict) -> list[str]:
    toks = tokens(rec["title"])
    if rec.get("codename"):
        toks.append(rec["codename"].lower())
    return [t for t in toks if (len(t) >= 4 or (t.isdigit() and len(t) >= 3)) and t not in GENERIC]


def query_name_tokens(query: str) -> list[str]:
    return [t for t in tokens(query) if (len(t) >= 4 or (t.isdigit() and len(t) >= 3)) and t not in GENERIC]


def people_tokens(world: dict) -> set[str]:
    """Names of staff in the public directory: a person's name is never a record's name."""
    out = set()
    for p in world["people"]:
        out.add(p["first"].lower())
        out.add(p["last"].lower())
    return out


def name_match(rec: dict, query: str, exclude: set | None = None) -> float:
    q = [t for t in query_name_tokens(query) if not exclude or t not in exclude]
    names = name_tokens(rec)
    best = 0.0
    for qt in q:
        for nt in names:
            best = max(best, dice(qt, nt))
    return best


def searchable(rec: dict) -> list[str]:
    return [stem(t) for t in tokens(rec["title"] + " " + TYPE_HINTS[rec["type"]] + " " + rec["body"])]


def body_match(rec: dict, query: str) -> float:
    q = [stem(t) for t in tokens(query)]
    if not q:
        return 0.0
    bag = set(searchable(rec))
    return sum(1 for t in q if t in bag) / len(q)


def score(rec: dict, query: str, exclude: set | None = None) -> float:
    return 2 * name_match(rec, query, exclude) + body_match(rec, query)


def search(records: list[dict], query: str, k: int = config.TOP_K, exclude: set | None = None) -> list[tuple[dict, float]]:
    """Top-k records by score, ties broken by id. Only records with a non-zero score are returned."""
    scored = [(r, score(r, query, exclude)) for r in records]
    scored = [(r, s) for r, s in scored if s > 0]
    scored.sort(key=lambda rs: (-rs[1], rs[0]["id"]))
    return scored[:k]


def rank_key(rec: dict, query: str, exclude: set | None = None) -> tuple[float, float]:
    """Name match first, then body match (the type word in a request separates records that share a code name)."""
    return (round(name_match(rec, query, exclude), 6), round(body_match(rec, query), 6))


def candidates(records: list[dict], query: str, k: int = config.TOP_K, exclude: set | None = None) -> list[dict]:
    """Records whose name matches the query above the threshold: the candidate set of template systems. Tokens in
    `exclude` (staff names) never count as record names."""
    out = [(r, name_match(r, query, exclude)) for r in records]
    out = [(r, m) for r, m in out if m >= config.MATCH_THRESHOLD]
    out.sort(key=lambda rm: (-rm[1], -body_match(rm[0], query), rm[0]["id"]))
    return [r for r, _ in out[:k]]
