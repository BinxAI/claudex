"""Project detection engine for claudex.

Analyzes existing projects to build a ProjectProfile without user input.
"""

import json
import tomllib
from pathlib import Path

from claudex import ProjectProfile

# Framework detection maps
PYTHON_FRAMEWORKS = {
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "starlette": "Starlette",
}

JS_FRAMEWORKS = {
    "next": "Next.js",
    "react": "React",
    "vue": "Vue",
    "express": "Express",
    "nuxt": "Nuxt",
    "svelte": "Svelte",
}

DB_INDICATORS = {
    "postgresql": ["sqlalchemy", "psycopg2", "asyncpg", "prisma", "django"],
    "mysql": ["mysqlclient", "pymysql"],
    "mongodb": ["pymongo", "motor", "mongoengine"],
    "sqlite": [],  # Default if ORM detected but no specific driver
}

LOCK_FILE_MAP = {
    "uv.lock": "uv",
    "poetry.lock": "poetry",
    "package-lock.json": "npm",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
}

FRAMEWORK_TO_PRESET = {
    "FastAPI": "python-fastapi",
    "Django": "python-django",
    "Flask": "python-fastapi",  # Closest match
    "Starlette": "python-fastapi",  # Closest match
    "Next.js": "nextjs",
    "React": "nextjs",  # Closest match
    "Vue": "generic",
    "Express": "generic",
}

SKIP_DIRS = {
    "node_modules",
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".tox",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    "htmlcov",
}

COMMON_SRC_NAMES = {
    "src",
    "app",
    "lib",
    "api",
    "core",
    "components",
    "pages",
    "hooks",
    "backend",
    "frontend",
    "server",
    "client",
}


def detect_project(path: Path) -> ProjectProfile:
    """Analyze project directory and return detected profile."""
    profile = ProjectProfile()

    _detect_name(path, profile)
    _detect_language(path, profile)
    _detect_python_deps(path, profile)
    _detect_js_deps(path, profile)
    _detect_package_manager(path, profile)
    _detect_python_version(path, profile)
    _detect_directories(path, profile)
    _detect_infrastructure(path, profile)
    _detect_entry_points(path, profile)
    _detect_existing_setup(path, profile)

    # Auto-select preset
    if profile.framework and profile.framework in FRAMEWORK_TO_PRESET:
        profile.preset_selected = FRAMEWORK_TO_PRESET[profile.framework]
    else:
        profile.preset_selected = "generic"

    return profile


def _detect_name(path: Path, profile: ProjectProfile) -> None:
    """Detect project name and description."""
    # Try pyproject.toml first
    pyproject_data = _read_pyproject(path)
    if pyproject_data:
        project_section = pyproject_data.get("project", {})
        profile.name = project_section.get("name", "")
        profile.description = project_section.get("description", "")

    # Try package.json
    if not profile.name:
        package_json = path / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text(encoding="utf-8"))
                profile.name = data.get("name", "")
                profile.description = data.get("description", "")
            except Exception:
                pass

    # Fallback to directory name
    if not profile.name:
        profile.name = path.name


def _detect_language(path: Path, profile: ProjectProfile) -> None:
    """Detect primary language."""
    has_pyproject = (path / "pyproject.toml").exists()
    has_package_json = (path / "package.json").exists()
    has_tsconfig = (path / "tsconfig.json").exists()

    if has_pyproject and has_package_json:
        profile.language = "mixed"
    elif has_pyproject:
        profile.language = "python"
    elif has_tsconfig:
        profile.language = "typescript"
    elif has_package_json:
        profile.language = "javascript"
    else:
        # Fallback: count files
        py_count = len(list(path.rglob("*.py")))
        ts_count = len(list(path.rglob("*.ts"))) + len(list(path.rglob("*.tsx")))
        js_count = len(list(path.rglob("*.js"))) + len(list(path.rglob("*.jsx")))

        if py_count > ts_count + js_count:
            profile.language = "python"
        elif ts_count > 0:
            profile.language = "typescript"
        elif js_count > 0:
            profile.language = "javascript"


def _detect_python_deps(path: Path, profile: ProjectProfile) -> None:
    """Detect Python dependencies and infer framework/database."""
    pyproject_data = _read_pyproject(path)
    if not pyproject_data:
        return

    # Collect all dependencies
    deps = set()

    project_deps = pyproject_data.get("project", {}).get("dependencies", [])
    if isinstance(project_deps, list):
        deps.update(dep.split("[")[0].split(">=")[0].split("==")[0].lower() for dep in project_deps)

    poetry_deps = pyproject_data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    if isinstance(poetry_deps, dict):
        deps.update(dep.lower() for dep in poetry_deps.keys() if dep != "python")

    # Detect framework
    for key, fw_name in PYTHON_FRAMEWORKS.items():
        if key in deps:
            profile.framework = fw_name
            break

    # Detect database
    for db_type, indicators in DB_INDICATORS.items():
        if any(ind in deps for ind in indicators):
            profile.has_db = True
            profile.db_type = db_type
            break

    # Detect Redis
    if "redis" in deps or "aioredis" in deps:
        profile.has_redis = True


def _detect_js_deps(path: Path, profile: ProjectProfile) -> None:
    """Detect JS/TS dependencies."""
    package_json = path / "package.json"
    if not package_json.exists():
        return

    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
        deps = set((data.get("dependencies", {}) or {}).keys())

        # Detect framework
        for key, fw_name in JS_FRAMEWORKS.items():
            if key in deps:
                profile.framework = fw_name
                break

        # Detect database (JS ORMs)
        if "pg" in deps or "postgres" in deps:
            profile.has_db = True
            profile.db_type = "postgresql"
        elif "mysql" in deps or "mysql2" in deps:
            profile.has_db = True
            profile.db_type = "mysql"
        elif "mongodb" in deps or "mongoose" in deps:
            profile.has_db = True
            profile.db_type = "mongodb"
        elif "prisma" in deps or "@prisma/client" in deps:
            profile.has_db = True

        # Detect Redis
        if "redis" in deps or "ioredis" in deps:
            profile.has_redis = True

    except Exception:
        pass


def _detect_package_manager(path: Path, profile: ProjectProfile) -> None:
    """Detect package manager by lock file recency."""
    lock_files = {}
    for lock_file, pm in LOCK_FILE_MAP.items():
        lock_path = path / lock_file
        if lock_path.exists():
            lock_files[pm] = lock_path.stat().st_mtime

    if lock_files:
        # Pick most recently modified
        profile.package_manager = max(lock_files, key=lock_files.get)  # type: ignore
    else:
        # Fallback detection
        pyproject_data = _read_pyproject(path)
        if pyproject_data and "tool" in pyproject_data and "poetry" in pyproject_data["tool"]:
            profile.package_manager = "poetry"
        elif (path / "pyproject.toml").exists():
            profile.package_manager = "pip"
        elif (path / "package.json").exists():
            profile.package_manager = "npm"


def _detect_python_version(path: Path, profile: ProjectProfile) -> None:
    """Detect Python version requirement."""
    pyproject_data = _read_pyproject(path)
    if pyproject_data:
        requires_python = pyproject_data.get("project", {}).get("requires-python", "")
        if requires_python:
            profile.python_version = requires_python


def _detect_directories(path: Path, profile: ProjectProfile) -> None:
    """Detect source and test directories, generate tree."""
    src_dirs = []
    test_dirs = []

    # Scan top-level directories
    try:
        for item in path.iterdir():
            if not item.is_dir() or item.name in SKIP_DIRS or item.name.startswith("."):
                continue

            if item.name in COMMON_SRC_NAMES:
                # Verify it contains files of the detected language
                if _contains_source_files(item, profile.language):
                    src_dirs.append(item.name)
            elif item.name in ("tests", "test"):
                test_dirs.append(item.name)

    except PermissionError:
        pass

    profile.src_dirs = src_dirs
    profile.test_dirs = test_dirs

    # Generate directory tree
    profile.directory_tree = _generate_tree(path)


def _contains_source_files(directory: Path, language: str) -> bool:
    """Check if directory contains files of specified language."""
    if language == "python":
        return any(directory.rglob("*.py"))
    elif language in ("typescript", "javascript", "mixed"):
        return any(
            directory.rglob("*.ts")
            or directory.rglob("*.tsx")
            or directory.rglob("*.js")
            or directory.rglob("*.jsx")
        )
    return True  # Unknown language, assume yes


def _generate_tree(path: Path, max_depth: int = 2) -> str:
    """Generate ASCII directory tree (depth 2)."""
    lines = [path.name + "/"]

    def walk(current: Path, prefix: str = "", depth: int = 0) -> None:
        if depth >= max_depth:
            return

        try:
            items = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        except PermissionError:
            return

        for item in items:
            if item.name in SKIP_DIRS or item.name.startswith("."):
                continue

            if item.is_dir():
                lines.append(f"{prefix}  {item.name}/")
                walk(item, prefix + "  ", depth + 1)

    walk(path)
    return "\n".join(lines)


def _detect_infrastructure(path: Path, profile: ProjectProfile) -> None:
    """Detect infrastructure files."""
    profile.has_docker = (path / "Dockerfile").exists() or (path / "docker-compose.yml").exists()
    profile.has_ci = (path / ".github" / "workflows").exists() or (path / ".gitlab-ci.yml").exists()
    profile.git_initialized = (path / ".git").exists()


def _detect_entry_points(path: Path, profile: ProjectProfile) -> None:
    """Detect entry point files."""
    entry_points = []

    candidates = [
        "main.py",
        "app.py",
        "manage.py",
        "index.ts",
        "index.js",
        "server.ts",
        "server.js",
    ]

    for candidate in candidates:
        if (path / candidate).exists():
            entry_points.append(candidate)

    for src_dir in profile.src_dirs:
        src_path = path / src_dir
        for candidate in candidates:
            if (src_path / candidate).exists():
                entry_points.append(f"{src_dir}/{candidate}")

    profile.entry_points = entry_points


def _detect_existing_setup(path: Path, profile: ProjectProfile) -> None:
    """Detect existing .claude/ setup and linter."""
    profile.existing_claude_dir = (path / ".claude").exists()
    profile.existing_claude_md = (path / "CLAUDE.md").exists()

    # Detect linter
    if (path / "ruff.toml").exists() or (path / "pyproject.toml").exists():
        pyproject_data = _read_pyproject(path)
        if pyproject_data and "tool" in pyproject_data and "ruff" in pyproject_data["tool"]:
            profile.existing_linter = "ruff"
    if (path / ".eslintrc.json").exists() or (path / ".eslintrc.js").exists():
        profile.existing_linter = "eslint"
    elif (path / "biome.json").exists():
        profile.existing_linter = "biome"


def _read_pyproject(path: Path) -> dict:
    """Read pyproject.toml using tomllib (stdlib 3.11+)."""
    pyproject = path / "pyproject.toml"
    if not pyproject.exists():
        return {}
    try:
        return tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except Exception:
        return {}  # Malformed TOML -> skip, don't crash
