"""CLI entry point for claudex."""

import argparse
import sys
from pathlib import Path

from claudex import __version__
from claudex.copier import PRESETS_DIR


def _parse_simple_yaml_line(line: str) -> tuple[str, str] | None:
    """Parse a simple 'key: value' line from YAML."""
    if ":" not in line or line.strip().startswith("-"):
        return None

    key, _, value = line.partition(":")
    key = key.strip()
    value = value.strip()

    if value == "|":
        return None  # Multiline marker, not a simple value

    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]

    return (key, value)


def _finalize_multiline(multiline_value: list[str]) -> str:
    """Convert multiline list to final string value."""
    return "\n".join(multiline_value).rstrip()


def load_preset(preset_name: str) -> dict:
    """Load a preset YAML file (simple parser, no PyYAML dependency)."""
    preset_file = PRESETS_DIR / f"{preset_name}.yaml"
    if not preset_file.exists():
        available = [f.stem for f in PRESETS_DIR.glob("*.yaml")]
        print(f"Error: Preset '{preset_name}' not found.")
        print(f"Available: {', '.join(sorted(available))}")
        sys.exit(1)

    config: dict[str, str] = {}
    current_key: str | None = None
    multiline_value: list[str] = []
    in_multiline = False

    for line in preset_file.read_text(encoding="utf-8").splitlines():
        # Skip comments and empty lines (but preserve in multiline)
        if line.strip().startswith("#") or not line.strip():
            if in_multiline:
                multiline_value.append("")
            continue

        # Start of multiline block
        if ": |" in line and not line.strip().startswith("-"):
            current_key = line.split(":")[0].strip()
            in_multiline = True
            multiline_value = []
            continue

        # Inside multiline block
        if in_multiline:
            if line.startswith("  "):
                multiline_value.append(line[2:])
                continue
            else:
                # End multiline, save it
                if current_key is not None:
                    config[current_key] = _finalize_multiline(multiline_value)
                in_multiline = False

        # Simple key: value line
        parsed = _parse_simple_yaml_line(line)
        if parsed:
            key, value = parsed
            config[key] = value

    # Handle trailing multiline block
    if in_multiline and current_key is not None:
        config[current_key] = _finalize_multiline(multiline_value)

    return config


def list_presets() -> list[str]:
    """List available preset names."""
    return sorted(f.stem for f in PRESETS_DIR.glob("*.yaml"))


def _confirm_init(profile, target: Path) -> bool:
    """Prompt user for confirmation before initializing."""
    print(f"\n  Detected: {profile.language or 'unknown'}", end="")
    if profile.framework:
        print(f" + {profile.framework}", end="")
    if profile.package_manager:
        print(f" + {profile.package_manager}", end="")
    if profile.db_type:
        print(f" + {profile.db_type}", end="")
    print()
    print(f"  Preset:   {profile.preset_selected} (auto-detected)")
    print(f"  Target:   {target}")
    print()

    try:
        answer = input("  Proceed? [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled.")
        return False

    if answer and answer not in ("y", "yes"):
        print("  Cancelled.")
        return False

    return True


def _init_claude_md(target: Path, profile, preset_config: dict, dry_run: bool) -> None:
    """Generate and write CLAUDE.md file."""
    from claudex.generator import generate_claude_md

    claude_md_content = generate_claude_md(profile, preset_config)
    claude_md_path = target / "CLAUDE.md"

    if not dry_run:
        claude_md_path.write_text(claude_md_content, encoding="utf-8")
        print(f"  CREATE: CLAUDE.md ({len(claude_md_content)} bytes)")
    else:
        print(f"  CREATE: {claude_md_path}")


def _init_project_files(target: Path, profile, dry_run: bool) -> None:
    """Copy template files and configure project."""
    from claudex.copier import (
        PROJECT_TEMPLATE,
        copy_tree,
        ensure_gitignore,
        patch_lint_hook,
    )

    claude_dir = target / ".claude"

    # Copy template files
    if not dry_run:
        claude_dir.mkdir(exist_ok=True)
    copy_tree(PROJECT_TEMPLATE, claude_dir, dry_run=dry_run)

    # Copy .mcp.json to project root
    mcp_template = PROJECT_TEMPLATE / "mcp.json.template"
    mcp_dest = target / ".mcp.json"
    if mcp_template.exists() and not mcp_dest.exists():
        if not dry_run:
            content = mcp_template.read_text(encoding="utf-8")
            mcp_dest.write_text(content, encoding="utf-8")
            print("  CREATE: .mcp.json")
        else:
            print(f"  CREATE: {mcp_dest}")
    elif mcp_dest.exists():
        print("  SKIP (exists): .mcp.json")

    # Patch lint hook from detection
    if not dry_run:
        patch_lint_hook(claude_dir, profile)

    # Add .claude/ to .gitignore
    if not dry_run:
        ensure_gitignore(target)


def _init_multi_agent_files(target: Path, dry_run: bool) -> None:
    """Copy multi-agent templates and compile YAML registries into individual agent files."""
    from claudex.compiler import compile_implementer_agents, compile_verifier_agents
    from claudex.copier import PROJECT_TEMPLATE

    claude_dir = target / ".claude"
    agents_src = PROJECT_TEMPLATE / "agents"
    agents_dest = claude_dir / "agents"

    registry_files = [
        (agents_src / "orchestrator.md", agents_dest / "orchestrator.md"),
        (agents_src / "implementers.yml", agents_dest / "implementers.yml"),
        (agents_src / "verifiers.yml", agents_dest / "verifiers.yml"),
    ]
    spec_commands = ["new-spec.md", "implement-spec.md", "context-handoff.md", "orchestrate.md"]
    commands_src = PROJECT_TEMPLATE / "commands"
    commands_dest = claude_dir / "commands"

    if not dry_run:
        agents_dest.mkdir(exist_ok=True)

    # Copy registry files (orchestrator.md + YAML registries)
    for src, dest in registry_files:
        if src.exists():
            if not dry_run:
                dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  CREATE: .claude/agents/{dest.name}")

    # Compile YAML registries into individual agent .md files
    if not dry_run:
        implementer_files = compile_implementer_agents(agents_src / "implementers.yml", agents_dest)
        verifier_files = compile_verifier_agents(agents_src / "verifiers.yml", agents_dest)
        for fname in implementer_files + verifier_files:
            print(f"  CREATE: .claude/agents/{fname}")
    else:
        print("  CREATE: .claude/agents/[8 implementer agent files] (dry run)")
        print("  CREATE: .claude/agents/[4 verifier agent files] (dry run)")

    # Copy spec/orchestration commands
    for fname in spec_commands:
        src = commands_src / fname
        dest = commands_dest / fname
        if src.exists():
            if not dry_run:
                dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  CREATE: .claude/commands/{fname}")

    print("\n  Multi-agent layer installed:")
    print("    .claude/agents/orchestrator.md      — route tasks automatically")
    print("    .claude/agents/[8 implementers]     — api, db, ui, testing, devops, security, ...")
    print("    .claude/agents/[4 verifiers]        — architecture, security, quality, test")
    print("    /orchestrate, /new-spec, /implement-spec, /context-handoff commands\n")


def cmd_init(args: argparse.Namespace) -> int:
    """Handle the init subcommand."""
    from claudex.detectors import detect_project

    target = Path(args.directory).resolve()
    if not target.is_dir():
        print(f"Error: '{target}' is not a directory.")
        return 2

    # Check for existing .claude/
    claude_dir = target / ".claude"
    if claude_dir.exists() and not args.force:
        print(f"Error: '{claude_dir}' already exists.")
        print("Use --force to overwrite, or 'claudex update' to refresh templates.")
        return 2

    # Detect project and load preset
    profile = detect_project(target)
    if args.preset:
        profile.preset_selected = args.preset
    preset_config = load_preset(profile.preset_selected)

    # Confirmation
    if not args.yes:
        if not _confirm_init(profile, target):
            return 0

    print(f"\n=== Initializing .claude/ in {target} ===\n")

    # Generate CLAUDE.md
    _init_claude_md(target, profile, preset_config, args.dry_run)

    # Copy template files and configure
    _init_project_files(target, profile, args.dry_run)

    # Multi-agent layer (optional)
    if getattr(args, "multi_agent", False):
        _init_multi_agent_files(target, args.dry_run)

    # Global config
    if args.setup_global:
        from claudex.copier import setup_global

        setup_global(dry_run=args.dry_run)

    print(f"\n  Done! .claude/ configured with '{profile.preset_selected}' preset.")
    print("  Start a new Claude Code session to pick up the config.\n")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """Handle the update subcommand."""
    from claudex.copier import PROJECT_TEMPLATE, copy_tree

    target = Path(args.directory).resolve()
    claude_dir = target / ".claude"

    if not claude_dir.exists():
        print(f"Error: '{claude_dir}' does not exist.")
        print("Run 'claudex init' first.")
        return 2

    print(f"\n=== Updating .claude/ in {target} ===\n")
    copy_tree(PROJECT_TEMPLATE, claude_dir, dry_run=args.dry_run, update_mode=True)

    print("\n  Templates updated. Session/feedback files preserved.")
    print("  CLAUDE.md preserved. Run 'init --force' to regenerate.\n")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Handle the validate subcommand."""
    from claudex.validator import validate_project

    target = Path(args.directory).resolve()
    passes, failures = validate_project(target)

    print(f"\n=== Validate .claude/ in {target} ===\n")

    for msg in passes:
        print(f"  PASS: {msg}")
    for msg in failures:
        print(f"  FAIL: {msg}")

    total = len(passes) + len(failures)
    print(f"\n  {len(passes)}/{total} checks passed.\n")

    return 0 if not failures else 1


def cmd_info(args: argparse.Namespace) -> int:
    """Handle the info subcommand."""
    from claudex.detectors import detect_project

    target = Path(args.directory).resolve()
    if not target.is_dir():
        print(f"Error: '{target}' is not a directory.")
        return 2

    profile = detect_project(target)

    print(f"\n=== Project Info: {target} ===\n")
    print(f"  Name:            {profile.name or '(unknown)'}")
    print(f"  Language:        {profile.language or '(unknown)'}")
    print(f"  Framework:       {profile.framework or '(none detected)'}")
    print(f"  Package manager: {profile.package_manager or '(none detected)'}")
    print(f"  Python version:  {profile.python_version or '(n/a)'}")
    print(f"  Database:        {profile.db_type or '(none detected)'}")
    print(f"  Redis:           {'yes' if profile.has_redis else 'no'}")
    print(f"  Docker:          {'yes' if profile.has_docker else 'no'}")
    print(f"  CI:              {'yes' if profile.has_ci else 'no'}")
    print(f"  Git:             {'yes' if profile.git_initialized else 'no'}")
    print(f"  Linter:          {profile.existing_linter or '(none detected)'}")
    print(f"  Existing .claude/: {'yes' if profile.existing_claude_dir else 'no'}")
    print(f"  Existing CLAUDE.md: {'yes' if profile.existing_claude_md else 'no'}")
    print(f"  Preset:          {profile.preset_selected}")

    if profile.src_dirs:
        print(f"  Source dirs:     {', '.join(profile.src_dirs)}")
    if profile.test_dirs:
        print(f"  Test dirs:       {', '.join(profile.test_dirs)}")
    if profile.entry_points:
        print(f"  Entry points:    {', '.join(profile.entry_points)}")

    if profile.directory_tree:
        print("\n  Directory tree:\n")
        for line in profile.directory_tree.splitlines():
            # Handle Windows console encoding
            try:
                print(f"    {line}")
            except UnicodeEncodeError:
                print(f"    {line.encode('ascii', 'replace').decode('ascii')}")

    print()
    return 0


def cmd_presets(_args: argparse.Namespace) -> int:
    """Handle the presets subcommand."""
    print("\nAvailable presets:\n")
    for name in list_presets():
        config = load_preset(name)
        desc = config.get("description", "No description")
        print(f"  {name:20s} - {desc}")
    print()
    return 0


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="claudex",
        description="Set up Claude Code for any project in one command",
    )
    parser.add_argument("--version", action="version", version=f"claudex {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    p_init = subparsers.add_parser("init", help="Initialize .claude/ in a project")
    p_init.add_argument("directory", nargs="?", default=".", help="Project directory (default: .)")
    p_init.add_argument("--preset", type=str, default=None, help="Override auto-detected preset")
    p_init.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing .claude/")
    p_init.add_argument(
        "--global", dest="setup_global", action="store_true", help="Also install ~/.claude/"
    )
    p_init.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    p_init.add_argument(
        "--multi-agent",
        action="store_true",
        help="Also install multi-agent templates (orchestrator, role registry, spec commands)",
    )

    # update
    p_update = subparsers.add_parser(
        "update", help="Update .claude/ templates (preserve user files)"
    )
    p_update.add_argument(
        "directory", nargs="?", default=".", help="Project directory (default: .)"
    )
    p_update.add_argument("--dry-run", action="store_true", help="Preview without writing files")

    # validate
    p_validate = subparsers.add_parser("validate", help="Check .claude/ setup health")
    p_validate.add_argument(
        "directory", nargs="?", default=".", help="Project directory (default: .)"
    )

    # info
    p_info = subparsers.add_parser("info", help="Show detected project profile (no writes)")
    p_info.add_argument("directory", nargs="?", default=".", help="Project directory (default: .)")

    # presets
    subparsers.add_parser("presets", help="List available presets")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "init": cmd_init,
        "update": cmd_update,
        "validate": cmd_validate,
        "info": cmd_info,
        "presets": cmd_presets,
    }

    handler = commands.get(args.command)
    if handler:
        sys.exit(handler(args))
    else:
        parser.print_help()
        sys.exit(0)
