# Core War hill: rules

You write one Redcode warrior. It is scored against a hidden hill of 30
human-written competitive warriors from the public history of the ICWS '94
King-of-the-Hill, spread over the whole strength range, from weak warriors to
some of the strongest ever written.

## Simulator and settings

pMARS 0.9.4, standard '94 hill settings: coresize 8000, 80000 cycles before a
tie, 8000 processes per warrior, max warrior length 100, min distance 100,
ICWS '94 instruction set with the pMARS extensions (SEQ/SNE/NOP, p-space LDP/STP
are allowed). Starting positions follow pMARS's fixed position series (`-f`),
so every score is exactly reproducible.

## Score

Against each hill warrior your warrior plays 100 rounds. Per round: win = 3 points, tie = 1, loss = 0. Your hill score is your mean
points per round over the whole hill divided by 3 (1 = every round won). The
reward rescales it so that a one-line imp (`mov.i #0, 1`, hill score 0.1581)
gets 0 and a strong human-written warrior (hill score 0.4856) gets 1:
reward = max(0, (hill score - 0.1581) / (0.4856 - 0.1581)). It can exceed 1.

## Validity

- The warrior must assemble with pMARS. A file that does not assemble scores 0.
- pMARS hangs on very long source lines, so comment lines are cut to 200
  characters and a code line longer than 200 characters makes the file invalid.
  Source files are limited to 20 000 bytes.
- Write your own warrior. A near-copy of a sparring warrior or of a hill
  warrior scores 0. Near-copy means the assembled code matches with a
  similarity of 0.8 or more (a copy pasted inside a larger file counts), or has
  the same instruction sequence with only constants changed (0.9 or more, for
  warriors of 8+ instructions). Every submission's closest match among about
  580 published warriors is also reported to the reviewers. Using published
  ideas and techniques is fine; submitting someone else's warrior is not.

## Sparring pool

10 public warriors of the same kind as the hill. None of them is on the hill.
Use them to test; `battle` plays them with exactly the scoring settings.
