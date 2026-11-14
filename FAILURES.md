# FAILURES.md — what frontier agents get wrong on this task

**Evidence base**
- 7 complete agent runs:
  - 5 fresh Claude Opus 5.5 runs (A, B, C, D2, E2);
  - 1 Opus 5.5 run with a lessons section added to the instructions (G);
  - 1 Claude Sonnet 5.5 run (F).
- All runs used the same arena: 45 minutes, pMARS, the language reference, and the 10
  sparring warriors.
- The 4 final LLM warriors from CodeClash's CC:Ladder (July 2026) serve as outside
  evidence.
- Each run's own log is summarised in `runs/*/run_*.md`.

**Where the numbers come from**
- `results/eval.md` (`make eval`);
- `results/generalization.json`;
- `results/per_opponent.json`.

## Headline

| | hidden-hill score | reward |
|---|---|---|
| human reference (Toxic, fixed before any run) | 0.486 | 1.000 |
| Opus 5.5, 5 fresh runs | 0.373 – 0.462 | mean 0.754, 95% CI [0.626, 0.882] |
| Opus 5.5 + lessons (G) | 0.387 | 0.700 |
| Sonnet 5.5 (F) | 0.203 | 0.136 |
| CodeClash ladder warriors (Opus 4.8, GPT-5.5, Sonnet 5, Gemini 3.5 Flash) | 0.077 – 0.339 | 0.000 – 0.552 |

All 7 runs scored below the reference. The best Opus run (D2) reached 0.929.

The failures below are decisions. They are not missing compute and not missing
information:
- Every agent had the exact scoring simulator.
- Every Opus agent swept dozens to hundreds of warrior configurations against the sparring pool.
- Every agent wrote working Redcode.

## F1. Optimising the visible test set (Goodhart on the sparring pool)

All agents treated the 10 sparring warriors as the objective. The typical search was
a random search over hundreds of constant sets, selected by sparring score. The
sparring score then overestimated the hidden score:

| run | sparring (100 rounds) | hidden hill | difference |
|---|---|---|---|
| A | 0.375 | 0.396 | +0.021 |
| B | 0.497 | 0.373 | −0.124 |
| C | 0.456 | 0.396 | −0.060 |
| D2 | 0.583 | 0.462 | −0.120 |
| E2 | 0.418 | 0.397 | −0.021 |
| G (lessons) | 0.430 | 0.387 | −0.043 |
| F (Sonnet) | 0.313 | 0.203 | −0.110 |
| **reference** | **0.489** | **0.486** | **−0.003** |

**Run B is the clearest case.**
- On the sparring pool, it scores above the human reference: 0.497 against 0.489.
- On the hidden hill, it is the worst of the five Opus runs: 0.373 against 0.486.
- Its constants were selected on the same 10 opponents it was scored on.

The human warrior does not drop at all. Sparring rank and hidden rank barely agree
across the Opus runs: B is 2nd on sparring and last on the hill.

## F2. Converging on one archetype

Every fresh Opus run tried roughly the same menu, in roughly the same order:
- silk paper;
- stone;
- scanner;
- a p-space switcher.

All of them concluded the same thing: "composites cost too much, the plain scanner
wins". Four of the five submitted a lone 0.5c `seq` scanner with a `spl` carpet and a
clear (A, B, C, D2). E2 submitted a lone silk paper.

The reference is a composite: its strategy line reads "qscan -> paper/imp". Composites
are common on the hidden hill too. By a keyword count of the warriors' own `;strategy`
lines, qscan appears in 14 of 30 and imps in 10.

The agents' composites failed because they were built and then dropped within minutes.
They reported one-off bugs in them, for example:
- a `mod.b` modifier error in D2;
- a scanner that bombed its own inactive half in G.

None of them spent tuning effort on a composite comparable to the hundreds of
configurations they swept for their final scanner or paper.

## F3. Seeing the weakness, naming it, not fixing it

Four of the five fresh Opus runs (A, B, C, E2) named their weak opponents in their
final reports: imp-based and qscan→stone/imp warriors. Typical lines:
- A: "weak spots: stone/imp warriors with quick-scan";
- B: "against imp-based warriors there are 22–45 % ties, I did not fix it";
- C: "weak spot: stone/imp and stone/paper preceded by a qscan";
- E2: "it only rarely wins against papers and the stone/imp warriors".

On the hidden hill, the ten imp-based opponents are exactly where the gap
concentrates. Mean points against them:

| | A | B | C | E2 | G | reference |
|---|---|---|---|---|---|---|
| imp-based opponents | 0.35 | 0.32 | 0.35 | 0.37 | 0.36 | 0.45 |
| others | 0.42 | 0.40 | 0.42 | 0.41 | 0.40 | 0.50 |

D2 is the exception: it was the only run to add `dat <2667` anti-imp bombs to its
clear (0.47 / 0.46). It is also the strongest run.

## F4. Stopping early with budget left

| run | A | B | C | D2 | E2 | F | G |
|---|---|---|---|---|---|---|---|
| minutes used of 45 | ~28 | ~27 | ~28 | ~25 | ~28 | ~8 | ~28 |

Every run stopped with 16–37 minutes unused, convinced it had converged. That
includes G, whose instructions said in so many words "use the whole time budget".
G acknowledged this in its report: "I stopped at about 28 of 45 minutes, although the
instructions asked to use the whole budget".

Sonnet 5.5 stopped after 8 minutes with a 3-instruction stone.

## F5. Telling an agent what went wrong does not fix it (one run)

Run G received a four-point lessons section, `task_src/lessons.md`. It covers F1–F4 in
general terms and contains no warrior code and no hidden-hill content.

| lesson | what G did |
|---|---|
| validation discipline (F1) | followed |
| private archetype test set with random positions (F1) | followed |
| try composites (F2) | followed: submitted a p-space scanner/paper composite |
| use the whole budget (F4) | ignored |

G scored 0.700, inside the fresh runs' range. Knowing the right strategy family did
not give it the engineering depth to make that family strong in 28 minutes.

This is a single run, so we claim only that lessons in the prompt did not close the
gap here. That is the motivation for training on environment experience (TRAINING.md)
instead of prompting.

## Why this matters beyond Core War

Agents increasingly build things that are judged against adversaries or distributions
they cannot see:
- exploit and defence code;
- trading and bidding strategies;
- game agents;
- code that must survive fuzzing or red-teaming.

In each case, they have a small visible test set and a hidden, adaptive opposition.

This task isolates that situation:
- **exact and deterministic:** the simulator is the scorer, and there is no noise to
  argue about;
- **cheap:** a few seconds per evaluation on 2 cores;
- **anchored to 30 years of human expert data,** so "stronger" is not hypothetical.

The failure it exposes is not "the model cannot code" or "the model lacks the rules".
It is that the agent:
- optimises what it can see;
- commits early to the first archetype that works;
- leaves its own diagnosed weaknesses unfixed;
- stops while budget remains.

Those are the same behaviours that make agent-written code pass visible tests and fail
in production.
