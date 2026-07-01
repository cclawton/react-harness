"""Instrumentation — per-turn logging for the full run.

Every turn is recorded as a structured log entry. The full run
is saved as JSON to runs/ for post-hoc analysis.

This is the "instrument" in "instrumented ReAct loop".
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .backend import Backend

logger = logging.getLogger(__name__)


@dataclass
class TurnRecord:
    """One iteration of the ReAct loop."""

    turn: int
    actor_text: str = ""
    action_name: str = ""
    action_args: dict = field(default_factory=dict)
    observation: str = ""
    elapsed_seconds: float = 0.0
    cost_so_far_usd: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn": self.turn,
            "actor_text": self.actor_text,
            "action_name": self.action_name,
            "action_args": self.action_args,
            "observation": self.observation,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "cost_so_far_usd": round(self.cost_so_far_usd, 6),
            "error": self.error,
        }


@dataclass
class RunRecord:
    """Full record of a ReAct loop run — saved as JSON."""

    goal: str
    actor_model: str
    verifier_model: str
    config: dict
    turns: list[TurnRecord] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    status: str = ""  # "success", "failed", "bounded", "escalated"
    verifier_result: dict = field(default_factory=dict)
    actor_usage: dict = field(default_factory=dict)
    verifier_usage: dict = field(default_factory=dict)
    total_cost_usd: float = 0.0
    total_seconds: float = 0.0

    def add_turn(self, turn: TurnRecord) -> None:
        self.turns.append(turn)

    def finalize(
        self,
        status: str,
        actor: Backend,
        verifier: Backend,
        verifier_result: dict,
    ) -> None:
        self.status = status
        self.finished_at = datetime.now().isoformat()
        self.actor_usage = actor.usage.to_dict()
        self.verifier_usage = verifier.usage.to_dict()
        self.total_cost_usd = actor.cost_usd + verifier.cost_usd
        self.verifier_result = verifier_result
        self.total_seconds = sum(t.elapsed_seconds for t in self.turns)

    def save(self, runs_dir: Path) -> Path:
        """Save the run record as JSON. Returns the file path."""
        runs_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{ts}-{self.status}.json"
        path = runs_dir / filename

        data = {
            "goal": self.goal,
            "actor_model": self.actor_model,
            "verifier_model": self.verifier_model,
            "config": self.config,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_seconds": round(self.total_seconds, 3),
            "total_turns": len(self.turns),
            "actor_usage": self.actor_usage,
            "verifier_usage": self.verifier_usage,
            "verifier_result": self.verifier_result,
            "turns": [t.to_dict() for t in self.turns],
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return path

    def summary(self) -> str:
        """One-line human summary for console / Signal output."""
        return (
            f"status={self.status} | turns={len(self.turns)} | "
            f"cost=${self.total_cost_usd:.4f} | time={self.total_seconds:.1f}s | "
            f"actor_tokens={self.actor_usage.get('total_tokens', 0)} | "
            f"verifier_tokens={self.verifier_usage.get('total_tokens', 0)}"
        )
