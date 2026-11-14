Write the strongest Core War warrior you can, in Redcode, and submit it.

## How it is scored

Your warrior plays a hidden hill of 30 human-written competitive warriors,
taken from the public history of the ICWS '94 King-of-the-Hill and spread
over the whole strength range, from weak warriors to some of the strongest
ever written. Against each hill warrior it
plays 100 rounds with pMARS 0.9.4 in standard '94 settings: coresize 8000,
80000 cycles before a tie, 8000 processes, max warrior length 100, min distance
100, ICWS '94 instructions with the pMARS extensions (p-space is allowed).
Starting positions follow pMARS's fixed position series (`-f`), so scores are
exactly reproducible.

Per round: win = 3 points, tie = 1, loss = 0. Your hill score is your mean
points per round over the whole hill divided by 3 (1 = every round won). The
reward rescales it so that a one-line imp (`mov.i #0, 1`, hill score 0.1581)
gets 0 and a strong human-written warrior (hill score 0.4856) gets 1:
reward = max(0, (hill score - 0.1581) / (0.4856 - 0.1581)). It can exceed 1.

A warrior that does not assemble scores 0. pMARS hangs on very long source
lines, so comment lines are cut to 200 characters and a code line longer than
200 characters makes the file invalid (files are limited to 20 000 bytes).

Write your own warrior. A near-copy of a sparring warrior or of a hill warrior
scores 0, and every submission's closest match among about 580 published
warriors is reported to the reviewers. Using published ideas and techniques is
fine; submitting someone else's warrior is not.

## What you have

- The MCP server `corewar`:
  - `get_rules` — these rules.
  - `list_sparring`, `get_sparring(name)` — 10 public sparring warriors of the
    same kind as the hill. None of them is on the hill.
  - `battle(source, opponents=None, rounds=100)` — play your warrior against
    sparring warriors with exactly the scoring settings.
  - `battle_custom(source, opponent_source, rounds=100)` — play two warriors of
    your own against each other.
  - `submit(source)` — set your final submission. You can submit as often as you
    like; the last accepted submission is the one scored.
  - `status` — what is currently submitted.
- In `/app`, local copies for fast iteration: `bin/pmars` (the scoring
  simulator), `doc/` (the Redcode language reference, the ICWS '94 draft and the
  pMARS manual; no strategy guides), `sparring/` and `tools/battle.py`
  (`python3 tools/battle.py my.red` plays the sparring pool with the scoring
  settings).

Submit with the `submit` tool. If nothing was submitted through the tool, the
file `/app/submission.red` is scored instead.

You have 45 minutes. Do not use the internet. Keep a valid submission in place
as you work: whatever is submitted when you stop is your result.
