"""Regression tests for the Core War environment (run with `make test`)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from arena import core  # noqa: E402

HILL = sorted((ROOT / "data" / "hill").glob("*.red"))
SPAR = sorted((ROOT / "data" / "sparring").glob("*.red"))
REF = (ROOT / "data" / "reference_toxic.red").read_text()
IMP = ";redcode-94\n        mov.i #0, 1\n"


def test_split_is_disjoint_and_as_documented():
    split = json.loads((ROOT / "data" / "split.json").read_text())
    assert len(HILL) == 30 and len(SPAR) == 10
    assert {p.stem for p in HILL} == set(split["hill"])
    assert {p.stem for p in SPAR} == set(split["sparring"])
    assert not ({p.stem for p in HILL} & {p.stem for p in SPAR})
    assert split["reference"] not in split["hill"] + split["sparring"]


def test_reference_is_elo_number_one():
    rank = json.loads((ROOT / "data" / "elo_ranking.json").read_text())["ranking"]
    assert rank[-1][0] == "toxic"


def test_reward_anchors_match_the_simulator():
    verify = (ROOT / "task_src" / "verify.py").read_text()
    assert "IMP = 1423 / 9000" in verify and "REF = 4370 / 9000" in verify
    # 30 opponents x 100 rounds x 3 points = 9000: scores are exact multiples of 1/9000
    assert round(core.hill_score(core.play_hill(IMP, HILL)) * 9000) == 1423
    assert round(core.hill_score(core.play_hill(REF, HILL)) * 9000) == 4370


def test_scores_are_deterministic():
    a = core.hill_score(core.play_hill(REF, HILL[:5]))
    b = core.hill_score(core.play_hill(REF, HILL[:5]))
    assert a == b


def test_sanitizer_blocks_the_long_line_hang():
    assert core.sanitize(";" + "x" * 300 + "\n") is not None
    assert len(core.sanitize(";" + "x" * 300 + "\n").splitlines()[0]) == core.MAX_LINE
    assert core.sanitize("mov 0, 1 " + "+0" * 200 + "\n") is None
    assert core.sanitize(";" * 30000) is None


def test_copy_gate_catches_sparring_and_hill_copies_but_not_originals():
    for p in SPAR[:3] + HILL[:3]:
        ins = core.assemble(p.read_text())[0]
        assert core.nearest_published(ins, [ROOT / "data" / "hill", ROOT / "data" / "sparring"])["copy"]
    for p in sorted((ROOT / "runs").rglob("*.red")):
        ins = core.assemble(p.read_text())[0]
        assert not core.nearest_published(ins, [ROOT / "data" / "hill", ROOT / "data" / "sparring"])["copy"], p


def test_task_dir_keeps_hidden_hill_out_of_agent_images():
    task = ROOT / "harbor" / "corewar-hill"
    if not task.exists():
        return
    env_files = {p.name for p in (task / "environment").rglob("*.red")}
    assert not env_files & {p.name for p in HILL}
    assert (task / "tests" / "data" / "hill").exists()
