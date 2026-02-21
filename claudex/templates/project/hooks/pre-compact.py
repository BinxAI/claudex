#!/usr/bin/env python3
"""PreCompact Hook — Auto-checkpoint before context compaction.

Saves session state so progress survives compaction.
"""

import json
from datetime import UTC, datetime
from pathlib import Path


def get_project_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists():
            return current
        current = current.parent
    return Path.cwd()


def auto_checkpoint():
    project_root = get_project_root()
    session_dir = project_root / ".claude" / "session"

    if not session_dir.exists():
        return {"status": "skip"}

    current_task = session_dir / "CURRENT_TASK.md"
    if not current_task.exists():
        return {"status": "skip"}

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    progress_file = session_dir / "TASK_PROGRESS.md"
    if progress_file.exists():
        try:
            content = progress_file.read_text(encoding="utf-8")
            marker = f"\n\n---\n_Auto-checkpoint before compaction: {now}_\n"
            progress_file.write_text(content + marker, encoding="utf-8")
        except Exception:
            pass

    return {"status": "ok", "checkpointed_at": now}


def main():
    result = auto_checkpoint()
    output = {"status": result.get("status", "ok")}
    if result.get("checkpointed_at"):
        output["user_message"] = f"Auto-checkpoint saved ({result['checkpointed_at']})"
    print(json.dumps(output))


if __name__ == "__main__":
    main()
