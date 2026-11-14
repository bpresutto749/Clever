"""Core War arena: pMARS wrapper, source sanitiser, near-copy check and hill scoring.

Everything that decides a reward lives here and is shared by the MCP sidecar
(sparring feedback), the verifier (hidden hill) and the local tools, so the three
can never disagree about the rules.
"""
from __future__ import annotations

import difflib
import os
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

PMARS = Path(os.environ.get("PMARS", Path(__file__).resolve().parent.parent / "pmars" / "pmars"))

# Standard ICWS '94 hill settings (pMARS defaults): coresize 8000, 80000 cycles,
# 8000 processes, max length 100, min distance 100.  -f uses pMARS's fixed
# position series, so every score is exactly reproducible.
ROUNDS = 100
BATTLE_TIMEOUT = 120          # seconds; a hung battle scores as a loss for the submission
MAX_LINE = 200                # pMARS 0.9.4 hangs on source lines longer than ~256 chars
MAX_SOURCE = 20000            # bytes
COPY_EXACT = 0.80
COPY_STRUCT = 0.90


# pMARS is C code from the 1990s with fixed-size buffers. Defence in depth: when
# running as root (the verifier's default), run it as an unprivileged user so a
# crafted warrior that crashed or subverted the simulator still could not write
# the reward file.
def _sim_kwargs():
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        try:
            import pwd
            pwd.getpwnam("nobody")
            return {"user": "nobody", "group": "nogroup" if _group_exists("nogroup") else None}
        except KeyError:
            pass
    return {}


def _group_exists(name):
    try:
        import grp
        grp.getgrnam(name)
        return True
    except KeyError:
        return False


def run_pmars(args, timeout):
    kw = {k: v for k, v in _sim_kwargs().items() if v is not None}
    return subprocess.run([str(PMARS), *args], capture_output=True, text=True, timeout=timeout,
                          cwd="/tmp", **kw)


# ---------------------------------------------------------------- sanitising
def sanitize(text: str) -> str | None:
    """Return a source pMARS can safely assemble, or None if the file is invalid.
    Comment lines are cut to MAX_LINE characters; an over-long code line loses its
    inline comment; a code line still longer than MAX_LINE makes the file invalid."""
    if len(text.encode("utf-8", "replace")) > MAX_SOURCE:
        return None
    out = []
    for line in text.replace("\r", "").split("\n"):
        if len(line) > MAX_LINE:
            if line.lstrip().startswith(";"):
                line = line[:MAX_LINE]
            else:
                line = line.split(";", 1)[0].rstrip()
                if len(line) > MAX_LINE:
                    return None
        out.append(line)
    return "\n".join(out) + "\n"


class Source:
    """A sanitised warrior written to a private temp file (context manager)."""

    def __init__(self, text: str):
        self.clean = sanitize(text)
        self.path = None

    def __enter__(self):
        if self.clean is not None:
            fd, p = tempfile.mkstemp(suffix=".red")
            with os.fdopen(fd, "w") as f:
                f.write(self.clean)
            os.chmod(p, 0o644)
            self.path = p
        return self

    def __exit__(self, *exc):
        if self.path:
            os.unlink(self.path)


# ---------------------------------------------------------------- assembling
def assemble(text: str) -> tuple[list[str], str]:
    """Assembled instructions (labels/comments removed) and pMARS's messages.
    An empty list means the warrior does not assemble."""
    with Source(text) as s:
        if s.path is None:
            return [], f"invalid source: a code line is longer than {MAX_LINE} characters or the file exceeds {MAX_SOURCE} bytes"
        try:
            p = run_pmars(["-r", "0", s.path], 30)
        except subprocess.TimeoutExpired:
            return [], "pMARS timed out while assembling"
    msgs = (p.stdout + p.stderr)
    ins, started = [], False
    for line in p.stdout.splitlines():
        if line.startswith("Program "):
            started = True
            continue
        if started:
            m = re.search(r"([A-Z]{3}\.[A-Z]{1,2})\s+(.*)$", line.strip())
            if m and not line.strip().startswith("ORG"):
                ins.append(m.group(1) + " " + re.sub(r"\s+", "", m.group(2)))
    if "Error" in msgs or "error" in msgs.split("Program ")[0]:
        if not ins:
            return [], msgs.strip()[-1500:]
    return ins, msgs.strip()[-1500:]


# ---------------------------------------------------------------- copy check
def _ratio(a, b):
    if not a or not b:
        return 0.0
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    matched = sum(bl.size for bl in sm.get_matching_blocks())
    contained = matched / min(len(a), len(b)) if min(len(a), len(b)) >= 6 else 0.0
    return max(sm.ratio(), contained)


def _structure(ins):
    return [re.sub(r"-?\d+", "", x) for x in ins]


def copy_match(ins: list[str], ref: list[str]) -> tuple[bool, float, float]:
    """exact: instructions with constants; counts containment, so pasting a
    published warrior inside a larger file is caught. struct: constants removed,
    symmetric ratio only (containment on structure alone flags unrelated code,
    e.g. a long decoy block that happens to contain a short warrior's opcodes)."""
    exact = _ratio(ins, ref)
    struct = 0.0
    if min(len(ins), len(ref)) >= 8:
        struct = difflib.SequenceMatcher(None, _structure(ins), _structure(ref), autojunk=False).ratio()
    return (exact >= COPY_EXACT or struct >= COPY_STRUCT), exact, struct


_ASM_CACHE: dict[str, list[str]] = {}


def nearest_published(ins: list[str], corpus_dirs: list[Path]) -> dict:
    best = {"copy": False, "exact": 0.0, "struct": 0.0, "warrior": None}
    for d in corpus_dirs:
        for f in sorted(Path(d).rglob("*.red")):
            key = str(f)
            if key not in _ASM_CACHE:
                _ASM_CACHE[key] = assemble(f.read_text(errors="replace"))[0]
            c, e, s = copy_match(ins, _ASM_CACHE[key])
            if (c, max(e, s)) > (best["copy"], max(best["exact"], best["struct"])):
                best = {"copy": c, "exact": round(e, 3), "struct": round(s, 3), "warrior": f.stem}
    return best


# ---------------------------------------------------------------- battles
@dataclass
class Result:
    opponent: str
    wins: int
    losses: int
    ties: int
    rounds: int
    error: str | None = None

    @property
    def points(self) -> float:            # KotH points per round / 3, in [0, 1]
        return (3 * self.wins + self.ties) / (3 * self.rounds)


def battle(a_path: str, b_path: str, name: str, rounds: int = ROUNDS) -> Result:
    try:
        p = run_pmars(["-b", "-k", "-r", str(rounds), "-f", a_path, b_path], BATTLE_TIMEOUT)
    except subprocess.TimeoutExpired:
        return Result(name, 0, rounds, 0, rounds, "timeout")
    lines = [l for l in p.stdout.strip().splitlines() if l.split() and l.split()[0].lstrip("-").isdigit()]
    if len(lines) < 2:
        return Result(name, 0, rounds, 0, rounds, (p.stdout + p.stderr).strip()[-300:] or "no result")
    w1, t1 = map(int, lines[-2].split()[:2])
    w2, _ = map(int, lines[-1].split()[:2])
    return Result(name, w1, w2, t1, rounds)


def play_hill(text: str, opponents: list[Path], rounds: int = ROUNDS, workers: int | None = None) -> list[Result]:
    """Battle a warrior source against every opponent file. Opponents are trusted
    files shipped with the task; they are sanitised too, for safety."""
    workers = workers or max(1, min(len(opponents), os.cpu_count() or 2))
    with Source(text) as s:
        if s.path is None:
            return [Result(o.stem, 0, rounds, 0, rounds, "invalid source") for o in opponents]
        opp_srcs = [Source(o.read_text(errors="replace")) for o in opponents]
        for o in opp_srcs:
            o.__enter__()
        try:
            with ThreadPoolExecutor(workers) as ex:
                return list(ex.map(lambda io: battle(s.path, io[1].path, io[0].stem, rounds),
                                   zip(opponents, opp_srcs)))
        finally:
            for o in opp_srcs:
                o.__exit__(None, None, None)


def hill_score(results: list[Result]) -> float:
    return sum(r.points for r in results) / len(results) if results else 0.0


def table(results: list[Result]) -> str:
    rows = [f"{'opponent':28s} {'win':>4s} {'loss':>4s} {'tie':>4s}  points"]
    for r in results:
        extra = f"  ({r.error})" if r.error else ""
        rows.append(f"{r.opponent:28s} {r.wins:4d} {r.losses:4d} {r.ties:4d}  {r.points:.3f}{extra}")
    rows.append(f"{'MEAN':28s} {'':14s}  {hill_score(results):.3f}")
    return "\n".join(rows)
