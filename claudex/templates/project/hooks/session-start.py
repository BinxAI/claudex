#!/usr/bin/env python3
"""Session Start Hook for Claude Code.

Runs when a new session begins:
- Checks for existing session files
- Warns about stale sessions
- Reports background queue and parallel session status
- Reminds to run /dev continue or /dev start
"""

import json
import time
from pathlib import Path


def get_project_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists():
            return current
        current = current.parent
    return Path.cwd()


def check_session_state() -> dict:
    project_root = get_project_root()
    session_dir = project_root / ".claude" / "session"
    current_task = session_dir / "CURRENT_TASK.md"

    result = {
        "has_session": False,
        "is_stale": False,
        "age_hours": 0,
        "task_name": None,
        "recommendation": None,
        "message": None,
    }

    if not session_dir.exists() or not current_task.exists():
        result["recommendation"] = "start"
        result["message"] = "No active task found. Run '/dev start <task>' to begin."
        return result

    result["has_session"] = True

    try:
        content = current_task.read_text(encoding="utf-8")
        if "## Task Description" in content:
            lines = content.split("## Task Description")[1].split("##")[0].strip().split("\n")
            result["task_name"] = (lines[0].strip() if lines else "Unknown")[:80]
    except Exception:
        pass

    try:
        mtime = current_task.stat().st_mtime
        age_hours = (time.time() - mtime) / 3600
        result["age_hours"] = round(age_hours, 1)

        if age_hours > 48:
            result["is_stale"] = True
            result["recommendation"] = "archive"
            result["message"] = (
                f"Session is {age_hours:.0f}h old. "
                f"Task: {result['task_name'] or 'Unknown'}. "
                f"Run '/dev continue' to resume or '/dev start' for new task."
            )
        else:
            result["recommendation"] = "continue"
            result["message"] = (
                f"Active session: {result['task_name'] or 'Unknown'} "
                f"({age_hours:.1f}h old). Run '/dev continue' to resume."
            )
    except Exception:
        result["message"] = "Active session found. Run '/dev continue' to resume."

    return result


def check_background_queue() -> str:
    """Check BACKGROUND_QUEUE.md for actionable items."""
    project_root = get_project_root()
    queue_file = project_root / ".claude" / "session" / "BACKGROUND_QUEUE.md"

    if not queue_file.exists():
        return ""

    try:
        content = queue_file.read_text(encoding="utf-8")
        kicked_count = content.count("| KICKED")
        queued_count = content.count("| QUEUED")

        messages = []

        if kicked_count > 0:
            mtime = queue_file.stat().st_mtime
            age_hours = (time.time() - mtime) / 3600
            if age_hours > 8:
                messages.append(
                    f"BACKGROUND QUEUE: {kicked_count} agent(s) kicked {age_hours:.0f}h ago "
                    f"- run '/background-queue review' to check results"
                )
            else:
                messages.append(f"BACKGROUND QUEUE: {kicked_count} agent(s) running")

        if queued_count > 0:
            messages.append(
                f"BACKGROUND QUEUE: {queued_count} task(s) queued "
                f"- run '/night-kick' to launch them"
            )

        return "\n".join(messages)
    except Exception:
        return ""


def check_parallel_sessions() -> str:
    """Check PARALLEL_SESSIONS.md for active parallel work."""
    project_root = get_project_root()
    parallel_file = project_root / ".claude" / "session" / "PARALLEL_SESSIONS.md"

    if not parallel_file.exists():
        return ""

    try:
        content = parallel_file.read_text(encoding="utf-8")
        if "No active parallel sessions" in content:
            return ""

        active_count = 0
        in_table = False
        for line in content.split("\n"):
            if "## Active Sessions" in line:
                in_table = True
                continue
            if in_table and line.startswith("##"):
                break
            if (
                in_table
                and line.startswith("|")
                and not line.startswith("| #")
                and not line.startswith("| -")
            ):
                active_count += 1

        if active_count > 0:
            return (
                f"PARALLEL SESSIONS: {active_count} active session(s)"
                " - check PARALLEL_SESSIONS.md before editing shared files"
            )
        return ""
    except Exception:
        return ""


def main():
    state = check_session_state()
    output = {
        "status": "ok",
        "has_active_session": state["has_session"],
        "recommendation": state["recommendation"],
    }

    # Check background queue and parallel sessions
    bg_status = check_background_queue()
    parallel_status = check_parallel_sessions()

    extra = []
    if bg_status:
        extra.append(bg_status)
    if parallel_status:
        extra.append(parallel_status)

    if extra:
        extra_msg = "\n".join(extra)
        if state["message"]:
            state["message"] += f"\n\n{extra_msg}"
        else:
            state["message"] = extra_msg

    if state["message"]:
        output["user_message"] = state["message"]
    print(json.dumps(output))


if __name__ == "__main__":
    main()
