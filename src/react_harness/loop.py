"""The ReAct loop — plan → act → observe → iterate.

This is the heart of the harness. It is deliberately readable:
the entire loop logic is in one function you can follow top to bottom.

Protocol: the model communicates actions via JSON in its response.
We parse the first JSON block found. Two action types:

  {"action": "done", "result": "summary of what was accomplished"}
  {"action": "<tool_name>", "args": {...}}

If the model output doesn't contain valid JSON, we feed the error
back as an observation and let it try again (counts as a turn).
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Any

from .backend import Backend
from .config import Config
from .instrumentation import RunRecord, TurnRecord
from .tools import execute_tool, tool_descriptions

logger = logging.getLogger(__name__)

ACTOR_SYSTEM_PROMPT = """\
You are an autonomous coding agent inside a ReAct loop.

GOAL:
{goal}

WORKING DIRECTORY: {workdir}

You have these tools:
{tools}

PROTOCOL:
Each turn, respond with EXACTLY ONE JSON block wrapped in ```json fences.
Choose an action:

  To call a tool:
  ```json
  {{"action": "<tool_name>", "args": {{...}}}}
  ```

  To signal completion:
  ```json
  {{"action": "done", "result": "<brief summary of what you accomplished>"}}
  ```

RULES:
- One action per turn. Wait for the observation before deciding the next step.
- Think briefly before the JSON block about what you're doing and why.
- Use list_files first to understand the codebase layout.
- Read files before editing them.
- After writing code, run the tests to verify.
- If something fails, read the error, understand it, and fix it. Don't retry blindly.
- When the goal is met, call "done" with a summary.

Turn {turn} of {max_turns}. Budget remaining: ${budget_remaining:.4f}.
"""


def _extract_json(text: str) -> dict | None:
    """Extract the first JSON object from model output. Returns None if not found.

    Handles:
    - Fenced code blocks (```json ... ```)
    - Raw JSON in the text
    - Nested braces (tracks brace depth)
    - Trailing extra braces (model sometimes adds extra })
    """
    # Try fenced code block first — extract the content between fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    candidates = []
    if match:
        candidates.append(match.group(1))

    # Also try the full text (in case there's no fence)
    candidates.append(text)

    for candidate in candidates:
        result = _parse_first_json(candidate)
        if result is not None:
            return result

    return None


def _parse_first_json(text: str) -> dict | None:
    """Find and parse the first balanced JSON object in text.

    Tracks brace depth to handle nested objects. Tolerates trailing
    extra braces by trying progressively shorter substrings.
    """
    # Find the first '{'
    start = text.find("{")
    if start == -1:
        return None

    # Walk forward tracking depth (respecting string literals)
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                # Found a balanced object — try to parse it
                candidate = text[start : i + 1]
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    pass
                # Keep looking for the next balanced object
    return None


def run_loop(
    goal: str,
    config: Config,
    actor: Backend,
    verifier: Backend,
) -> RunRecord:
    """Run the ReAct loop to completion. Returns a RunRecord."""

    run = RunRecord(
        goal=goal,
        actor_model=actor.model,
        verifier_model=verifier.model,
        config={
            "max_turns": config.max_turns,
            "max_cost_usd": config.max_cost_usd,
            "max_wall_clock_seconds": config.max_wall_clock_seconds,
            "workdir": str(config.workdir),
        },
        started_at=datetime.now().isoformat(),
    )

    import os

    # The conversation history — accumulates across turns
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": ACTOR_SYSTEM_PROMPT.format(
                goal=goal,
                workdir=config.workdir,
                tools=tool_descriptions(),
                turn=1,
                max_turns=config.max_turns,
                budget_remaining=config.max_cost_usd,
            ),
        }
    ]

    start_time = time.time()

    for turn_num in range(1, config.max_turns + 1):
        elapsed = time.time() - start_time
        remaining_budget = config.max_cost_usd - actor.cost_usd - verifier.cost_usd

        # --- Bounded termination checks ---
        if remaining_budget <= 0:
            run.status = "bounded"
            logger.warning("Budget exhausted ($%.4f)", config.max_cost_usd)
            break
        if elapsed > config.max_wall_clock_seconds:
            run.status = "bounded"
            logger.warning("Wall clock limit exceeded (%ds)", config.max_wall_clock_seconds)
            break

        # Update system prompt with current turn/budget
        messages[0]["content"] = ACTOR_SYSTEM_PROMPT.format(
            goal=goal,
            workdir=config.workdir,
            tools=tool_descriptions(),
            turn=turn_num,
            max_turns=config.max_turns,
            budget_remaining=remaining_budget,
        )

        turn_start = time.time()
        record = TurnRecord(turn=turn_num)

        # --- PLAN (model proposes next action) ---
        try:
            # Dynamic max_tokens watch + bump (if turns consistently >6k output)
            current_max = getattr(config, '_effective_max_tokens', config.max_tokens)
            result = actor.chat(messages, temperature=0.0, max_tokens=current_max)
        except Exception as e:
            record.error = f"Actor API error: {e}"
            record.elapsed_seconds = time.time() - turn_start
            record.cost_so_far_usd = actor.cost_usd
            run.add_turn(record)
            run.status = "failed"
            break

        record.actor_text = result.text
        messages.append({"role": "assistant", "content": result.text})

        # Log actual output tokens this turn + dynamic bump if hitting 6k+
        last_ct = actor.usage.completion_tokens - getattr(actor, "_prev_ct", 0)
        setattr(actor, "_prev_ct", actor.usage.completion_tokens)
        logger.info("  Actor output tokens this turn: %d (max_tokens=%d)", last_ct, current_max)

        if last_ct >= 6000:
            streak = getattr(config, "_high_token_streak", 0) + 1
            config._high_token_streak = streak
            if streak >= 2:
                new_max = min(16384, max(8192, current_max * 2))
                config._effective_max_tokens = new_max
                logger.warning("High token usage streak detected. Bumping max_tokens %d → %d", current_max, new_max)
        else:
            config._high_token_streak = 0

        # --- Parse the action ---
        action = _extract_json(result.text)
        if action is None:
            obs = (
                "ERROR: Could not parse JSON from your response. "
                "Output a single JSON block in ```json fences. "
                f"Available tools: {', '.join(['done', 'run_command', 'read_file', 'write_file', 'list_files', 'run_tests'])}"
            )
            record.action_name = "(parse_error)"
            record.observation = obs
            record.elapsed_seconds = time.time() - turn_start
            record.cost_so_far_usd = actor.cost_usd
            run.add_turn(record)
            messages.append({"role": "user", "content": obs})
            continue

        record.action_name = action.get("action", "(unknown)")
        record.action_args = action.get("args", {})

        # --- ACT + OBSERVE ---
        if record.action_name == "done":
            record.observation = f"[agent signalled completion: {action.get('result', '')}]"
            record.elapsed_seconds = time.time() - turn_start
            record.cost_so_far_usd = actor.cost_usd
            run.add_turn(record)

            # --- VERIFY (separate verifier) ---
            verify_result = _verify(goal, config, actor, verifier, messages)
            if verify_result["passed"]:
                run.status = "success"
            else:
                run.status = "escalated"
            run.finalize(run.status, actor, verifier, verify_result)
            return run

        observation = execute_tool(record.action_name, record.action_args, config)
        record.observation = observation
        record.elapsed_seconds = time.time() - turn_start
        record.cost_so_far_usd = actor.cost_usd
        run.add_turn(record)

        # --- ITERATE (feed observation back) ---
        messages.append({"role": "user", "content": f"Observation:\n{observation}"})

        logger.info(
            "Turn %d/%d | %s | %.1fs | $%.4f",
            turn_num, config.max_turns, record.action_name,
            record.elapsed_seconds, actor.cost_usd,
        )

    else:
        # Loop exhausted all turns without "done"
        run.status = "bounded"
        logger.warning("Max turns (%d) exhausted", config.max_turns)

    # Finalize without verifier if we didn't reach "done"
    run.finalize(run.status, actor, verifier, {"passed": False, "reason": "loop ended without completion signal"})
    return run


def _verify(
    goal: str,
    config: Config,
    actor: Backend,
    verifier: Backend,
    conversation: list[dict[str, str]],
) -> dict[str, Any]:
    """Run the separate verifier. Returns {passed: bool, reason: str, ...}.

    The verifier sees:
    - The original goal
    - The full conversation (actions + observations)
    - The current state of the working directory (via a fresh listing)

    The verifier does NOT run tools. It makes a single judgment call.
    """
    verifier_prompt = f"""\
You are a VERIFIER — a separate agent whose ONLY job is to judge whether the ACTOR met the goal.

GOAL:
{goal}

WORKING DIRECTORY: {config.workdir}

ACTOR'S CONVERSATION (actions and observations):
{_summarize_conversation(conversation)}

VERIFICATION INSTRUCTIONS:
1. Read the goal carefully.
2. Check whether the actor's actions and observations show the goal was met.
3. Be strict — if there's no evidence of success, say it failed.
4. If tests were run, check if they passed.

Respond with a JSON block:
```json
{{"passed": true/false, "reason": "<one or two sentences explaining your judgment>", "confidence": 0.0-1.0}}
```
"""
    try:
        result = verifier.chat(
            [{"role": "user", "content": verifier_prompt}],
            temperature=0.0,
        )
        parsed = _extract_json(result.text)
        if parsed and "passed" in parsed:
            return parsed
        return {
            "passed": False,
            "reason": f"Verifier output could not be parsed: {result.text[:500]}",
            "confidence": 0.0,
        }
    except Exception as e:
        return {"passed": False, "reason": f"Verifier API error: {e}", "confidence": 0.0}


def _summarize_conversation(conversation: list[dict[str, str]]) -> str:
    """Compress the conversation for the verifier (avoid context blowup)."""
    lines = []
    for msg in conversation[1:]:  # skip system prompt
        role = msg["role"]
        content = msg["content"]
        # Truncate long observations
        if len(content) > 2000:
            content = content[:1000] + f"\n...[truncated {len(content) - 2000} chars]...\n" + content[-1000:]
        lines.append(f"--- {role} ---\n{content}\n")
    return "\n".join(lines)
