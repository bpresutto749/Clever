"""Verifier: scores the submitted warrior on the hidden hill.

Runs in its own container (environment_mode = "separate"). The hidden hill and
the corpus exist only here. The submission comes from the artifacts Harbor
collects after the run: the last accepted `submit` (arena sidecar), or, if that
is empty, /app/submission.red from the agent container.

hill_score = mean KotH points per round over the hill / 3, in [0, 1].
reward = (hill_score - IMP) / (REF - IMP), floored at 0: the fraction of the way
from a one-line imp (`mov.i #0, 1`, hill score 0.1650) to the human
expert reference Toxic (0.4866). 1.0 = reference level; it can exceed 1.
It is 0 when the file is missing, does not assemble, or is a near-copy of a
sparring or hill warrior (those would make the score meaningless).
"""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from arena import core  # noqa: E402

import os
OUT = Path(os.environ.get("VERIFIER_OUT", "/logs/verifier"))
HILL = sorted((HERE / "data" / "hill").glob("*.red"))
assert len(HILL) == 30, "hidden hill missing"
SPARRING = HERE / "data" / "sparring"
CORPUS = HERE / "data" / "corpus"
IMP = 7427 / 45000   # hill_score of `mov.i #0, 1` at 500 rounds (0.165044)
REF = 21899 / 45000  # hill_score of the reference, solution/reference.red (0.486644)


# In a separate verifier environment Harbor re-creates every artifact at its
# *source* path (the `destination` only names the copy on the host). So the
# sidecar's submission appears at /results/submission.red and the agent's file at
# /app/submission.red. /logs/artifacts is never read: the agent can write there.
SUBMISSION_PATHS = [Path(os.environ.get("SIDECAR_SUBMISSION", "/results/submission.red")),
                    Path(os.environ.get("APP_SUBMISSION", "/app/submission.red"))]


def find_submission():
    for p in SUBMISSION_PATHS:
        if p.is_file() and p.read_text(errors="replace").strip():
            return p, p.read_text(errors="replace")
    return None, ""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    reward = {"reward": 0.0, "hill_score": 0.0}
    details = {"hill_size": len(HILL), "rounds": core.ROUNDS}
    path, src = find_submission()
    details["source_file"] = str(path) if path else None
    if path is None:
        details["reason"] = "no submission"
    else:
        details["sha256"] = hashlib.sha256(src.encode()).hexdigest()
        ins, msgs = core.assemble(src)
        details["length"] = len(ins)
        if not ins:
            details["reason"] = "does not assemble"
            details["pmars"] = msgs
        else:
            gate = core.nearest_published(ins, [HERE / "data" / "hill", SPARRING])
            pub = core.nearest_published(ins, [CORPUS])
            details["nearest_hill_or_sparring"] = gate
            details["nearest_published"] = pub
            details["nearest_published_similarity"] = max(pub["exact"], pub["struct"])
            if gate["copy"]:
                details["reason"] = f"near-copy of {gate['warrior']}"
            else:
                res = core.play_hill(src, HILL)
                score = core.hill_score(res)
                reward.update({"reward": round(max(0.0, (score - IMP) / (REF - IMP)), 6),
                               "hill_score": round(score, 6)})
                details["per_opponent"] = {r.opponent: {"wins": r.wins, "losses": r.losses, "ties": r.ties,
                                                        "points": round(r.points, 4), "error": r.error} for r in res}
                details["reason"] = "scored"
    details["seconds"] = round(time.time() - t0, 1)
    (OUT / "reward.json").write_text(json.dumps(reward))
    (OUT / "details.json").write_text(json.dumps(details, indent=1))
    print(json.dumps(reward))
    print(details.get("reason"))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # always leave a reward file
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "reward.json").write_text(json.dumps({"reward": 0.0, "hill_score": 0.0}))
        (OUT / "details.json").write_text(json.dumps({"reason": f"verifier error: {e!r}"}))
        print("verifier error", repr(e))
