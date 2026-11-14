PY ?= python3
HARBOR ?= harbor
MODEL ?= anthropic/claude-opus-5-5
TASK = harbor/corewar-hill

.PHONY: all pmars task lint test eval baselines exploits harbor-reference harbor-nop harbor-agent harbor-all clean

all: pmars task test eval

pmars:
	$(MAKE) -C pmars pmars

# Generate the Harbor task directory from the sources (single source of truth).
task:
	$(PY) build_task.py

lint: task
	$(HARBOR) lint $(TASK)

# Unit and regression tests: scoring anchors, sanitiser, copy gate, exploit regressions.
test: pmars
	$(PY) -m pytest -q tests

# One command, no Docker needed: reference, baselines, recorded agent runs -> results/eval.md
eval: pmars
	$(PY) eval.py --markdown results/eval.md --json results/eval.json \
	  "reference=data/reference_toxic.red" \
	  "opus-5.5=runs/opus-5.5/*.red" \
	  "opus-5.5-lessons=runs/opus-5.5-lessons/*.red" \
	  "sonnet-5.5=runs/sonnet-5.5/*.red" \
	  "codeclash-ladder-2026-07=runs/codeclash-ladder-2026-07/*.red" \
	  "baselines=baselines/*.red"
	@cat results/eval.md

# The exploit and simple-strategy sweep behind EXPLOITS.md
exploits: pmars
	$(PY) exploits/run_exploits.py

# Harbor runs (need Docker). Judges' protocol: reference, do-nothing, 3+ agent runs.
harbor-reference: task
	$(HARBOR) run -p $(TASK) -a oracle
harbor-nop: task
	$(HARBOR) run -p $(TASK) -a nop
harbor-agent: task
	$(HARBOR) run -p $(TASK) -a opencode -m $(MODEL) -k 3
harbor-all: harbor-reference harbor-nop harbor-agent

clean:
	$(MAKE) -C pmars clean
	rm -rf harbor
