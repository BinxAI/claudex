#!/usr/bin/env python3
"""Pre-Tool-Use Hook for Claude Code.

Runs BEFORE Claude executes Write/Edit/MultiEdit tools.
Blocks actions that violate workflow rules.

Architecture layers are configured in LAYER_CONFIG below.
Customize the layers dict to match your project structure.
"""

import json
import sys
from pathlib import Path

# === CUSTOMIZE THIS FOR YOUR PROJECT ===
# Map layer paths to forbidden imports
LAYER_CONFIG = {
    # "src/core/": ["sqlalchemy", "redis", "httpx", "fastapi"],
    # "src/db/": [],  # db can import anything below it
}

# File basenames that should NOT appear in certain layers
LAYER_FILE_BLOCKS = {
    # "src/core/": ["llm", "openai", "anthropic", "client"],
}

# Layers that should not import from each other (sibling isolation)
SIBLING_BLOCKS = {
    # "src/worker/": ["from src.api"],
    # "src/db/": ["from src.worker", "from src.api"],
}


def get_project_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists():
            return current
        current = current.parent
    return Path.cwd()


def check_layer_placement(file_path: str) -> tuple[bool, str]:
    """Check if file is being created/edited in correct architectural layer."""
    path_str = str(Path(file_path)).replace("\\", "/").lower()

    # Check file basename blocks
    for layer, blocked_names in LAYER_FILE_BLOCKS.items():
        if f"/{layer}" in path_str:
            basename = Path(file_path).name.lower()
            for kw in blocked_names:
                if kw in basename:
                    return False, (
                        f"BLOCKED: Files matching '{kw}' don't belong in {layer}. File: {file_path}"
                    )

    return True, ""


def check_file_size(file_path: str, content: str) -> tuple[bool, str]:
    MAX_LINES = 500
    WARN_LINES = 300
    lines = content.count("\n") + 1

    if lines > MAX_LINES:
        return False, (
            f"BLOCKED: File has {lines} lines (max: {MAX_LINES}). "
            f"Split into smaller modules. File: {file_path}"
        )

    if lines > WARN_LINES:
        print(
            json.dumps(
                {
                    "warning": (
                        f"File has {lines} lines (ideal: <={WARN_LINES}). Consider refactoring."
                    )
                }
            ),
            file=sys.stderr,
        )

    return True, ""


def check_session_exists() -> tuple[bool, str]:
    project_root = get_project_root()
    session_dir = project_root / ".claude" / "session"
    current_task = session_dir / "CURRENT_TASK.md"

    if not current_task.exists():
        return False, (
            "BLOCKED: No active task. Run '/dev start <task>' first to initialize session."
        )

    try:
        import time

        mtime = current_task.stat().st_mtime
        age_hours = (time.time() - mtime) / 3600
        if age_hours > 48:
            print(
                json.dumps(
                    {"warning": f"Session is {age_hours:.0f} hours old. Consider archiving."}
                ),
                file=sys.stderr,
            )
    except Exception:
        pass

    return True, ""


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"allow": True}))
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        print(json.dumps({"allow": True}))
        return

    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "")

    if not file_path:
        print(json.dumps({"allow": True}))
        return

    if not any(file_path.endswith(ext) for ext in [".py", ".ts", ".tsx", ".js", ".jsx"]):
        print(json.dumps({"allow": True}))
        return

    path_lower = file_path.replace("\\", "/").lower()
    if "/.claude/" in path_lower or "/tests/" in path_lower:
        print(json.dumps({"allow": True}))
        return

    checks = [
        ("session", lambda: check_session_exists()),
        ("layer", lambda: check_layer_placement(file_path)),
    ]

    if tool_name == "Write" and content:
        checks.append(("size", lambda: check_file_size(file_path, content)))

    for _check_name, check_fn in checks:
        allowed, message = check_fn()
        if not allowed:
            print(json.dumps({"allow": False, "message": message}))
            return

    print(json.dumps({"allow": True}))


if __name__ == "__main__":
    main()
