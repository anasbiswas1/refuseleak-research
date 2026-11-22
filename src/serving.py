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
        model_id = config.MODELS[tag]
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
        self.model_id = config.MODELS[tag]

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

    def messages(self, messages: list[dict], max_tokens: int = 300, temperature: float = 0.0) -> str:
        """One greedy completion for a full message list (the agent of notebook 08)."""
        r = self._with_retries(lambda: self.client.chat.completions.create(
            model=self.model_id, messages=messages, max_tokens=max_tokens, temperature=temperature, seed=0))
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


def make_llm(tag: str, port: int = 8000):
    if DRY_RUN:
        from scripted import ScriptedLLM
        return ScriptedLLM(tag)
    import openai
    client = openai.OpenAI(base_url=f"http://127.0.0.1:{port}/v1", api_key="EMPTY", timeout=300, max_retries=0)
    return VLLMChat(client, tag)


def records_root(name: str = "02_records"):
    return (config.DATA / f"dry_run_{name}") if DRY_RUN else (config.REPORTS / name)
