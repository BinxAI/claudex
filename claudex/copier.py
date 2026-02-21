"""File copying and template operations for claudex."""

import shutil
import sys
from pathlib import Path

from claudex import ProjectProfile

# Package data directory
PACKAGE_DIR = Path(__file__).parent.resolve()
GLOBAL_TEMPLATE = PACKAGE_DIR / "templates" / "global"
PROJECT_TEMPLATE = PACKAGE_DIR / "templates" / "project"
PRESETS_DIR = PACKAGE_DIR / "presets"

# Files preserved during --update (never overwritten)
PRESERVE_ON_UPDATE = {
    "session/CURRENT_TASK.md",
    "session/TASK_PROGRESS.md",
    "session/VALIDATION_STATE.md",
    "session/CONTEXT_SUMMARY.md",
    "session/BACKGROUND_QUEUE.md",
    "session/PARALLEL_SESSIONS.md",
    "session/TOKEN_LOG.md",
    "feedback/VIOLATIONS_LOG.md",
    "feedback/LESSONS_LEARNED_INDEX.md",
    "feedback/PATTERN_CORRECTIONS.md",
    "feedback/IMPROVEMENT_PROPOSALS.md",
    "knowledge/",
    "docs/",
}


def copy_tree(
    src: Path,
    dst: Path,
    dry_run: bool = False,
    update_mode: bool = False,
    skip_patterns: set = None,
    preserve_on_update: set = None,
    _root_dst: Path = None,
) -> None:
    """Copy directory tree from templates to destination."""
    skip_patterns = skip_patterns or set()
    preserve_on_update = preserve_on_update or PRESERVE_ON_UPDATE
    root_dst = _root_dst if _root_dst is not None else dst

    for item in sorted(src.iterdir()):
        dest_path = dst / item.relative_to(src)

        # Skip if matches skip patterns
        if item.name in skip_patterns or str(item.relative_to(src)) in skip_patterns:
            continue

        # Strip .template suffix from filenames
        if dest_path.name.endswith(".template"):
            dest_path = dest_path.with_name(dest_path.name.replace(".template", ""))

        # Path traversal protection
        if not dest_path.resolve().is_relative_to(root_dst.resolve()):
            print(f"  ERROR: Path traversal blocked: {dest_path}")
            sys.exit(1)

        if item.is_dir():
            if item.name == "__pycache__":
                continue
            if not dry_run:
                dest_path.mkdir(parents=True, exist_ok=True)
            else:
                print(f"  mkdir {dest_path}")
            copy_tree(
                item, dest_path, dry_run, update_mode, skip_patterns, preserve_on_update, root_dst
            )

        elif item.is_file():
            # In update mode, preserve user-modified files.
            # Use root_dst (not dst) so that paths like "session/CURRENT_TASK.md"
            # match correctly in recursive calls where dst is already "session/".
            if update_mode:
                rel = str(dest_path.relative_to(root_dst)).replace("\\", "/")
                if any(rel.startswith(p.rstrip("/")) for p in preserve_on_update):
                    if dest_path.exists():
                        print(f"  SKIP (preserved): {dest_path.name}")
                        continue

            if dry_run:
                action = "UPDATE" if dest_path.exists() else "CREATE"
                print(f"  {action}: {dest_path}")
                continue

            try:
                content = item.read_text(encoding="utf-8")
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_text(content, encoding="utf-8")
            except UnicodeDecodeError:
                shutil.copy2(item, dest_path)


def patch_lint_hook(claude_dir: Path, profile: ProjectProfile) -> None:
    """Patch stop-lint-check.py with detected lint dirs/extensions."""
    lint_hook = claude_dir / "hooks" / "stop-lint-check.py"
    if not lint_hook.exists():
        return

    content = lint_hook.read_text(encoding="utf-8")

    dirs: list[str] = profile.src_dirs + profile.test_dirs or ["src/", "tests/"]
    # Ensure trailing slashes
    dirs = [d if d.endswith("/") else d + "/" for d in dirs]

    exts: list[str]
    if profile.language == "python":
        exts = [".py"]
    elif profile.language in ("typescript", "javascript"):
        exts = [".ts", ".tsx", ".js", ".jsx"]
    elif profile.language == "mixed":
        exts = [".py", ".ts", ".tsx", ".js", ".jsx"]
    else:
        exts = [".py"]

    content = content.replace('LINT_DIRS = ["src/", "tests/"]', f"LINT_DIRS = {dirs!r}")
    content = content.replace('LINT_EXTENSIONS = [".py"]', f"LINT_EXTENSIONS = {exts!r}")
    lint_hook.write_text(content, encoding="utf-8")


def patch_lint_hook_from_preset(claude_dir: Path, preset_config: dict) -> None:
    """Patch stop-lint-check.py from preset config (legacy support)."""
    lint_hook = claude_dir / "hooks" / "stop-lint-check.py"
    if not lint_hook.exists():
        return

    content = lint_hook.read_text(encoding="utf-8")

    lint_dirs_str = preset_config.get("lint_dirs", "")
    if lint_dirs_str and isinstance(lint_dirs_str, str):
        dirs = [
            line.strip().lstrip("- ").strip('"').strip("'")
            for line in lint_dirs_str.strip().splitlines()
            if line.strip().startswith("-")
        ]
        if dirs:
            content = content.replace('LINT_DIRS = ["src/", "tests/"]', f"LINT_DIRS = {dirs!r}")

    lint_ext_str = preset_config.get("lint_extensions", "")
    if lint_ext_str and isinstance(lint_ext_str, str):
        exts = [
            line.strip().lstrip("- ").strip('"').strip("'")
            for line in lint_ext_str.strip().splitlines()
            if line.strip().startswith("-")
        ]
        if exts:
            content = content.replace('LINT_EXTENSIONS = [".py"]', f"LINT_EXTENSIONS = {exts!r}")

    lint_hook.write_text(content, encoding="utf-8")


def ensure_gitignore(project_dir: Path) -> None:
    """Add .claude/ to .gitignore if not already present."""
    gitignore = project_dir / ".gitignore"
    existing = ""
    if gitignore.exists():
        existing = gitignore.read_text(encoding="utf-8")

    if ".claude/" not in existing:
        with open(gitignore, "a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("\n# Claude Code config\n.claude/\n")


def setup_global(dry_run: bool = False) -> None:
    """Install global ~/.claude/ configuration."""
    home = Path.home()
    claude_dir = home / ".claude"

    print("\n=== Setting up global ~/.claude/ config ===\n")

    if not dry_run:
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "rules").mkdir(exist_ok=True)

    copy_tree(GLOBAL_TEMPLATE, claude_dir, dry_run)

    settings_file = claude_dir / "settings.json"
    if settings_file.exists() and not dry_run:
        print("  NOTE: ~/.claude/settings.json already exists.")
        print("  Template saved to ~/.claude/settings.json.new")
        print("  Merge manually if needed.")
        dest = claude_dir / "settings.json.new"
        content = (GLOBAL_TEMPLATE / "settings.json").read_text(encoding="utf-8")
        dest.write_text(content, encoding="utf-8")

    print("\n  Global config installed.")
    print("  Files: ~/.claude/CLAUDE.md, settings.json, rules/\n")
