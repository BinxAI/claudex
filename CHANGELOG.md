# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] — v1.1.0

### Added

- Stack-aware LAYER_CONFIG patching: `claudex init` writes enforced layer rules
  into `pre-tool-use.py` based on detected stack (python-fastapi, python-django, nextjs, generic)
- `claudex/layer_configs.py`: per-stack LAYER_CONFIG + SIBLING_BLOCKS presets

### Changed

- README.md: updated badges, PyPI install instructions, multi-agent documentation, roadmap

---

## [1.0.0] — 2026-02-21

### Added

- `claudex init --multi-agent`: installs orchestrator + 12 compiled agent files
- `claudex/compiler.py`: compiles `implementers.yml` + `verifiers.yml` YAML registries
  into individual agent `.md` files (8 implementers + 4 verifiers)
- Agent templates: `api-engineer`, `database-engineer`, `ui-designer`, `testing-engineer`,
  `devops-engineer`, `security-engineer`, `data-engineer`, `docs-engineer`
- Verifier templates: `architecture-verifier`, `security-verifier`, `quality-verifier`, `test-verifier`
- Multi-agent commands: `/orchestrate`, `/new-spec`, `/create-spec`, `/implement-spec`, `/context-handoff`
- Session hook upgrades: `session-end.py` harvests memory → MEMORY.md on every session exit
- Session hook upgrades: `pre-compact.py` extracts state → PRE_COMPACT_SNAPSHOT.md before compaction
- `token-budget.py` hook: tracks cumulative token spend, warns at 80%, blocks at 100%
- `TOKEN_LOG.md` session template for token budget tracking
- Full CI/CD pipeline: lint + test matrix (Python 3.11/3.12 × ubuntu/windows/macos) + CodeQL + PyPI OIDC release
- PyPI publication as `binxai-claudex` via OIDC Trusted Publisher (zero secrets)
- `pyyaml>=6.0` runtime dependency for YAML registry compilation

### Changed

- `claudex/copier.py`: `PRESERVE_ON_UPDATE` includes `session/TOKEN_LOG.md`
- `claudex/cli.py`: `_init_multi_agent_files()` now calls compiler to generate agent files

### Fixed

- Pre-existing E501/E741 lint errors across 7 source files
- Missing `tests/fixtures/empty_project/` directory (caused all 6 CI matrix jobs to fail)
- `copier.py`: `root_dst` was not passed through recursive calls (broke `update_mode` path matching)

---

## [0.1.0] — 2026-02-14

### Added

- Initial release: `claudex init`, `claudex update`, `claudex validate`, `claudex info`, `claudex presets`
- Project detection: language, framework, package manager, database, infrastructure
- Preset system: `python-fastapi`, `python-django`, `nextjs`, `generic`
- CLAUDE.md generation from actual project structure
- Hook templates: `pre-tool-use.py`, `post-tool-use.py`, `session-start.py`,
  `session-end.py`, `pre-compact.py`, `stop-lint-check.py`
- Slash command templates: `/dev`, `/audit`, `/parallel`, `/background-queue`,
  `/night-kick`, `/expert-*`, and more
- `claudex update`: preserves user session files, feedback logs, knowledge base
- `claudex validate`: health check with pass/fail reporting
- Path traversal protection in `copy_tree()`
- `.gitignore` auto-update to exclude `.claude/`
- Global config support via `claudex init --global`
