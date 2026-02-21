#!/usr/bin/env python3
"""Post-Tool-Use Hook for Claude Code.

Runs AFTER Claude executes Write/Edit/MultiEdit tools.
Checks for architectural violations and logs them.

Customize LAYER_RULES to match your project's architecture.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

# === CUSTOMIZE THIS FOR YOUR PROJECT ===
# Map layer paths to forbidden imports
LAYER_RULES = {
    # "src/core/": {
    #     "forbidden_imports": ["sqlalchemy", "redis", "httpx", "fastapi"],
    #     "no_import_from": [],
    # },
    # "src/db/": {
    #     "forbidden_imports": [],
    #     "no_import_from": ["from src.worker", "from src.api"],
    # },
}


def get_project_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists():
            return current
        current = current.parent
    return Path.cwd()


def log_violation(violation_type: str, file_path: str, message: str, severity: str = "MEDIUM"):
    project_root = get_project_root()
    log_file = project_root / ".claude" / "feedback" / "VIOLATIONS_LOG.md"

    if not log_file.exists():
        return

    try:
        content = log_file.read_text(encoding="utf-8")
        ids = re.findall(r"### V(\d+)", content)
        next_id = max([int(i) for i in ids], default=0) + 1
        timestamp = datetime.now().strftime("%Y-%m-%d")

        entry = f"""
---

### V{next_id:03d} - {timestamp} - {severity}

**Type**: {violation_type}
**File**: {file_path}

**What Happened**:
{message}

**Root Cause**:
Auto-detected by post-tool-use hook

**Tags**: #auto-detected #{violation_type.lower().replace(" ", "-")}
"""

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)

    except Exception:
        pass


def check_for_violations(file_path: str, content: str) -> list:
    violations = []
    path_str = str(file_path).replace("\\", "/").lower()

    for layer_path, rules in LAYER_RULES.items():
        if f"/{layer_path}" not in path_str:
            continue

        for lib in rules.get("forbidden_imports", []):
            if f"import {lib}" in content or f"from {lib}" in content:
                violations.append(
                    {
                        "type": "Architecture",
                        "severity": "CRITICAL",
                        "message": f"Layer '{layer_path}' imports forbidden library '{lib}'.",
                    }
                )

        for pattern in rules.get("no_import_from", []):
            if pattern in content:
                violations.append(
                    {
                        "type": "Architecture",
                        "severity": "HIGH",
                        "message": (
                            f"Layer '{layer_path}' has forbidden import pattern: '{pattern}'."
                        ),
                    }
                )

    # Hardcoded secrets check (all layers)
    secret_patterns = ["api_key=", "password=", "secret=", "token="]
    for pattern in secret_patterns:
        if pattern in content.lower():
            if "os.getenv" not in content and "os.environ" not in content:
                violations.append(
                    {
                        "type": "Security",
                        "severity": "CRITICAL",
                        "message": (
                            f"Possible hardcoded secret detected ('{pattern}')."
                            " Use environment variables."
                        ),
                    }
                )

    return violations


def update_session_files(file_path: str, action: str):
    project_root = get_project_root()
    context_file = project_root / ".claude" / "session" / "CONTEXT_SUMMARY.md"

    if not context_file.exists():
        return

    try:
        content = context_file.read_text(encoding="utf-8")
        if file_path not in content:
            marker = "## Files Modified This Session"
            if marker in content:
                timestamp = datetime.now().strftime("%H:%M")
                new_entry = f"- [{Path(file_path).name}]({file_path}): {action} at {timestamp}\n"
                parts = content.split(marker)
                if len(parts) == 2:
                    section = parts[1]
                    lines = section.split("\n")
                    insert_idx = 0
                    for i, line in enumerate(lines):
                        if line.startswith("- "):
                            insert_idx = i + 1
                        elif line.startswith("## ") and i > 0:
                            break
                    lines.insert(insert_idx, new_entry.strip())
                    new_content = parts[0] + marker + "\n".join(lines)
                    context_file.write_text(new_content, encoding="utf-8")
    except Exception:
        pass


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"status": "ok"}))
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        print(json.dumps({"status": "ok"}))
        return

    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "") or tool_input.get("new_string", "")

    if not file_path:
        print(json.dumps({"status": "ok"}))
        return

    action = "created" if tool_name == "Write" else "modified"
    update_session_files(file_path, action)

    path_lower = file_path.replace("\\", "/").lower()
    is_source = any(file_path.endswith(ext) for ext in [".py", ".ts", ".tsx", ".js", ".jsx"])
    is_config = "/.claude/" in path_lower
    is_test = "/tests/" in path_lower

    if is_source and not is_config and not is_test:
        violations = check_for_violations(file_path, content)
        for v in violations:
            log_violation(v["type"], file_path, v["message"], v["severity"])
        if violations:
            print(json.dumps({"status": "violations_logged", "count": len(violations)}))
            return

    print(json.dumps({"status": "ok"}))


if __name__ == "__main__":
    main()
