"""Result files: every report carries the runtime version, the world version and the git head that produced it."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pandas as pd

import config


def git_head() -> str:
    r = subprocess.run(["git", "-C", str(config.REPO_DIR), "rev-parse", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() or "unknown"


def stamp() -> dict:
    return {"runtime_version": config.RUNTIME_VERSION, "world_version": config.WORLD_VERSION,
            "git_head": git_head(), "written": time.strftime("%Y-%m-%dT%H:%M:%S")}


def write_json(name: str, payload: dict) -> Path:
    path = config.REPORTS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**payload, "_stamp": stamp()}, indent=2, default=str))
    return path


def write_csv(name: str, df: pd.DataFrame) -> Path:
    path = config.REPORTS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def read_json(name: str) -> dict:
    return json.loads((config.REPORTS / name).read_text())
