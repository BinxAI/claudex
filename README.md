# claudex (binxai-claudex)

> **Set up Claude Code for any project in one command**

Python CLI that analyzes your project and installs a complete `.claude/` configuration:
project-specific CLAUDE.md, enforcement hooks, slash commands, and a full multi-agent layer.

[![CI](https://github.com/BinxAI/claudex/actions/workflows/ci.yml/badge.svg)](https://github.com/BinxAI/claudex/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/binxai-claudex.svg)](https://pypi.org/project/binxai-claudex/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Installation

```bash
pip install binxai-claudex
```

**Windows note**: If the `claudex` command isn't found after install, run `python -m claudex` or add your Python Scripts directory to PATH.

---

## Quick Start

```bash
# Standard setup (auto-detects stack)
claudex init /path/to/project --yes

# With multi-agent layer (orchestrator + 12 specialist agents)
claudex init /path/to/project --yes --multi-agent

# See what would be detected without making changes
claudex info /path/to/project

# Update templates without regenerating CLAUDE.md
claudex update /path/to/project

# Health check an existing .claude/ setup
claudex validate /path/to/project
```

---

## Why Multi-Agent?

Each context handoff between agents carries a ~5% degradation risk in quality and context fidelity.
Across a 10-agent pipeline: **0.95^10 = 60% effective throughput**.

ClaudeX's `--multi-agent` layer addresses this with a **structured Context Handoff Protocol** — a
machine-readable format that passes task state, decisions, file ownership, and done conditions
between agents. Every handoff is explicit, auditable, and zero-ambiguity.

---

## Features

### Smart Detection

Analyzes your project to detect:

- Language (Python, TypeScript, JavaScript)
- Framework (FastAPI, Django, Flask, Next.js, React, Vue)
- Package manager (uv, poetry, pip, npm, pnpm, yarn)
- Database (PostgreSQL, MySQL, MongoDB, SQLite)
- Infrastructure (Docker, CI, Git)

### Architecture Enforcement (Stack-Aware)

`claudex init` writes real layer enforcement rules into `pre-tool-use.py` based on your detected stack.

**Python / FastAPI:**

```python
LAYER_CONFIG = {
    "src/core/": ["sqlalchemy", "fastapi", "redis", "httpx"],  # no framework imports
    "src/db/":   [],                                            # can import core
    "src/api/":  [],                                            # can import core + db
}
SIBLING_BLOCKS = {
    "src/core/":   ["from src.db", "from src.api", "from src.worker"],
    "src/worker/": ["from src.api"],
}
```

**Next.js:**

```python
LAYER_CONFIG = {
    "src/lib/":        ["react"],           # lib must not import components
    "src/components/": ["next/server"],     # components must not use server APIs
}
```

Rules are enforced on every `Write`/`Edit` tool call — violations are blocked before they land.

### Generated CLAUDE.md

Uses **actual project data** (not generic templates):

- Real directory tree from your project
- Quick-start commands for your package manager
- Framework-specific testing strategies
- Layer rules tailored to your architecture

### Multi-Agent Layer (`--multi-agent`)

Installs a complete agent coordination system:

```text
.claude/agents/
  orchestrator.md          — routes tasks to the right specialist automatically
  implementers.yml         — role registry (source of truth)
  verifiers.yml            — verifier registry
  api-engineer.md          — compiled from registry
  database-engineer.md
  ui-designer.md
  testing-engineer.md
  devops-engineer.md
  security-engineer.md
  data-engineer.md
  docs-engineer.md
  architecture-verifier.md
  security-verifier.md
  quality-verifier.md
  test-verifier.md

.claude/commands/
  /orchestrate             — route any task to correct specialist, no manual selection
  /new-spec                — create a spec from a task description
  /create-spec             — turn a rough idea into a structured spec
  /implement-spec          — 5-phase: plan → handoff → implement → verify → close
  /context-handoff         — structured agent-to-agent context transfer
```

### Hooks (Installed Automatically)

| Hook | Trigger | Purpose |
| ---- | ------- | ------- |
| `pre-tool-use.py` | Before Write/Edit | Layer enforcement, file size limits |
| `post-tool-use.py` | After Write/Edit | Architecture rule audit |
| `session-start.py` | Session open | Load CURRENT_TASK.md, show parallel sessions |
| `session-end.py` | Session close | Harvest memory → MEMORY.md |
| `pre-compact.py` | Before compaction | Extract state → PRE_COMPACT_SNAPSHOT.md |
| `token-budget.py` | Before any tool | Track token spend → TOKEN_LOG.md |
| `stop-lint-check.py` | On /stop | Run lint + format before Claude exits |

### Auto-Preset Selection

| Detected Stack | Preset |
| -------------- | ------ |
| FastAPI + SQLAlchemy | `python-fastapi` |
| Django + DRF | `python-django` |
| Next.js + TypeScript | `nextjs` |
| Anything else | `generic` |

---

## Commands Reference

### `claudex init [DIR]`

Initialize `.claude/` for a project.

**Options:**

- `--preset <name>` — Override auto-detection
- `--yes` — Skip confirmation
- `--force` — Overwrite existing `.claude/`
- `--global` — Also install `~/.claude/` global config
- `--multi-agent` — Install orchestrator + 12 specialist agent files
- `--dry-run` — Preview without writing

**What it creates:**

```text
.claude/
  hooks/        — 7 Python hooks (enforcement + lifecycle)
  commands/     — 17+ slash commands (/dev, /audit, /parallel, ...)
  rules/        — Development guidelines (workflow, naming, testing)
  session/      — Task persistence (CURRENT_TASK.md, TASK_PROGRESS.md, TOKEN_LOG.md, ...)
  agents/       — [--multi-agent] orchestrator + 12 agent files + registries
  feedback/     — Violation tracking
  knowledge/    — 100x patterns reference
CLAUDE.md       — Generated from your actual project structure
.mcp.json       — MCP server config template
```

### `claudex update [DIR]`

Refresh templates without overwriting user files.

**Preserved on update:**

- `session/CURRENT_TASK.md`, `session/TASK_PROGRESS.md`, `session/TOKEN_LOG.md`
- `session/BACKGROUND_QUEUE.md`, `session/PARALLEL_SESSIONS.md`
- `feedback/*` — violations, lessons, corrections
- `knowledge/*` — user-added knowledge files
- `docs/*`

### `claudex validate [DIR]`

Health check the `.claude/` setup.

```text
✓ PASS: .claude/ directory exists
✓ PASS: All required directories present
✓ PASS: settings.json exists and hooks registered
✓ PASS: CLAUDE.md exists
✗ FAIL: .gitignore does not include .claude/
```

### `claudex info [DIR]`

Show detection results without making changes.

### `claudex presets`

List all available presets.

---

## 100x Developer Workflow

The scaffold implements the **100x Developer Framework** for maximum throughput.

### Background Agents (Night Queue)

```bash
/background-queue add "Add unit tests for user service"
/background-queue add "Fix lint warnings in api/ directory"
/night-kick              # generates headless launch commands
# copy-paste, agents run overnight
/background-queue review # check results next morning
```

### Parallel Sessions

```bash
/parallel plan "Sprint 5: Add real-time features"
# Creates PARALLEL_SESSIONS.md with file ownership and merge order

# Launch sessions in separate terminals
cd ../project-session-a && /dev start ...
cd ../project-session-b && /dev start ...

/parallel status         # check progress
/parallel merge-order    # get correct merge sequence
```

### Multi-Agent Spec Implementation

```bash
# Route any task automatically
/orchestrate "add a POST /users endpoint with email validation"

# Full spec lifecycle
/new-spec "user authentication with JWT"
/implement-spec docs/specs/user-auth.md
# → plans agent assignments
# → generates context handoff docs
# → delegates to implementers in order
# → runs verifiers (architecture, security, quality, tests)
# → produces final-verification.md
```

### Slash Commands

| Command | Purpose |
| ------- | ------- |
| `/dev start <task>` | Initialize task with session files |
| `/dev continue` | Resume after compaction |
| `/dev checkpoint` | Save progress |
| `/dev validate` | Run all validations |
| `/dev complete` | Complete with full QA |
| `/orchestrate <task>` | Auto-route to specialist agent |
| `/implement-spec <file>` | 5-phase multi-agent implementation |
| `/context-handoff` | Structured agent-to-agent handoff |
| `/audit` | Code quality + security audit |
| `/run-tests` | Execute test suite |
| `/validate-architecture` | Check layer placement |
| `/parallel` | Plan and manage parallel sessions |
| `/night-kick` | Launch background agent queue |
| `/expert-backend` | Senior backend specialist |
| `/expert-frontend` | Senior frontend specialist |
| `/expert-devops` | Senior DevOps specialist |
| `/expert-qa` | Senior QA specialist |

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint + format
ruff check claudex/ tests/
ruff format claudex/ tests/
```

---

## Requirements

- Python 3.11+
- `pyyaml>=6.0` (installed automatically)
- Git (for parallel session worktree support)

---

## Customization

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
layer_rules:
  - Core layer: pure business logic
quick_start: |
  npm install && npm run dev
```

### Modify Templates

Edit files in `claudex/templates/project/`:

- `hooks/` — customize Python hooks
- `commands/` — add slash commands
- `rules/` — modify development guidelines
- `agents/` — edit agent role definitions

---

## Roadmap

- [x] Publish to PyPI (`pip install binxai-claudex`)
- [x] Multi-agent layer (`--multi-agent` flag)
- [x] Agent file compilation (YAML registries → individual agent .md files)
- [x] Stack-aware LAYER_CONFIG (architecture enforcement on init)
- [ ] Add more presets (Flask, Express, Vue, Svelte)
- [ ] Preset inheritance (`extends:` in YAML)
- [ ] `preview` command (show what CLAUDE.md would look like)
- [ ] Monorepo support (detect sub-projects)

---

**Made for Claude Code** — Anthropic's official CLI for Claude.
