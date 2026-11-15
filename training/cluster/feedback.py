"""Feedback turns (FEEDBACK_TURNS=K, with PROMPT_STYLE=arch): the model gets what the agent's
`battle` tool returns. After each draft, the warrior plays the 30 sparring warriors, the visible
pool of the environment (never the hidden hill), and the model is shown the same table
(ids s01..s30, wins / losses / ties / points) or pMARS's messages if the draft does not assemble,
and writes a new version. The sample's final warrior is its best draft on the sparring pool."""
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from common import ROOT, core

SPARRING = sorted((ROOT / "data" / "sparring").glob("*.red"))
SPAR_ROUNDS = 50
ASK = ("Write an improved version. Reply with the complete new warrior only, in one ```redcode block "
       "that starts with ;redcode-94 and a ;name line.")


def _spar_one(args):
    src, rounds = args
    ins, msgs = core.assemble(src)
    if not ins:
        return {"valid": False, "score": None, "text": "does not assemble:\n" + msgs[-600:]}
    res = core.play_hill(src, SPARRING, rounds, workers=1)
    for i, r in enumerate(res, 1):
        r.opponent = f"s{i:02d}"                     # public ids, as in the agent's tool
    return {"valid": True, "score": core.hill_score(res), "text": core.table(res)}


def spar_many(sources, rounds=SPAR_ROUNDS, workers=None):
    # "spawn": the parent process holds the vLLM engine, which must not be forked
    with ProcessPoolExecutor(workers, mp_context=multiprocessing.get_context("spawn")) as ex:
        return list(ex.map(_spar_one, [(s, rounds) for s in sources], chunksize=4))


def feedback_text(fb, dwarf_score, rounds=SPAR_ROUNDS):
    head = (f"Result of your warrior against the 30 sparring warriors ({rounds} rounds each; "
            "points = (3 x wins + ties) / (3 x rounds), so 1.0 means every round won):\n\n")
    ref = f"\n\nFor comparison, the documentation's Dwarf scores {dwarf_score:.3f} in the same test. "
    return head + fb["text"] + ref + ASK
