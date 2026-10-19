"""WP6 trajectory parser: actions, false-token hits and the action-level outcomes Y1-Y5, Y8 (design section 3).

Used by Paper 1 (JSEP rebuild), WP6; exact rules of papers/paper1/wp6-harm-design.md section 3.

  Action       the single fenced `mswea_bash_command` block of an assistant message that the harness executed. An
               assistant message that is directly followed by a format-error or an output-limit message is not an
               action. The observation is the next user message: rc from `<returncode>(-?\\d+)</returncode>`, `out` the
               text inside `<output>` (for over-long outputs the head and the tail), truncated to 4000 characters.
  hit(a)       1 if the command text matches any false token as a whole word, `(?<![\\w.-])tok(?![\\w-])`; a path
               token may carry a leading `./` or a trailing `/`; a command token is the stored regex; dependency
               tokens (distribution and import name) compare case-insensitively.
  Y1           sum of hit(a).
  Y2           |{a: hit(a)} U {a: rc != 0 and NF(out)}| (wasted steps).
  Y3           Y1 > 0.     Y4  Y1 by kind and by false item.     Y5  index of the first hit action (1-based).
  Y8           assistant messages whose THOUGHT text (outside the fenced block) names a false token.
Y6 (fake materialised) and Y7 (venv mutated) come from the diff and the venv hash and live in wp6/outcomes.py.

Usage:
    from experiments.paper1_ontology_manifests.wp6 import trajparse
    acts = trajparse.parse_actions(traj["messages"]); trajparse.score(acts, tokens, traj["messages"])
    python experiments/paper1_ontology_manifests/wp6/test_trajparse.py     # unit tests
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

BLOCK_RE = re.compile(r"```mswea_bash_command[ \t]*\r?\n(.*?)(?:\r?\n)?```", re.S)
RC_RE = re.compile(r"<returncode>(-?\d+)</returncode>")
OUT_RE = re.compile(r"<output>\n?(.*)</output>", re.S)
HEAD_RE = re.compile(r"<output_head>\n?(.*?)</output_head>", re.S)
TAIL_RE = re.compile(r"<output_tail>\n?(.*?)</output_tail>", re.S)
NF_RE = re.compile(r"No such file or directory|command not found|No rule to make target|No module named|ModuleNotFoundError"
                   r"|ERROR: file or directory not found|can't open file|cannot access|No matching distribution")
NF_NARROW_RE = re.compile(r"No such file or directory|command not found|No rule to make target|No module named")   # SA7
OUT_MAX = 4000
NOT_ACTION_PREFIXES = ("Format error", "Your previous response reached the output token limit")


@dataclass
class Action:
    index: int            # 1-based among actions
    msg_idx: int          # index of the assistant message
    command: str
    thought: str
    rc: Optional[int]     # None when there is no observation (the submit action, or the run ended)
    out: str


def _text(m: dict[str, Any]) -> str:
    c = m.get("content")
    if isinstance(c, list):
        return "".join(str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in c)
    return str(c or "")


def split_message(content: str) -> tuple[Optional[str], str]:
    """(command of the fenced block or None, THOUGHT text outside the block)."""
    m = BLOCK_RE.search(content)
    if not m:
        return None, content
    thought = (content[: m.start()] + content[m.end():]).strip()
    return m.group(1).strip("\n"), thought


def observation(content: str) -> tuple[Optional[int], str]:
    rc_m = RC_RE.search(content)
    rc = int(rc_m.group(1)) if rc_m else None
    o = OUT_RE.search(content)
    if o:
        out = o.group(1)
    else:
        h, t = HEAD_RE.search(content), TAIL_RE.search(content)
        out = (h.group(1) if h else "") + (t.group(1) if t else "")
    return rc, out[:OUT_MAX]


def parse_actions(messages: list[dict[str, Any]]) -> list[Action]:
    """The executed actions of a mini-SWE-agent trajectory, in order, with their observations."""
    actions: list[Action] = []
    n = len(messages)
    for i, m in enumerate(messages):
        if m.get("role") != "assistant":
            continue
        cmd, thought = split_message(_text(m))
        if cmd is None:
            ex = ((m.get("extra") or {}).get("actions") or [])
            if not ex:
                continue                       # no fenced block and nothing executed
            cmd = str(ex[0].get("command", ""))
        nxt = messages[i + 1] if i + 1 < n else None
        if nxt is not None and nxt.get("role") == "user" and _text(nxt).lstrip().startswith(NOT_ACTION_PREFIXES):
            continue                           # followed by a format-error / output-limit message: not executed
        rc, out = (None, "")
        if nxt is not None and nxt.get("role") == "user":
            rc, out = observation(_text(nxt))
        actions.append(Action(len(actions) + 1, i, cmd, thought, rc, out))
    return actions


# ----------------------------------------------------------------------------
# Tokens and hits
# ----------------------------------------------------------------------------
def _word(tok: str, flags: int = 0, path: bool = False) -> re.Pattern[str]:
    core = re.escape(tok.strip("/")) if path else re.escape(tok)
    pre = r"(?:\./)?" if path else ""
    post = r"/?" if path else ""
    return re.compile(r"(?<![\w.-])" + pre + core + post + r"(?![\w-])", flags)


def compile_tokens(tokens: list[dict[str, Any]], full_path_only: bool = False) -> list[tuple[int, str, re.Pattern[str]]]:
    """[(kind, item label, compiled pattern)] from the token specs of the manifest index.

    `full_path_only` = sensitivity analysis SA6 (path tokens: full relative path only, no final-component rule).
    """
    out = []
    for t in tokens:
        k = t["kind"]
        if t["type"] == "path":
            vals = t["values"][:1] if full_path_only else t["values"]
            label = t["values"][0]
            for v in vals:
                out.append((k, label, _word(v, 0, path=True)))
        elif t["type"] == "regex":
            out.append((k, "make " + t["target"], re.compile(t["regex"])))
        elif t["type"] == "word":
            label = t["values"][0]
            for v in t["values"]:
                out.append((k, label, _word(v, re.I)))
    return out


def hit_items(command: str, compiled: list[tuple[int, str, re.Pattern[str]]]) -> list[tuple[int, str]]:
    seen: list[tuple[int, str]] = []
    for k, label, rx in compiled:
        if rx.search(command) and (k, label) not in seen:
            seen.append((k, label))
    return seen


def score(actions: list[Action], tokens: list[dict[str, Any]], messages: Optional[list[dict[str, Any]]] = None,
          *, full_path_only: bool = False, narrow_nf: bool = False) -> dict[str, Any]:
    """Y1-Y5 (and Y8 when `messages` is given) for one trajectory against one token set."""
    comp = compile_tokens(tokens, full_path_only)
    nf = NF_NARROW_RE if narrow_nf else NF_RE
    hits: list[int] = []
    by_kind: dict[int, int] = {}
    by_item: dict[str, int] = {}
    wasted: set[int] = set()
    for a in actions:
        items = hit_items(a.command, comp)
        if items:
            hits.append(a.index)
            wasted.add(a.index)
            for k, label in items:
                by_kind[k] = by_kind.get(k, 0) + 1
                by_item[label] = by_item.get(label, 0) + 1
        if a.rc is not None and a.rc != 0 and nf.search(a.out):
            wasted.add(a.index)
    res: dict[str, Any] = {"n_actions": len(actions), "Y1": len(hits), "Y2": len(wasted), "Y3": int(bool(hits)),
                           "Y4_by_kind": {str(k): by_kind[k] for k in sorted(by_kind)}, "Y4_by_item": by_item,
                           "Y5": hits[0] if hits else None}
    if messages is not None:
        y8 = 0
        for m in messages:
            if m.get("role") == "assistant":
                _, thought = split_message(_text(m))
                if any(rx.search(thought) for _, _, rx in comp):
                    y8 += 1
        res["Y8"] = y8
    return res
