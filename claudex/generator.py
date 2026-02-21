"""CLAUDE.md generator for claudex.

Generates project-specific CLAUDE.md from detected ProjectProfile + preset config.
"""

from claudex import ProjectProfile


def generate_claude_md(profile: ProjectProfile, preset_config: dict) -> str:
    """Build CLAUDE.md from actual project analysis + preset layer rules."""
    sections = [
        _section_header(profile),
        _section_constraints(profile),
        _section_architecture(profile, preset_config),
        _section_layer_rules(profile, preset_config),
        _section_workflow(),
        _section_testing(profile),
        _section_quick_start(profile, preset_config),
    ]
    return "\n\n---\n\n".join(s for s in sections if s)


def _section_header(profile: ProjectProfile) -> str:
    """Generate header with project name and description."""
    lines = [f"# {profile.name}"]

    if profile.description:
        lines.append("")
        lines.append("## Project Overview")
        lines.append("")
        lines.append(profile.description)

    return "\n".join(lines)


def _section_constraints(profile: ProjectProfile) -> str:
    """Generate hard constraints section."""
    lines = [
        "## Hard Constraints (Non-negotiable)",
        "",
    ]

    # Always include these
    constraints = [
        "**Never commit** - `.claude/`, `.env`, `.env.*`, `*.pem`, `*.key`, `*.token`,"
        " `credentials.json`, `secrets.yaml`",
        "**Always commit tests** - Test files in `tests/` must be committed for CI",
        "**Clean git history** - No AI tool names, no Co-Authored-By AI lines in commits/PRs",
    ]

    # Add rule versioning if DB detected
    if profile.has_db:
        constraints.insert(
            1,
            "**Rule versioning** - All business rules versioned,"
            " evaluations reference rule_version_id",
        )

    for i, constraint in enumerate(constraints, 1):
        lines.append(f"{i}. {constraint}")

    return "\n".join(lines)


def _section_architecture(profile: ProjectProfile, preset_config: dict) -> str:
    """Generate architecture section with actual directory tree."""
    lines = [
        "## Architecture",
        "",
        "### Repository Structure",
        "",
        "```",
    ]

    # Use actual directory tree from detection
    if profile.directory_tree:
        lines.append(profile.directory_tree)
    else:
        # Fallback to preset architecture tree
        preset_tree = preset_config.get("architecture_tree", "")
        if preset_tree:
            lines.append(preset_tree)
        else:
            lines.append(f"{profile.name}/")
            if profile.src_dirs:
                for src in profile.src_dirs:
                    lines.append(f"  {src}/")
            if profile.test_dirs:
                for test in profile.test_dirs:
                    lines.append(f"  {test}/")

    lines.append("```")
    lines.append("")

    # Layer responsibilities from preset or generate
    lines.append("### Layer Responsibilities")
    lines.append("")

    layer_desc = preset_config.get("layer_description", "")
    if layer_desc:
        lines.append(layer_desc)
    elif profile.src_dirs:
        # Generate generic description
        lines.append("Project follows standard layered architecture:")
        lines.append("")
        for src in profile.src_dirs:
            lines.append(f"- `{src}/` - Application source code")
        if profile.test_dirs:
            for test in profile.test_dirs:
                lines.append(f"- `{test}/` - Test suites")

    return "\n".join(lines)


def _section_layer_rules(profile: ProjectProfile, preset_config: dict) -> str:
    """Generate layer rules from preset (if defined)."""
    layer_rules = preset_config.get("layer_rules", "")
    if not layer_rules:
        return ""

    lines = [
        "## Layer Rules",
        "",
        layer_rules,
    ]
    return "\n".join(lines)


def _section_workflow() -> str:
    """Generate workflow section (static)."""
    return """## Development Workflow

Follow the standard development workflow in `.claude/rules/development/DEVELOPMENT_WORKFLOW.md`:

1. Use `/dev start <task>` to initialize
2. Follow TDD approach for core modules
3. Run `/validate-architecture` before implementation
4. Run `/run-tests` before completion
5. Use `/dev complete` for final QA"""


def _section_testing(profile: ProjectProfile) -> str:
    """Generate testing strategy section."""
    lines = [
        "## Testing Strategy",
        "",
    ]

    if profile.language == "python":
        lines.extend(
            [
                "| Layer | Test Type | Coverage Target |",
                "|-------|-----------|-----------------|",
                "| Core/Domain | Unit tests | 95% |",
                "| Application | Unit + Integration | 80% |",
                "| Infrastructure | Integration | 70% |",
                "| E2E | Full pipeline | Critical paths |",
            ]
        )
    elif profile.language in ("typescript", "javascript"):
        lines.extend(
            [
                "| Layer | Test Type | Coverage Target |",
                "|-------|-----------|-----------------|",
                "| Components | Unit tests | 90% |",
                "| Hooks/Utils | Unit tests | 90% |",
                "| Integration | API tests | 80% |",
                "| E2E | Full workflows | Critical paths |",
            ]
        )
    else:
        lines.append("Write tests for all business logic with appropriate coverage targets.")

    return "\n".join(lines)


def _section_quick_start(profile: ProjectProfile, preset_config: dict) -> str:
    """Generate quick start commands from profile data."""
    lines = [
        "## Quick Start",
        "",
        "```bash",
    ]

    commands = _build_quick_start_commands(profile)

    if commands:
        lines.extend(commands)
    else:
        # Fallback to preset
        preset_quickstart = preset_config.get("quick_start", "")
        if preset_quickstart:
            lines.append(preset_quickstart)
        else:
            lines.append("# No quick start commands detected")

    lines.append("```")
    return "\n".join(lines)


def _build_quick_start_commands(profile: ProjectProfile) -> list[str]:
    """Build quick start command list from profile."""
    commands = []
    pm = profile.package_manager

    # Install deps
    if pm == "uv":
        commands.append("uv sync")
    elif pm == "poetry":
        commands.append("poetry install")
    elif pm == "pip":
        commands.append("pip install -r requirements.txt")
    elif pm == "npm":
        commands.append("npm install")
    elif pm == "pnpm":
        commands.append("pnpm install")
    elif pm == "yarn":
        commands.append("yarn install")

    # Docker
    if profile.has_docker:
        commands.append("")
        commands.append("# Start services")
        commands.append("docker-compose up -d")

    # DB migrations
    if profile.has_db and profile.language == "python":
        commands.append("")
        commands.append("# Run migrations")
        if profile.framework == "Django":
            commands.append("python manage.py migrate")
        elif any("alembic" in ep for ep in profile.entry_points):
            commands.append("alembic upgrade head")

    # Dev server
    dev_command = _build_dev_server_command(profile)
    if dev_command:
        commands.append("")
        commands.append("# Start dev server")
        commands.append(dev_command)

    return commands


def _build_dev_server_command(profile: ProjectProfile) -> str:
    """Build development server command."""
    # Check entry points
    for ep in profile.entry_points:
        if ep == "manage.py":
            return "python manage.py runserver"
        elif "main.py" in ep or "app.py" in ep:
            if profile.framework == "FastAPI":
                module = ep.replace("/", ".").replace(".py", "")
                return f"uvicorn {module}:app --reload"
            elif profile.framework == "Flask":
                return "flask run"

    # Fallback for JS/TS
    if profile.language in ("typescript", "javascript"):
        pm = profile.package_manager or "npm"
        return f"{pm} run dev"

    return ""
