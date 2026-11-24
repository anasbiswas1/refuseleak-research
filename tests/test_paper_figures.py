"""Tests of src/paper_figures.py (notebook 12): paper names, table builders, figure files, on small synthetic inputs."""
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import paper_figures as F  # noqa: E402


def test_config_and_system_names():
    assert F.config_parts("L2-RT-pre") == ("L2 Clarifier and private action", "Template", "Pre-filter")
    assert F.system_name("L2-RT-pre") == "LoRe (selected)"
    assert F.system_name("B5") == "B5 Post-filter RAG"
    assert F.system_name("L3-RF-post") == "L3 Leak notice (positive control), Free LLM, Post-filter"
    assert F.config_label("L2-RT-pre").endswith("(selected: LoRe)")
    assert F.config_label("L2-RT-post") == "L2 Clarifier and private action, Template, Post-filter"


def test_code_key_pattern():
    for bad in ("qwen25_7b", "llama31_8b", "L2-RT-pre", "eps_hat", "identical_share", "adv_hi"):
        assert F.CODE_KEY.search(bad), bad
    for ok in ("Qwen2.5-7B-Instruct", "LoRe (selected)", "Pre-filter retrieval", "[MH-7263]", "D6 Stack", "K2 Projector"):
        assert not F.CODE_KEY.search(ok), ok


def test_md_table():
    md = F.md_table(pd.DataFrame({"A": ["x|y", "z"], "B": [0.12345, np.nan]})).splitlines()
    assert md[0] == "| A | B |" and md[1] == "|---|---|"
    assert md[2] == "| x/y | 0.123 |" and md[3] == "| z |  |"


def test_overlap_table(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("# 2. What already exists (overlap)\n\nintro\n\n| **Component** | **Status** |\n|---|---|\n"
                    "| Phenomenon | Taken |\n| Certificate | Open |\n\n**Classical ideas we cite**\n")
    t = F.overlap_table(plan)
    assert list(t.columns) == ["Component", "Status"] and t["Status"].tolist() == ["Taken", "Open"]


def test_figures_without_data_are_600_dpi_and_use_paper_names(tmp_path):
    for fn in (F.figure1, F.figure2):
        r = fn(tmp_path)
        assert r["dpi"] == 600 and r["code_keys"] == []
        c = F.check_figure_file(tmp_path / f"{r['name']}.png", r["width_in"])
        assert c["dpi_at_print_width"] >= 600
        assert (tmp_path / f"{r['name']}.pdf").exists()


def test_figure7_from_synthetic_coverage(tmp_path):
    rows = [{"model": m, "alpha": a, "coverage": 1 - a, "coverage_lo": 1 - a - 0.02, "coverage_hi": 1 - a + 0.02,
             "mean_set_size": 2 - 3 * a} for m in F.MODELS for a in F.ALPHA_GRID]
    r = F.figure7(tmp_path, pd.DataFrame(rows))
    assert r["png_pixels"][0] == round(F.FULL_W * F.DPI) and r["code_keys"] == []
    chk = F.figure_check(tmp_path, [r])
    assert chk.loc[0, "code_keys"] == "none" and bool(chk.loc[0, "pdf"])


def test_figure9_from_synthetic_sensitivity(tmp_path):
    rows = [{"domain": d, "class": c, "n": n, "rep": r, "eps_hat": base / n ** 0.5 + 0.01 * r, "certified": c == "pre" and n >= 1500}
            for d in ("meridian", "enron") for c, base in (("pre", 3.0), ("post", 6.0), ("L3", 9.0)) for n in (250, 500, 1000, 2000)
            for r in range(3)]
    r = F.figure9(tmp_path, pd.DataFrame(rows), 0.10, {"meridian": 1375, "enron": 1168})
    assert r["png_pixels"][0] == round(F.FULL_W * F.DPI) and r["code_keys"] == []
    chk = F.figure_check(tmp_path, [r])
    assert chk.loc[0, "dpi_at_print_width"] >= 600 and chk.loc[0, "code_keys"] == "none" and bool(chk.loc[0, "pdf"])


def test_figure5_takes_the_attackers_in_the_file(tmp_path):
    systems = ["B0", "B1", "B2", "B3", "B5", "O2", "B4", "B6", "O1", "L2-RT-pre"]
    rows = [{"model": m, "system": s, "attacker": a, "adv": 0.1, "adv_lo": 0.0} for m in F.MODELS for s in systems
            for a in ("D1", "D2", "D3", "D4", "D5", "D6", "D7")]
    pd.DataFrame(rows).to_csv(tmp_path / "att7.csv", index=False)
    r = F.figure5(tmp_path, tmp_path, "att7.csv")
    assert r["code_keys"] == [] and "D7" in F.ATTACKERS


def test_baseline_table_uses_paper_names(tmp_path):
    cols = dict(identical_share=1.0, max_adv=0.02, max_adv_hi=0.06, worst_attacker="D6", bound_at_delta=0.07,
                disclosure_world1=0.0, resolved_legit=0.9, resolved_auth=1.0)
    for f in ("04b_main.csv", "07d_main.csv"):
        pd.DataFrame([{"model": m, "system": s, **cols} for m in F.MODELS for s in ("B4", "L2-RT-pre")]).to_csv(tmp_path / f, index=False)
    t = F.baseline_table(tmp_path)
    assert set(t["System"]) == {"B4 Universal reply", "LoRe (selected)"}
    assert set(t["Model"]) == set(F.MODELS.values()) and set(t["Strongest attacker"]) == {"D6 Stack"}
    assert t["Resolved on a fresh draw: authorised"].isna().all()
    assert not any(F.CODE_KEY.search(str(c)) for c in t.columns)
    assert not any(F.CODE_KEY.search(str(v)) for v in t.to_numpy().ravel())


def test_paired_timing_detects_a_shift_and_not_its_absence(tmp_path):
    (tmp_path / "10_timing").mkdir()
    rng = np.random.default_rng(0)
    for m in F.MODELS:
        rows = []
        for i in range(60):
            base = float(rng.uniform(0.3, 0.5))
            for w in (0, 1):
                rows.append({"system": "L2-RT-post", "uid": f"certify-{i:05d}", "split": "certify", "world": w,
                             "latency_raw": base + 0.05 * w, "n_tokens": 40})
                rows.append({"system": "L2-RT-pre", "uid": f"certify-{i:05d}", "split": "certify", "world": w,
                             "latency_raw": base + float(rng.normal(0, 1e-3)), "n_tokens": 40})
        with gzip.open(tmp_path / "10_timing" / f"{m}.jsonl.gz", "wt") as fh:
            fh.write("\n".join(json.dumps(r) for r in rows))
    p = F.paired_timing(tmp_path).set_index(["model", "system"])
    for m in F.MODELS:
        assert abs(p.loc[(m, "L2-RT-post"), "time_diff_s"] - 0.05) < 1e-9 and p.loc[(m, "L2-RT-post"), "time_p"] < 1e-6
        assert p.loc[(m, "L2-RT-pre"), "time_p"] > 0.001
        assert p.loc[(m, "L2-RT-pre"), "tokens_p"] == 1.0


def test_captions_cover_every_figure(tmp_path):
    path = F.write_captions(tmp_path)
    text = path.read_text()
    for i, name in enumerate(F.CAPTIONS, start=1):
        assert f"**Figure {i}.**" in text and name in text
    for cap in F.CAPTIONS.values():
        assert "\u2014" not in cap and not F.CODE_KEY.search(cap)
