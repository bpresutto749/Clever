"""MCP sidecar for the Core War task.

Tools (streamable HTTP on :8000/mcp):
  get_rules()                  - the scoring rules and settings
  list_sparring()              - names of the public sparring warriors
  get_sparring(name)           - source of one sparring warrior
  battle(source, opponents, rounds) - play a warrior against sparring warriors
  battle_custom(source, opponent_source, rounds) - play two sources of your own
  submit(source)               - set your final submission (last accepted one counts)
  status()                     - what is currently submitted

The hidden hill never enters this container: the verifier scores the submission
in its own container. This service only keeps the submission and its history
under /results, which Harbor collects as an artifact after the run.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from arena import core

DATA = Path(os.environ.get("ARENA_DATA", "/srv/data"))
SPARRING = DATA / "sparring"
RESULTS = Path(os.environ.get("RESULTS_DIR", "/results"))
RULES = (Path(__file__).resolve().parent / "RULES.md").read_text()
MAX_ROUNDS = 500

_lock = threading.Lock()
mcp = FastMCP(
    "corewar",
    instructions="Core War arena. Read get_rules, test warriors with battle, and set your final warrior with submit.",
    host=os.environ.get("HOST", "0.0.0.0"),
    port=int(os.environ.get("PORT", "8000")),
)


def _sparring():
    return sorted(SPARRING.glob("*.red"))


def _log(event: dict):
    RESULTS.mkdir(parents=True, exist_ok=True)
    event["t"] = round(time.time(), 3)
    with (RESULTS / "events.jsonl").open("a") as f:
        f.write(json.dumps(event) + "\n")


@mcp.tool()
def get_rules() -> str:
    """Scoring rules, simulator settings and what counts as a valid submission."""
    return RULES


@mcp.tool()
def list_sparring() -> str:
    """Names of the 10 public sparring warriors (none of them is on the hidden hill)."""
    return "\n".join(p.stem for p in _sparring())


@mcp.tool()
def get_sparring(name: str) -> str:
    """Redcode source of one sparring warrior."""
    for p in _sparring():
        if p.stem == name:
            return p.read_text(errors="replace")
    return f"unknown sparring warrior {name!r}; call list_sparring"


@mcp.tool()
def battle(source: str, opponents: list[str] | None = None, rounds: int = 100) -> str:
    """Play your warrior (Redcode source) against sparring warriors (all of them by
    default) with the scoring settings. Returns wins/losses/ties and KotH points."""
    rounds = max(1, min(int(rounds), MAX_ROUNDS))
    opps = [p for p in _sparring() if not opponents or p.stem in set(opponents)]
    if not opps:
        return "no such sparring warrior; call list_sparring"
    ins, msgs = core.assemble(source)
    if not ins:
        return "does not assemble:\n" + msgs
    res = core.play_hill(source, opps, rounds)
    _log({"event": "battle", "sha": hashlib.sha256(source.encode()).hexdigest()[:16],
          "opponents": [o.stem for o in opps], "rounds": rounds, "mean": core.hill_score(res)})
    return core.table(res)


@mcp.tool()
def battle_custom(source: str, opponent_source: str, rounds: int = 100) -> str:
    """Play two warriors of your own against each other (e.g. a new version against an old one)."""
    rounds = max(1, min(int(rounds), MAX_ROUNDS))
    for s in (source, opponent_source):
        ins, msgs = core.assemble(s)
        if not ins:
            return "does not assemble:\n" + msgs
    with core.Source(source) as a, core.Source(opponent_source) as b:
        r = core.battle(a.path, b.path, "opponent", rounds)
    return core.table([r])


@mcp.tool()
def submit(source: str) -> str:
    """Set your final submission. You may submit many times; the last accepted
    submission is the one that is scored on the hidden hill."""
    with _lock:
        ins, msgs = core.assemble(source)
        if not ins:
            _log({"event": "submit", "accepted": False, "reason": "does not assemble"})
            return "rejected: does not assemble\n" + msgs
        cp = core.nearest_published(ins, [SPARRING])
        if cp["copy"]:
            _log({"event": "submit", "accepted": False, "reason": f"near-copy of {cp['warrior']}"})
            return f"rejected: near-copy of sparring warrior {cp['warrior']}"
        RESULTS.mkdir(parents=True, exist_ok=True)
        tmp = RESULTS / "submission.red.tmp"
        tmp.write_text(source)
        tmp.replace(RESULTS / "submission.red")
        sha = hashlib.sha256(source.encode()).hexdigest()[:16]
        _log({"event": "submit", "accepted": True, "sha": sha, "length": len(ins)})
        return f"accepted ({len(ins)} instructions, sha {sha}). This is now your final submission."


@mcp.tool()
def status() -> str:
    """Whether a submission is set, and its first lines."""
    p = RESULTS / "submission.red"
    if not p.exists():
        return "no submission yet"
    return "current submission:\n" + "\n".join(p.read_text().splitlines()[:12])


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request):
    return JSONResponse({"ok": True})


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
