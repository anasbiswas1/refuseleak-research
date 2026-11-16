"""Permitted views (Equation 1), low-equivalence of paired worlds (Equation 2) and the requester-view projection of
tool status codes. Everything a leak-free system shows the requester must be a function of what this module returns."""
from __future__ import annotations

import hashlib
import json


def can_read(person: dict, rec: dict) -> bool:
    acl = rec["acl"]
    return "all" in acl["depts"] or person["dept"] in acl["depts"] or person["pid"] in acl["people"]


def person(world: dict, pid: int) -> dict:
    return world["people"][pid]


def permitted_view(world: dict, pid: int) -> list[dict]:
    """V_u(D): the records the requester may read, in id order."""
    p = person(world, pid)
    return [r for r in world["records"] if can_read(p, r)]


def restricted_records(world: dict, pid: int) -> list[dict]:
    p = person(world, pid)
    return [r for r in world["records"] if not can_read(p, r)]


def view_hash(world: dict, pid: int) -> str:
    """Hash of the permitted view, the requester's own entry and the public people directory."""
    view = permitted_view(world, pid)
    blob = json.dumps({"view": view, "me": person(world, pid), "people": world["people"]}, sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()


def low_equivalent(w0: dict, w1: dict, pid: int) -> bool:
    """Equation 2: the requester's permitted views of the two worlds are identical."""
    return view_hash(w0, pid) == view_hash(w1, pid)


def acl_label(rec: dict, world: dict) -> str:
    acl = rec["acl"]
    if "all" in acl["depts"]:
        return "all staff"
    parts = []
    if acl["depts"]:
        parts.append(", ".join(acl["depts"]) + " department" + ("s" if len(acl["depts"]) > 1 else ""))
    if acl["people"]:
        parts.append("named staff: " + ", ".join(world["people"][p]["name"] for p in acl["people"]))
    return "; ".join(parts)


# ----------------------------------------------------------------------------- tool status projection
PRIVILEGED_STATUS = {"ok": "ok", "forbidden": "403 forbidden", "not_found": "404 not found"}


def requester_view_status(status: str) -> str:
    """The requester-visible status: 403 and 404 collapse to one code, so existence cannot be read off the code."""
    return "ok" if status == "ok" else "no accessible item"
