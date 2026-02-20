#!/usr/bin/env python3
"""SessionEnd Hook — Memory harvest + session marker on exit.

Runs when the session ends:
- Extracts key learnings from session files -> writes to MEMORY.md
- Marks TASK_PROGRESS.md with session end timestamp
"""

import json
import re
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


def get_project_slug(project_root: Path) -> str:
    """Convert project path to Claude Code project slug (matches ~/.claude/projects/ naming)."""
    path_str = str(project_root).replace("\\", "/")
    slug = path_str.replace(":", "").replace("/", "-").strip("-")
    return slug


def find_memory_file(project_root: Path) -> "Path | None":
    """Locate MEMORY.md in the Claude Code project memory directory."""
    slug = get_project_slug(project_root)
    user_home = Path.home()

    candidates = [
        user_home / ".claude" / "projects" / slug / "memory" / "MEMORY.md",
        # Also try with drive letter doubled (Windows Claude Code format)
        user_home / ".claude" / "projects" / (slug.replace("-", "--", 1)) / "memory" / "MEMORY.md",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # If none exist, use first candidate if parent dir exists
    first = candidates[0]
    if first.parent.exists():
        return first

    return None


def extract_completed_tasks(progress_text: str) -> list:
    """Extract completed task lines from TASK_PROGRESS.md."""
    completed = []
    for line in progress_text.split("\n"):
        line = line.strip()
        if line.startswith("\u2705") or re.match(r"^-\s*\[x\]", line, re.IGNORECASE):
            task = re.sub(r"^[-\u2705\s\[x\]]+", "", line, flags=re.IGNORECASE).strip()
            if task:
                completed.append(task)
    return completed[:5]


def extract_decisions(context_text: str) -> list:
    """Extract architectural decisions from CONTEXT_SUMMARY.md."""
    decisions = []
    in_decisions = False
    for line in context_text.split("\n"):
        if "decision" in line.lower() or "architecture" in line.lower():
            in_decisions = True
        if in_decisions and line.strip().startswith("-"):
            decision = line.strip().lstrip("- ").strip()
            if decision and len(decision) > 10:
                decisions.append(decision)
    return decisions[:3]


def harvest_memory(project_root: Path) -> dict:
    """Scan session files and extract harvestable learnings."""
    session_dir = project_root / ".claude" / "session"
    result = {"task": None, "completed": [], "decisions": [], "violations": 0}

    current_task = session_dir / "CURRENT_TASK.md"
    if current_task.exists():
        try:
            content = current_task.read_text(encoding="utf-8")
            for heading in ("## Task Description", "## Task"):
                if heading in content:
                    lines = content.split(heading)[1].split("##")[0].strip().split("\n")
                    result["task"] = lines[0].strip()[:80] if lines else None
                    break
        except Exception:
            pass

    progress_file = session_dir / "TASK_PROGRESS.md"
    if progress_file.exists():
        try:
            result["completed"] = extract_completed_tasks(progress_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    context_file = session_dir / "CONTEXT_SUMMARY.md"
    if context_file.exists():
        try:
            result["decisions"] = extract_decisions(context_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    violations_log = project_root / ".claude" / "feedback" / "VIOLATIONS_LOG.md"
    if violations_log.exists():
        try:
            content = violations_log.read_text(encoding="utf-8")
            result["violations"] = len(re.findall(r"### V\d+", content))
        except Exception:
            pass

    return result


def write_memory_entry(project_root: Path, harvest: dict, date_str: str) -> None:
    """Write harvested session learnings to MEMORY.md."""
    if not harvest["completed"] and not harvest["decisions"]:
        return

    memory_file = find_memory_file(project_root)
    if memory_file is None:
        return

    try:
        content = memory_file.read_text(encoding="utf-8") if memory_file.exists() else ""
        entry_lines = ["\n\n## Session " + date_str]
        if harvest["task"]:
            entry_lines.append("**Task**: " + harvest["task"])
        if harvest["completed"]:
            entry_lines.append("**Completed**:")
            for item in harvest["completed"]:
                entry_lines.append("- " + item)
        if harvest["decisions"]:
            entry_lines.append("**Decisions**:")
            for d in harvest["decisions"]:
                entry_lines.append("- " + d)
        if harvest["violations"] > 0:
            v = harvest["violations"]
            entry_lines.append(f"**Violations logged**: {v} total (see VIOLATIONS_LOG.md)")
        memory_file.write_text(content + "\n".join(entry_lines), encoding="utf-8")
    except Exception:
        pass


def main():
    project_root = get_project_root()
    now = datetime.now(UTC)
    date_str = now.strftime("%Y-%m-%d %H:%M UTC")

    reason = "unknown"
    try:
        hook_input = json.loads(sys.stdin.read())
        reason = hook_input.get("matcher", "exit")
    except Exception:
        pass

    # 1. Mark TASK_PROGRESS.md with session end timestamp
    progress_file = project_root / ".claude" / "session" / "TASK_PROGRESS.md"
    if progress_file.exists():
        try:
            content = progress_file.read_text(encoding="utf-8")
            marker = "\n\n---\n_Session ended: " + date_str + " (reason: " + reason + ")_\n"
            progress_file.write_text(content + marker, encoding="utf-8")
        except Exception:
            pass

    # 2. Harvest learnings into MEMORY.md
    try:
        harvest = harvest_memory(project_root)
        write_memory_entry(project_root, harvest, date_str[:10])
    except Exception:
        pass

    print(json.dumps({"status": "ok"}))


if __name__ == "__main__":
    main()
