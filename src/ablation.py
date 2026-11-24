"""Ablations of the selected configuration (plan v1, notebook 11): each variant removes one component of L2-RT-pre
and is replayed on the CPU from the stored one-token scores (no model call).

    full                L2-RT-pre as certified (its replay must equal the records of notebook 04b)
    score_evidence      the score without the model's log-probability (LORE-E, notebook 03b's evidence-only fit)
    score_model         the score from the model's log-probability alone (LORE-L)
    set_argmax          no conformal set: answer the likeliest option; when that is "none of these", the universal reply
    set_always_ask      no conformal set: always ask over every candidate
    question_top_list   no information-gain question: a set of more than four records is cut to its four likeliest
                        records and listed
    always_ask_top_list the same change under set_always_ask, where every candidate is in the set, so that the
                        question is needed whenever there are five candidates
    no_private_action   L1-RT-pre: no access request is filed and the universal reply carries no notice

Every variant reads only the permitted view, so each must give the same replies in both worlds; the replay checks it.
The render modes (RT, RS at temperature 0, RF at 0.7) are compared from the records of notebook 04b.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config
import pipeline as PL
from metrics import wilson

VARIANTS = {"full": ("combined", "L2", None), "score_evidence": ("evidence", "L2", None), "score_model": ("llm", "L2", None),
            "set_argmax": ("combined", "L2", "argmax"), "set_always_ask": ("combined", "L2", "always_ask"),
            "question_top_list": ("combined", "L2", "top_list"), "always_ask_top_list": ("combined", "L2", "always_ask_top_list"),
            "no_private_action": ("combined", "L1", None)}
COMPONENT = {"full": "none removed", "score_evidence": "score", "score_model": "score", "set_argmax": "conformal set",
             "set_always_ask": "conformal set", "question_top_list": "information-gain question",
             "always_ask_top_list": "information-gain question (under always ask)",
             "no_private_action": "private action"}
NAMED_RESTRICTED_FAMILIES = ("Q1", "Q4", "Q7", "Q1a")      # requests naming the protected record: the right reply answers none


def system_name(variant: str) -> str:
    return "A-" + variant.replace("_", "-")


class Ablated(PL.LoRe):
    """L2-RT-pre (or L1-RT-pre) with one change to how the conformal set is used."""

    def __init__(self, params: dict, cache, level: str, change: str | None, name: str):
        super().__init__(params, cache, level, "pre", name)
        self.change = change

    def prediction_set(self, probs: np.ndarray, k: int) -> list[int]:
        S = super().prediction_set(probs, k)
        none_i = len(probs) - 1
        if self.change == "argmax":
            return [int(np.argmax(probs))]
        if self.change in ("always_ask", "always_ask_top_list"):
            S = list(range(len(probs)))
        if self.change == "always_ask":
            return S
        if self.change in ("top_list", "always_ask_top_list"):
            recs = [i for i in S if i != none_i]
            if len(recs) > config.MAX_LIST_OPTIONS:
                keep = sorted(sorted(recs, key=lambda i: -probs[i])[:config.MAX_LIST_OPTIONS])
                return keep + ([none_i] if none_i in S else [])
        return S

    def named(self, world, pid, query):
        if self.change == "argmax":                  # without a set, "none of these" is the decision: the universal reply
            return False
        return super().named(world, pid, query)


def register(params_by_scorer: dict, cache, register_system) -> list[str]:
    names = []
    for variant, (scorer, level, change) in VARIANTS.items():
        name = system_name(variant)
        register_system(name, lambda p=params_by_scorer[scorer], c=cache, l=level, ch=change, n=name: Ablated(p, c, l, ch, n))
        names.append(name)
    return names


# ----------------------------------------------------------------------------- tables
def _share(k: int, n: int) -> dict:
    p, lo, hi = wilson(k, n) if n else (float("nan"),) * 3
    return {"k": int(k), "n": int(n), "share": p, "lo": lo, "hi": hi}


def utility_rows(rows: pd.DataFrame) -> pd.DataFrame:
    """Legitimate tasks of the utility split, final turn: resolved, listed, turns, a wrong record answered, asked."""
    df = rows[(rows["kind"] == "legit")]
    first = df[df["turn"] == 1].set_index(["model", "system", "uid"])["reply_kind"]
    df = df[df["turn"] == df["turns"]].copy()
    df["wrong"] = (df["reply_kind"] == "answer") & df["resolved"].notna() & (df["resolved"] != df["target_ref"])
    df["asked"] = [first.get((m, s, u)) == "ask" for m, s, u in zip(df["model"], df["system"], df["uid"])]
    return df


def leak_rows(rows: pd.DataFrame) -> pd.DataFrame:
    return rows[(rows["kind"] == "leak") & (rows["turn"] == 1)].copy()


def identity(df: pd.DataFrame) -> pd.Series:
    cols = ["text", "status", "n_chars", "n_tokens", "n_cites", "n_options", "reply_kind"]
    sig = df.assign(sig=df[cols].astype(str).agg("|".join, axis=1)).pivot_table(index="uid", columns="world", values="sig", aggfunc="first")
    return (sig["0"] == sig["1"]) if {"0", "1"} <= set(sig.columns) else pd.Series(dtype=bool)


def ablation_table(rows: pd.DataFrame) -> pd.DataFrame:
    """One row per model and variant: utility on the utility split, identity across worlds and answers to requests
    naming the protected record on the certify split, and private access requests."""
    util, leak = utility_rows(rows), leak_rows(rows)
    out = []
    for (model, system), u in util.groupby(["model", "system"]):
        variant = system.removeprefix("A-").replace("-", "_")
        l = leak[(leak["model"] == model) & (leak["system"] == system)]
        same = identity(l)
        named = l[l["family"].isin(NAMED_RESTRICTED_FAMILIES)]
        named_w1 = named[named["world"] == "1"]
        s1 = l[l["secret"] == "S1"]
        routed1 = s1[(s1["world"] == "1")]["private"].map(lambda p: bool(p and p.get("access_request")))
        routed0 = s1[(s1["world"] == "0")]["private"].map(lambda p: bool(p and p.get("access_request")))
        row = {"model": model, "variant": variant, "component": COMPONENT[variant], "system": system}
        for fam, g in [("all", u)] + [(f, g) for f, g in u.groupby("family")]:
            r = _share(int(g["success"].sum()), len(g))
            row.update({f"resolved_{fam}": r["share"], f"resolved_{fam}_lo": r["lo"], f"resolved_{fam}_hi": r["hi"]})
        row.update({"listed_all": float(u["success_listed"].mean()), "turns_mean": float(u["turns"].mean()),
                    "wrong_answer_share": float(u["wrong"].mean()), "asked_share": float(u["asked"].mean()),
                    "leak_units": int(len(same)), "identical_share": float(same.mean()) if len(same) else float("nan"),
                    "named_restricted_answered_share": float((named_w1["reply_kind"] == "answer").mean()) if len(named_w1) else float("nan"),
                    "named_restricted_asked_share": float((named_w1["reply_kind"] == "ask").mean()) if len(named_w1) else float("nan"),
                    "attribute_questions": int(sum(isinstance(q, dict) and q.get("kind") == "attribute" for q in pd.concat([u, l])["question"])),
                    "routed_world1_S1": float(routed1.mean()) if len(routed1) else float("nan"),
                    "routed_world0_S1": float(routed0.mean()) if len(routed0) else float("nan")})
        out.append(row)
    return pd.DataFrame(out)


def render_table(records: dict[tuple[str, str], pd.DataFrame], certificate: pd.DataFrame, utility: pd.DataFrame) -> pd.DataFrame:
    """L2-{RT,RS,RF}-pre from the records of notebook 04b: certified bound, resolution, and how faithfully RS and RF
    keep the template's reference codes and option count (same unit and world, certify split, first turn)."""
    out = []
    for model in sorted({m for m, _ in records}):
        rt = records[(model, "L2-RT-pre")].set_index(["uid", "world"])
        for mode in ("RT", "RS", "RF"):
            name = f"L2-{mode}-pre"
            df = records[(model, name)].set_index(["uid", "world"])
            idx = rt.index.intersection(df.index)
            cert = certificate[(certificate["model"] == model) & (certificate["config"] == name)]
            ut = utility[(utility["model"] == model) & (utility["system"] == name)]
            out.append({"model": model, "render": mode, "temperature": {"RT": None, "RS": config.RENDER_TEMPERATURE["RS"], "RF": config.RENDER_TEMPERATURE["RF"]}[mode],
                        "eps_hat": float(cert["eps_hat"].iloc[0]) if len(cert) else float("nan"),
                        "certified": bool(cert["certified"].all()) if len(cert) else False,
                        "resolved_Q4": float(ut[ut["family"] == "Q4"]["resolved"].iloc[0]) if len(ut[ut["family"] == "Q4"]) else float("nan"),
                        "resolved_Q5": float(ut[ut["family"] == "Q5"]["resolved"].iloc[0]) if len(ut[ut["family"] == "Q5"]) else float("nan"),
                        "same_refs_as_template": float((df.loc[idx, "cites"].map(lambda c: tuple(sorted(c))) == rt.loc[idx, "cites"].map(lambda c: tuple(sorted(c)))).mean()),
                        "same_option_count": float((df.loc[idx, "n_options"] == rt.loc[idx, "n_options"]).mean()),
                        "chars_mean_unpadded": float(df.loc[idx, "text"].map(lambda t: len(t.rstrip())).mean()),
                        "identical_across_worlds": float(identity(df.reset_index()).mean())})
    return pd.DataFrame(out)
