"""WP5 agent run: one mini-SWE-agent (text-based mode) episode on one task, one condition, one model.

Used by Paper 1 (JSEP rebuild), WP5.

mini-SWE-agent 2.4.6, `LitellmTextbasedModel` (no tool calling), pointed at NVIDIA NIM through the
OpenAI-compatible endpoint. The agent shell runs in a scrubbed environment (no API keys) with the task
venv first on PATH. The condition's manifest text is rendered as a "Repository manifest" section of the
instance template and also written to the repo root as CLAUDE.md.

Usage:
    imported by wp5.runner.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any

import litellm
import minisweagent
import yaml
from minisweagent.agents.default import DefaultAgent
from minisweagent.environments.local import LocalEnvironment, _run
from minisweagent.models.litellm_textbased_model import LitellmTextbasedModel

from . import envs
from .common import run

logger = logging.getLogger("wp5.agent")

MANIFEST_BLOCK = "{% if manifest %}\n\n{{ manifest }}\n{% endif %}"   # text carries '## Repository context'
NOISE_RE = re.compile(r"(^|/)(\.pytest_cache|__pycache__|\.hypothesis|\.mypy_cache|\.ruff_cache|\.tox)(/|$)|\.egg-info(/|$)|\.pyc$")


class WallTimeAbort(Exception):
    """Raised inside a model call that is already past the wall-time budget (aborts retries)."""


class KeyPool:
    """Rotating pool of NIM API keys shared by all agent threads of this process (deviation 10).

    Round-robin over keys, skipping keys that returned a 429 in the last `cooldown_s` seconds when another
    key is free. Only env-var names are ever recorded; values never leave this object.
    """

    def __init__(self, names: list[str], cooldown_s: float = 15.0):
        self.keys = [(n, os.environ[n]) for n in names if os.environ.get(n)]
        if not self.keys:
            raise RuntimeError("key pool is empty: none of %s is set" % names)
        self.cooldown_s = cooldown_s
        self._i = 0
        self._last429: dict[str, float] = {}
        self._lock = threading.Lock()

    def next(self, exclude: frozenset = frozenset()) -> tuple[str, str]:
        with self._lock:
            now = time.time()
            order = [self.keys[(self._i + j) % len(self.keys)] for j in range(len(self.keys))]
            order = [k for k in order if k[0] not in exclude] or order
            cool = [k for k in order if now - self._last429.get(k[0], 0) >= self.cooldown_s]
            pick = (cool or sorted(order, key=lambda k: self._last429.get(k[0], 0)))[0]
            self._i = (self.keys.index(pick) + 1) % len(self.keys)
            return pick

    def mark_429(self, name: str) -> None:
        with self._lock:
            self._last429[name] = time.time()


_POOLS: dict[tuple, KeyPool] = {}
_POOLS_LOCK = threading.Lock()


def get_pool(names: list[str]) -> KeyPool:
    with _POOLS_LOCK:
        return _POOLS.setdefault(tuple(names), KeyPool(list(names)))


class CountingModel(LitellmTextbasedModel):
    """Text-based litellm model that counts rate-limit / overload / timeout errors and honours a deadline."""

    abort_exceptions = [*LitellmTextbasedModel.abort_exceptions, WallTimeAbort]

    def __init__(self, deadline: float, pool: "KeyPool | None" = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.pool = pool
        self.keys_used: dict[str, int] = {}
        self.deadline = deadline
        self.err_counts: dict[str, int] = {}
        self.n_queries = 0
        self._lock = threading.Lock()

    def _bump(self, key: str) -> None:
        with self._lock:
            self.err_counts[key] = self.err_counts.get(key, 0) + 1

    def _bump_key(self, name: str) -> None:
        with self._lock:
            self.keys_used[name] = self.keys_used.get(name, 0) + 1

    def _query(self, messages: list[dict], **kwargs: Any):
        if time.time() > self.deadline + 120:
            raise WallTimeAbort("past wall-time budget while retrying")
        self.n_queries += 1
        try:
            if self.pool is None:
                return super()._query(messages, **kwargs)
            tried: set[str] = set()
            while True:  # on a 429 switch to the next key before the retry layer backs off
                name, value = self.pool.next(frozenset(tried))
                tried.add(name)
                self._bump_key(name)
                try:
                    return super()._query(messages, **{**kwargs, "api_key": value})
                except litellm.exceptions.RateLimitError:
                    self._bump("429")
                    self.pool.mark_429(name)
                    if len(tried) >= len(self.pool.keys):
                        raise
        except litellm.exceptions.RateLimitError:
            raise
        except litellm.exceptions.ServiceUnavailableError:
            self._bump("503")
            raise
        except litellm.exceptions.Timeout:
            self._bump("timeout")
            raise
        except litellm.exceptions.InternalServerError:
            self._bump("5xx_other")
            raise
        except litellm.exceptions.APIConnectionError:
            self._bump("connection")
            raise
        except litellm.exceptions.APIError as e:  # other HTTP errors (400 etc.)
            self._bump(f"http_{getattr(e, 'status_code', 'x')}")
            raise


class ScrubbedEnv(LocalEnvironment):
    """LocalEnvironment that runs commands with ONLY the configured env (no inherited API keys)."""

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict[str, Any]:
        command = action.get("command", "")
        cwd = cwd or self.config.cwd or os.getcwd()
        try:
            result = _run(command, cwd, dict(self.config.env), timeout or self.config.timeout)
            output = {"output": result.stdout, "returncode": result.returncode, "exception_info": ""}
        except Exception as e:  # noqa: BLE001
            raw = getattr(e, "output", None)
            raw = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else (raw or "")
            output = {"output": raw, "returncode": -1,
                      "exception_info": f"An error occurred while executing the command: {e}",
                      "extra": {"exception_type": type(e).__name__, "exception": str(e)}}
        self._check_finished(output)
        return output

    def get_template_vars(self, **kwargs: Any) -> dict[str, Any]:
        import platform
        return {**self.config.model_dump(), **platform.uname()._asdict(), **kwargs}


def base_config() -> dict[str, Any]:
    cfg = yaml.safe_load((Path(minisweagent.__file__).parent / "config" / "mini_textbased.yaml").read_text())
    tpl = cfg["agent"]["instance_template"]
    marker = "{{task}}"
    assert marker in tpl
    cfg["agent"]["instance_template"] = tpl.replace(marker, marker + MANIFEST_BLOCK, 1)
    return cfg


def clean_repo(repo_dir: Path) -> None:
    """Back to the base commit. Ignored build products of the editable install (egg-info, extensions) are kept;
    every other untracked or ignored file is removed, so one run leaves nothing for the next."""
    run(["git", "reset", "--hard", "--quiet", "HEAD"], cwd=repo_dir)
    run(["git", "clean", "-fdxq", "-e", "*.egg-info", "-e", "*.so", "-e", "*.pyd", "-e", "__editable__*",
         "-e", "build/"], cwd=repo_dir)


def extract_diff(repo_dir: Path) -> str:
    """Agent patch against the base commit (plan 4.1): git add -A; git diff --cached, minus caches and build noise."""
    run(["git", "add", "-A"], cwd=repo_dir)
    rc, names = run(["git", "diff", "--cached", "--name-only", "HEAD"], cwd=repo_dir)
    keep = [n for n in names.splitlines() if n and not NOISE_RE.search(n)]
    if not keep:
        return ""
    rc, diff = run(["git", "diff", "--cached", "--binary", "HEAD", "--", *keep], cwd=repo_dir, timeout=120)
    if rc != 0:
        return ""
    from .metrics import filter_diff
    return filter_diff(diff, set())


def run_agent(cfg: dict, task: dict, model_cfg: dict, cond_text: str, root: Path, repo_dir: Path,
              traj_path: Path) -> dict[str, Any]:
    """Run one episode; returns metrics + the agent's diff. Never raises."""
    ac = cfg["agent"]
    clean_repo(repo_dir)
    mcfg = base_config()
    acfg = dict(mcfg["agent"])
    acfg.update(step_limit=ac["step_limit"], cost_limit=0, wall_time_limit_seconds=ac["wall_time_limit_seconds"],
                output_path=traj_path,
                max_consecutive_format_errors=ac.get("max_consecutive_format_errors", 3))
    os.environ["MSWEA_MODEL_RETRY_STOP_AFTER_ATTEMPT"] = str(ac["max_retries"])
    pool = get_pool(ac["key_pool"]) if ac.get("key_pool") else None
    kwargs: dict[str, Any] = dict(api_base=ac["nim_base_url"], api_key=os.environ[model_cfg["key_env"]],
                                  max_tokens=ac["max_tokens"], timeout=ac["model_timeout_s"], num_retries=0,
                                  drop_params=True)
    if model_cfg.get("extra_body"):  # e.g. thinking off for nemotron (chat_template_kwargs.enable_thinking=false)
        kwargs["extra_body"] = model_cfg["extra_body"]
    for k in ("temperature", "top_p"):
        if ac.get(k) is not None:
            kwargs[k] = ac[k]
    t0 = time.time()
    model = CountingModel(deadline=t0 + ac["wall_time_limit_seconds"], pool=pool, model_name="openai/" + model_cfg["name"],
                          cost_tracking="ignore_errors", model_kwargs=kwargs,
                          observation_template=mcfg["model"]["observation_template"],
                          format_error_template=mcfg["model"]["format_error_template"])
    env = ScrubbedEnv(cwd=str(repo_dir), timeout=ac["command_timeout_s"], env=envs.venv_env(cfg, root))
    agent = DefaultAgent(model, env, **acfg)
    exit_status, error = "", ""
    try:
        res = agent.run(task["problem_statement"], manifest=cond_text)
        exit_status = res.get("exit_status", "")
    except WallTimeAbort:
        exit_status = "WallTimeAbort"
    except Exception as e:  # noqa: BLE001
        exit_status = type(e).__name__
        error = repr(e)[:300]
    wall = time.time() - t0
    diff = extract_diff(repo_dir)
    ptok = ctok = n_fmt = n_len = 0
    model_id_returned = None
    assistant_text = []
    for m in agent.messages:
        if m.get("role") == "assistant":
            model_id_returned = model_id_returned or (m.get("extra", {}).get("response") or {}).get("model")
            assistant_text.append(str(m.get("content") or ""))
            u = (m.get("extra", {}).get("response") or {}).get("usage") or {}
            ptok += u.get("prompt_tokens", 0) or 0
            ctok += u.get("completion_tokens", 0) or 0
        if m.get("role") == "user" and isinstance(m.get("content"), str):
            if m["content"].startswith("Format error"):
                n_fmt += 1
            elif m["content"].startswith("Your previous response reached the output token limit"):
                n_len += 1
    return {"exit_status": exit_status, "error": error, "steps": agent.n_calls, "wall_s": round(wall, 1),
            "prompt_tokens": ptok, "completion_tokens": ctok, "format_errors": n_fmt, "length_cutoffs": n_len,
            "api_errors": dict(model.err_counts), "n_queries": model.n_queries, "keys_used": dict(model.keys_used), "diff": diff,
            "temperature": ac.get("temperature"), "top_p": ac.get("top_p"),
            "model_id_returned": model_id_returned,
            "mini_version": minisweagent.__version__, "assistant_text": "\n".join(assistant_text)}
