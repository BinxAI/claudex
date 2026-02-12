# claudex v1.0 Implementation Plan

## Problem Statement

Current state: `main.py` is a 428-line file copier. It takes a preset name, does string replacement on `{{TEMPLATE_VARS}}`, and copies ~65 files into `.claude/`. The generated CLAUDE.md is generic boilerplate that doesn't reflect the actual project.

Target state: A pip-installable CLI that **reads the actual project** before generating config. One command, real output, ready to develop.

---

## What Needs to Change (Concrete)

### 1. Project Detection Engine

**File**: `claude_scaffold/detectors.py` (~200 lines)

Reads actual project files to determine:

```python
@dataclass
class ProjectProfile:
    name: str                          # from package.json/pyproject.toml/directory name
    description: str                   # from package.json description or pyproject.toml
    language: str                      # "python" | "typescript" | "javascript" | "mixed"
    framework: str | None              # "fastapi" | "django" | "flask" | "nextjs" | "react" | "express" | None
    package_manager: str | None        # "uv" | "poetry" | "pip" | "npm" | "pnpm" | "yarn" | None
    src_dirs: list[str]                # actual directories found (e.g. ["src/", "app/", "lib/"])
    test_dirs: list[str]               # actual test directories found
    has_docker: bool                   # docker-compose.yml or Dockerfile exists
    has_ci: bool                       # .github/workflows/ exists
    has_db: bool                       # alembic/ or migrations/ or prisma/ exists
    db_type: str | None                # "postgresql" | "sqlite" | "mysql" | None
    has_redis: bool
    entry_points: list[str]            # main files (main.py, app.py, index.ts, etc.)
    directory_tree: str                # actual tree output (depth 2)
    existing_claude_md: bool           # project already has CLAUDE.md
    existing_claude_dir: bool          # project already has .claude/
    git_initialized: bool
    monorepo: bool                     # multiple package.json or pyproject.toml
```

**Detection logic** (all file-based, no execution needed):

| What            | How                                                                                                                           |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Language        | Check for `pyproject.toml`, `setup.py`, `package.json`, `tsconfig.json`, `go.mod`, `Cargo.toml`                   |
| Framework       | Read dependency lists:`pyproject.toml [dependencies]`, `package.json dependencies`                                        |
| Package manager | `uv.lock` -> uv, `poetry.lock` -> poetry, `package-lock.json` -> npm, `pnpm-lock.yaml` -> pnpm, `yarn.lock` -> yarn |
| Source dirs     | Walk top-level dirs, match common patterns (`src/`, `app/`, `lib/`, `components/`, `pages/`)                        |
| Test dirs       | Walk for `tests/`, `test/`, `__tests__/`, `spec/`                                                                     |
| Docker          | Check `docker-compose.yml`, `Dockerfile`, `docker-compose.yaml`                                                         |
| CI              | Check `.github/workflows/`                                                                                                  |
| Database        | Check dependency lists for sqlalchemy/alembic/prisma/typeorm/django.db, check for `migrations/` dir                         |
| Redis           | Check dependency lists for redis/ioredis/bull                                                                                 |
| Entry points    | Check for `main.py`, `app.py`, `manage.py`, `index.ts`, `server.ts`, `index.js`                                   |
| Directory tree  | `os.walk()` with depth=2, skip `node_modules`, `__pycache__`, `.git`, `.venv`, `venv`                             |
| Monorepo        | Multiple `package.json` or `pyproject.toml` at different depths                                                           |

**Framework detection map**:

```python
PYTHON_FRAMEWORKS = {
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "starlette": "Starlette",
    "tornado": "Tornado",
}

JS_FRAMEWORKS = {
    "next": "Next.js",
    "react": "React",
    "vue": "Vue",
    "svelte": "Svelte",
    "express": "Express",
    "nestjs": "NestJS",
    "nuxt": "Nuxt",
}
```

---

### 2. CLAUDE.md Generator

**File**: `claude_scaffold/generator.py` (~250 lines)

Replaces the current template approach. Instead of `{{TEMPLATE_VARS}}`, builds CLAUDE.md from `ProjectProfile` data.

```python
def generate_claude_md(profile: ProjectProfile) -> str:
    """Build CLAUDE.md from actual project analysis."""
    sections = []
    sections.append(_header(profile))
    sections.append(_hard_constraints(profile))
    sections.append(_architecture(profile))        # uses actual directory_tree
    sections.append(_layer_rules(profile))          # from preset + detection
    sections.append(_development_workflow(profile))
    sections.append(_testing_strategy(profile))
    sections.append(_quick_start(profile))          # uses actual package_manager + entry_points
    return "\n\n---\n\n".join(sections)
```

**Key difference from current**: Every section uses real data.

Example - Quick Start for a detected FastAPI + uv project:

```markdown
## Quick Start

```bash
uv sync
docker-compose up -d
alembic upgrade head
uvicorn src.api.main:app --reload
```

```

Example - Quick Start for a detected Next.js + pnpm project:
```markdown
## Quick Start

```bash
pnpm install
pnpm dev
```

```

The generator builds these from `profile.package_manager`, `profile.has_docker`, `profile.has_db`, `profile.entry_points`.

---

### 3. CLI Restructure

**File**: `claude_scaffold/cli.py` (~150 lines)

Replace argparse in main.py with a proper CLI. Still zero external dependencies (argparse is stdlib).

```

claudex init [DIR]           # Detect + generate + copy templates
claudex init [DIR] --preset python-fastapi  # Use preset hints (override detection)
claudex update [DIR]         # Re-copy templates, preserve session/feedback
claudex validate [DIR]       # Check .claude/ health (missing files, stale hooks)
claudex info [DIR]           # Show detected project profile (dry-run detection)
claudex presets              # List available presets

```

**`init` flow**:
1. Run detection on DIR (default: cwd)
2. If preset given, merge preset data with detected data (detected wins on conflicts)
3. If no preset given, auto-select preset from detection (FastAPI detected -> python-fastapi preset)
4. Generate CLAUDE.md from profile
5. Copy template files (.claude/, .mcp.json)
6. Apply lint config from detection
7. Add .claude/ to .gitignore
8. Print summary of what was set up

**`validate` flow**:
1. Check .claude/ directory exists
2. Check all expected files present (hooks, commands, rules)
3. Check CLAUDE.md exists at project root
4. Check .gitignore includes .claude/
5. Check .mcp.json exists (warn if not)
6. Print pass/fail report

**`info` flow**:
1. Run detection only
2. Print ProjectProfile as formatted table
3. Show which preset would be auto-selected
4. Exit (no files written)

---

### 4. Package Structure

```

claudex/
├── pyproject.toml              # Package metadata, [project.scripts] entry point
├── README.md                   # Existing, update install instructions
├── LICENSE                     # MIT
├── claude_scaffold/            # Python package (rename from flat main.py)
│   ├── __init__.py             # Version only
│   ├── cli.py                  # CLI entry point + argument parsing
│   ├── detectors.py            # ProjectProfile detection
│   ├── generator.py            # CLAUDE.md generation from profile
│   ├── copier.py               # Template file copying (extracted from main.py)
│   ├── validator.py            # validate command logic
│   └── presets.py              # Preset loading (extracted from main.py)
├── templates/                  # Renamed from global/ + project/ split
│   ├── global/                 # ~/.claude/ files (same as current global/)
│   └── project/                # .claude/ files (same as current project/)
├── presets/                    # Same as current
│   ├── python-fastapi.yaml
│   ├── python-django.yaml
│   ├── nextjs.yaml
│   └── generic.yaml
└── tests/                      # Package tests
    ├── test_detectors.py
    ├── test_generator.py
    ├── test_copier.py
    └── fixtures/               # Fake project dirs for testing detection
        ├── fastapi_project/
        ├── nextjs_project/
        └── empty_project/

```

**pyproject.toml** (key parts):
```toml
[project]
name = "claudex"
version = "1.0.0"
description = "Set up Claude Code for any project in one command"
requires-python = ">=3.10"
dependencies = []  # Zero dependencies

[project.scripts]
claudex = "claude_scaffold.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["claude_scaffold"]

[tool.hatch.build]
include = [
    "claude_scaffold/",
    "templates/",
    "presets/",
]
```

**Install**: `pip install claudex` (or `pipx install claudex`)

After install, user runs: `claudex init .` from any project directory.

---

### 5. What Gets Copied vs Generated

| Item                  | Current                      | v1.0                                                        |
| --------------------- | ---------------------------- | ----------------------------------------------------------- |
| CLAUDE.md             | Template + string replace    | **Generated** from ProjectProfile                     |
| .claude/hooks/        | Copied as-is                 | Copied as-is (universal)                                    |
| .claude/commands/     | Copied as-is                 | Copied as-is (universal)                                    |
| .claude/rules/        | Copied as-is                 | Copied as-is (universal)                                    |
| .claude/session/      | Copied as-is                 | Copied as-is (universal)                                    |
| .claude/feedback/     | Copied as-is                 | Copied as-is (universal)                                    |
| .claude/knowledge/    | Copied as-is                 | Copied as-is (universal)                                    |
| .mcp.json             | Copied from template         | Copied as-is (universal)                                    |
| .claude/settings.json | Copied from template         | Copied as-is (universal)                                    |
| stop-lint-check.py    | Template + lint dir patching | **Patched** from detection (actual dirs + extensions) |

The hooks, commands, rules, session, and feedback files are framework-agnostic. They work the same whether the project is FastAPI or Next.js. The only project-specific outputs are:

1. **CLAUDE.md** - generated from real project analysis
2. **stop-lint-check.py** - patched with actual lint directories
3. **Preset selection** - auto-detected or user-specified

---

## Build Sequence (In Order)

### Step 1: Package restructure

- Create `claude_scaffold/` package directory
- Move `main.py` logic into `cli.py`, `copier.py`, `presets.py`
- Move `global/` and `project/` into `templates/`
- Create `pyproject.toml` with `[project.scripts]`
- Verify `pip install -e .` works and `claudex --help` runs

### Step 2: Detection engine

- Create `detectors.py` with `detect_project(path) -> ProjectProfile`
- Add detection for: language, framework, package_manager, src_dirs, test_dirs, directory_tree
- Add detection for: has_docker, has_ci, has_db, has_redis, entry_points
- Create `claudex info .` command to test detection output
- Write tests with fixture directories

### Step 3: CLAUDE.md generator

- Create `generator.py` with `generate_claude_md(profile) -> str`
- Replace template-based CLAUDE.md with generated one
- Wire into `init` command
- Write tests comparing output for different project profiles

### Step 4: Validate command

- Create `validator.py` with health checks
- Wire into `claudex validate .`
- Write tests

### Step 5: Polish + tests

- Auto-preset selection from detection
- Merge logic (preset hints + detected data)
- Update README with real install/usage instructions
- Full test suite
- Test on 3+ real projects

---

## What's NOT in v1.0 (Cut Explicitly)

| Feature                                                | Why Cut                                                          |
| ------------------------------------------------------ | ---------------------------------------------------------------- |
| Interactive prompts                                    | Adds complexity,`--preset` flag is sufficient                  |
| MCP auto-configuration                                 | Requires auth tokens, can't automate safely                      |
| Semantic code analysis                                 | AST parsing is framework-specific, file detection is 90% as good |
| `claudex upgrade` (migrate between versions) | Adds complexity,`update` is sufficient                         |
| Plugin system for custom presets                       | Presets in YAML are already extensible                           |
| Web UI / TUI                                           | CLI is the right interface for this tool                         |
| Auto-detection of coding style (tabs vs spaces, etc.)  | Linter config already handles this                               |

---

## Success Criteria

1. `pip install claudex` works on Python 3.10+
2. `claudex init .` on a FastAPI project produces a CLAUDE.md with actual directory structure, actual package manager commands, actual framework name
3. `claudex init .` on a Next.js project produces a different, correct CLAUDE.md
4. `claudex init .` on an empty directory produces a sensible generic config
5. `claudex validate .` catches missing files
6. `claudex info .` shows what was detected
7. Zero external dependencies
8. Works on Windows, macOS, Linux
9. Total package: <100KB installed

---

## Estimated Scope

| Step                       | Files Changed/Created      | Lines                 |
| -------------------------- | -------------------------- | --------------------- |
| 1. Package restructure     | 6 new, 1 deleted (main.py) | ~500 (mostly moved)   |
| 2. Detection engine        | 1 new + 1 test             | ~300                  |
| 3. CLAUDE.md generator     | 1 new + 1 test             | ~350                  |
| 4. Validate command        | 1 new + 1 test             | ~100                  |
| 5. Polish                  | README, preset tweaks      | ~100                  |
| **Total new code**   |                            | **~850 lines**  |
| **Total with tests** |                            | **~1200 lines** |
