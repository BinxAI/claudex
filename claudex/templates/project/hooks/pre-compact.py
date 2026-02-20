#!/usr/bin/env python3
"""PreCompact Hook — State extraction + auto-checkpoint before context compaction.

Saves full session state snapshot so progress survives compaction.
"""

import json
import re
from datetime import UTC, datetime
from pathlib import Path


def get_project_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists():
            return current
        current = current.parent
    return Path.cwd()


def read_section(text: str, heading: str) -> str:
    if heading not in text:
        return ""
    parts = text.split(heading)[1]
    m = re.search(r"\n##\s", parts)
    if m:
        parts = parts[: m.start()]
    return parts.strip()[:500]


def extract_state(session_dir: Path) -> dict:
    state = {
        "task": None,
        "phase": None,
        "completed_steps": [],
        "active_decisions": [],
        "modified_files": [],
        "next_actions": [],
        "validation_gates": [],
    }

    ct = session_dir / "CURRENT_TASK.md"
    if ct.exists():
        try:
            text = ct.read_text(encoding="utf-8")
            for h in ("## Task Description", "## Task"):
                desc = read_section(text, h)
                if desc:
                    state["task"] = desc.split("\n")[0].strip()[:120]
                    break
            ph = read_section(text, "## Current Phase")
            if ph:
                state["phase"] = ph.split("\n")[0].strip()
        except Exception:
            pass

    pf = session_dir / "TASK_PROGRESS.md"
    if pf.exists():
        try:
            for line in pf.read_text(encoding="utf-8").split("\n"):
                s = line.strip()
                if re.match(r"^[-✅]\s*\[x\]", s, re.IGNORECASE) or s.startswith("✅"):
                    step = re.sub(r"^[-✅\s\[x\]]+", "", s, flags=re.IGNORECASE).strip()
                    if step:
                        state["completed_steps"].append(step)
                elif re.match(r"^-\s*\[\s\]", s):
                    action = re.sub(r"^-\s*\[\s\]\s*", "", s).strip()
                    if action:
                        state["next_actions"].append(action)
            state["completed_steps"] = state["completed_steps"][-8:]
            state["next_actions"] = state["next_actions"][:5]
        except Exception:
            pass

    cf = session_dir / "CONTEXT_SUMMARY.md"
    if cf.exists():
        try:
            text = cf.read_text(encoding="utf-8")
            ds = ""
            for h in ("## Key Decisions", "## Decisions", "## Architectural Decisions"):
                ds = read_section(text, h)
                if ds:
                    break
            for line in ds.split("\n"):
                line = line.strip().lstrip("- ").strip()
                if line and len(line) > 10:
                    state["active_decisions"].append(line[:120])
            state["active_decisions"] = state["active_decisions"][:5]
            fs = ""
            for h in ("## Modified Files", "## Files Modified", "## Files Modified This Session"):
                fs = read_section(text, h)
                if fs:
                    break
            for line in fs.split("\n"):
                line = line.strip()
                if line.startswith("-"):
                    state["modified_files"].append(line.lstrip("- ").strip()[:80])
            state["modified_files"] = state["modified_files"][:10]
        except Exception:
            pass

    vf = session_dir / "VALIDATION_STATE.md"
    if vf.exists():
        try:
            for line in vf.read_text(encoding="utf-8").split("\n"):
                if "✅" in line or "❌" in line or "[x]" in line.lower():
                    g = line.strip()[:80]
                    if g:
                        state["validation_gates"].append(g)
            state["validation_gates"] = state["validation_gates"][:6]
        except Exception:
            pass

    return state


def write_snapshot(session_dir: Path, state: dict, timestamp: str) -> None:
    snapshot = session_dir / "PRE_COMPACT_SNAPSHOT.md"
    lines = [
        "# Pre-Compact Snapshot",
        "_Saved: " + timestamp + "_",
        "_Re-inject this context after compaction to restore session state._",
        "",
    ]
    if state["task"]:
        lines += ["## Active Task", state["task"], ""]
    if state["phase"]:
        lines += ["## Current Phase", state["phase"], ""]
    if state["completed_steps"]:
        lines.append("## Completed Steps")
        for s in state["completed_steps"]:
            lines.append("- ✅ " + s)
        lines.append("")
    if state["next_actions"]:
        lines.append("## Next Actions")
        for a in state["next_actions"]:
            lines.append("- [ ] " + a)
        lines.append("")
    if state["active_decisions"]:
        lines.append("## Architectural Decisions Made")
        for d in state["active_decisions"]:
            lines.append("- " + d)
        lines.append("")
    if state["modified_files"]:
        lines.append("## Files Modified This Session")
        for f in state["modified_files"]:
            lines.append("- " + f)
        lines.append("")
    if state["validation_gates"]:
        lines.append("## Validation Gate Status")
        for g in state["validation_gates"]:
            lines.append("  " + g)
        lines.append("")
    lines += ["---", "_To resume: read this file and continue from Next Actions above._"]
    try:
        snapshot.write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass


def auto_checkpoint(project_root: Path, timestamp: str) -> dict:
    session_dir = project_root / ".claude" / "session"
    if not session_dir.exists():
        return {"status": "skip"}
    if not (session_dir / "CURRENT_TASK.md").exists():
        return {"status": "skip"}
    pf = session_dir / "TASK_PROGRESS.md"
    if pf.exists():
        try:
            content = pf.read_text(encoding="utf-8")
            marker = f"\n\n---\n_Auto-checkpoint before compaction: {timestamp}_\n"
            pf.write_text(content + marker, encoding="utf-8")
        except Exception:
            pass
    state = extract_state(session_dir)
    write_snapshot(session_dir, state, timestamp)
    return {"status": "ok", "checkpointed_at": timestamp}


def main():
    project_root = get_project_root()
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    result = auto_checkpoint(project_root, now)
    output = {"status": result.get("status", "ok")}
    if result.get("checkpointed_at"):
        ts = result["checkpointed_at"]
        output["user_message"] = (
            f"Pre-compact snapshot saved ({ts})"
            " — state preserved in PRE_COMPACT_SNAPSHOT.md"
        )
    print(json.dumps(output))


if __name__ == "__main__":
    main()
