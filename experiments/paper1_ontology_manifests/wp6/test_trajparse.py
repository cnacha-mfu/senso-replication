"""Unit tests of the WP6 trajectory parser on synthetic trajectories and on WP5 trajectories (Paper 1, WP6).

Used by Paper 1 (JSEP rebuild), WP6; design papers/paper1/wp6-harm-design.md section 3 ("the parser is unit-tested on
hand-written trajectories and on WP5 trajectories with expected counts committed before the run freeze").

The WP5 part checks the parser against an independent count that never touches the parser's regexes: the number of
actions is the number of assistant messages with a non-empty `extra.actions` (the harness's own record), the return code
is `extra.returncode` of the next message, and wasted-step / hit counts come from plain string tests on those records. The
expected values are generated once by `--make-expected` into `trajparse_expected.json` (committed before the run freeze).

Usage:
    python experiments/paper1_ontology_manifests/wp6/test_trajparse.py              # run all tests
    python experiments/paper1_ontology_manifests/wp6/test_trajparse.py --make-expected   # (re)write the expected file
"""

from __future__ import annotations

import gzip
import json
import random
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.paper1_ontology_manifests.wp6 import trajparse as tp  # noqa: E402

WP5_TRAJ = PROJECT_ROOT / "experiments/paper1_ontology_manifests/results/real_v2/wp5/runs/trajectories"
EXPECTED = Path(__file__).with_name("trajparse_expected.json")
N_WP5 = 20


def A(cmd: str, thought: str = "THOUGHT: look") -> dict:
    return {"role": "assistant", "content": f"{thought}\n\n```mswea_bash_command\n{cmd}\n```", "extra": {"actions": [{"command": cmd}]}}


def O(out: str, rc: int = 0) -> dict:
    return {"role": "user", "content": f"<returncode>{rc}</returncode>\n<output>\n{out}</output>"}


FORMAT_ERR = {"role": "user", "content": "Format error:\n\n<error>\nExpected exactly 1 action, found 2.\n</error>\n"}
LIMIT_ERR = {"role": "user", "content": "Your previous response reached the output token limit (finish_reason=length) ..."}
SYS = [{"role": "system", "content": "s"}, {"role": "user", "content": "task"}]

TOK_PATH = {"kind": 1, "type": "path", "values": ["pkg/core", "core"]}
TOK_MAKE = {"kind": 3, "type": "regex", "regex": r"\bmake\b[^|;&\n]*\btest\b", "target": "test"}
TOK_DEP = {"kind": 4, "type": "word", "values": ["httpx"]}
TOK_RM = {"kind": 2, "type": "path", "values": ["pkg/old/legacy.py", "legacy.py"]}


class Synthetic(unittest.TestCase):
    def test_hits_and_word_boundaries(self):
        m = SYS + [A("ls pkg/core/"), O(""), A("cat ./pkg/core/x.py"), O("x"), A("grep -r hardcore ."), O(""),
                   A("grep -rn core pkg"), O(""), A("cat pkg/core-utils.py"), O("", 1), A("echo corelib")]
        acts = tp.parse_actions(m)
        self.assertEqual(len(acts), 6)
        r = tp.score(acts, [TOK_PATH], m)
        # hits: ls pkg/core/ (full), ./pkg/core/x.py (full), grep -rn core pkg (final component). Not: hardcore, core-utils, corelib.
        self.assertEqual(r["Y1"], 3)
        self.assertEqual(r["Y5"], 1)
        self.assertEqual(r["Y4_by_kind"], {"1": 3})
        r6 = tp.score(acts, [TOK_PATH], m, full_path_only=True)      # SA6: full path only
        self.assertEqual(r6["Y1"], 2)

    def test_format_error_after_assistant_is_not_an_action(self):
        m = SYS + [A("ls pkg/core"), FORMAT_ERR, A("ls pkg/core"), LIMIT_ERR, A("ls pkg/core"), O("x")]
        acts = tp.parse_actions(m)
        self.assertEqual([a.index for a in acts], [1])
        self.assertEqual(tp.score(acts, [TOK_PATH])["Y1"], 1)

    def test_wasted_steps_union(self):
        m = SYS + [A("cat pkg/core/a.py"), O("cat: pkg/core/a.py: No such file or directory", 1),    # hit and NF: once
                   A("cat missing.py"), O("cat: missing.py: No such file or directory", 1),               # NF only
                   A("cat ok.py"), O("No such file or directory in the text but rc 0", 0),                # rc 0: not NF
                   A("python -m foo"), O("/usr/bin/python: No module named foo", 1),
                   A("pip install zzz"), O("ERROR: No matching distribution found for zzz", 1),
                   A("cat ok.py"), O("fine")]
        acts = tp.parse_actions(m)
        r = tp.score(acts, [TOK_PATH])
        self.assertEqual((r["Y1"], r["Y2"]), (1, 4))
        r7 = tp.score(acts, [TOK_PATH], narrow_nf=True)              # SA7: the first four strings only
        self.assertEqual(r7["Y2"], 3)

    def test_command_and_dependency_tokens(self):
        m = SYS + [A("make test"), O("make: *** No rule to make target 'test'.  Stop.", 2),
                   A("cd x && make -C docs test"), O("", 2),
                   A("make tests"), O("", 2),                 # \btest\b does not match 'tests'
                   A("pip install HTTPX"), O("ok"),
                   A("python -c 'import httpx'"), O("", 1),
                   A("pip install httpx-sse"), O("ok"),     # '-' continues the word: no hit
                   A("grep -r httpx.py .")]                  # '.py' ... (?![\w-]) lets '.' pass: hit by design
        acts = tp.parse_actions(m)
        r = tp.score(acts, [TOK_MAKE, TOK_DEP])
        self.assertEqual(r["Y4_by_kind"], {"3": 2, "4": 3})
        self.assertEqual(r["Y1"], 5)

    def test_removed_file_token(self):
        m = SYS + [A("cat pkg/old/legacy.py"), O("No such file or directory", 1), A("find . -name legacy.py"), O("")]
        r = tp.score(tp.parse_actions(m), [TOK_RM])
        self.assertEqual((r["Y1"], r["Y2"]), (2, 2))

    def test_observation_parsing(self):
        long_out = "x" * 6000
        head_tail = {"role": "user", "content": "<returncode>0</returncode>\n<warning>too long</warning><output_head>\nHEAD\n</output_head>"
                                                 "\n<elided_chars>5 characters elided</elided_chars>\n<output_tail>\nTAIL\n</output_tail>"}
        exc = {"role": "user", "content": "<exception>timed out</exception>\n<returncode>-1</returncode>\n<output>\n</output>"}
        m = SYS + [A("a"), O(long_out), A("b"), head_tail, A("c"), exc, A("echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"),
                   {"role": "exit", "content": "", "extra": {"exit_status": "Submitted"}}]
        acts = tp.parse_actions(m)
        self.assertEqual(len(acts[0].out), 4000)
        self.assertIn("HEAD", acts[1].out)
        self.assertIn("TAIL", acts[1].out)
        self.assertEqual(acts[2].rc, -1)
        self.assertIsNone(acts[3].rc)                      # the submit action has no observation
        self.assertEqual(len(acts), 4)

    def test_thought_uptake(self):
        m = SYS + [A("ls", "THOUGHT: the manifest mentions pkg/core so I will look there"), O(""),
                   A("ls", "THOUGHT: nothing relevant"), O("")]
        self.assertEqual(tp.score(tp.parse_actions(m), [TOK_PATH], m)["Y8"], 1)

    def test_command_inside_thought_is_not_an_action(self):
        m = SYS + [{"role": "assistant", "content": "THOUGHT: I could run `ls pkg/core` here but will not.", "extra": {}}, O("")]
        self.assertEqual(tp.parse_actions(m), [])


# ----------------------------------------------------------------------------
# WP5 trajectories against an independent count
# ----------------------------------------------------------------------------
def load(name: str) -> dict:
    return json.loads(gzip.open(WP5_TRAJ / name, "rt").read())


def independent(traj: dict, token_path: str | None) -> dict:
    """Counts from the harness's own records (extra.actions / extra.returncode / extra.raw_output); no parser code."""
    ms = traj["messages"]
    n = nf = hits = 0
    wasted = set()
    cmds = []
    for i, m in enumerate(ms):
        ex = (m.get("extra") or {}).get("actions") if m.get("role") == "assistant" else None
        if not ex:
            continue
        n += 1
        cmd = ex[0]["command"]
        cmds.append(cmd)
        nxt = ms[i + 1] if i + 1 < len(ms) else {}
        e = nxt.get("extra") or {}
        rc = int(e["returncode"]) if str(e.get("returncode", "")).lstrip("-").isdigit() else None
        raw = (e.get("raw_output") or "")[:4000]
        is_nf = rc not in (None, 0) and any(s in raw for s in (
            "No such file or directory", "command not found", "No rule to make target", "No module named",
            "ModuleNotFoundError", "ERROR: file or directory not found", "can't open file", "cannot access",
            "No matching distribution"))
        # token test without the parser's regex: maximal runs of [\w./-] ("pieces"); a hit is a piece that is the token
        # (after an optional ./), or continues it with '/', '.' (the design's boundary rule lets '.' and '/' follow)
        hit = False
        if token_path:
            for piece in re.findall(r"[\w./-]+", cmd):
                pc = piece[2:] if piece.startswith("./") else piece
                if pc == token_path or pc.startswith((token_path + "/", token_path + ".")):
                    hit = True
                    break
        hits += hit
        if is_nf or hit:
            wasted.add(n)
        nf += is_nf
    return {"n_actions": n, "n_nf": nf, "Y1": hits, "Y2": len(wasted)}


def pick_token(traj: dict) -> str | None:
    """The first plain relative path that a `cat`/`sed`/`ls` command of the trajectory names (a token that does get hit)."""
    for m in traj["messages"]:
        for a in ((m.get("extra") or {}).get("actions") or []) if m.get("role") == "assistant" else []:
            mm = re.match(r"^(?:cat|ls|head|tail|sed -n '[^']*')\s+(?:-\S+\s+)*((?:[\w-]+/)+[\w.-]+)\s*$", a["command"])
            if mm:
                return mm.group(1)
    return None


def sample_names() -> list[str]:
    names = sorted(p.name for p in WP5_TRAJ.glob("*.traj.json.gz"))
    return random.Random(20261009).sample(names, N_WP5)


class Wp5Trajectories(unittest.TestCase):
    def test_against_independent_counts(self):
        if not EXPECTED.exists() or not WP5_TRAJ.exists():
            self.skipTest("expected file or WP5 trajectories missing")
        exp = json.loads(EXPECTED.read_text())
        self.assertEqual(len(exp["trajectories"]), N_WP5)
        for name, e in exp["trajectories"].items():
            t = load(name)
            acts = tp.parse_actions(t["messages"])
            tok = [{"kind": 1, "type": "path", "values": [e["token"]]}] if e["token"] else []
            r = tp.score(acts, tok)
            self.assertEqual(len(acts), e["n_actions"], name)
            self.assertEqual(r["Y1"], e["Y1"], name)
            self.assertEqual(r["Y2"], e["Y2"], name)
            self.assertEqual(sum(1 for a in acts if a.rc not in (None, 0) and tp.NF_RE.search(a.out)), e["n_nf"], name)

    def test_expected_has_hits_and_not_found(self):
        if not EXPECTED.exists():
            self.skipTest("expected file missing")
        exp = json.loads(EXPECTED.read_text())["trajectories"].values()
        self.assertGreater(sum(e["Y1"] for e in exp), 0)
        self.assertGreater(sum(e["n_nf"] for e in exp), 0)


def make_expected() -> None:
    out = {}
    for name in sample_names():
        t = load(name)
        tok = pick_token(t)
        out[name] = {"token": tok, **independent(t, tok)}
    EXPECTED.write_text(json.dumps({"note": "independent counts (extra.actions / extra.returncode / raw_output), seed 20261009",
                                    "trajectories": out}, indent=1))
    print(f"wrote {EXPECTED} ({len(out)} trajectories)")


if __name__ == "__main__":
    if "--make-expected" in sys.argv:
        make_expected()
    else:
        unittest.main(verbosity=2)
