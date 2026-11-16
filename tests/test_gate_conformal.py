"""Tests of the certificate (src/gate.py, Equations 15 to 19 and Proposition 3) against scipy and by simulation, of
split conformal prediction (src/conformal.py, Proposition 2) on exchangeable synthetic scores, and of the attacker
evaluation protocol on scripted observations."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("REFUSELEAK_REPO_ROOT", str(ROOT))
os.environ["REFUSELEAK_DRY_RUN"] = "1"
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from scipy.stats import binomtest  # noqa: E402

import attackers as AT  # noqa: E402
import baselines as B  # noqa: E402
import conformal as C  # noqa: E402
import config  # noqa: E402
import gate as G  # noqa: E402
import harness as H  # noqa: E402
import serving  # noqa: E402
import world as W  # noqa: E402
from metrics import advantage  # noqa: E402


@pytest.mark.parametrize("k,n,eps", [(500, 1000, 0.10), (560, 1000, 0.10), (430, 1000, 0.10), (1500, 3000, 0.05)])
def test_p_value_matches_scipy_one_sided_tails(k, n, eps):
    hi = binomtest(k, n, (1 + eps) / 2, alternative="less").pvalue
    lo = binomtest(k, n, (1 - eps) / 2, alternative="greater").pvalue
    assert G.p_value(k, n, eps) == pytest.approx(max(hi, lo), rel=1e-9)


def test_certificate_accepts_chance_attackers_and_rejects_leaky_ones():
    n, eps, delta_m = 3000, 0.10, 0.05 / 24
    assert G.simulate(0.50, n, eps, delta_m) > 0.99         # power at chance (Equation 19 gives n ~ 1370 for 80%)
    assert 0.55 < G.simulate(0.52, n, eps, delta_m) < 0.80   # 3.3 standard deviations below the boundary, threshold at 2.86
    assert G.simulate(0.56, n, eps, delta_m) <= delta_m + 0.01   # at the boundary the false-certification rate is at most delta_m
    assert G.simulate(0.60, n, eps, delta_m) == 0.0
    assert G.simulate(0.40, n, eps, delta_m) == 0.0          # a below-chance attacker is as leaky as an above-chance one


def test_config_p_value_is_the_worst_attacker_and_bonferroni_applies():
    counts = {"a": {"D1": (1500, 3000), "D2": (1530, 3000)}, "b": {"D1": (1700, 3000), "D2": (1500, 3000)}}
    cert = G.certify(counts, 0.10, 0.05)
    assert cert["a"]["certified"] and not cert["b"]["certified"]
    assert cert["a"]["threshold"] == pytest.approx(0.025)
    assert G.select(cert, {"a": 0.7, "b": 0.9}, "a") == "a"
    assert G.select({"b": cert["b"]}, {"b": 0.9}, "fallback") == "fallback"
    assert G.certified_bound(counts["a"], 0.025) <= 0.10 < G.certified_bound(counts["b"], 0.025)


def test_sample_size_formula():
    assert 1300 <= G.sample_size(0.10, 0.05 / 24, 0.8) <= 1450
    assert G.sample_size(0.05, 0.05 / 24, 0.8) > 4 * G.sample_size(0.10, 0.05 / 24, 0.8) * 0.95


def test_advantage_interval_contains_zero_at_chance():
    a = advantage(500, 1000)
    assert a["adv"] == 0.0 and a["adv_lo"] == 0.0
    b = advantage(700, 1000)
    assert b["adv"] == pytest.approx(0.4) and b["adv_lo"] > 0.3
    c = advantage(300, 1000)
    assert c["adv"] == pytest.approx(0.4) and c["adv_lo"] > 0.3


def test_split_conformal_coverage_on_exchangeable_scores():
    rng = np.random.default_rng(0)
    m, alpha = 6, 0.10
    def draw(n):
        logits = rng.normal(0, 1, (n, m))
        labels = rng.integers(0, m, n)
        logits[np.arange(n), labels] += rng.normal(1.5, 1.0, n)
        return logits, labels
    cal_l, cal_y = draw(2000)
    T = C.fit_temperature(cal_l, cal_y)
    cal_p = C.temperature_scale(cal_l, T)
    scores = 1 - cal_p[np.arange(len(cal_y)), cal_y]
    qhat = C.threshold(scores, alpha)
    covs = []
    for _ in range(20):
        te_l, te_y = draw(1000)
        te_p = C.temperature_scale(te_l, T)
        cov, size = C.coverage(list(te_p), te_y, qhat)
        covs.append(cov)
        assert 1.0 <= size <= m
    assert np.mean(covs) >= 1 - alpha - 0.02
    assert C.threshold(np.array([0.1, 0.2, 0.3]), 0.10) == 1.0        # (n+1)(1-alpha) exceeds n: the set is everything
    assert 0 <= C.ece(cal_p, cal_y) <= 1


def test_attackers_on_scripted_observations():
    pool = W.load_pool(ROOT / "suite_data" / "does_not_exist.json")
    llm = serving.make_llm("qwen25_7b")
    units = [W.build_unit("probe", i, pool) for i in range(60)]
    by_uid = {u["uid"]: u for u in units}
    rows = []
    for u in units:
        for wk in ("1", "0"):
            rows += H.run_unit(u, wk, ["B3", "B4"], llm, "stub")
    emb, nli = AT.make_embedder(), AT.make_nli()
    b4 = AT.prepare([r for r in rows if r["system"] == "B4"], by_uid)
    b3 = AT.prepare([r for r in rows if r["system"] == "B3"], by_uid)
    for name in config.ATTACKERS:
        r4 = AT.evaluate(b4, AT.Attacker(name, embedder=emb, nli=nli))
        assert r4["adv_lo"] == 0.0, (name, r4)               # identical observations: nothing to learn
    r3 = AT.evaluate(b3, AT.Attacker("D1"))
    assert r3["n"] == 60 and r3["adv"] > 0.0
    judged = AT.judge_disclosure(b3, nli)
    assert len(judged) == 60
