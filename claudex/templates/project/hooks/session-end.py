#!/usr/bin/env python3
"""SessionEnd Hook — Mark session files on exit."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def get_project_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists():
            return current
        current = current.parent
    return Path.cwd()


def main():
    project_root = get_project_root()
    progress_file = project_root / ".claude" / "session" / "TASK_PROGRESS.md"

    if progress_file.exists():
        try:
            reason = "unknown"
            try:
                hook_input = json.loads(sys.stdin.read())
                reason = hook_input.get("matcher", "exit")
            except Exception:
                pass

            now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
            content = progress_file.read_text(encoding="utf-8")
            marker = f"\n\n---\n_Session ended: {now} (reason: {reason})_\n"
            progress_file.write_text(content + marker, encoding="utf-8")
        except Exception:
            pass

    print(json.dumps({"status": "ok"}))


if __name__ == "__main__":
    main()
