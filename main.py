#!/usr/bin/env python3
"""Entry point for the ReAct harness.

Usage:
  python main.py --goal "..." --workdir /path/to/project
  python main.py --goal-file goal.md --workdir /path/to/project

The harness runs the ReAct loop, prints a summary, and saves a
JSON run record to runs/.
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure src/ is on the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from react_harness.config import Config
from react_harness.backend import Backend
from react_harness.loop import run_loop


def main() -> int:
    parser = argparse.ArgumentParser(description="ReAct coding harness")
    parser.add_argument(
        "--goal",
        type=str,
        default=None,
        help="The goal specification (what does 'done' look like?)",
    )
    parser.add_argument(
        "--goal-file",
        type=str,
        default=None,
        help="Read goal from a file (markdown or plain text)",
    )
    parser.add_argument(
        "--workdir",
        type=str,
        default=None,
        help="Working directory for tool execution (default: cwd)",
    )
    parser.add_argument(
        "--actor-model",
        type=str,
        default=None,
        help="Override actor model (default: from .env)",
    )
    parser.add_argument(
        "--verifier-model",
        type=str,
        default=None,
        help="Override verifier model (default: from .env)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Override max turns",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    args = parser.parse_args()

    # --- Logging ---
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # --- Goal ---
    if args.goal_file:
        goal = Path(args.goal_file).read_text().strip()
    elif args.goal:
        goal = args.goal
    else:
        print("Error: provide --goal or --goal-file", file=sys.stderr)
        return 1

    # --- Config ---
    config = Config()
    if args.workdir:
        config.workdir = Path(args.workdir).resolve()
    if args.actor_model:
        config.actor_model = args.actor_model
    if args.verifier_model:
        config.verifier_model = args.verifier_model
    if args.max_turns:
        config.max_turns = args.max_turns

    # --- Validate ---
    if not config.api_key:
        print("Error: OPENROUTER_API_KEY not set. Copy .env.example to .env and fill in your key.", file=sys.stderr)
        return 1

    print(f"{'='*60}")
    print(f"ReAct Harness")
    print(f"{'='*60}")
    print(f"  Actor:    {config.actor_model}")
    print(f"  Verifier: {config.verifier_model}")
    print(f"  Workdir:  {config.workdir}")
    print(f"  Limits:   {config.max_turns} turns | ${config.max_cost_usd} | {config.max_wall_clock_seconds}s")
    print(f"  Goal:     {goal[:200]}{'...' if len(goal) > 200 else ''}")
    print(f"{'='*60}")
    print()

    # --- Run ---
    actor = Backend(model=config.actor_model, config=config)
    verifier = Backend(model=config.verifier_model, config=config)

    run = run_loop(goal=goal, config=config, actor=actor, verifier=verifier)

    # --- Results ---
    print()
    print(f"{'='*60}")
    print(f"RESULT: {run.status}")
    print(f"{'='*60}")
    print(f"  {run.summary()}")
    if run.verifier_result:
        print(f"  Verifier: passed={run.verifier_result.get('passed')} "
              f"confidence={run.verifier_result.get('confidence', 'N/A')}")
        print(f"  Verifier reason: {run.verifier_result.get('reason', 'N/A')}")
    print()

    # --- Save run record ---
    run_path = run.save(config.runs_dir)
    print(f"Run record saved to: {run_path}")

    return 0 if run.status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
