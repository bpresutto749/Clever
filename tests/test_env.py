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
    assert "IMP = 7427 / 45000" in verify and "REF = 21899 / 45000" in verify
    # 30 opponents x 500 rounds x 3 points = 45000: scores are exact multiples of 1/45000
    assert round(core.hill_score(core.play_hill(IMP, HILL)) * 45000) == 7427
    assert round(core.hill_score(core.play_hill(REF, HILL)) * 45000) == 21899


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


def test_task_keeps_hill_and_sparring_source_out_of_the_agent_image():
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "build_task.py")], check=True, capture_output=True)
    task = ROOT / "harbor" / "corewar-hill"
    env_files = {p.name for p in (task / "environment").rglob("*.red")}
    assert not env_files & {p.name for p in HILL}
    dockerfile = (task / "environment" / "Dockerfile").read_text()
    assert "sparring" not in dockerfile.replace("sparring warriors' source", "")
    assert (task / "tests" / "data" / "hill").exists()
    toml = (task / "task.toml").read_text()
    assert 'network_mode = "allowlist"' in toml and 'url = "http://localhost:8000/mcp"' in toml
    pub = (ROOT / "harbor" / "corewar-hill-public" / "task.toml").read_text()
    assert 'network_mode = "public"' in pub and 'url = "http://arena:8000/mcp"' in pub


def test_assembly_uses_the_battle_context():
    # a source that is an imp when assembled alone and something else in a 2-warrior battle
    src = ";redcode-94\nfor (2-WARRIORS)\n        mov.i #0, 1\nrof\nfor (WARRIORS-1)\n        spl #0, #0\n        jmp -1\nrof\n"
    ins, _ = core.assemble(src)
    assert ins == ["SPL.B #0,#0", "JMP.B $-1,$0"], ins


def test_padding_and_retuning_do_not_escape_the_gate():
    gate = [ROOT / "data" / "hill", ROOT / "data" / "sparring"]
    for f in sorted((ROOT / "exploits" / "cases").glob("*.red")):
        if f.name.startswith("d2_"):
            continue
        ins = core.assemble(f.read_text())[0]
        assert core.nearest_published(ins, gate)["copy"], f.name
