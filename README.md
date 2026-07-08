# ReAct Harness

A readable, instrumented ReAct (Reason + Act) loop for comparing LLM coding agents on real tasks.

## Why

Static benchmarks (SWE-bench, FrontierSWE) tell you which model scores higher on 30-minute evals. They don't tell you what happens when you give a model a multi-file job with real error recovery required. This harness runs the same ReAct loop across different models and measures what actually matters: success rate, tool-call efficiency, error recovery, and real dollar cost.

## July 2026 Experiment

I ran the same five coding tasks on GLM-5.2 and Claude Opus 4.8. Treat this as a small anecdotal loop-engineering run, not a benchmark-grade verdict: it was one run per task/model, used a transcript-reading verifier, and did not originally publish raw traces in this repo.

Observed in that run:

- **GLM-5.2**: 5/5 completed for **$0.25** total (~57k tokens avg)
- **Claude Opus 4.8**: 4/5 completed for **$6.29** total (~185k tokens avg)

The one task Opus dropped (recursive parser) is the interesting case: GLM solved it in 6 turns for $0.019. Opus took 16 turns, spent $1.77, and escalated because the verifier rejected the transcript.

See [RESULTS.md](RESULTS.md) for the full per-task table, caveats, and reproduction notes.

**Repo:** https://github.com/cclawton/react-harness

## Principles

1. **Readable** — the entire loop logic fits in one file (`src/react_harness/loop.py`).
2. **Backend-agnostic** — swap any OpenRouter model without changing loop code.
3. **Producer ≠ Verifier** — the model running the loop is not the model judging the result.
4. **Instrumented** — every turn logged: tool calls, tokens, cost, elapsed time. Full run saved as JSON.
5. **Bounded** — hard limits on turns, cost, and wall-clock time.
6. **Escalation** — on failure or budget exhaustion, surfaces to the human with a summary.

## Quick Start

```bash
# 1. Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env: add your OpenRouter API key (OPENROUTER_API_KEY=...)

# 3. Run a single task
python main.py \
  --actor-model z-ai/glm-5.2 \
  --verifier-model openai/gpt-4o-mini \
  --goal-file examples/recursive_parser_goal.md \
  --workdir examples/recursive_parser_glm
```

## Running the Full Comparison

```bash
./run_comparison.sh
```

This runs all 5 tasks on both models and writes rows to `runs/comparison_results.csv`. By default it uses `openai/gpt-4o-mini` as a fixed verifier; override with `VERIFIER_MODEL=... ./run_comparison.sh`.

## Architecture

```
src/react_harness/
├── config.py           — .env loading, limits, paths
├── backend.py          — OpenRouter client + per-model cost tracking
├── tools.py            — terminal, file I/O, test runner (the act surface)
├── loop.py             — the ReAct loop: plan → act → observe → iterate → verify
├── instrumentation.py  — per-turn + per-run logging, JSON output
└── __init__.py
main.py                 — CLI entry point
runs/                   — JSON run records (auto-generated)
examples/               — sample tasks with goal.md + workdir
```

## The Loop

```
GOAL (explicit, verifiable spec)
  ↓
PLAN (model proposes next action as JSON)
  ↓
ACT (execute tool — terminal, file, test runner)
  ↓
OBSERVE (capture real output — stdout, stderr, exit code)
  ↓
ITERATE (feed observation back to model)
  ↓
VERIFY (separate verifier checks: did we meet the goal?)
  ↓
DONE or ESCALATE
```

The model communicates via a simple JSON protocol:

```json
{"action": "run_tests", "args": {"command": "python -m pytest -v"}}
```

```json
{"action": "done", "result": "Created solution.py with is_prime() — all 13 tests pass"}
```

## What It Measures

| Metric                | Why |
|-----------------------|-----|
| Success rate          | Did it reach a working solution? |
| Tool-call count       | How many actions to get there? |
| Error recovery        | How many failed actions were recovered? |
| Token cost            | Real dollar cost per completed task |
| Wall-clock time       | How long in real seconds? |
| Verifier confidence   | Did the separate verifier agree it's done? |

## License

MIT — use it, fork it, run your own comparisons.

---

*My own tests, my own machine. Views mine, not my employer's.*