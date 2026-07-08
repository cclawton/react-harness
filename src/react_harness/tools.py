"""Tools — the act surface the loop can call.

Each tool takes a dict of args, returns a string observation.
Tools are deliberately simple and deterministic: terminal, file I/O, test runner.
No web, no browser — keep the surface small and inspectable.
"""

import json
import subprocess
from pathlib import Path

from .config import Config

# Max output length per tool call (chars). Prevents context blowup.
MAX_OUTPUT = 8000


def _safe_path(config: Config, path: str) -> Path:
    """Resolve a model-supplied path and ensure it stays inside workdir."""
    candidate = Path(path)
    if candidate.is_absolute():
        raise ValueError("absolute paths are not allowed")

    workdir = config.workdir.resolve()
    full = (workdir / candidate).resolve()
    try:
        full.relative_to(workdir)
    except ValueError as exc:
        raise ValueError("path escapes the working directory") from exc
    return full


def _truncate(text: str, limit: int = MAX_OUTPUT) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return (
        text[:half]
        + f"\n\n... [truncated {len(text) - limit} chars] ...\n\n"
        + text[-half:]
    )


def run_command(args: dict, config: Config) -> str:
    """Execute a shell command in the workdir. Returns stdout+stderr+exit code."""
    command = args.get("command", "")
    if not command:
        return "ERROR: missing 'command' argument"

    timeout = min(args.get("timeout", 120), 300)
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(config.workdir),
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        output += f"\n[exit code: {result.returncode}]"
        return _truncate(output)
    except subprocess.TimeoutExpired:
        return f"ERROR: command timed out after {timeout}s"
    except Exception as e:
        return f"ERROR: {e}"


def read_file(args: dict, config: Config) -> str:
    """Read a file's contents. Path is relative to workdir."""
    path = args.get("path", "")
    if not path:
        return "ERROR: missing 'path' argument"

    try:
        full = _safe_path(config, path)
    except ValueError as e:
        return f"ERROR: invalid path '{path}': {e}"

    if not full.exists():
        return f"ERROR: file not found: {path}"
    if full.is_dir():
        return f"ERROR: {path} is a directory, not a file"

    try:
        content = full.read_text(errors="replace")
        return _truncate(content)
    except Exception as e:
        return f"ERROR: {e}"


def write_file(args: dict, config: Config) -> str:
    """Write content to a file. Path is relative to workdir. Creates parent dirs."""
    path = args.get("path", "")
    content = args.get("content", "")
    if not path:
        return "ERROR: missing 'path' argument"

    try:
        full = _safe_path(config, path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        return f"OK: wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"ERROR: {e}"


def list_files(args: dict, config: Config) -> str:
    """List files in a directory (recursive, relative paths)."""
    path = args.get("path", ".")
    try:
        full = _safe_path(config, path)
    except ValueError as e:
        return f"ERROR: invalid path '{path}': {e}"

    if not full.exists():
        return f"ERROR: directory not found: {path}"

    workdir = config.workdir.resolve()
    lines = []
    for p in sorted(full.rglob("*")):
        if any(part in {".git", "__pycache__", "node_modules", ".venv"} for part in p.parts):
            continue
        rel = p.relative_to(workdir)
        kind = "DIR " if p.is_dir() else "FILE"
        lines.append(f"{kind}  {rel}")
    return _truncate("\n".join(lines)) if lines else "(empty)"


def run_tests(args: dict, config: Config) -> str:
    """Run the test suite and capture pass/fail summary."""
    command = args.get("command", "python -m pytest -v 2>&1")
    timeout = min(args.get("timeout", 120), 300)
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(config.workdir),
        )
        output = result.stdout + "\n" + result.stderr
        output += f"\n[exit code: {result.returncode}]"
        return _truncate(output)
    except subprocess.TimeoutExpired:
        return f"ERROR: tests timed out after {timeout}s"
    except Exception as e:
        return f"ERROR: {e}"


# Tool registry — maps tool name → (function, description)
TOOLS: dict[str, tuple] = {
    "run_command": (
        run_command,
        "Execute a shell command. Args: {command: str, timeout?: int}. Returns stdout, stderr, exit code.",
    ),
    "read_file": (
        read_file,
        "Read a file's contents. Args: {path: str}. Path relative to workdir.",
    ),
    "write_file": (
        write_file,
        "Write content to a file. Args: {path: str, content: str}. Creates parent dirs.",
    ),
    "list_files": (
        list_files,
        "List files recursively. Args: {path?: str, default '.'}.",
    ),
    "run_tests": (
        run_tests,
        "Run the test suite. Args: {command?: str, timeout?: int}. Default: python -m pytest -v.",
    ),
}


def execute_tool(name: str, args: dict, config: Config) -> str:
    """Dispatch a tool call. Returns the observation string."""
    if name not in TOOLS:
        return f"ERROR: unknown tool '{name}'. Available: {', '.join(TOOLS.keys())}"
    func, _ = TOOLS[name]
    try:
        return func(args, config)
    except Exception as e:
        return f"ERROR: tool '{name}' raised: {e}"


def tool_descriptions() -> str:
    """Return a human-readable description of all tools for the system prompt."""
    lines = []
    for name, (_, desc) in TOOLS.items():
        lines.append(f"  - {name}: {desc}")
    return "\n".join(lines)
