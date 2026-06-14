#!/usr/bin/env python3
"""Claude Code status line: model | context-token usage | session cost.

Reads the status JSON from stdin, then parses the session transcript
(JSONL) for the most recent assistant `usage` block to report how much of
the context window is currently in use.
"""
import json
import os
import sys

CONTEXT_LIMIT = 1_000_000  # context window (1M)


def human(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.0f}m"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def latest_context_tokens(transcript_path):
    """Return total input-side tokens of the most recent assistant turn."""
    if not transcript_path or not os.path.exists(transcript_path):
        return None
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return None
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        usage = (ev.get("message") or {}).get("usage")
        if not usage:
            continue
        return (
            usage.get("input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
        )
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        data = {}

    model = (data.get("model") or {}).get("display_name", "Claude")
    cost = (data.get("cost") or {}).get("total_cost_usd")
    transcript = data.get("transcript_path")

    # ANSI dim/colors
    DIM = "\033[2m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    RESET = "\033[0m"

    parts = [f"{CYAN}{model}{RESET}"]

    ctx = latest_context_tokens(transcript)
    if ctx is not None:
        pct = ctx / CONTEXT_LIMIT * 100
        color = GREEN if pct < 60 else YELLOW if pct < 85 else "\033[31m"
        parts.append(
            f"{color}ctx {human(ctx)}/{human(CONTEXT_LIMIT)} ({pct:.0f}%){RESET}"
        )

    if cost is not None:
        parts.append(f"{DIM}${cost:.4f}{RESET}")

    sys.stdout.write(f" {DIM}|{RESET} ".join(parts))


if __name__ == "__main__":
    main()
