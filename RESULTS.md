# ReAct Harness Experiment Results — July 2026

**Models compared:** GLM-5.2 (`z-ai/glm-5.2`) vs Claude Opus 4.8 (`anthropic/claude-opus-4.8`)

**Setup:** Identical ReAct loop, same 5 coding tasks, same tools, same verification, same termination rules (max 30 turns, $2 cap, 1h wall clock). Separate verifier model used for final check.

**Tasks** (all self-contained in `examples/`):
- `csv_normalizer`
- `recursive_parser` (the interesting failure case)
- `broken_api_client`
- `markdown_converter`
- `pipeline_debug`

## Per-Task Results

| Ex | Example              | Model       | Status    | Turns | Cost    | Time   | Tokens   | Verifier Conf |
|----|----------------------|-------------|-----------|-------|---------|--------|----------|---------------|
| 1  | csv_normalizer       | GLM-5.2     | success   | 7     | $0.0071 | 16s    | 10,426   | 1.00          |
| 1  | csv_normalizer       | Opus 4.8    | success   | 12    | $0.6726 | 78s    | 93,531   | 0.85          |
| 2  | recursive_parser     | GLM-5.2     | success   | 6     | $0.0191 | 430s   | 18,191   | 1.00          |
| 2  | recursive_parser     | Opus 4.8    | escalated | 16    | $1.7705 | 177s   | 267,512  | 0.70          |
| 3  | broken_api_client    | GLM-5.2     | success   | 7     | $0.0136 | 39s    | 18,020   | 1.00          |
| 3  | broken_api_client    | Opus 4.8    | success   | 8     | $0.4955 | 68s    | 66,093   | 0.98          |
| 4  | markdown_converter   | GLM-5.2     | success   | 15    | $0.1535 | 1250s  | 139,842  | 1.00          |
| 4  | markdown_converter   | Opus 4.8    | success   | 14    | $1.6339 | 207s   | 228,673  | 0.97          |
| 5  | pipeline_debug       | GLM-5.2     | success   | 14    | $0.0584 | 111s   | 99,042   | 1.00          |
| 5  | pipeline_debug       | Opus 4.8    | success   | 19    | $1.7185 | 128s   | 270,463  | 0.97          |

## Aggregate Summary

| Metric                    | GLM-5.2     | Opus 4.8    |
|---------------------------|-------------|-------------|
| Success rate              | 5/5 (100%)  | 4/5 (80%)   |
| Total cost                | $0.2517     | $6.2910     |
| Avg cost per task         | $0.0503     | $1.2582     |
| Avg turns                 | 9.8         | 13.8        |
| Avg verifier confidence   | 1.00        | 0.89        |
| Avg tokens per task       | 57,104      | 185,254     |

**Cost ratio:** ~25× more expensive for Opus.  
**Token ratio:** ~3.2× more tokens for Opus.  
**Success rate:** GLM won outright.

## Recursive Parser Vignette (the dropped task)

**GLM-5.2**  
- 6 turns, $0.0191, 18k tokens  
- Clean solution in minimal steps, perfect verifier confidence.

**Claude Opus 4.8**  
- 16 turns, $1.7705, 267k tokens  
- Escalated after hitting cost/turn limits.  
- Overthought an algorithmic task, repeatedly revised approach instead of converging.

## Key Findings

1. GLM-5.2 cost **25× less** than Opus across the full suite.
2. GLM-5.2 had a **higher success rate** (5/5 vs 4/5).
3. GLM used fewer turns on 4 of 5 tasks.
4. Opus was faster in wall-clock time on some tasks (generates tokens faster) but used far more of them.
5. GLM was dramatically more token-efficient.
6. Both models struggled most with the 4-file `markdown_converter` task.
7. Opus's token verbosity was its main weakness — consistently 3–10× more tokens than necessary.

## Run Data Location

All raw run records live in the repository at:

```
runs/
├── 20260701-*.json
├── 20260702-*.json
└── comparison_results.csv   (summary, populated by run_comparison.sh)
```

Each JSON contains the full turn-by-turn trace, tool calls, token usage, costs, and final status.

## Reproducibility

```bash
# One-time setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OpenRouter key

# Run the full comparison (10 runs)
./run_comparison.sh

# Or run a single task
python main.py \
  --actor-model z-ai/glm-5.2 \
  --verifier-model z-ai/glm-5.2 \
  --goal-file examples/recursive_parser_goal.md \
  --workdir examples/recursive_parser_glm
```

See [README.md](README.md) for architecture and loop details.

---

*All numbers from the author's own API spend on public list-price models. Five tasks is a sample, not a verdict on either model.*