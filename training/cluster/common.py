"""Shared helpers for the cluster port of the expert-iteration loop (training/cluster/README.md).
Kept as it ran on 14-15 November 2026; training/common.py is the maintained version."""
import json
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]            # repository root
sys.path.insert(0, str(ROOT))
from arena import core  # noqa: E402
import subprocess  # noqa: E402


# Bulk scoring settings, applied here so that arena/core.py stays untouched: pMARS output is
# decoded with errors="replace", and ARENA_BATTLE_TIMEOUT (seconds) can replace core.BATTLE_TIMEOUT.
class _TolerantSubprocess:
    def __getattr__(self, name):
        return getattr(subprocess, name)

    @staticmethod
    def run(*args, **kw):
        if kw.get("text"):
            kw.setdefault("errors", "replace")
        return subprocess.run(*args, **kw)


core.subprocess = _TolerantSubprocess()
core.BATTLE_TIMEOUT = int(os.environ.get("ARENA_BATTLE_TIMEOUT", core.BATTLE_TIMEOUT))

# Training reward pool: the agent's own 30 sparring warriors (same distribution as the
# hidden hill, r = 0.83 with it over agent-level warriors, results/proxy_check.md),
# plus the 60-warrior training hill for breadth. Neither contains a hidden-hill warrior.
TRAIN_HILL = sorted((ROOT / "data" / "sparring").glob("*.red")) + sorted((ROOT / "training" / "train_hill").glob("*.red"))
EVAL_HILL = sorted((ROOT / "data" / "hill").glob("*.red"))
GATE_DIRS = [ROOT / "data" / "hill", ROOT / "data" / "sparring"]
CORPUS = [ROOT / "data" / "corpus"]
# Hidden-hill scores at 500 rounds (points / 45000). The reward is the environment's own:
# 0 at Dwarf, 1 at the reference (README, "How it is scored"). The one-line Imp scores 7427,
# above Dwarf, so it earns 0.052; what keeps training off the Imp is the selection floor
# below (TRAIN_FLOOR), not the reward.
DWARF, IMP, REF = 6637 / 45000, 7427 / 45000, 21899 / 45000
FLOOR = DWARF
# Same idea on the training pool (50 rounds): Dwarf 0.2509, Imp 0.2152. Samples must beat
# this to be kept as SFT data (run_expert_iteration.sh passes it as --min-score).
TRAIN_FLOOR = 0.2509
# Archetype examples shown in the prompt. Everything in baselines/ counts as published for
# the training copy check, so the model has to change them, not hand them back.
EXAMPLES = ["imp", "dwarf", "stone_spl", "silk_paper", "scanner_basic"]
EXAMPLE_DIRS = [ROOT / "baselines"]
EXAMPLE_GATE = os.environ.get("EXAMPLE_GATE", "1") != "0"      # the CPU smoke test turns it off
# PROMPT_STYLE=examples (default): the task, five textbook archetype warriors, the reference.
# PROMPT_STYLE=primer: a subset of the agent's /app/doc and nothing else: the task,
# doc/strategy_primer.md (no code), the documentation's example Dwarf, the reference.
# PROMPT_STYLE=docs: the same plus doc/corewar-glossary.html as plain text, the agent's own
# glossary, which carries short code fragments of the common techniques. The agent's
# beginners' guide, ICWS '94 draft and pMARS manual do not fit in the context and are left out.
# PROMPT_STYLE=arch: the colleague's training/mlx protocol (arch_prompts.py is his prompts.py,
# unchanged): a compact reference and the primer's archetypes without warrior code, one prompt per
# archetype, selection of the top fraction within each archetype (generate.py, select_sft.py).
PROMPT_STYLE = os.environ.get("PROMPT_STYLE", "examples")

DOC_FILES = ["index.md", "opcodes.md", "modifiers.md", "addressing_modes.md", "labels.md", "operands.md", "metadata.md"]


def _html_text(path):
    import html
    t = Path(path).read_text(errors="replace")
    t = re.sub(r"(?is)<(script|style|head).*?</\1>", "", t)
    t = re.sub(r"(?i)<br\s*/?>|</(p|dt|dd|li|h\d|tr|pre)>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(l.rstrip() for l in t.splitlines())).strip()


def build_prompt():
    doc = "\n\n".join((ROOT / "doc" / "redcode" / f).read_text() for f in DOC_FILES)
    examples = "\n\n".join("```redcode\n" + (ROOT / "baselines" / f"{n}.red").read_text().strip() + "\n```" for n in EXAMPLES)
    if PROMPT_STYLE in ("primer", "docs"):
        glossary = ("Core War glossary (from the documentation):\n\n" + _html_text(ROOT / "doc" / "corewar-glossary.html") + "\n\n"
                    if PROMPT_STYLE == "docs" else "")
        return (
            "Write an original Core War warrior in Redcode (ICWS '94, pMARS 0.9.4, coresize 8000, "
            "80000 cycles, 8000 processes, max length 100, min distance 100). It will fight a hill of "
            "strong human-written warriors; per round win = 3 points, tie = 1, loss = 0. "
            "Reply with the complete warrior in a single ```redcode code block, starting with ;redcode-94 "
            "and a ;name line. Do not copy published warriors: the example below is one, and a copy of it "
            "scores zero.\n\n"
            + (ROOT / "doc" / "strategy_primer.md").read_text().strip() + "\n\n"
            "Example warrior from the documentation (Dwarf):\n\n```redcode\n"
            + (ROOT / "doc" / "example_dwarf.red").read_text().strip() + "\n```\n\n"
            + glossary +
            "Redcode reference:\n\n" + doc
        )
    return (
        "Write an original Core War warrior in Redcode (ICWS '94, pMARS 0.9.4, coresize 8000, "
        "80000 cycles, 8000 processes, max length 100, min distance 100). It will fight a hill of "
        "strong human-written warriors; per round win = 3 points, tie = 1, loss = 0. "
        "Reply with the complete warrior in a single ```redcode code block, starting with ;redcode-94 "
        "and a ;name line. Do not copy published warriors.\n\n"
        "Below are textbook examples of the basic archetypes. They are a starting point, not an answer: "
        "the Imp and the Dwarf are trivial and score zero, a copy or a constants-only variant of any "
        "example scores zero, and only a warrior that beats the Imp and the Dwarf on the hill earns "
        "anything. Combine and change the ideas (bombing step, bomb type, decoys, imp gates, "
        "paper/stone/scanner mixes).\n\n" + examples + "\n\n"
        "Redcode reference:\n\n" + doc
    )


CODE_RE = re.compile(r"```(?:redcode|red|asm)?\s*\n(.*?)```", re.S)


def extract(text):
    m = CODE_RE.findall(text)
    src = max(m, key=len) if m else text
    return src.strip() + "\n"


def _score_one(args):
    src, hill, rounds = args
    ins, _ = core.assemble(src)
    if not ins:
        return {"valid": False, "copy": False, "score": 0.0, "len": 0, "published_sim": 0.0}
    gate = core.nearest_published(ins, GATE_DIRS)
    pub = core.nearest_published(ins, CORPUS)
    ex = core.nearest_published(ins, EXAMPLE_DIRS) if EXAMPLE_GATE else {"copy": False}
    if gate["copy"] or pub["copy"] or ex["copy"]:
        # training never rewards published warriors, even ones the eval gate would allow
        return {"valid": True, "copy": True, "score": 0.0, "len": len(ins), "published_sim": max(pub["exact"], pub["struct"])}
    s = core.hill_score(core.play_hill(src, [Path(h) for h in hill], rounds, workers=1))
    return {"valid": True, "copy": False, "score": s, "len": len(ins), "published_sim": max(pub["exact"], pub["struct"])}


def score_many(sources, hill, rounds=50, workers=None):
    hill = [str(h) for h in hill]
    with ProcessPoolExecutor(workers) as ex:
        return list(ex.map(_score_one, [(s, hill, rounds) for s in sources], chunksize=4))


def reward(hill_score):
    return min(1.0, max(0.0, (hill_score - FLOOR) / (REF - FLOOR)))


def write_jsonl(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def read_jsonl(path):
    return [json.loads(l) for l in open(path)]
