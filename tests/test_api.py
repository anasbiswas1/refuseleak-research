"""Tests of the API responder path (notebook 16): the Claude client on a fake SDK, the cost meter and its cap, the
dry-run stand-in, the judge of an API responder, and the scale table with a responder that ran only some systems."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import config  # noqa: E402
import judge as J  # noqa: E402
import paper_figures as F  # noqa: E402
import serving  # noqa: E402


class FakeMessages:
    def __init__(self, log):
        self.log = log

    def create(self, **kw):
        self.log.append(kw)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="Project Willow is in the design phase. [MH-0001]")], stop_reason="end_turn",
                               usage=SimpleNamespace(input_tokens=700, output_tokens=20, output_tokens_details=SimpleNamespace(thinking_tokens=0)))


class FakeClient:
    def __init__(self):
        self.log = []
        self.messages = FakeMessages(self.log)


def test_anthropic_chat_messages_and_meter():
    meter = serving.CostMeter(cap_usd=1.0)
    llm = serving.AnthropicChat("claude_haiku_55", meter, client=FakeClient())
    text, ntok, lat = llm.chat("SYSTEM", "Status of Project Willow?", [{"role": "assistant", "text": "Which one?"}, {"role": "user", "text": "The brief"}])
    kw = llm.client.log[0]
    assert kw["model"] == "claude-haiku-5-5" and kw["system"] == "SYSTEM" and kw["max_tokens"] == config.API_MAX_TOKENS
    assert "temperature" not in kw and kw["thinking"] == {"type": "disabled"}     # the API accepts no temperature; Claude 5 thinks unless told not to
    assert [m["role"] for m in kw["messages"]] == ["user", "assistant", "user"] and kw["messages"][0]["content"] == "Status of Project Willow?"
    assert text.startswith("Project Willow") and ntok == 20 and lat >= 0
    rep = meter.report()
    assert rep["by_model"]["claude_haiku_55"]["calls"] == 1 and rep["by_model"]["claude_haiku_55"]["input_tokens"] == 700
    assert rep["by_model"]["claude_haiku_55"]["stop_reasons"] == {"end_turn": 1} and rep["by_model"]["claude_haiku_55"]["thinking_tokens"] == 0
    assert abs(meter.total_usd() - (700 * 0.10 + 20 * 0.50) / 1e6) < 1e-12 and rep["total_usd"] >= 0
    sonnet = serving.AnthropicChat("claude_sonnet_55", meter, client=FakeClient())
    sonnet.chat("S", "q", [])
    assert sonnet.client.log[0]["thinking"] == {"type": "between_tools"}
    assert abs(meter.total_usd() - (700 * 0.10 + 20 * 0.50 + 700 * 2.0 + 20 * 10.0) / 1e6) < 1e-12
    with pytest.raises(NotImplementedError):
        llm.choice_logprobs("s", "u", "ABC")


def test_cost_cap_stops_the_run():
    meter = serving.CostMeter(cap_usd=0.002, log_every=0)
    llm = serving.AnthropicChat("claude_sonnet_55", meter, client=FakeClient())
    llm.chat("S", "q", [])                                           # 700 * 2 + 20 * 10 = 1600 / 1e6 = 0.0016, under the cap
    with pytest.raises(serving.CostMeter.BudgetExceeded):
        llm.chat("S", "q", [])                                       # 0.0032: the cap is passed when this response is priced
    assert meter.report()["by_model"]["claude_sonnet_55"]["calls"] == 2
    with pytest.raises(serving.CostMeter.BudgetExceeded):
        llm.chat("S", "q", [])                                       # waiting requests fail before being sent
    assert meter.report()["by_model"]["claude_sonnet_55"]["calls"] == 2 and len(llm.client.log) == 2


def test_cost_meter_carries_an_earlier_session():
    prev = {"by_model": {"claude_haiku_55": {"calls": 10, "input_tokens": 7000, "output_tokens": 200, "usd": 0.0008}}}
    meter = serving.CostMeter(cap_usd=1.0, previous=prev, log_every=0)
    assert abs(meter.total_usd() - 0.0008) < 1e-12
    llm = serving.AnthropicChat("claude_haiku_55", meter, client=FakeClient())
    llm.chat("S", "q", [])
    assert meter.report()["by_model"]["claude_haiku_55"]["calls"] == 11


def test_dry_run_uses_the_stand_in(monkeypatch):
    monkeypatch.setattr(serving, "DRY_RUN", True)
    llm = serving.make_llm("claude_haiku_55")
    assert type(llm).__name__ == "ScriptedLLM"
    monkeypatch.setattr(serving, "DRY_RUN", False)
    with pytest.raises(AssertionError):                               # a real API responder needs a cap
        serving.make_llm("claude_haiku_55")


def test_api_models_are_not_main_models_and_have_a_judge():
    for tag in config.API_MODELS:
        assert tag not in config.MODELS and tag not in config.SCALE_MODELS and tag in config.API_PRICE_PER_MTOK and tag in config.API_THINKING
        assert J.other_model(tag) in config.MODELS and J.family(tag) == "claude"
    assert J.other_model("qwen25_7b") == "llama31_8b" and J.other_model("llama31_8b") == "qwen25_7b"


def test_scale_table_with_partial_responder(tmp_path):
    base = pd.DataFrame([{"model": m, "system": s, "max_adv": 0.3 if s == "B0" else 0.02, "resolved_legit": 0.9}
                         for m in config.MODELS for s in ("B0", "B1", "L2-RT-pre")])
    base.to_csv(tmp_path / "13_main_meridian.csv", index=False)
    pd.DataFrame([{"model": "qwen25_14b", "system": s, "max_adv": 0.25, "resolved_legit": 0.95} for s in ("B0", "B1", "L2-RT-pre")]).to_csv(tmp_path / "14_main.csv", index=False)
    pd.DataFrame([{"model": "claude_haiku_55", "system": s, "max_adv": 0.4, "resolved_legit": 0.6} for s in ("B0", "B1", "L2-RT-pre")]
                 + [{"model": "claude_sonnet_55", "system": s, "max_adv": 0.5, "resolved_legit": float("nan")} for s in ("B0", "B1")]).to_csv(tmp_path / "16_main.csv", index=False)
    t = F.scale_table(tmp_path, ["14_main.csv", "16_main.csv"])
    assert "Claude Sonnet 5.5: largest attacker advantage" in t.columns
    row = t[t["System"] == "SameView (selected)"].iloc[0]
    assert row["Claude Sonnet 5.5: largest attacker advantage"] == "n/a" and row["Claude Haiku 5.5: resolved"] == 0.6
    assert t[t["System"] == "B0 Privileged agent"].iloc[0]["Claude Sonnet 5.5: resolved"] == "n/a"
    assert not [c for c in t.columns if F.CODE_KEY.search(c)]
