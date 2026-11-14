PY ?= python3
HARBOR ?= harbor
MODEL ?= anthropic/claude-opus-5-5
TASK = harbor/corewar-hill
STOP_EARLY_RUNS = $(shell cat runs/final-env/start_times.txt 2>/dev/null)

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
	  "final-env-opus-5.5=runs/final-env/opus-5.5/*.red" \
	  "v1-opus-5.5=runs/opus-5.5/*.red" \
	  "v1-opus-5.5-lessons=runs/opus-5.5-lessons/*.red" \
	  "v1-sonnet-5.5=runs/sonnet-5.5/*.red" \
	  "codeclash-ladder-2026-07=runs/codeclash-ladder-2026-07/*.red" \
	  "baselines=baselines/*.red"
	@cat results/eval.md

# The exploit and simple-strategy sweep behind EXPLOITS.md
exploits: pmars
	$(PY) exploits/run_exploits.py
	$(PY) exploits/stop_early.py $(STOP_EARLY_RUNS)

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
