"""vLLM server lifecycle (one model on the GPU at a time) and the responder-model factory.

With REFUSELEAK_DRY_RUN=1 no server is started and every model tag maps to the scripted stand-in; this is how the
notebooks are tested on CPU before a GPU session. Dry-run records are written under a separate root and are never
a result source."""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request

import config

DRY_RUN = os.environ.get("REFUSELEAK_DRY_RUN") == "1"


def hf_id(tag: str) -> str:
    """Hugging Face id of a model tag: the two main models and the scale-check model of notebook 14."""
    return {**config.MODELS, **config.SCALE_MODELS}[tag]


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex(("127.0.0.1", port)) == 0


def served_model(port: int) -> str | None:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/models", timeout=3) as r:
            data = json.loads(r.read())
            return data["data"][0]["id"] if data.get("data") else None
    except Exception:
        return None


class Server:
    """Starts vLLM's OpenAI-compatible server for one model tag in its own process group and stops it fully, so
    that the next model gets the GPU memory back."""

    proc: subprocess.Popen | None = None
    tag: str | None = None

    def __init__(self, port: int = 8000, gpu_frac: float = 0.90, max_model_len: int = 4096,
                 extra_args: list[str] | None = None, log_path: str = "/content/vllm.log"):
        self.port, self.gpu_frac, self.max_model_len = port, gpu_frac, max_model_len
        self.extra_args, self.log_path = list(extra_args or []), log_path

    def ensure(self, tag: str, timeout: int = 1800):
        if DRY_RUN:
            self.tag = tag
            return
        model_id = hf_id(tag)
        if served_model(self.port) == model_id:
            self.tag = tag
            return
        self.stop()
        cmd = [sys.executable, "-m", "vllm.entrypoints.openai.api_server", "--model", model_id,
               "--port", str(self.port), "--gpu-memory-utilization", str(self.gpu_frac),
               "--max-model-len", str(self.max_model_len), "--seed", "0", *self.extra_args]
        print("launching:", " ".join(cmd), flush=True)
        Server.proc = subprocess.Popen(cmd, stdout=open(self.log_path, "w"), stderr=subprocess.STDOUT,
                                       start_new_session=True)
        t0 = time.time()
        while time.time() - t0 < timeout:
            if Server.proc.poll() is not None:
                raise RuntimeError(f"vLLM exited early (code {Server.proc.returncode}):\n{self.tail()}")
            if served_model(self.port) == model_id:
                Server.tag = self.tag = tag
                print(f"{tag} up after {time.time() - t0:.0f} s", flush=True)
                return
            time.sleep(5)
        raise RuntimeError(f"vLLM did not come up in {timeout} s:\n{self.tail()}")

    def tail(self, n: int = 40) -> str:
        try:
            return "".join(open(self.log_path).readlines()[-n:])
        except OSError:
            return "(no log)"

    def stop(self):
        if DRY_RUN:
            return
        p = Server.proc
        if p is not None and p.poll() is None:
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                p.wait(timeout=90)
            except Exception:
                try:
                    os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                except Exception:
                    pass
        elif _port_open(self.port):           # a server started by an earlier cell run of this runtime
            subprocess.run(["pkill", "-f", "vllm.entrypoints.openai.api_server"], capture_output=True)
        t0 = time.time()
        while _port_open(self.port) and time.time() - t0 < 120:
            time.sleep(2)
        time.sleep(5)                          # let the driver release GPU memory
        Server.proc, Server.tag = None, None


class VLLMChat:
    """One chat completion per call: system prompt, the earlier turns, the query. Greedy, seeded."""

    def __init__(self, client, tag: str):
        self.client, self.tag = client, tag
        self.model_id = hf_id(tag)

    def chat(self, system_prompt: str, query: str, history: list[dict]):
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}]
        for h in history:
            messages.append({"role": h["role"], "content": h["text"]})
        t0 = time.time()
        r = self._with_retries(lambda: self.client.chat.completions.create(
            model=self.model_id, messages=messages, max_tokens=config.MAX_TOKENS, temperature=config.TEMPERATURE, seed=0))
        lat = time.time() - t0
        text = (r.choices[0].message.content or "").strip()
        ntok = r.usage.completion_tokens if r.usage else len(text.split())
        return text, ntok, lat

    def messages(self, messages: list[dict], max_tokens: int = 300, temperature: float = 0.0, stop: list[str] | None = None) -> str:
        """One greedy completion for a full message list (the agent of notebook 08)."""
        r = self._with_retries(lambda: self.client.chat.completions.create(
            model=self.model_id, messages=messages, max_tokens=max_tokens, temperature=temperature, seed=0, stop=stop))
        return r.choices[0].message.content or ""

    def choice_logprobs(self, system_prompt: str, user_prompt: str, letters: str) -> dict:
        """Log-probability of each option letter as the first generated token (KnowNo-style scoring). Letters that
        are not among the top-20 tokens are absent from the result."""
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        r = self._with_retries(lambda: self.client.chat.completions.create(
            model=self.model_id, messages=messages, max_tokens=1, temperature=0.0, seed=0, logprobs=True, top_logprobs=20))
        out = {}
        content = r.choices[0].logprobs.content if r.choices[0].logprobs else []
        if content:
            for tl in content[0].top_logprobs:
                tok = tl.token.strip().strip(")").strip(".").upper()
                if len(tok) == 1 and tok in letters and (tok not in out or tl.logprob > out[tok]):
                    out[tok] = float(tl.logprob)
        return out

    def complete(self, prompt: str, max_tokens: int = 120, temperature: float = 0.7, n: int = 1, seed: int = 0) -> list[str]:
        """Sampled completions for the paraphrase pool (notebook 01)."""
        r = self._with_retries(lambda: self.client.chat.completions.create(
            model=self.model_id, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens,
            temperature=temperature, n=n, seed=seed))
        return [(c.message.content or "").strip() for c in r.choices]

    @staticmethod
    def _with_retries(call, attempts: int = 4):
        """Transient server errors (timeouts, connection resets while the server is busy) are retried with a pause;
        the request itself is unchanged, so a retried greedy completion is the same completion."""
        for k in range(attempts):
            try:
                return call()
            except Exception as e:            # noqa: BLE001
                if k == attempts - 1:
                    raise
                time.sleep(5 * (k + 1))


class CostMeter:
    """Thread-safe count of API tokens and their price; raises BudgetExceeded once the cap is passed, so that a
    notebook never spends more than the amount set before it started."""

    class BudgetExceeded(RuntimeError):
        pass

    def __init__(self, cap_usd: float, previous: dict | None = None, log_every: int = 500):
        """`previous`: the report of an earlier session of the same notebook, so that the cap covers the total."""
        import threading
        self.cap_usd, self.lock, self.log_every = float(cap_usd), threading.Lock(), log_every
        self.by_model: dict[str, dict] = {k: {kk: (float(vv) if kk == "usd" else (dict(vv) if isinstance(vv, dict) else int(vv))) for kk, vv in v.items()}
                                          for k, v in (previous or {}).get("by_model", {}).items()}
        self.t0 = time.time()
        self.calls_at_start = sum(d["calls"] for d in self.by_model.values())

    def check(self):
        """Called before a request: once the cap is passed, every waiting request fails without being sent."""
        total = self.total_usd()
        if total > self.cap_usd:
            raise CostMeter.BudgetExceeded(f"API spend {total:.2f} USD passed the cap of {self.cap_usd:.2f} USD; records so far are saved")

    def add(self, tag: str, input_tokens: int, output_tokens: int, stop_reason: str | None = None, thinking_tokens: int = 0):
        pin, pout = config.API_PRICE_PER_MTOK[tag]
        with self.lock:
            d = self.by_model.setdefault(tag, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "usd": 0.0})
            d["calls"] += 1
            d["input_tokens"] += int(input_tokens)
            d["output_tokens"] += int(output_tokens)
            d["usd"] += (input_tokens * pin + output_tokens * pout) / 1e6
            d["thinking_tokens"] = d.get("thinking_tokens", 0) + int(thinking_tokens or 0)
            sr = d.setdefault("stop_reasons", {})
            sr[str(stop_reason)] = sr.get(str(stop_reason), 0) + 1
            calls, usd, total = d["calls"], d["usd"], self.total_usd()
        if self.log_every and calls % self.log_every == 0:
            rate = (sum(x["calls"] for x in self.by_model.values()) - self.calls_at_start) / max(1e-9, (time.time() - self.t0) / 60)
            print(f"    {tag}: {calls} calls, {usd:.2f} USD ({total:.2f} in all), {rate:.0f} calls per minute", flush=True)
        self.check()

    def total_usd(self) -> float:
        return float(sum(d["usd"] for d in self.by_model.values()))

    def report(self) -> dict:
        return {"cap_usd": self.cap_usd, "total_usd": round(self.total_usd(), 4),
                "by_model": {k: {**v, "usd": round(v["usd"], 4)} for k, v in self.by_model.items()}}


class AnthropicChat:
    """The responder interface of VLLMChat on the Claude Messages API: one greedy completion per call, the system
    prompt as the system field, the query and the earlier turns as messages. Token counts come from the response."""

    def __init__(self, tag: str, meter: CostMeter, client=None):
        import anthropic
        self.tag, self.meter = tag, meter
        self.model_id = config.API_MODELS[tag]
        self.client = client or anthropic.Anthropic(max_retries=8, timeout=120)
        self.thinking = dict(config.API_THINKING.get(tag) or {}) or None
        self.thinking_rejected: str | None = None       # set if the API refused the thinking setting; the call is then made without it

    def _create(self, **kw):
        import anthropic
        if self.thinking and not self.thinking_rejected:
            try:
                return self.client.messages.create(thinking=self.thinking, **kw)
            except anthropic.BadRequestError as e:
                if "thinking" not in str(e).lower():
                    raise
                self.thinking_rejected = str(e)[:200]
                print(f"    {self.tag}: the API refused thinking={self.thinking}; continuing without the field ({self.thinking_rejected})", flush=True)
        return self.client.messages.create(**kw)

    def chat(self, system_prompt: str, query: str, history: list[dict]):
        """One completion at the API's default sampling: the Claude API accepts no temperature, so the replies of these
        responders are sampled, as they would be in deployment."""
        self.meter.check()
        messages = [{"role": "user", "content": query}]
        for h in history:
            messages.append({"role": h["role"], "content": h["text"]})
        t0 = time.time()
        r = self._create(model=self.model_id, system=system_prompt, messages=messages, max_tokens=config.API_MAX_TOKENS)
        lat = time.time() - t0
        text = "".join(getattr(b, "text", "") for b in r.content if getattr(b, "type", "text") == "text").strip()
        details = getattr(r.usage, "output_tokens_details", None)
        thinking_tokens = int(getattr(details, "thinking_tokens", 0) or 0) if details is not None else 0
        self.meter.add(self.tag, r.usage.input_tokens, r.usage.output_tokens, getattr(r, "stop_reason", None), thinking_tokens)
        return text, int(r.usage.output_tokens), lat

    def choice_logprobs(self, system_prompt: str, user_prompt: str, letters: str) -> dict:
        raise NotImplementedError("the Claude API returns no token log-probabilities; SameView uses the evidence-only scorer with it")


def make_llm(tag: str, port: int = 8000, meter: CostMeter | None = None):
    if DRY_RUN:
        from scripted import ScriptedLLM
        return ScriptedLLM(tag)
    if tag in config.API_MODELS:
        assert meter is not None, "an API responder needs a CostMeter with a spending cap"
        return AnthropicChat(tag, meter)
    import openai
    client = openai.OpenAI(base_url=f"http://127.0.0.1:{port}/v1", api_key="EMPTY", timeout=300, max_retries=0)
    return VLLMChat(client, tag)


def records_root(name: str = "02_records"):
    return (config.DATA / f"dry_run_{name}") if DRY_RUN else (config.REPORTS / name)
