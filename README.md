# Claudex

> **Set up Claude Code for any project in one command**

Zero-dependency Python CLI that analyzes your project and generates a complete `.claude/` configuration with project-specific CLAUDE.md, hooks, commands, and development workflows.

[![Tests](https://github.com/Binx808/claudex/actions/workflows/test.yml/badge.svg)](https://github.com/Binx808/claudex/actions/workflows/test.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Features

✨ **Smart Detection** - Analyzes your project (pyproject.toml, package.json, directory structure) to detect:
- Language (Python, TypeScript, JavaScript)
- Framework (FastAPI, Django, Flask, Next.js, React, Vue)
- Package manager (uv, poetry, pip, npm, pnpm, yarn)
- Database (PostgreSQL, MySQL, MongoDB, SQLite)
- Infrastructure (Docker, CI, Git)

📝 **Generated CLAUDE.md** - Uses **actual project data** (not templates):
- Real directory tree from your project
- Quick start commands for your package manager
- Framework-specific testing strategies
- Layer rules tailored to your architecture

🎯 **Auto-Preset Selection** - Detects your stack and chooses the best preset:
- `python-fastapi` for FastAPI projects
- `python-django` for Django projects
- `nextjs` for Next.js projects
- `generic` fallback for everything else

🔒 **Security Built-In** - Path traversal protection, never commits secrets

---

## Installation

```bash
# Install from source (for now)
cd /path/to/claudex
pip install -e .

# Or build and install wheel
python -m build
pip install dist/claudex-1.0.0-*.whl
```

**Coming soon**: `pip install claudex` (PyPI)

**Windows Note**: If `pip install` completes but the `claudex` command isn't found, you have three options:
1. Use `python -m claudex` instead of `claudex` for all commands
2. Use the provided `claudex.bat` wrapper script
3. Add your Python Scripts directory to PATH

---

## Quick Start

```bash
# Initialize a new project
claudex init /path/to/project --yes

# See what would be detected first
claudex info /path/to/project

# Update an existing .claude/ setup (preserves user files)
claudex update /path/to/project

# Validate your .claude/ setup
claudex validate /path/to/project

# List available presets
claudex presets
```

---

## Commands

### `claudex init [DIR]`

Initialize .claude/ configuration for a project.

**Options**:
- `--preset <name>` - Override auto-detection (python-fastapi, python-django, nextjs, generic)
- `--yes` - Skip confirmation prompt
- `--force` - Overwrite existing .claude/
- `--global` - Also install ~/.claude/ global config

**Example**:
```bash
# Auto-detect and initialize
cd my-fastapi-project
claudex init . --yes

# Override preset
claudex init /path/to/django-app --preset python-django

# Full setup: global + project
claudex init . --yes --global
```

**What it creates**:
- `.claude/` directory with:
  - `hooks/` - 6 Python hooks (pre/post-tool-use, session lifecycle)
  - `commands/` - 17 slash commands (`/dev`, `/audit`, `/parallel`, etc.)
  - `rules/` - Development guidelines (workflow, naming, testing)
  - `session/` - Task persistence files
  - `feedback/` - Violation tracking
  - `knowledge/` - 100x patterns reference
- `CLAUDE.md` - Generated from your actual project structure
- `.mcp.json` - MCP server config template
- Updates `.gitignore` to include `.claude/`

---

### `claudex update [DIR]`

Update existing .claude/ files without regenerating CLAUDE.md.

**Preserves**:
- `session/CURRENT_TASK.md`
- `session/TASK_PROGRESS.md`
- `session/BACKGROUND_QUEUE.md`
- `session/PARALLEL_SESSIONS.md`
- `feedback/*` (violations, lessons, corrections)
- `knowledge/*` (user-added knowledge files)
- `docs/*`

**Example**:
```bash
claudex update .
```

---

### `claudex validate [DIR]`

Health check your .claude/ setup.

**Checks**:
- `.claude/` directory exists
- Required subdirectories present (hooks, commands, rules, session, feedback)
- Required files present (settings.json, all hook scripts)
- `CLAUDE.md` exists at project root
- `.gitignore` includes `.claude/`
- `.mcp.json` exists (warns if missing)

**Example**:
```bash
claudex validate /path/to/project
```

**Output**:
```
✓ PASS: .claude/ directory exists
✓ PASS: All required directories present
✗ FAIL: Missing .claude/hooks/session-start.py
✓ PASS: CLAUDE.md exists
✗ FAIL: .gitignore does not include .claude/

Validation failed. Run 'claudex init --force' to restore.
```

---

### `claudex info [DIR]`

Show detection results without making changes.

**Example**:
```bash
claudex info /path/to/fastapi-project
```

**Output**:
```
Project: my-fastapi-app
Language: python
Framework: FastAPI
Package manager: uv
Python version: >=3.11
Database: postgresql
Redis: yes
Docker: yes
CI: yes
Auto-selected preset: python-fastapi

Directory tree:
  my-fastapi-app/
    src/
      api/
      core/
      db/
    tests/
      unit/
      integration/
    client/
```

---

### `claudex presets`

List all available presets with descriptions.

**Example**:
```bash
claudex presets
```

**Output**:
```
Available presets:

python-fastapi - Python + FastAPI + SQLAlchemy + PostgreSQL
python-django  - Python + Django + DRF + PostgreSQL
nextjs         - Next.js + TypeScript + Tailwind + TanStack Query
generic        - Minimal setup for any project
```

---

## Presets

Each preset provides tailored configuration for specific stacks:

### `python-fastapi`
- **Stack**: Python + FastAPI + SQLAlchemy + PostgreSQL
- **Architecture**: Domain/Application/Agents/Infrastructure layers
- **Quick start**: `uv sync`, `docker-compose up -d`, `uvicorn app:app --reload`
- **Testing**: pytest with 95% domain coverage target

### `python-django`
- **Stack**: Python + Django + Django REST Framework + PostgreSQL
- **Architecture**: Django apps with clean separation
- **Quick start**: `poetry install`, `python manage.py migrate`, `python manage.py runserver`
- **Testing**: Django test framework

### `nextjs`
- **Stack**: Next.js + TypeScript + Tailwind CSS + TanStack Query
- **Architecture**: App router with components/hooks/lib
- **Quick start**: `pnpm install`, `pnpm dev`
- **Testing**: Vitest + React Testing Library

### `generic`
- **Stack**: Any language/framework
- **Architecture**: Minimal recommendations
- **Quick start**: Auto-detected or manual
- **Testing**: Standard coverage targets

---

## After Setup

### 1. Configure MCP (Optional)

Edit `.mcp.json` to connect Claude Code to GitHub:

```bash
# Get your GitHub token
gh auth token

# Paste into .mcp.json "args" for github server
```

### 2. Start Claude Code

```bash
cd /path/to/project
# Claude Code will auto-load .claude/ configuration
```

### 3. Begin Development

```bash
# Start your first task
/dev start "implement user authentication"

# Continue after break
/dev continue

# Complete when done
/dev complete
```

---

## 100x Developer Workflow

The scaffold implements the **100x Developer Framework** for maximum throughput:

### Background Agents (Night Queue)

Accumulate tasks during deep work, execute overnight:

```bash
/background-queue add "Add unit tests for user service"
/background-queue add "Fix lint warnings in api/ directory"
/background-queue add "Update docstrings in core modules"
/night-kick                 # Generates headless launch commands
# Copy-paste commands, agents run overnight
/background-queue review    # Check results next morning
```

### Parallel Sessions

Split large features across multiple Claude Code sessions:

```bash
/parallel plan "Sprint 5: Add real-time features"
# Creates PARALLEL_SESSIONS.md with:
# - Session table (file ownership, no overlaps)
# - Merge order (dependency-aware)
# - Worktree creation commands

# Launch sessions in separate terminals
cd ../project-session-a && /dev start ...
cd ../project-session-b && /dev start ...

/parallel status         # Check progress
/parallel merge-order    # Get correct merge sequence
/parallel cleanup        # Remove completed worktrees
```

### AI Code Review

Automatically runs on every PR:

```yaml
# .github/workflows/claude-code-review.yml (created by scaffold)
- Project-specific review rules
- Architecture compliance checks
- Tag @claude in any PR comment for on-demand review
```

---

## Slash Commands Reference

| Command | Purpose |
|---------|---------|
| `/dev start <task>` | Initialize new task with session files |
| `/dev continue` | Resume from session files after compaction |
| `/dev checkpoint` | Save progress to disk |
| `/dev validate` | Run all validations |
| `/dev complete` | Complete task with full QA |
| `/audit` | Code quality and security audit |
| `/run-tests` | Execute test suite with reporting |
| `/validate-architecture` | Check layer placement and dependencies |
| `/validate-consistency` | Cross-layer schema/type/enum check |
| `/background-queue` | Manage background agent task queue |
| `/night-kick` | Launch queued background agents |
| `/parallel` | Plan and manage parallel sessions |
| `/report-violation` | Log and track workflow violations |
| `/improve-workflow` | Analyze feedback and propose improvements |
| `/expert-*` | Consult specialized subagents |

---

## Customization

### Modify Detection Logic

Edit `claudex/detectors.py`:
- `PYTHON_FRAMEWORKS` - Add new Python frameworks
- `JS_FRAMEWORKS` - Add new JavaScript frameworks
- `DB_INDICATORS` - Add database detection patterns

### Add New Presets

Create `claudex/presets/your-preset.yaml`:

```yaml
name: your-stack
description: Your custom stack description
architecture_tree: |
  project/
    src/
    tests/
layer_description: |
  - **src/**: Application code
  - **tests/**: Test suite
layer_rules:
  - Domain layer: Pure business logic
  - Application layer: Use cases
quick_start: |
  npm install
  npm run dev
```

### Modify Templates

Edit files in `claudex/templates/project/`:
- `hooks/` - Customize Python hooks
- `commands/` - Add new slash commands
- `rules/` - Modify development guidelines

---

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e .
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_detectors.py -v

# Run with coverage
pytest tests/ --cov=claudex --cov-report=html
```

### Running CI Locally

```bash
# Lint
ruff check claudex/ tests/

# Format check
ruff format claudex/ tests/ --check

# Auto-fix
ruff check claudex/ tests/ --fix
ruff format claudex/ tests/
```

---

## Troubleshooting

### Issue: Detection fails on Windows

**Symptom**: Unicode errors when printing directory tree

**Fix**: Unicode encoding is handled internally with fallback to ASCII. If you still see errors, set:
```bash
set PYTHONIOENCODING=utf-8
```

### Issue: Templates not found after pip install

**Symptom**: `FileNotFoundError: templates/project/`

**Fix**: Templates are inside the package. If using editable install (`pip install -e .`), ensure you're in the repo directory. For normal install, templates resolve via `__file__`.

### Issue: Can't detect my framework

**Symptom**: Auto-selects `generic` preset when it should detect FastAPI/Django/Next.js

**Fix**: Check your dependencies:
- **Python**: Must be in `pyproject.toml` `[project.dependencies]` or `[tool.poetry.dependencies]`
- **JavaScript**: Must be in `package.json` `dependencies` (not `devDependencies`)

### Issue: CLAUDE.md not project-specific

**Symptom**: Generated CLAUDE.md has generic architecture tree

**Fix**: Detection couldn't find source directories. Ensure:
- Python: `src/` or `app/` directory with `.py` files
- JavaScript: `src/` or `app/` directory with `.ts`/`.tsx`/`.js` files

---

## Requirements

- Python 3.11+ (for `tomllib` stdlib)
- No external dependencies (stdlib only)
- Git (for worktree support in parallel sessions)

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Submit a pull request

---

## Roadmap

- [ ] Publish to PyPI
- [ ] Add more presets (Flask, Express, Vue, Svelte)
- [ ] Preset inheritance (`extends:` in YAML)
- [ ] Detection confidence scores
- [ ] `preview` command (show what would be generated)
- [ ] Monorepo support (detect sub-projects)

---

**Made for Claude Code** - Anthropic's official CLI for Claude
