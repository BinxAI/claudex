#\!/usr/bin/env python3
# Token Budget Hook -- PreToolUse cost tracking and session budget enforcement.
#
# Reads cumulative token usage from TOKEN_LOG.md.
# Warns at WARN_THRESHOLD, blocks at BLOCK_THRESHOLD.
# Edit the config below to match your session budget and model costs.

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# === CONFIGURE FOR YOUR PROJECT ===
SESSION_TOKEN_BUDGET = 200_000   # tokens per session
WARN_THRESHOLD = 0.80            # warn at 80%
BLOCK_THRESHOLD = 1.00           # block at 100%
# Token cost per 1M tokens (USD) -- Claude Sonnet 4 defaults
INPUT_COST_PER_MTK = 3.00
OUTPUT_COST_PER_MTK = 15.00
# Estimated input/output split
INPUT_RATIO = 0.70
OUTPUT_RATIO = 0.30
# ===================================


def get_project_root() -> Path:
    current = Path.cwd()
    while current \!= current.parent:
        if (current / ".claude").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_token_log(project_root: Path) -> Path:
    return project_root / ".claude" / "session" / "TOKEN_LOG.md"


def read_cumulative_tokens(token_log: Path) -> int:
    if not token_log.exists():
        return 0
    try:
        content = token_log.read_text(encoding="utf-8")
        total = 0
        for line in content.split("
"):
            if line.strip().startswith("|") and "Cumulative" not in line and "---" not in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    try:
                        total = int(parts[3].replace(",", ""))
                    except (ValueError, IndexError):
                        pass
        return total
    except Exception:
        return 0


def estimate_turn_tokens(tool_input: dict) -> int:
    # Rough estimate: count chars in tool input / 4
    try:
        serialized = json.dumps(tool_input)
        return max(100, len(serialized) // 4)
    except Exception:
        return 200


def append_token_log(token_log: Path, turn: int, tokens: int, cumulative: int) -> None:
    cost = (
        (tokens * INPUT_RATIO / 1_000_000 * INPUT_COST_PER_MTK) +
        (tokens * OUTPUT_RATIO / 1_000_000 * OUTPUT_COST_PER_MTK)
    )
    try:
        if not token_log.exists():
            header = [
                "# Token Budget Log",
                "Session started: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "Budget: " + str(SESSION_TOKEN_BUDGET) + " tokens",
                "",
                "| Turn | Est. Tokens | Cumulative | Cost (USD) |",
                "|------|-------------|------------|------------|"
            ]
            token_log.write_text("
".join(header) + "
", encoding="utf-8")
        row = "| " + str(turn) + " | " + str(tokens) + " | " + str(cumulative) + " | $" + f"{cost:.3f}" + " |"
        with token_log.open("a", encoding="utf-8") as f:
            f.write(row + "
")
    except Exception:
        pass


def get_turn_number(token_log: Path) -> int:
    if not token_log.exists():
        return 1
    try:
        content = token_log.read_text(encoding="utf-8")
        rows = [l for l in content.split("
") if l.startswith("|") and "Turn" not in l and "---" not in l]
        return len(rows) + 1
    except Exception:
        return 1


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except Exception:
        print(json.dumps({"status": "ok"}))
        return

    project_root = get_project_root()
    token_log = get_token_log(project_root)

    cumulative = read_cumulative_tokens(token_log)
    turn_tokens = estimate_turn_tokens(hook_input.get("tool_input", {}))
    new_cumulative = cumulative + turn_tokens
    turn_number = get_turn_number(token_log)

    append_token_log(token_log, turn_number, turn_tokens, new_cumulative)

    usage_ratio = new_cumulative / SESSION_TOKEN_BUDGET

    if usage_ratio >= BLOCK_THRESHOLD:
        cost = (
            (new_cumulative * INPUT_RATIO / 1_000_000 * INPUT_COST_PER_MTK) +
            (new_cumulative * OUTPUT_RATIO / 1_000_000 * OUTPUT_COST_PER_MTK)
        )
        print(json.dumps({
            "status": "error",
            "message": (
                "Token budget exhausted: " + str(new_cumulative) + "/" + str(SESSION_TOKEN_BUDGET)
                + " tokens (~$" + f"{cost:.2f}" + ")"
                + ". Start a new session or increase SESSION_TOKEN_BUDGET in token-budget.py."
            )
        }))
        return

    output = {"status": "ok"}

    if usage_ratio >= WARN_THRESHOLD:
        cost = (
            (new_cumulative * INPUT_RATIO / 1_000_000 * INPUT_COST_PER_MTK) +
            (new_cumulative * OUTPUT_RATIO / 1_000_000 * OUTPUT_COST_PER_MTK)
        )
        pct = int(usage_ratio * 100)
        output["user_message"] = (
            "Token budget " + str(pct) + "% used (" + str(new_cumulative) + "/" + str(SESSION_TOKEN_BUDGET)
            + " tokens, ~$" + f"{cost:.2f}" + ")"
            + ". Consider checkpointing and starting a fresh session soon."
        )

    print(json.dumps(output))


if __name__ == "__main__":
    main()
