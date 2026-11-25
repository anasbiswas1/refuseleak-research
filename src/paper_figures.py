"""Figures 1 to 8 and the tables of the paper (plan v1, Section 13; notebook 12), drawn from committed reports only.

Every figure is saved as PNG at 600 dpi and as PDF, with the paper's names in legends and axes (never code keys)
and no title inside the figure: the caption carries it. Widths follow a two-column journal page: 7.2 in for a
full-width figure.
"""
from __future__ import annotations

import gzip
import json
import re
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch  # noqa: E402

DPI = 600
FULL_W = 7.2
MODELS = {"qwen25_7b": "Qwen2.5-7B-Instruct", "llama31_8b": "Llama-3.1-8B-Instruct"}
SYSTEMS = {"B0": "B0 Privileged agent", "B1": "B1 Privacy prompt", "B2": "B2 Output redaction", "B3": "B3 Triggered refusal",
           "B4": "B4 Universal reply", "B5": "B5 Post-filter RAG", "B6": "B6 Typed collapse", "O1": "O1 Permitted-view oracle",
           "O2": "O2 Full-view clarifier", "L2-RT-pre": "SameView (selected)"}
ATTACKERS = {"D1": "D1 Bag of words", "D2": "D2 Embedding kNN", "D3": "D3 Entailment", "D4": "D4 LLM judge",
             "D5": "D5 Side channels", "D6": "D6 Stack", "D7": "D7 Fine-tuned entailment"}
SCALE_MODELS = {"qwen25_14b": "Qwen2.5-14B-Instruct (4-bit)"}
FAMILIES = {"Q1": "Q1 direct", "Q1a": "Q1a direct, attribute", "Q2": "Q2 topic", "Q2a": "Q2a topic, attribute", "Q3": "Q3 person",
            "Q3b": "Q3b person, type-aware", "Q4": "Q4 near-name", "Q5": "Q5 ambiguous", "Q6": "Q6 aggregate", "Q7": "Q7 access"}    # notebook 14: the scale check on the Domain 1 held-out test
TIE = "Several tied"            # more than one attacker at the largest advantage (tables with seven attackers)
ADAPTIVE = {"A1": "A1 Attribute search", "A2": "A2 Five-query entailment", "A3": "A3 Count and list", "A4": "A4 Misspelt names"}
LEVELS = {"L0": "L0 Universal reply", "L1": "L1 Clarifier", "L2": "L2 Clarifier and private action", "L3": "L3 Leak notice (positive control)"}
RENDERS = {"RT": "Template", "RS": "Slot-restricted LLM", "RF": "Free LLM"}
RETRIEVALS = {"pre": "Pre-filter", "post": "Post-filter"}
ARMS = {"raw": "Raw tool outputs", "generic": "Generic error", "trimmed": "Requester-view listing", "projection": "Requester-view projection (SameView)"}
ABLATIONS = {"full": "SameView as certified", "score_evidence": "Score: permitted-view evidence only", "score_model": "Score: model log-probability only",
             "set_argmax": "No conformal set: answer the likeliest", "set_always_ask": "No conformal set: always ask",
             "question_top_list": "No attribute question: list the four likeliest", "always_ask_top_list": "Always ask, no attribute question",
             "no_private_action": "No private action (L1)"}
# Okabe-Ito colour-blind safe palette
C = {"black": "#000000", "orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442", "blue": "#0072B2",
     "vermillion": "#D55E00", "purple": "#CC79A7", "grey": "#7F7F7F"}
LEVEL_COLOR = {"L0": C["grey"], "L1": C["sky"], "L2": C["blue"], "L3": C["vermillion"]}
RENDER_MARKER = {"RT": "o", "RS": "s", "RF": "^"}
MODEL_STYLE = {"qwen25_7b": "-", "llama31_8b": "--"}
SYSTEM_COLOR = {"L2-RT-pre": C["blue"], "B1": C["purple"], "B3": C["vermillion"], "B5": C["orange"]}


def style():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
                         "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
                         "lines.linewidth": 1.2, "savefig.dpi": DPI, "pdf.fonttype": 42, "ps.fonttype": 42})


CODE_KEY = re.compile(r"qwen25_7b|llama31_8b|\bL[0-3]-R[TSF]-(?:pre|post)\b|adv_|eps_hat|resolved_|_share\b")


def figure_text(fig) -> list:
    """Every string drawn in the figure (titles, labels, tick labels, legends, annotations)."""
    from matplotlib.text import Text
    return [t.get_text() for t in fig.findobj(Text) if t.get_text().strip()]


def save(fig, out: Path, name: str) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    code_keys = sorted({t for t in figure_text(fig) if CODE_KEY.search(t)})
    w, h = fig.get_size_inches()
    fig.savefig(out / f"{name}.png", dpi=DPI, bbox_inches=None, facecolor="white")
    fig.savefig(out / f"{name}.pdf", bbox_inches=None, facecolor="white")
    plt.close(fig)
    return {"name": name, "width_in": round(float(w), 2), "height_in": round(float(h), 2), "dpi": DPI,
            "png_pixels": [int(round(w * DPI)), int(round(h * DPI))], "code_keys": code_keys}


def box(ax, x, y, w, h, text, fc, ec="#333333", fs=7, bold_first=True, lw=0.8, ls="-", radius=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.004,rounding_size={radius}", fc=fc, ec=ec, lw=lw, ls=ls))
    lines = text.split("\n")
    if bold_first and len(lines) > 1:
        ax.text(x + w / 2, y + h - 0.012, lines[0], ha="center", va="top", fontsize=fs, fontweight="bold")
        ax.text(x + w / 2, y + h / 2 - 0.012, "\n".join(lines[1:]), ha="center", va="center", fontsize=fs - 0.8, linespacing=1.15)
    else:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold_first else "normal")


def arrow(ax, p, q, color="#333333", ls="-", lw=1.0, text=None, tx=0.0, ty=0.0, fs=6.3, rad=0.0, style_="-|>"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style_, mutation_scale=8, color=color, lw=lw, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=1, shrinkB=1))
    if text:
        ax.text((p[0] + q[0]) / 2 + tx, (p[1] + q[1]) / 2 + ty, text, fontsize=fs, ha="center", va="center", color=color,
                bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))


# ----------------------------------------------------------------------------- Figure 1: framework
def figure1(out: Path) -> dict:
    style()
    fig = plt.figure(figsize=(FULL_W, 4.7))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    bands = [(0.71, 0.27, "#FBE3D6", "#D55E00", "Privileged\nband", "sees every record,\naccess list and\nowner; never\nreplies to the user"),
             (0.37, 0.29, "#DCEBF7", "#0072B2", "Requester-\nview band", "sees only the\nrecords this\nrequester may\nopen; the only\nband that replies"),
             (0.03, 0.29, "#DDF1E6", "#009E73", "Release band\n(offline)", "runs the built\npipeline on\npaired worlds\nbefore\ndeployment")]
    for y, h, fc, ec, title, sub in bands:
        ax.add_patch(FancyBboxPatch((0.012, y), 0.976, h, boxstyle="round,pad=0.002,rounding_size=0.012", fc=fc, ec=ec, lw=1.0))
        ax.add_patch(FancyBboxPatch((0.018, y + 0.008), 0.118, h - 0.016, boxstyle="round,pad=0.002,rounding_size=0.01", fc="white", ec=ec, lw=0.6, alpha=0.75))
        ax.text(0.077, y + h - 0.025, title, fontsize=8, fontweight="bold", color=ec, va="top", ha="center", linespacing=1.05)
        ax.text(0.077, y + h / 2 - 0.035, sub, fontsize=6.0, color="#333333", va="center", ha="center", style="italic", linespacing=1.12)
    # privileged band
    box(ax, 0.16, 0.75, 0.17, 0.15, "Access lists\nowners, labels,\nwho may open what", "white")
    box(ax, 0.37, 0.75, 0.17, 0.15, "Full index\nall records,\nrestricted ones included", "white")
    box(ax, 0.57, 0.75, 0.17, 0.15, "Private actions\naccess request filed\nwith the owner", "white")
    box(ax, 0.80, 0.75, 0.175, 0.15, "K1 Controller\npermission checks,\naudit log", "white")
    arrow(ax, (0.33, 0.825), (0.37, 0.825))
    arrow(ax, (0.80, 0.825), (0.74, 0.825))
    ax.text(0.77, 0.84, "after\nthe reply", fontsize=5.2, ha="center", va="bottom", color="#333333", linespacing=1.0)
    # requester-view band
    box(ax, 0.17, 0.44, 0.18, 0.16, "K2 Projector\nbuilds the requester's\nindex; 403 and 404\nbecome one code", "white")
    box(ax, 0.40, 0.44, 0.18, 0.16, "K3 Conformal clarifier\nscores candidates and\n\"none of these\"; answers,\nasks or gives one reply", "white")
    box(ax, 0.63, 0.44, 0.165, 0.16, "K4 Renderer\ntemplate or slot-bound\nLLM; length bucket;\nlatency floor", "white")
    box(ax, 0.85, 0.47, 0.125, 0.10, "Requester\nasks and reads\nthe reply", "white", ec=C["blue"])
    arrow(ax, (0.35, 0.52), (0.40, 0.52))
    arrow(ax, (0.58, 0.52), (0.63, 0.52))
    arrow(ax, (0.795, 0.525), (0.85, 0.525), text="reply", ty=0.022)
    # the query: from the requester, under the chain, into K2
    ax.plot([0.912, 0.912, 0.26], [0.47, 0.405, 0.405], color="#333333", lw=1.0)
    arrow(ax, (0.26, 0.405), (0.26, 0.44))
    ax.text(0.59, 0.405, "query", fontsize=6.3, ha="center", va="center", bbox=dict(fc="#DCEBF7", ec="none", pad=0.4))
    # crossings between the privileged and requester bands
    arrow(ax, (0.43, 0.75), (0.30, 0.60), color=C["blue"], lw=1.4)
    ax.text(0.30, 0.685, "permitted view only", fontsize=6.3, color=C["blue"], ha="right", va="center", fontweight="bold")
    ax.annotate("", xy=(0.49, 0.605), xytext=(0.49, 0.75),
                arrowprops=dict(arrowstyle="-|>", color=C["vermillion"], lw=1.0, ls=(0, (3, 2)), mutation_scale=8))
    ax.text(0.49, 0.685, "\u2715", fontsize=12, color=C["vermillion"], ha="center", va="center", fontweight="bold",
            bbox=dict(fc="white", ec="none", pad=0.1))
    ax.text(0.51, 0.685, "restricted records never reach K3 or K4", fontsize=6.3, color=C["vermillion"], ha="left", va="center")
    arrow(ax, (0.912, 0.57), (0.89, 0.75), color=C["vermillion"], ls=(0, (3, 2)), lw=0.9)
    ax.text(0.93, 0.685, "query", fontsize=6.0, color=C["vermillion"], ha="left", va="center")
    # release band
    box(ax, 0.16, 0.07, 0.18, 0.16, "Paired worlds\nsame permitted view;\nthe protected fact\ntrue in one only", "white")
    box(ax, 0.38, 0.07, 0.18, 0.16, "Attacker family\nD1 to D6, trained on\nboth worlds and frozen", "white")
    box(ax, 0.60, 0.07, 0.18, 0.16, "K5 Certificate\nLearn-then-Test bounds\nevery attacker's advantage\nat \u03b5 with probability 1 \u2212 \u03b4", "white")
    box(ax, 0.82, 0.07, 0.155, 0.16, "Configuration \u03bb*\nthe most useful\ncertified setting", "white")
    arrow(ax, (0.34, 0.15), (0.38, 0.15)); arrow(ax, (0.56, 0.15), (0.60, 0.15)); arrow(ax, (0.78, 0.15), (0.82, 0.15))
    arrow(ax, (0.90, 0.23), (0.86, 0.37), color=C["green"], lw=1.4)
    ax.text(0.905, 0.345, "fixes \u03bb*", fontsize=6.3, color=C["green"], ha="left", va="center", fontweight="bold")
    arrow(ax, (0.22, 0.37), (0.24, 0.23), color=C["green"], lw=1.0, ls=(0, (3, 2)))
    ax.text(0.245, 0.345, "K2 to K4 run on both worlds", fontsize=6.3, color=C["green"], ha="left", va="center")
    return save(fig, out, "figure1_framework")


# ----------------------------------------------------------------------------- Figure 2: paired-world game
def figure2(out: Path) -> dict:
    style()
    fig = plt.figure(figsize=(FULL_W, 2.9))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    perm = ["Cedar Lane supply agreement", "Water leak, Cedar meeting room", "Larch transaction memo"]

    def world(y, label, hidden):
        ax.add_patch(FancyBboxPatch((0.015, y), 0.335, 0.41, boxstyle="round,pad=0.003,rounding_size=0.015", fc="#F7F7F7", ec="#555555", lw=0.8))
        ax.text(0.03, y + 0.385, label, fontsize=7.2, fontweight="bold", va="top")
        ax.add_patch(FancyBboxPatch((0.028, y + 0.03), 0.205, 0.285, boxstyle="round,pad=0.002,rounding_size=0.01", fc="none", ec=C["blue"], lw=0.9, ls=(0, (4, 2))))
        ax.text(0.13, y + 0.292, "permitted view", fontsize=5.6, color=C["blue"], ha="center", va="center", style="italic")
        for i, p in enumerate(perm):
            ax.add_patch(FancyBboxPatch((0.04, y + 0.195 - i * 0.075), 0.18, 0.058, boxstyle="round,pad=0.002,rounding_size=0.008", fc="#DCEBF7", ec=C["blue"], lw=0.6))
            ax.text(0.13, y + 0.224 - i * 0.075, p, fontsize=5.4, ha="center", va="center")
        if hidden:
            ax.add_patch(FancyBboxPatch((0.248, y + 0.06), 0.09, 0.22, boxstyle="round,pad=0.002,rounding_size=0.008", fc="#FBE3D6", ec=C["vermillion"], lw=0.8))
            ax.text(0.293, y + 0.17, "Project\nCedar\nmemo\n(restricted)", fontsize=5.4, ha="center", va="center", color="#8A2B00")
        else:
            ax.add_patch(FancyBboxPatch((0.248, y + 0.06), 0.09, 0.22, boxstyle="round,pad=0.002,rounding_size=0.008", fc="white", ec="#AAAAAA", lw=0.6, ls=(0, (2, 2))))
            ax.text(0.293, y + 0.17, "no such\nrecord", fontsize=5.4, ha="center", va="center", color="#777777")

    world(0.545, "World 0: the protected fact is false", False)
    world(0.045, "World 1: the protected fact is true", True)
    ax.text(0.13, 0.5, "= same in both worlds", fontsize=6.0, color=C["blue"], ha="center", va="center", fontweight="bold")
    box(ax, 0.40, 0.41, 0.10, 0.18, "Coin b\nworld b\nis drawn", "white")
    arrow(ax, (0.35, 0.75), (0.40, 0.55)); arrow(ax, (0.35, 0.25), (0.40, 0.45))
    box(ax, 0.545, 0.39, 0.14, 0.22, "Assistant\nthe built pipeline\nanswers the\nattacker's request", "#DCEBF7", ec=C["blue"])
    arrow(ax, (0.50, 0.50), (0.545, 0.50))
    box(ax, 0.73, 0.39, 0.12, 0.22, "Reply y\ntext, options,\nerror code,\ncitations,\nlength, time", "white")
    arrow(ax, (0.685, 0.50), (0.73, 0.50))
    box(ax, 0.885, 0.39, 0.10, 0.22, "Attacker\nguesses\n\u0062\u0302 from y", "#FBE3D6", ec=C["vermillion"])
    arrow(ax, (0.85, 0.50), (0.885, 0.50))
    ax.text(0.69, 0.17, "advantage = |2 \u00b7 Pr[\u0062\u0302 = b] \u2212 1|\n0 means the reply tells the attacker nothing about b",
            fontsize=7.2, ha="center", va="center", bbox=dict(fc="#FFFBEA", ec="#C9A400", lw=0.7, boxstyle="round,pad=0.4"))
    ax.text(0.69, 0.83, "The attacker chooses the request and knows the requester's permitted view.\nIt does not know which world was drawn.",
            fontsize=6.6, ha="center", va="center", style="italic", color="#333333")
    return save(fig, out, "figure2_paired_worlds")


# ----------------------------------------------------------------------------- Figure 3: mechanism on Project Cedar
CEDAR_UNITS = {"Q1": ("test-00828", "What do we have on the Cedar memo?"), "Q5": ("test-00765", "Can you retrieve Cedar for me?"),
               "Q7": ("test-00717", "Is there anyone who can provide access to Project Cedar?")}


def cedar_replies(reports: Path, model: str = "qwen25_7b") -> dict:
    """Turn-1 replies of B1, B3, B4 (notebook 06 records) and SameView (notebook 04b records, test split) for the three
    Project Cedar units, in both worlds."""
    want = {u: f for f, (u, _) in CEDAR_UNITS.items()}
    out = {}
    for name, src in (("B1", "06_records"), ("B3", "06_records"), ("B4", "06_records"), ("L2-RT-pre", "04b_records")):
        with gzip.open(reports / src / model / f"{name}.jsonl.gz", "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["uid"] in want and r["turn"] == 1 and r["kind"] == "leak" and (name != "L2-RT-pre" or r.get("runtime") == "3"):
                    out[(want[r["uid"]], name, r["world"])] = r["text"].rstrip()
    return out


def short(t: str, width: int, lines: int) -> str:
    """Wrap each line of a reply separately (lists keep their line breaks) and cut after a number of lines."""
    out = []
    for para in t.replace("\r", "").split("\n"):
        para = " ".join(para.split())
        if para:
            out += textwrap.wrap(para, width, subsequent_indent="   " if para[:2].rstrip(".").isdigit() else "")
    return "\n".join(out[:lines]) + (" \u2026" if len(out) > lines else "")


def figure3(out: Path, reports: Path) -> dict:
    style()
    rep = cedar_replies(reports)
    cols = ["B1", "B3", "B4", "L2-RT-pre"]
    fig = plt.figure(figsize=(FULL_W, 7.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    x0, cw, top, bottom = 0.135, 0.2155, 0.965, 0.045
    for j, s in enumerate(cols):
        ax.text(x0 + j * cw + cw / 2, top, SYSTEMS[s], fontsize=7.6, fontweight="bold", ha="center", va="center",
                color=C["blue"] if s == "L2-RT-pre" else "#222222")
    rh = (top - 0.02 - bottom) / 3
    for i, fam in enumerate(["Q1", "Q5", "Q7"]):
        y = top - 0.02 - (i + 1) * rh
        ax.text(0.012, y + rh / 2, short(f"\u201c{CEDAR_UNITS[fam][1]}\u201d", 17, 6), fontsize=6.6, va="center", ha="left", style="italic")
        for j, s in enumerate(cols):
            t0, t1 = rep.get((fam, s, "0"), ""), rep.get((fam, s, "1"), "")
            same = t0 == t1
            ec = C["green"] if same else C["vermillion"]
            ch = rh / 2 - 0.022
            for k, (wk, t) in enumerate((("0", t0), ("1", t1))):
                yy = y + rh / 2 - 0.004 if k == 0 else y + 0.012
                ax.add_patch(FancyBboxPatch((x0 + j * cw + 0.004, yy), cw - 0.012, ch, boxstyle="round,pad=0.002,rounding_size=0.008",
                                            fc="#FAFAFA" if wk == "0" else "#F1F1F1", ec=ec, lw=0.9))
                ax.text(x0 + j * cw + 0.010, yy + ch - 0.008, f"World {wk}", fontsize=5.6, fontweight="bold", va="top", color="#555555")
                ax.text(x0 + j * cw + 0.010, yy + ch - 0.026, short(t, 35, 9), fontsize=5.0, va="top", ha="left", linespacing=1.12)
            ax.text(x0 + j * cw + cw - 0.010, y + rh - 0.024, "same in both worlds" if same else "differs between worlds",
                    fontsize=5.4, ha="right", va="bottom", color=ec, fontweight="bold")
    legend = [Patch(fc="white", ec=C["green"], label="reply identical in both worlds: nothing to learn"),
              Patch(fc="white", ec=C["vermillion"], label="reply changes with the hidden record: a leak")]
    ax.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.55, -0.004), ncol=2, frameon=False, fontsize=6.6)
    return save(fig, out, "figure3_cedar_mechanism")


# ----------------------------------------------------------------------------- Figure 4: frontier
def frontier_data(reports: Path, cert_file: str = "04b_certificate.csv", util_file: str = "04b_utility.csv") -> pd.DataFrame:
    cert = pd.read_csv(reports / cert_file)
    ut = pd.read_csv(reports / util_file)
    e = cert.groupby(["model", "config"]).agg(eps_hat=("eps_hat", "first"), certified=("certified", "all")).reset_index()
    u = ut[ut["family"].isin(["Q4", "Q5"])].groupby(["model", "system"])["resolved"].mean().rename("success").reset_index()
    df = e.merge(u, left_on=["model", "config"], right_on=["model", "system"], how="left").drop(columns="system")
    parts = df["config"].str.split("-", expand=True)
    return df.assign(level=parts[0], render=parts[1], retrieval=parts[2])


def figure4(out: Path, reports: Path, selected: dict, eps: float, cert_file: str = "04b_certificate.csv") -> dict:
    style()
    df = frontier_data(reports, cert_file)
    jitter = {"RT": -0.014, "RS": 0.0, "RF": 0.014}
    lvl_shift = {"L0": 0.0, "L1": -0.005, "L2": 0.005, "L3": 0.0}
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 3.1), sharey=True)
    for ax, (m, mname) in zip(axes, MODELS.items()):
        d = df[df["model"] == m]
        ax.axhspan(0, eps, color=C["green"], alpha=0.06, lw=0)
        ax.axhline(eps, color="#444444", lw=0.8, ls=(0, (4, 2)))
        ax.text(0.405, eps + 0.005, f"\u03b5 = {eps:.2f}: certified at or below", fontsize=6.3, color="#444444")
        for r in d.itertuples():
            x = r.success + jitter[r.render] + lvl_shift[r.level]
            filled = r.retrieval == "pre"
            ax.scatter(x, r.eps_hat, s=26, marker=RENDER_MARKER[r.render], facecolor=LEVEL_COLOR[r.level] if filled else "white",
                       edgecolor=LEVEL_COLOR[r.level], lw=1.0, zorder=3)
            if r.config == selected[m]:
                ax.scatter(x, r.eps_hat, s=150, marker="o", facecolor="none", edgecolor="black", lw=1.0, zorder=4)
                ax.annotate("selected \u03bb*", (x, r.eps_hat), xytext=(-62, -16), textcoords="offset points", fontsize=6.5,
                            arrowprops=dict(arrowstyle="-", lw=0.6))
        l3 = d[d["level"] == "L3"]
        ax.annotate("L3 positive\ncontrol: rejected", (l3["success"].mean() - 0.02, l3["eps_hat"].median()), xytext=(-78, 0),
                    textcoords="offset points", fontsize=6.3, color=C["vermillion"], va="center",
                    arrowprops=dict(arrowstyle="-", lw=0.6, color=C["vermillion"]))
        l0 = d[d["level"] == "L0"]
        ax.annotate("L0: never asks,\nloses half the requests", (l0["success"].mean() + 0.02, l0["eps_hat"].max()), xytext=(14, 10),
                    textcoords="offset points", fontsize=6.3, color="#555555", arrowprops=dict(arrowstyle="-", lw=0.6, color="#777777"))
        ax.set_xlabel("Clarification success")
        ax.text(0.5, 1.02, mname, transform=ax.transAxes, ha="center", fontsize=7.6, fontweight="bold")
        ax.set_xlim(0.40, 1.02)
        ax.set_ylim(0.0, max(0.36, df["eps_hat"].max() + 0.02))
        ax.grid(alpha=0.25, lw=0.5)
    axes[0].set_ylabel("Certified bound \u03b5\u0302")
    handles = [Patch(fc=LEVEL_COLOR[k], ec=LEVEL_COLOR[k], label=v) for k, v in LEVELS.items()]
    handles += [Line2D([], [], ls="", marker=RENDER_MARKER[k], mfc="#999999", mec="#666666", label=f"{v} wording") for k, v in RENDERS.items()]
    handles += [Line2D([], [], ls="", marker="o", mfc="#666666", mec="#666666", label="Pre-filter retrieval (filled)"),
                Line2D([], [], ls="", marker="o", mfc="white", mec="#666666", label="Post-filter retrieval (open)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=6.3, bbox_to_anchor=(0.5, 0.0), columnspacing=1.5)
    fig.subplots_adjust(left=0.08, right=0.99, top=0.92, bottom=0.36, wspace=0.08)
    return save(fig, out, "figure4_frontier")


# ----------------------------------------------------------------------------- Figure 5: heatmap
def figure5(out: Path, reports: Path, att_file: str = "04b_attackers.csv") -> dict:
    style()
    a = pd.read_csv(reports / att_file)
    order = ["B0", "B1", "B2", "B3", "B5", "O2", "B4", "B6", "O1", "L2-RT-pre"]
    cols = [k for k in ATTACKERS if k in set(a["attacker"])]
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 3.8), sharey=True)
    for ax, (m, mname) in zip(axes, MODELS.items()):
        p = a[a["model"] == m].pivot_table(index="system", columns="attacker", values="adv").reindex(order)[cols]
        lo = a[a["model"] == m].pivot_table(index="system", columns="attacker", values="adv_lo").reindex(order)[cols]
        im = ax.imshow(p.to_numpy(), cmap="Reds", vmin=0, vmax=0.6, aspect="auto")
        for i in range(p.shape[0]):
            for j in range(p.shape[1]):
                v, l = p.iat[i, j], lo.iat[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6, color="white" if v > 0.42 else "black",
                        fontweight="bold" if l > 0.10 else "normal")
        ax.set_xticks(range(len(cols))); ax.set_xticklabels([ATTACKERS[k] for k in cols], fontsize=6.2, rotation=35, ha="right", rotation_mode="anchor")
        ax.set_yticks(range(len(order))); ax.set_yticklabels([SYSTEMS[s] for s in order])
        ax.axhline(5.5, color="black", lw=0.8)
        ax.text(0.5, 1.02, mname, transform=ax.transAxes, ha="center", fontsize=7.6, fontweight="bold")
        ax.tick_params(length=0)
        for sp in ax.spines.values():
            sp.set_visible(False)
    cb = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02, extend="max")
    cb.set_label("Attacker advantage, held-out test units")
    fig.subplots_adjust(left=0.2, right=0.88, top=0.93, bottom=0.2, wspace=0.06)
    return save(fig, out, "figure5_advantage_heatmap")


# ----------------------------------------------------------------------------- Figure 6: adaptive attackers
def figure6(out: Path, reports: Path) -> dict:
    style()
    a = pd.read_csv(reports / "09_adaptive.csv")
    a = a[a["secret"] == "all"]
    best = a.groupby(["model", "system", "attacker", "k"])["acc"].max().reset_index()
    fig, axes = plt.subplots(1, 4, figsize=(FULL_W, 2.5), sharey=True)
    for ax, (att, aname) in zip(axes, ADAPTIVE.items()):
        d = best[best["attacker"] == att]
        for (m, s), g in d.groupby(["model", "system"]):
            ax.plot(g["k"], g["acc"], ls=MODEL_STYLE[m], color=SYSTEM_COLOR.get(s, "#333333"), marker="o", ms=2.5, lw=1.1)
        ax.axhline(0.5, color="#888888", lw=0.6)
        ax.axhline(0.55, color="#888888", lw=0.6, ls=(0, (2, 2)))
        ax.set_xticks(sorted(d["k"].unique()))
        ax.set_xlabel("Turns")
        ax.text(0.5, 1.03, aname, transform=ax.transAxes, ha="center", fontsize=7.2, fontweight="bold")
        ax.set_ylim(0.4, 1.02)
        ax.grid(alpha=0.25, lw=0.5)
    axes[0].set_ylabel("Best attacker accuracy")
    handles = [Line2D([], [], color=SYSTEM_COLOR[s], lw=1.4, label=SYSTEMS[s]) for s in ("L2-RT-pre", "B1", "B3", "B5")]
    handles += [Line2D([], [], color="#333333", ls=MODEL_STYLE[m], label=n) for m, n in MODELS.items()]
    handles += [Line2D([], [], color="#888888", lw=0.6, label="chance (0.5)"), Line2D([], [], color="#888888", lw=0.6, ls=(0, (2, 2)), label="accuracy 0.55 (advantage 0.10)")]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, fontsize=6.3)
    fig.subplots_adjust(left=0.07, right=0.99, top=0.9, bottom=0.36, wspace=0.08)
    return save(fig, out, "figure6_adaptive_attackers")


# ----------------------------------------------------------------------------- Figure 7: coverage against alpha
ALPHA_GRID = tuple(float(a) for a in np.round(np.arange(0.02, 0.3001, 0.01), 2))


def coverage_grid(reports: Path, alphas=ALPHA_GRID, scorer: str = "combined") -> pd.DataFrame:
    """Coverage and mean set size of the selected scorer on notebook 03b's test tasks, for a grid of alpha, from the
    committed parameters and stored scores (thresholds per tie-size stratum recomputed for each alpha, as in 03b)."""
    import calibrate as CB
    import clarifier as CL
    import config
    import world as W
    pool = W.load_pool()
    tasks = CB.task_lists(pool)
    rows, units = CB.prompt_rows(tasks), CB.unit_map(tasks)
    params = json.load(open(reports / "03b_params.json"))
    out = []
    for m in MODELS:
        cache = CL.ScoreCache(reports / "03_scores" / f"{m}.jsonl")
        X = CB.design_rows(rows, units, cache)
        cov = CB.coverage_table_v2(rows, X, params[m][scorer], alphas=alphas)
        out.append(cov[cov["subset"] == "exchangeable"].assign(model=m, scorer=scorer))
    return pd.concat(out, ignore_index=True)


def figure7(out: Path, cov: pd.DataFrame) -> dict:
    """cov: alpha, model, coverage, coverage_lo, coverage_hi, mean_set_size (the exchangeable test tasks)."""
    style()
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.6))
    for m, mname in MODELS.items():
        d = cov[cov["model"] == m].sort_values("alpha")
        axes[0].plot(d["alpha"], d["coverage"], ls=MODEL_STYLE[m], color=C["blue"], marker="o", ms=1.8, label=mname)
        axes[0].fill_between(d["alpha"], d["coverage_lo"], d["coverage_hi"], color=C["blue"], alpha=0.12 if m == "qwen25_7b" else 0.06, lw=0)
        axes[1].plot(d["alpha"], d["mean_set_size"], ls=MODEL_STYLE[m], color=C["orange"], marker="o", ms=1.8, label=mname)
    al = np.linspace(cov["alpha"].min(), cov["alpha"].max(), 50)
    axes[0].plot(al, 1 - al, color="#444444", lw=0.8, ls=(0, (4, 2)), label="target 1 − α")
    axes[0].set_xlabel("Miscoverage level α"); axes[0].set_ylabel("Coverage of the intended option")
    axes[1].set_xlabel("Miscoverage level α"); axes[1].set_ylabel("Mean prediction-set size")
    for ax in axes:
        ax.grid(alpha=0.25, lw=0.5)
        ax.axvline(0.10, color="#888888", lw=0.6, ls=":")
    axes[0].legend(frameon=False, fontsize=6.4, loc="lower left")
    axes[1].legend(frameon=False, fontsize=6.4)
    fig.subplots_adjust(left=0.08, right=0.99, top=0.96, bottom=0.17, wspace=0.28)
    return save(fig, out, "figure7_coverage")


# ----------------------------------------------------------------------------- Figure 8: side channel
def figure8(out: Path, reports: Path) -> dict:
    style()
    d = pd.read_csv(reports / "10_figure8.csv.gz")
    fig, axes = plt.subplots(2, 2, figsize=(FULL_W, 4.4))
    rows = (("L2-RT-pre", "Pre-filter retrieval (L2, template): the two worlds coincide"),
            ("L2-RT-post", "Post-filter retrieval (L2, template): restricted records take retrieval slots"))
    for i, (sys_, label) in enumerate(rows):
        g = d[d["system"] == sys_]
        bins = np.arange(0, max(701, int(g["raw_chars"].max()) + 21), 20)
        for w, col, ls, lw in (("0", C["sky"], "-", 2.2), ("1", C["vermillion"], (0, (3, 1.5)), 1.1)):
            x = g[g["world"].astype(str) == w]["raw_chars"]
            axes[i, 0].hist(x, bins=bins, histtype="step", lw=lw, ls=ls, color=col, density=True, label=f"World {w}")
        axes[i, 0].set_ylabel("Density")
        cites = sorted(g["n_cites"].unique())
        width = 0.38
        for k, (w, col) in enumerate((("0", C["sky"]), ("1", C["vermillion"]))):
            x = g[g["world"].astype(str) == w]["n_cites"]
            share = [float((x == c).mean()) for c in cites]
            axes[i, 1].bar(np.arange(len(cites)) + (k - 0.5) * width, share, width=width, color=col, label=f"World {w}")
        axes[i, 1].set_xticks(range(len(cites))); axes[i, 1].set_xticklabels([str(int(c)) for c in cites])
        axes[i, 1].set_ylabel("Share of replies")
        axes[i, 0].text(0.0, 1.07, label, transform=axes[i, 0].transAxes, fontsize=7.4, fontweight="bold", ha="left")
        for ax in axes[i]:
            ax.grid(alpha=0.25, lw=0.5)
    axes[1, 0].set_xlabel("Reply length before padding (characters)")
    axes[1, 1].set_xlabel("Records cited in the reply")
    axes[0, 1].legend(frameon=False, fontsize=6.6)
    fig.subplots_adjust(left=0.08, right=0.99, top=0.93, bottom=0.11, hspace=0.42, wspace=0.22)
    return save(fig, out, "figure8_side_channel")


def session_table(reports: Path, file: str = "15_session_certificate.csv") -> pd.DataFrame:
    """The certificate over multi-turn sessions: the deployed configuration and the controls, per model."""
    d = pd.read_csv(reports / file)
    rows = []
    for _, r in d.sort_values(["role", "model", "system"], ascending=[False, True, True]).iterrows():
        rows.append({"Model": MODELS.get(r["model"], r["model"]), "System": SYSTEMS.get(r["system"], r["system"]),
                     "Role": "deployed configuration" if r["role"] == "deployed" else "control",
                     "Sessions": int(r["sessions"]), "Attackers (policy, pool, learner)": int(r["attackers"]),
                     "Largest advantage": round(float(r["max_adv"]), 3), "Upper bound (95%)": round(float(r["max_adv_hi"]), 3),
                     "Certified bound": round(float(r["eps_hat"]), 2), "Certified at 0.10": "yes" if bool(r["certified"]) else "no"})
    return pd.DataFrame(rows)


def scale_table(reports: Path, main_file: str = "14_main.csv", base_file: str = "13_main_meridian.csv") -> pd.DataFrame:
    """Domain 1 held-out test with seven attackers: largest attacker advantage and share of mistyped and ambiguous
    requests resolved, per system, for the two main models and the larger responder of notebook 14."""
    d = pd.concat([pd.read_csv(reports / base_file), pd.read_csv(reports / main_file)], ignore_index=True)
    names = {**MODELS, **SCALE_MODELS}
    order = ["B0", "B1", "B2", "B3", "B5", "O2", "B4", "B6", "O1", "L2-RT-pre"]
    rows = []
    for s in [x for x in order if x in set(d["system"])]:
        r = {"System": SYSTEMS.get(s, s)}
        for m, name in names.items():
            x = d[(d["model"] == m) & (d["system"] == s)]
            r[f"{name}: largest attacker advantage"] = float(x["max_adv"].iloc[0]) if len(x) else float("nan")
        for m, name in names.items():
            x = d[(d["model"] == m) & (d["system"] == s)]
            r[f"{name}: resolved"] = float(x["resolved_legit"].iloc[0]) if len(x) else float("nan")
        rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- Figure 10: the leak by query family
def figure10(out: Path, fam: pd.DataFrame) -> dict:
    """Strongest attacker's advantage per query family (columns) and system (rows), Domain 1 held-out test, both
    models. Cells with a lower 95% bound above 0.10 are marked."""
    style()
    order = ["B0", "B1", "B2", "B3", "B5", "O2", "B4", "B6", "O1", "L2-RT-pre"]
    fams = [f for f in FAMILIES if f in set(fam["family"])]
    models = [m for m in MODELS if m in set(fam["model"])]
    fig, axes = plt.subplots(1, len(models), figsize=(FULL_W, 3.6), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, m in zip(axes, models):
        d = fam[fam["model"] == m]
        p = d.pivot_table(index="system", columns="family", values="adv").reindex(order)[fams]
        lo = d.pivot_table(index="system", columns="family", values="adv_lo").reindex(order)[fams]
        im = ax.imshow(p.to_numpy(), cmap="Reds", vmin=0, vmax=1, aspect="auto")
        for i in range(len(order)):
            for j in range(len(fams)):
                v, l = p.iloc[i, j], lo.iloc[i, j]
                if np.isnan(v):
                    ax.text(j, i, "n/a", ha="center", va="center", fontsize=5.4, color="#777777")
                    continue
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=5.6,
                        color="white" if v > 0.55 else ("#888888" if l == 0 else "#222222"), fontweight="bold" if l > 0.10 else "normal")
        ax.set_xticks(range(len(fams))); ax.set_xticklabels([FAMILIES[f] for f in fams], fontsize=6.0, rotation=35, ha="right", rotation_mode="anchor")
        ax.set_yticks(range(len(order))); ax.set_yticklabels([SYSTEMS[k] for k in order], fontsize=6.6)
        ax.set_title(MODELS[m], fontsize=8, pad=4)
        ax.axhline(5.5, color="#333333", lw=0.8)
        ax.tick_params(length=0)
    fig.subplots_adjust(left=0.185, right=0.895, top=0.93, bottom=0.26, wspace=0.07)
    cax = fig.add_axes([0.91, 0.26, 0.012, 0.67])
    cb = fig.colorbar(im, cax=cax)
    cb.set_label("Strongest attacker's advantage, held-out test units", fontsize=6.6)
    cb.ax.tick_params(labelsize=6.2)
    return save(fig, out, "figure10_family_heatmap")


# ----------------------------------------------------------------------------- Figure 9: the certificate against the number of certify units
SENS_CLASS = {"pre": "Pre-filter, levels L0 to L2", "post": "Post-filter, levels L0 to L2", "L3": "L3 positive control"}
SENS_COLOR = {"pre": C["blue"], "post": C["green"], "L3": C["vermillion"]}
DOMAIN_STYLE = {"meridian": "-", "enron": "--"}
DOMAIN_NAME = {"meridian": "Domain 1 (synthetic enterprise)", "enron": "Domain 2 (Enron e-mail)"}


def figure9(out: Path, sens: pd.DataFrame, eps: float, n_eq19: dict) -> dict:
    """Median certified bound with its 10th to 90th percentile band (left) and the share of configurations certified
    at eps (right) against the number of certify units, from random subsets of the stored per-unit guesses."""
    style()
    top = max(0.5, float(np.ceil(sens.groupby(["domain", "class", "n"])["eps_hat"].quantile(0.9).max() * 20) / 20) + 0.05)
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.9))
    for dom in [d for d in DOMAIN_STYLE if d in set(sens["domain"])]:
        d = sens[sens["domain"] == dom]
        for cls in SENS_CLASS:
            g = d[d["class"] == cls]
            if g.empty:
                continue
            q = g.groupby("n")["eps_hat"].quantile([0.1, 0.5, 0.9]).unstack()
            share = g.groupby("n")["certified"].mean()
            axes[0].plot(q.index, q[0.5], ls=DOMAIN_STYLE[dom], color=SENS_COLOR[cls], marker="o", ms=2.2)
            if dom == "meridian":
                axes[0].fill_between(q.index, q[0.1], q[0.9], color=SENS_COLOR[cls], alpha=0.14, lw=0)
            nudge = {"pre": 0.0, "post": 0.012, "L3": -0.012}[cls]          # post-filter and L3 both sit at zero: drawn apart
            axes[1].plot(share.index, share.values + (nudge if share.max() == 0 else 0.0), ls=DOMAIN_STYLE[dom], color=SENS_COLOR[cls], marker="o", ms=2.2)
    for ax in axes:
        ax.set_xscale("log")
        ax.set_xticks([250, 500, 1000, 2000, 3000])
        ax.set_xticklabels(["250", "500", "1,000", "2,000", "3,000"])
        ax.minorticks_off()
        for dom, n_d in n_eq19.items():
            ax.axvline(n_d, color="#555555", lw=0.7, ls=":")
        ax.set_xlabel("Certify units n")
        ax.grid(alpha=0.25, lw=0.5)
    axes[0].axhline(eps, color="#444444", lw=0.8, ls=(0, (4, 2)))
    axes[0].text(260, eps + 0.008, f"\u03b5 = {eps:.2f}", fontsize=6.3, color="#444444")
    for dom, n_d in n_eq19.items():
        axes[0].text(n_d * 0.97, top - 0.005, f"{n_d:,}", rotation=90, ha="right", va="top", fontsize=5.8, color="#555555")
    axes[0].text(max(n_eq19.values()) * 1.05, top - 0.005, "Equation 19,\n80% power", fontsize=6.0, color="#555555", va="top")
    axes[0].set_ylabel("Certified bound \u03b5\u0302")
    axes[0].set_ylim(0, top)
    axes[1].set_ylabel(f"Share certified at \u03b5 = {eps:.2f}")
    axes[1].set_ylim(-0.03, 1.03)
    handles = [Line2D([], [], color=SENS_COLOR[k], lw=1.6, label=v) for k, v in SENS_CLASS.items()]
    handles += [Line2D([], [], color="#555555", ls=DOMAIN_STYLE[k], lw=1.0, label=v) for k, v in DOMAIN_NAME.items() if k in set(sens["domain"])]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=6.4, bbox_to_anchor=(0.5, 0.0))
    fig.subplots_adjust(left=0.08, right=0.99, top=0.97, bottom=0.29, wspace=0.28)
    return save(fig, out, "figure9_sensitivity")


def check_figure_file(path: Path, width_in: float) -> dict:
    """Pixel size of a saved PNG and the resolution at the intended printed width."""
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size
    return {"file": path.name, "pixels": [w, h], "dpi_at_print_width": round(w / width_in, 1)}


# ============================================================================= Tables (plan Section 13)
DOMAINS = {"meridian": "Domain 1 (synthetic enterprise)", "enron": "Domain 2 (Enron e-mail)"}
CHANNELS = {"as_built": "As built", "no_padding": "Padding removed", "length": "Length only", "citations": "Citations only",
            "options": "Options only", "status": "Status code only", "latency": "Latency only"}
LEARNERS = {"bow": "Bag of words", "nli": "Entailment", "side": "Side channels", "stack": "Stack"}
COMPONENT_NAMES = {"none removed": "none", "score": "candidate score", "conformal set": "conformal set",
                   "information-gain question": "attribute question", "information-gain question (under always ask)":
                   "attribute question (under always ask)", "private action": "private access request"}


def config_parts(cfg: str) -> tuple:
    """'L2-RT-pre' -> ('L2 Clarifier and private action', 'Template', 'Pre-filter')."""
    level, render, retrieval = cfg.split("-")
    return LEVELS[level], RENDERS[render], RETRIEVALS[retrieval]


def system_name(s: str) -> str:
    if s in SYSTEMS:
        return SYSTEMS[s]
    if s.count("-") == 2 and s.split("-")[0] in LEVELS:
        return ", ".join(config_parts(s))
    return s


def config_label(cfg: str) -> str:
    """Configuration name for tables that list configurations; the selected one is marked."""
    return ", ".join(config_parts(cfg)) + (" (selected: SameView)" if cfg == "L2-RT-pre" else "")


def overlap_table(plan: Path) -> pd.DataFrame:
    """The overlap table of plan Section 2, as written before any method code."""
    text = Path(plan).read_text(encoding="utf-8")
    start = text.index("# 2. What already exists")
    end = text.index("**Classical ideas", start)
    rows = []
    for line in text[start:end].splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|-: "):
            continue
        rows.append([c.strip().replace("**", "") for c in line.strip("|").split("|")])
    return pd.DataFrame(rows[1:], columns=rows[0])


def baseline_table(reports: Path, sources=(("04b_main.csv", "meridian"), ("07d_main.csv", "enron"))) -> pd.DataFrame:
    """Held-out leakage and utility of the baselines, the references and the selected configuration, both domains."""
    out = []
    for f, dom in sources:
        d = pd.read_csv(reports / f)
        out.append(pd.DataFrame({
            "Domain": DOMAINS[dom], "Model": d["model"].map(MODELS), "System": d["system"].map(system_name),
            "Identical replies across worlds": d["identical_share"], "Largest attacker advantage": d["max_adv"],
            "Upper bound (95%)": d["max_adv_hi"], "Strongest attacker": d["worst_attacker"].map({**ATTACKERS, "tie": TIE}),
            "Protected fact stated in world 1": d["disclosure_world1"],
            "Resolved: mistyped and ambiguous requests": d["resolved_legit"],
            "Resolved: authorised requests": d["resolved_auth"],
            "Resolved on a fresh draw: mistyped and ambiguous": d.get("resolved_legit_fresh", np.nan),
            "Resolved on a fresh draw: authorised": d.get("resolved_auth_fresh", np.nan)}))
    return pd.concat(out, ignore_index=True).round(3)


def certification_table(reports: Path, sources=(("04b_certificate.csv", "04b_utility.csv", "meridian"),
                                               ("07d_certificate.csv", "07d_utility.csv", "enron"))) -> pd.DataFrame:
    """Certified bound per configuration and model, with clarification success, both domains."""
    out = []
    for cert_f, ut_f, dom in sources:
        cert, ut = pd.read_csv(reports / cert_f), pd.read_csv(reports / ut_f)
        e = cert.groupby(["model", "config"]).agg(eps_hat=("eps_hat", "first"), certified=("certified", "all"),
                                                  worst=("adv_hi", "max")).reset_index()
        u = ut[ut["family"].isin(["Q4", "Q5"])].assign(k=lambda x: x["resolved"] * x["n"]).groupby(["model", "system"])
        u = (u["k"].sum() / u["n"].sum()).rename("success").reset_index()
        df = e.merge(u, left_on=["model", "config"], right_on=["model", "system"], how="left")
        for m in MODELS:
            g = df[df["model"] == m]
            for _, r in g.iterrows():
                lv, rd, rt = config_parts(r["config"])
                out.append({"Domain": DOMAINS[dom], "Model": MODELS[m], "Level": lv, "Wording": rd, "Retrieval": rt,
                            "Certified bound": r["eps_hat"], "Certified at 0.10": "yes" if r["certified"] else "no",
                            "Clarification success": r["success"], "_order": r["config"]})
    t = pd.DataFrame(out)
    lvl = {v: i for i, v in enumerate(LEVELS.values())}
    rnd = {v: i for i, v in enumerate(RENDERS.values())}
    t = t.assign(_l=t["Level"].map(lvl), _r=t["Wording"].map(rnd), _p=(t["Retrieval"] == "Post-filter").astype(int),
                 _m=t["Model"].map({v: i for i, v in enumerate(MODELS.values())}), _d=t["Domain"].map({v: i for i, v in enumerate(DOMAINS.values())}))
    t = t.sort_values(["_d", "_m", "_l", "_r", "_p"]).drop(columns=["_order", "_l", "_r", "_p", "_m", "_d"])
    return t.reset_index(drop=True).round(3)


def ablation_table(reports: Path) -> pd.DataFrame:
    d = pd.read_csv(reports / "11_ablation.csv")
    order = {k: i for i, k in enumerate(ABLATIONS)}
    d = d.assign(_v=d["variant"].map(order), _d=d["domain"].map({"meridian": 0, "enron": 1}),
                 _m=d["model"].map({m: i for i, m in enumerate(MODELS)})).sort_values(["_d", "_m", "_v"])
    return pd.DataFrame({
        "Domain": d["domain"].map(DOMAINS), "Model": d["model"].map(MODELS), "Variant": d["variant"].map(ABLATIONS),
        "Component removed": d["component"].map(lambda c: COMPONENT_NAMES.get(c, c)),
        "Resolved": d["resolved_all"], "Wrong record given": d["wrong_answer_share"], "Asked a question": d["asked_share"],
        "Mean turns": d["turns_mean"], "Attribute questions asked": d["attribute_questions"],
        "Access request filed when the record exists": d["routed_world1_S1"],
        "Identical replies across worlds": d["identical_share"]}).reset_index(drop=True).round(3)


def render_table(reports: Path) -> pd.DataFrame:
    d = pd.read_csv(reports / "11_render.csv")
    d = d.assign(_m=d["model"].map({m: i for i, m in enumerate(MODELS)}), _r=d["render"].map({r: i for i, r in enumerate(RENDERS)}))
    d = d.sort_values(["_m", "_r"])
    return pd.DataFrame({
        "Model": d["model"].map(MODELS), "Wording": d["render"].map(RENDERS),
        "Temperature": d["temperature"].map(lambda t: "none" if pd.isna(t) else f"{t:g}"),
        "Certified bound": d["eps_hat"], "Certified at 0.10": d["certified"].map({True: "yes", False: "no"}),
        "Resolved: mistyped": d["resolved_Q4"], "Resolved: ambiguous": d["resolved_Q5"],
        "Same record codes as the template": d["same_refs_as_template"], "Same number of options": d["same_option_count"],
        "Mean reply length (characters)": d["chars_mean_unpadded"],
        "Identical replies across worlds": d["identical_across_worlds"]}).reset_index(drop=True).round(3)


def agent_table(reports: Path, file: str = "08b_agent.csv") -> pd.DataFrame:
    d = pd.read_csv(reports / file)
    order = {k: i for i, k in enumerate(ARMS)}
    d = d.assign(_a=d["system"].map(order), _m=d["model"].map({m: i for i, m in enumerate(MODELS)})).sort_values(["_m", "_a"])
    return pd.DataFrame({
        "Model": d["model"].map(MODELS), "Error handling": d["system"].map(ARMS),
        "Identical replies across worlds": d["identical_share"], "Largest attacker advantage": d["max_adv"],
        "Upper bound (95%)": d["max_adv_hi"], "Strongest attacker": d["worst_attacker"].map({**ATTACKERS, "tie": TIE}),
        "Restricted file named in world 1": d["disclosure_world1"], "Owner named in world 1": d["owner_named_world1"],
        "Task completion": d["completion"], "Mean tool calls": d["mean_tool_calls_leak"]}).reset_index(drop=True).round(3)


def adaptive_table(reports: Path) -> pd.DataFrame:
    d = pd.read_csv(reports / "09_main.csv")
    sys_order = {"L2-RT-pre": 0, "B1": 1, "B3": 2, "B5": 3}
    d = d.assign(_s=d["system"].map(sys_order), _m=d["model"].map({m: i for i, m in enumerate(MODELS)})).sort_values(["_m", "attacker", "_s"])
    return pd.DataFrame({
        "Model": d["model"].map(MODELS), "Attacker": d["attacker"].map(ADAPTIVE), "System": d["system"].map(system_name),
        "Test units": d["test_units"], "Identical transcripts across worlds": d["identical_share"],
        "Advantage after one turn": d["adv_turn1"], "Advantage after the last turn": d["adv_last"],
        "Upper bound (95%)": d["adv_last_hi"], "Best learner": d["best_learner_last"].map(LEARNERS),
        "Protected fact stated in world 1": d["disclosure_world1"]}).reset_index(drop=True).round(3)


def side_table(reports: Path) -> pd.DataFrame:
    """Side-channel attacker advantage per channel set: baselines (train to test) and the 24 configurations (train to certify)."""
    d = pd.read_csv(reports / "10_side.csv")
    piv = d.pivot_table(index=["source", "model", "system"], columns="channels", values=["adv", "adv_hi"]).reset_index()
    rows = []
    for _, r in piv.iterrows():
        held = r[("source", "")].startswith("06")
        row = {"Units": "held-out test" if held else "certify split", "Model": MODELS[r[("model", "")]],
               "System": system_name(r[("system", "")]) if held else config_label(r[("system", "")])}
        for ch, name in CHANNELS.items():
            row[f"{name}: advantage"] = r[("adv", ch)]
            row[f"{name}: upper bound"] = r[("adv_hi", ch)]
        rows.append(row)
    t = pd.DataFrame(rows)
    cfgs = [f"{l}-{r}-{p}" for l in LEVELS for r in RENDERS for p in RETRIEVALS]
    rank = {**{system_name(k): i for i, k in enumerate(SYSTEMS)}, **{config_label(k): 100 + i for i, k in enumerate(cfgs)}}
    t = t.assign(_u=(t["Units"] == "certify split").astype(int), _m=t["Model"].map({v: i for i, v in enumerate(MODELS.values())}),
                 _s=t["System"].map(rank)).sort_values(["_u", "_m", "_s"]).drop(columns=["_u", "_m", "_s"])
    return t.reset_index(drop=True).round(3)


def paired_timing(reports: Path) -> pd.DataFrame:
    """Per configuration, the same certify units measured in both worlds: mean difference in raw reply time and in
    tokens (world 1 minus world 0) and two-sided Wilcoxon signed-rank p-values."""
    from scipy import stats
    import side as SD
    out = []
    for m in MODELS:
        f = reports / "10_timing" / f"{m}.jsonl.gz"
        if not f.exists():
            continue
        df = SD.load_timing(f)
        df = df[df["split"] != "train"].assign(world=lambda x: x["world"].astype(int))
        for sysn, g in df.groupby("system"):
            lat = g.pivot_table(index="uid", columns="world", values="latency_raw").dropna()
            tok = g.pivot_table(index="uid", columns="world", values="n_tokens").dropna()
            dl, dt = lat[1] - lat[0], tok[1] - tok[0]
            pt = float(stats.wilcoxon(dt[dt != 0]).pvalue) if int((dt != 0).sum()) >= 10 else 1.0
            out.append({"model": m, "system": sysn, "units": int(len(dl)), "time_diff_s": float(dl.mean()),
                        "time_p": float(stats.wilcoxon(dl).pvalue), "tokens_diff": float(dt.mean()), "tokens_p": pt})
    return pd.DataFrame(out)


def timing_table(reports: Path) -> pd.DataFrame:
    """Measured reply times (the larger of the two worlds), the paired difference between worlds on the same certify
    units, and the frozen timing attacker with the floor off and on."""
    t = pd.read_csv(reports / "10_timing.csv")
    a = pd.read_csv(reports / "10_timing_attackers.csv")
    pt = paired_timing(reports).set_index(["model", "system"])
    g = t.groupby(["model", "system"]).agg(median=("median_s", "max"), p99=("p99_s", "max"), mx=("max_s", "max")).reset_index()
    rows = []
    for _, r in g.iterrows():
        sel = a[(a["model"] == r["model"]) & (a["system"] == r["system"])].set_index("channels")
        rows.append({"Model": MODELS[r["model"]], "Configuration": config_label(r["system"]),
                     "Median reply time (s)": r["median"], "99th percentile (s)": r["p99"], "Longest (s)": r["mx"],
                     "Paired time difference, world 1 minus world 0 (s)": pt.loc[(r["model"], r["system"]), "time_diff_s"],
                     "Paired time difference: Wilcoxon p": pt.loc[(r["model"], r["system"]), "time_p"],
                     "Paired token difference": pt.loc[(r["model"], r["system"]), "tokens_diff"],
                     "Paired token difference: Wilcoxon p": pt.loc[(r["model"], r["system"]), "tokens_p"],
                     "Timing attacker, no floor: advantage": sel.loc["latency_floor_off", "adv"],
                     "Timing attacker, no floor: upper bound": sel.loc["latency_floor_off", "adv_hi"],
                     "Timing attacker, 1 s floor: advantage": sel.loc["latency_floor_on", "adv"],
                     "Timing attacker, 1 s floor: upper bound": sel.loc["latency_floor_on", "adv_hi"]})
    t = pd.DataFrame(rows)
    order = {config_label(k): i for i, k in enumerate(["L2-RT-pre", "L2-RT-post", "L2-RF-pre", "L2-RF-post"])}
    t = t.assign(_m=t["Model"].map({v: i for i, v in enumerate(MODELS.values())}), _s=t["Configuration"].map(order))
    return t.sort_values(["_m", "_s"]).drop(columns=["_m", "_s"]).reset_index(drop=True).round(3)


TABLES = {"table1_overlap": ("Overlap with existing work, disclosed before any method code (plan Section 2).", None),
          "table2_baselines": ("Held-out leakage and utility of the baselines, the references and SameView.", baseline_table),
          "table3_certification": ("Certified bound and clarification success for every configuration.", certification_table),
          "table4_ablations": ("Ablations of SameView, replayed from the stored scores.", ablation_table),
          "table5_wording": ("Wording mode of the replies: template, slot-restricted and free LLM.", render_table),
          "table6_agent": ("Privileged tool-using agent (AgentDojo workspace) with four kinds of error handling.", agent_table),
          "table7_adaptive": ("Adaptive multi-turn attackers against SameView and the baselines.", adaptive_table),
          "table8_side_channels": ("Side-channel attacker advantage per channel set.", side_table),
          "table9_timing": ("Measured reply time and the timing attacker.", timing_table)}


def md_table(df: pd.DataFrame, digits: int = 3) -> str:
    """A plain Markdown table (pandoc converts it to a Word table)."""
    def cell(v):
        if isinstance(v, float):
            return "" if np.isnan(v) else f"{v:.{digits}f}"
        return str(v).replace("|", "/")
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "|".join("---" for _ in df.columns) + "|"]
    lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)



TABLE_NOTES = {
    "table2_baselines": "Advantage is |2 x accuracy - 1| of the strongest frozen attacker on held-out test units (one hash-picked world per unit); the upper bound is the Wilson 95% limit. Resolved: share of mistyped (Q4) and ambiguous (Q5) requests for which the user reaches the intended permitted record, and share of authorised requests (Q8) answered. SameView is the selected configuration of each domain and model. Fresh draw (Domain 2 only): legitimate and authorised units drawn after the clarifier rule of runtime 3 was fixed, for the systems that use the clarifier or the permitted view.",
    "table3_certification": "Certified bound: the smallest epsilon at which the Learn-then-Test procedure certifies the configuration against all six attackers with probability 0.95 (certify split). Clarification success: resolved share of mistyped and ambiguous requests on the utility split. Domain 2 certifies ten configurations: the eight template ones and the two LLM-worded variants of the level selected in Domain 1.",
    "table4_ablations": "Each variant removes one component from the selected configuration and is replayed from the stored candidate scores. Access request filed when the record exists: share of existence requests in world 1 for which the private controller files a request with the record's owner (the reply is the same in both worlds).",
    "table8_side_channels": "One attacker (gradient boosting) per channel set, trained on the train split and frozen; advantage on one hash-picked world per unit. Held-out test rows are the baselines; certify-split rows are the 24 configurations.",
    "table9_timing": "Times measured live on one L4 GPU with fresh scores and fresh free-text wording (no caches). Paired difference: the same certify units in both worlds. With the 1 s floor every template reply takes exactly 1 s, so the attacker sees identical times and its accuracy equals the share of world-1 units among the 600 (advantage 0.057); the upper bound reflects the sample size, not a difference between the worlds. Free-text replies take 4 to 14 s, above the floor.",
}


def write_tables(reports: Path, plan: Path, out: Path, tables: dict | None = None, notes: dict | None = None,
                 title: str = "# Tables (drawn from the committed reports)") -> dict:
    """Every table (or the `tables` given: name -> (caption, builder of the reports folder)) as CSV, plus tables.md."""
    tables, notes = (TABLES if tables is None else tables), (TABLE_NOTES if notes is None else notes)
    out.mkdir(parents=True, exist_ok=True)
    md, info = [title, ""], {}
    for name, (caption, fn) in tables.items():
        df = overlap_table(plan) if fn is None else fn(reports)
        df.to_csv(out / f"{name}.csv", index=False)
        md += [f"## {name.split('_')[0].capitalize().replace('Table', 'Table ')}", "", caption, "", md_table(df), ""]
        if name in notes:
            md += [f"Note. {notes[name]}", ""]
        info[name] = {"rows": int(len(df)), "columns": list(df.columns)}
    (out / "tables.md").write_text("\n".join(md), encoding="utf-8")
    return info



# ============================================================================= Headline numbers
def _f(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 4)


def headline_numbers(reports: Path, cov: pd.DataFrame) -> dict:
    """The numbers the manuscript quotes, read from the committed reports (one place, so text and tables agree)."""
    n = {"epsilon": 0.10, "delta": 0.05, "domains": {}}
    leaky = ["B0", "B1", "B2", "B3", "B5", "O2"]
    for dom, main_f, sel_f in (("domain1", "04b_main.csv", "04b_selection.json"), ("domain2", "07d_main.csv", "07d_selection.json")):
        d, sel = pd.read_csv(reports / main_f), json.load(open(reports / sel_f))
        n["domains"][dom] = {}
        for m in MODELS:
            g = d[d["model"] == m].set_index("system")
            sm = sel["models"][m]
            lam = sm["selected"]
            eps = sm["eps_hat"] if isinstance(sm["eps_hat"], dict) else None
            cert = pd.read_csv(reports / main_f.replace("main", "certificate"))
            cm = cert[cert["model"] == m].groupby("config")["eps_hat"].first()
            worst = g.loc[leaky, "max_adv"].idxmax()
            n["domains"][dom][m] = {
                "selected": lam, "eps_hat_selected": _f(cm.get(lam)), "certified": f"{sm['n_certified']} of {len(cm)}",
                "L3_all_rejected": bool(sm["checks"]["L3_all_rejected"]), "post_filter_certified": len(sm["checks"]["post_certified"]),
                "lore_heldout_max_adv": _f(g.loc["L2-RT-pre", "max_adv"]), "lore_heldout_upper": _f(g.loc["L2-RT-pre", "max_adv_hi"]),
                "lore_resolved_legit": _f(g.loc["L2-RT-pre", "resolved_legit"]), "lore_resolved_auth": _f(g.loc["L2-RT-pre", "resolved_auth"]),
                "lore_resolved_legit_fresh": _f(g.loc["L2-RT-pre"].get("resolved_legit_fresh")),
                "lore_resolved_auth_fresh": _f(g.loc["L2-RT-pre"].get("resolved_auth_fresh")),
                "universal_reply_resolved_legit": _f(g.loc["B4", "resolved_legit"]), "oracle_resolved_legit": _f(g.loc["O1", "resolved_legit"]),
                "worst_baseline": worst, "worst_baseline_max_adv": _f(g.loc[worst, "max_adv"]),
                "baselines_with_lower_bound_above_eps": None}
            att = pd.read_csv(reports / main_f.replace("main", "attackers"))
            a = att[(att["model"] == m) & att["system"].isin(leaky)]
            n["domains"][dom][m]["baselines_with_lower_bound_above_eps"] = sorted(a[a["adv_lo"] > 0.10]["system"].unique().tolist())
            if eps is not None and lam in eps:
                n["domains"][dom][m]["eps_hat_selected"] = _f(eps[lam])
        if "C4_coverage" in sel["models"][next(iter(MODELS))]:
            n["domains"][dom]["c4_coverage_alpha_0.10"] = {m: {k: _f(v) if not isinstance(v, (bool, str)) else v
                                                         for k, v in sel["models"][m]["C4_coverage"].items()} for m in MODELS}
    n["coverage_domain1"] = {m: {f"{a:.2f}": {"coverage": _f(r["coverage"]), "lower": _f(r["coverage_lo"]), "set_size": _f(r["mean_set_size"])}
                                 for a, r in cov[cov["model"] == m].set_index("alpha").iterrows() if round(a, 2) in (0.05, 0.10, 0.20)}
                             for m in MODELS}
    ad = pd.read_csv(reports / "09_main.csv")
    n["adaptive"] = {m: {"lore_max_adv_last": _f(ad[(ad.model == m) & (ad.system == "L2-RT-pre")]["adv_last"].max()),
                         "lore_max_upper_any_turn": _f(ad[(ad.model == m) & (ad.system == "L2-RT-pre")]["max_adv_hi_any_k"].max()),
                         "controls_last_turn": {f"{r.attacker}-{r.system}": _f(r.adv_last) for r in ad[(ad.model == m) & (ad.system != "L2-RT-pre")].itertuples()}}
                     for m in MODELS}
    ag = pd.read_csv(reports / "08b_agent.csv")
    n["agent"] = {m: {r.system: {"max_adv": _f(r.max_adv), "upper": _f(r.max_adv_hi), "completion": _f(r.completion)}
                      for r in ag[ag.model == m].itertuples()} for m in MODELS}
    sd = pd.read_csv(reports / "10_side.csv")
    cfg = sd[sd["source"].str.startswith("04b") & (sd["channels"] == "as_built")]
    pre, post = cfg[cfg["system"].str.endswith("pre") & ~cfg["system"].str.startswith("L3")], cfg[cfg["system"].str.endswith("post") & ~cfg["system"].str.startswith("L3")]
    stat = sd[sd["source"].str.startswith("04b") & sd["system"].str.endswith("post") & ~sd["system"].str.startswith("L3")]
    n["side_channels"] = {"pre_filter_max_adv": _f(pre["adv"].max()), "post_filter_max_adv": _f(post["adv"].max()),
                          "post_filter_min_adv": _f(post["adv"].min()),
                          "post_filter_status_only_max": _f(stat[stat.channels == "status"]["adv"].max()),
                          "post_filter_citations_only_max": _f(stat[stat.channels == "citations"]["adv"].max())}
    tm = pd.read_csv(reports / "10_timing.csv")
    n["timing"] = {"template_longest_s": _f(tm[tm.system.str.contains("-RT-")]["max_s"].max()),
                   "free_text_longest_s": _f(tm[tm.system.str.contains("-RF-")]["max_s"].max()),
                   "floor_s": json.load(open(reports / "10_summary.json"))["latency_floor_s"]}
    ab = pd.read_csv(reports / "11_ablation.csv")
    n["ablations"] = {}
    for dom in ("meridian", "enron"):
        for m in MODELS:
            g = ab[(ab.domain == dom) & (ab.model == m)].set_index("variant")
            n["ablations"][f"{dom}|{m}"] = {"full_resolved": _f(g.loc["full", "resolved_all"]),
                                            "argmax_resolved": _f(g.loc["set_argmax", "resolved_all"]),
                                            "argmax_wrong_record": _f(g.loc["set_argmax", "wrong_answer_share"]),
                                            "always_ask_asked": _f(g.loc["set_always_ask", "asked_share"]),
                                            "full_asked": _f(g.loc["full", "asked_share"]),
                                            "routed_world1_full": _f(g.loc["full", "routed_world1_S1"]),
                                            "routed_world1_without_private_action": _f(g.loc["no_private_action", "routed_world1_S1"])}
    n["ablation_full_reproduces_records"] = json.load(open(reports / "11_summary.json"))["full_reproduces_04b"]
    return n



# ============================================================================= Captions and checks
CAPTIONS = {
    "figure1_framework": (
        "SameView in three bands. The privileged band (top) holds the access lists, the full index, the permission "
        "controller (K1) and private actions such as filing an access request with a record's owner; it never replies "
        "to the user. The requester-view band (middle) is the only band that replies: it builds the requester's own index, "
        "where a forbidden record and a missing record give the same code (K2), scores the candidates and \"none of these\" "
        "with a conformal clarifier that answers, asks or gives one fixed reply (K3), and words the reply with a template or "
        "a slot-bound language model, a length bucket and a latency floor (K4). Restricted records never reach K3 or K4. "
        "The release band (bottom) runs offline before deployment: the built pipeline runs on paired worlds, a family of "
        "attackers is trained and frozen, a Learn-then-Test certificate bounds every attacker's advantage at \u03b5 with "
        "probability 1 \u2212 \u03b4 (K5), and the most useful certified configuration \u03bb* is deployed."),
    "figure2_paired_worlds": (
        "The paired-world game. Both worlds give the requester the same permitted view; the protected fact (here, that a "
        "restricted Project Cedar memo exists) is true only in world 1. A coin picks the world, the built assistant answers "
        "the attacker's request, and the attacker guesses the world from everything it sees: text, options, error code, "
        "citations, length and time. The advantage is 0 when the reply says nothing about which world was drawn."),
    "figure3_cedar_mechanism": (
        "The Project Cedar example (Qwen2.5-7B-Instruct, Domain 1): three requests (rows) answered by four systems (columns) "
        "in both worlds. Orange frames mark replies that change with the hidden record. The privacy prompt (B1) states the "
        "restricted memo's contents or who can open it, or stops answering a request it answers in the other world; the "
        "triggered refusal (B3) refuses only when the "
        "restricted record exists, so the refusal itself is the leak. The universal reply (B4) and SameView give the same reply in "
        "both worlds: B4 lists the permitted records that match, while SameView asks which permitted record the user means and "
        "offers \"none of these\". Long replies are cut with an ellipsis."),
    "figure4_frontier": (
        "Leakage against usefulness for the 24 configurations of Domain 1. Vertical axis: certified bound \u03b5\u0302, the "
        "smallest \u03b5 certified with probability 0.95 against all seven attackers on the certify split. Horizontal axis: "
        "share of mistyped and ambiguous requests resolved on the utility split. Shaded: certified at \u03b5 = 0.10. Every "
        "pre-filter configuration of levels L0 to L2 is certified; every post-filter configuration and every L3 positive "
        "control is rejected. The universal reply (L0) is certified but resolves about half of the requests; the ringed "
        "point is the selected configuration \u03bb*. Points are shifted slightly sideways by wording and level so that "
        "they do not hide each other."),
    "figure5_advantage_heatmap": (
        "Advantage of each attacker (columns) against each system (rows) on held-out test units of Domain 1, for both "
        "models. Bold: the lower 95% bound is above 0.10. Systems above the line decide what to say from restricted data "
        "and leak; systems below the line decide from the permitted view only, and every attacker stays near zero."),
    "figure6_adaptive_attackers": (
        "Adaptive multi-turn attackers (Domain 1): accuracy of the best transcript learner against the number of turns "
        "(solid: Qwen2.5-7B-Instruct; dashed: Llama-3.1-8B-Instruct). The controls are the baselines each attack can "
        "succeed against: B1 for the attribute fact, B3 for existence and B5 for existence and membership. Against SameView the "
        "transcripts are identical in both worlds at every turn, so accuracy stays at the share of world-1 units; "
        "against the controls, extra turns raise it."),
    "figure7_coverage": (
        "Conformal clarifier on the Domain 1 test tasks: coverage of the intended option with its Wilson 95% band (left) "
        "and mean prediction-set size (right) against the miscoverage level \u03b1. Dashed: target 1 \u2212 \u03b1. "
        "Dotted: \u03b1 = 0.10, used by SameView. Coverage follows the target and the sets shrink as \u03b1 grows."),
    "figure8_side_channel": (
        "Side channels of the clarifier with template wording (level L2), both models pooled, certify split. Left: reply "
        "length before padding; right: number of records cited. With pre-filter retrieval (top) the two worlds give the same "
        "distributions. With post-filter retrieval (bottom) a restricted record takes one of the five retrieval slots and is "
        "then removed, so in world 1 the reply never cites five records."),
    "figure9_sensitivity": (
        "The certificate against the number of certify units, from random subsets of the stored per-unit guesses of all "
        "seven attackers (200 subsets per size, drawn without replacement; the largest size is the full split and gives the "
        "certificate of Table 3). Left: median certified bound, with its 10th to 90th percentile band in Domain 1. Right: "
        "share of configurations certified at \u03b5 = 0.10; post-filter configurations and the L3 positive control are never "
        "certified (drawn just above and below zero). Dotted lines: the size Equation 19 gives for 80% power against "
        "one attacker at chance (1,375 units in Domain 1 at \u03b4/24; 1,168 in Domain 2 at \u03b4/10). Solid: Domain 1 (24 configurations); dashed: "
        "Domain 2 (10 configurations)."),
    "figure10_family_heatmap": (
        "The leak by query family: the advantage of each system's strongest attacker (the one of Table 7, chosen on the "
        "whole held-out split) read per query family (columns) and system (rows) in Domain 1, for both models. Bold: the "
        "lower 95% bound is above 0.10; grey: the lower bound is zero. Families have 110 to 330 test units each, so the "
        "intervals are wider than in Figure 5. Systems above the line decide from restricted data, and where they leak "
        "depends on the request: the triggered refusal and the full-view clarifier leak when the request names the record "
        "(Q1, Q4, Q5, Q7) and not when it asks about a person or an attribute; the privileged agent and the privacy prompt "
        "leak on nearly every family. Systems below the line stay at the floor in every family: the values repeated down "
        "a column of the lower block are that family's share of world-1 units, which is what a constant guess scores."),
}


def write_captions(out: Path) -> Path:
    lines = ["# Figure captions (drafts for the manuscript)", ""]
    for i, (name, cap) in enumerate(CAPTIONS.items(), start=1):
        lines += [f"**Figure {i}.** {cap}", "", f"File: `{name}.png` and `{name}.pdf`", ""]
    path = out / "captions.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def figure_check(out: Path, results: list) -> pd.DataFrame:
    """Size, resolution at the printed width, PDF presence and code keys for every figure saved."""
    rows = []
    for r in results:
        c = check_figure_file(out / f"{r['name']}.png", r["width_in"])
        rows.append({"figure": r["name"], "width_in": r["width_in"], "height_in": r["height_in"], "png_pixels": "x".join(map(str, c["pixels"])),
                     "dpi_at_print_width": c["dpi_at_print_width"], "pdf": (out / f"{r['name']}.pdf").exists(),
                     "code_keys": "; ".join(r["code_keys"]) or "none"})
    return pd.DataFrame(rows)
