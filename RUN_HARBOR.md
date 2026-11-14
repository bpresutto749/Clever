# Running the task with Harbor + OpenCode

You need Docker, Harbor (`uv tool install harbor`, or `pip install harbor`) and an API key
for one model provider. The examples use OpenAI and Gemini, whose sponsor credits are
available at Junction.

```bash
git clone <this repo> && cd corewar-env
make task                      # generates harbor/corewar-hill and harbor/corewar-hill-public

export OPENAI_API_KEY=...      # or GEMINI_API_KEY=... / ANTHROPIC_API_KEY=...

# 1. Reference (oracle): submits the human reference warrior via MCP. Expect reward 1.0.
harbor run -p harbor/corewar-hill -a oracle

# 2. Do-nothing. Expect reward 0.
harbor run -p harbor/corewar-hill -a nop

# 3. The agent: OpenCode, 3 attempts.
harbor run -p harbor/corewar-hill -a opencode -m openai/<model> -k 3
#    e.g.  -m google/<gemini model>   or   -m anthropic/<claude model>
```

**Model endpoint not on the allowlist.** The agent phase runs with an allowlist of common
inference hosts (see `task.toml`). If your provider endpoint is not on it, add the host:
`--allow-agent-host <host>`.

**Docker host without egress control.** If your Docker host cannot run Harbor's egress
control, Harbor fails as the agent phase starts. In that case, use the public-network
variant: `-p harbor/corewar-hill-public`. See EXPLOITS.md for what that variant gives up.

## What to look at

| file in the job's trial directory | what it shows |
|---|---|
| `verifier/reward.txt` | the reward, one number in [0, 1] |
| `verifier/details.json` | the raw hill score, the unclipped reward, the closest published warrior, and wins / losses / ties per hidden-hill opponent |
| `artifacts/results/events.jsonl` | every battle and submission the agent made, with timestamps |
| `artifacts/results/history/` | the source of every accepted submission |
| `agent/` | the OpenCode trajectory |

To score every submission of a run on both the visible pool and the hidden hill:

```bash
python3 exploits/trajectories.py --spar data/sparring --out my_run <trial>/artifacts/results:<start epoch>
```

That table is how FAILURES.md shows the visible score rising while the hidden score does
not.
