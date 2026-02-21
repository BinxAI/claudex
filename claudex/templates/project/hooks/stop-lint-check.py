#!/usr/bin/env python3
"""Stop Hook — Check lint/format only if source files were modified.

Runs after Claude finishes a turn. Only fires lint/format check
if git detects modified .py files in src/ or tests/.
"""

import json
import subprocess
from pathlib import Path

# === CUSTOMIZE: directories to lint ===
LINT_DIRS = ["src/", "tests/"]
LINT_EXTENSIONS = [".py"]


def get_project_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists():
            return current
        current = current.parent
    return Path.cwd()


def has_modified_files() -> bool:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--"] + LINT_DIRS,
            capture_output=True,
            text=True,
            cwd=str(get_project_root()),
            timeout=10,
        )
        files = [
            f
            for f in result.stdout.strip().split("\n")
            if any(f.endswith(ext) for ext in LINT_EXTENSIONS)
        ]
        return len(files) > 0
    except Exception:
        return False


def run_lint_check() -> dict:
    root = str(get_project_root())
    issues = []

    try:
        result = subprocess.run(
            ["ruff", "check"] + LINT_DIRS + ["--quiet"],
            capture_output=True,
            text=True,
            cwd=root,
            timeout=30,
        )
        if result.returncode != 0:
            count = len([ln for ln in result.stdout.strip().split("\n") if ln.strip()])
            issues.append(f"Lint: {count} issue(s) — run `ruff check {' '.join(LINT_DIRS)} --fix`")
    except FileNotFoundError:
        pass

    try:
        result = subprocess.run(
            ["ruff", "format"] + LINT_DIRS + ["--check", "--quiet"],
            capture_output=True,
            text=True,
            cwd=root,
            timeout=30,
        )
        if result.returncode != 0:
            fmt_cmd = f"ruff format {' '.join(LINT_DIRS)}"
            issues.append(f"Format: files need reformatting — run `{fmt_cmd}`")
    except FileNotFoundError:
        pass

    return {"clean": len(issues) == 0, "issues": issues}


def main():
    if not has_modified_files():
        print(json.dumps({"status": "ok"}))
        return

    result = run_lint_check()
    if result["clean"]:
        print(json.dumps({"status": "ok"}))
    else:
        output = {
            "status": "ok",
            "user_message": "Lint/format issues detected:\n"
            + "\n".join(f"  - {i}" for i in result["issues"]),
        }
        print(json.dumps(output))


if __name__ == "__main__":
    main()
