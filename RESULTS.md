# ReAct Harness Experiment Results — July 2026

**Models compared:** GLM-5.2 (z-ai/glm-5.2) vs Claude Opus 4.8 (anthropic/claude-opus-4.8)

**Setup:** Identical ReAct loop, same 5 coding tasks, same tools, same verification, same termination rules (max 30 turns, $2 cap, 1h wall clock). Separate verifier model.

**Tasks (all in `examples/`):**
- csv_normalizer
- recursive_parser (the interesting failure case)
- broken_api_client
- markdown_converter
- pipeline_debug

## Headline Results

| Model          | Tasks Completed | Total Cost | Avg Tokens/Task | Notes |
|----------------|-----------------|------------|-----------------|-------|
| GLM-5.2       | 5/5            | $0.25     | 57k            | All succeeded cleanly |
| Claude Opus 4.8 | 4/5          | $6.29     | 185k           | Dropped recursive_parser |

**Cost ratio:** ~25× more expensive for Opus.  
**Token ratio:** ~3.2× more tokens for Opus.  
**Success rate:** GLM won outright (5/5 vs 4/5).

## Recursive Parser Vignette (the dropped task)

**GLM-5.2:**
- 6 turns
- $0.019
- Clean solution in minimal steps

**Claude Opus 4.8:**
- 16 turns
- $1.77
- Escalated after hitting cost/turn limits
- Overthought an algorithmic task, repeatedly revised approach instead of converging

Full run records (JSON) for the 10 primary runs are in `runs/`. Raw logs and intermediate attempts are not published.

## Reproducibility

Clone the repo, set up `.env` with OpenRouter key, and run:

```bash
./run_comparison.sh
```

Or run individual tasks via `main.py`.

See README.md for full setup and the loop architecture.

---

*All numbers from the author's own API spend on public list-price models. Five tasks is a sample, not a verdict on either model.*