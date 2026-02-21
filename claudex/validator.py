"""Health check validator for claudex.

Validates .claude/ directory setup and reports issues.
"""

from pathlib import Path

REQUIRED_DIRS = ["hooks", "commands", "rules", "session", "feedback"]

REQUIRED_FILES = [
    "settings.json",
    "hooks/session-start.py",
    "hooks/pre-tool-use.py",
    "hooks/post-tool-use.py",
    "hooks/pre-compact.py",
    "hooks/stop-lint-check.py",
    "hooks/session-end.py",
]


def validate_project(path: Path) -> tuple[list[str], list[str]]:
    """Validate .claude/ setup. Returns (passes, failures)."""
    passes = []
    failures = []

    # Check .claude/ exists
    claude_dir = path / ".claude"
    if not claude_dir.exists():
        failures.append("'.claude/' directory not found - run 'claudex init' to create it")
        return passes, failures

    passes.append("'.claude/' directory exists")

    # Check required subdirectories
    for dirname in REQUIRED_DIRS:
        subdir = claude_dir / dirname
        if subdir.exists():
            passes.append(f"'.claude/{dirname}/' exists")
        else:
            failures.append(f"Missing '.claude/{dirname}/' - run 'claudex init --force' to restore")

    # Check required files
    for filepath in REQUIRED_FILES:
        file = claude_dir / filepath
        if file.exists():
            passes.append(f"'.claude/{filepath}' exists")
        else:
            failures.append(f"Missing '.claude/{filepath}' - run 'claudex init --force' to restore")

    # Check CLAUDE.md at project root
    claude_md = path / "CLAUDE.md"
    if claude_md.exists():
        passes.append("'CLAUDE.md' exists at project root")
    else:
        failures.append(
            "Missing 'CLAUDE.md' at project root - run 'claudex init --force' to generate"
        )

    # Check .gitignore
    gitignore = path / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if ".claude/" in content:
            passes.append("'.gitignore' contains '.claude/'")
        else:
            failures.append(
                "'.gitignore' missing '.claude/' entry"
                " - add it manually or run 'claudex init --force'"
            )
    else:
        failures.append("No '.gitignore' file - create one with '.claude/' entry")

    # Check .mcp.json (warn only)
    mcp_json = path / ".mcp.json"
    if mcp_json.exists():
        passes.append("'.mcp.json' exists (MCP integration enabled)")
    else:
        passes.append("'.mcp.json' missing (optional - enables MCP integration)")

    return passes, failures
