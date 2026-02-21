"""Tests for project detection engine."""

from pathlib import Path

from claudex.detectors import (
    ProjectProfile,
    _detect_directories,
    _detect_js_deps,
    _detect_language,
    _detect_package_manager,
    _detect_python_deps,
    detect_project,
)

# Fixture paths
FIXTURES = Path(__file__).parent / "fixtures"
FASTAPI_PROJECT = FIXTURES / "fastapi_project"
NEXTJS_PROJECT = FIXTURES / "nextjs_project"
DJANGO_PROJECT = FIXTURES / "django_project"
EMPTY_PROJECT = FIXTURES / "empty_project"


class TestDetectLanguage:
    """Test language detection."""

    def test_detects_python_from_pyproject(self):
        profile = ProjectProfile()
        _detect_language(FASTAPI_PROJECT, profile)
        assert profile.language == "python"

    def test_detects_typescript_from_package_json_and_tsx(self):
        profile = ProjectProfile()
        _detect_language(NEXTJS_PROJECT, profile)
        assert profile.language in ("typescript", "javascript")

    def test_detects_python_for_django(self):
        profile = ProjectProfile()
        _detect_language(DJANGO_PROJECT, profile)
        assert profile.language == "python"

    def test_returns_empty_for_empty_project(self):
        profile = ProjectProfile()
        _detect_language(EMPTY_PROJECT, profile)
        assert profile.language == ""


class TestDetectPythonDeps:
    """Test Python dependency detection."""

    def test_detects_fastapi_framework(self):
        profile = ProjectProfile()
        _detect_python_deps(FASTAPI_PROJECT, profile)
        assert profile.framework == "FastAPI"

    def test_detects_postgresql_database(self):
        profile = ProjectProfile()
        _detect_python_deps(FASTAPI_PROJECT, profile)
        assert profile.has_db is True
        assert profile.db_type == "postgresql"

    def test_detects_django_framework(self):
        profile = ProjectProfile()
        _detect_python_deps(DJANGO_PROJECT, profile)
        assert profile.framework == "Django"

    def test_handles_missing_pyproject(self):
        profile = ProjectProfile()
        _detect_python_deps(EMPTY_PROJECT, profile)
        assert profile.framework is None
        assert profile.has_db is False


class TestDetectJsDeps:
    """Test JavaScript dependency detection."""

    def test_detects_nextjs_framework(self):
        profile = ProjectProfile()
        _detect_js_deps(NEXTJS_PROJECT, profile)
        assert profile.framework == "Next.js"

    def test_detects_prisma_database(self):
        profile = ProjectProfile()
        _detect_js_deps(NEXTJS_PROJECT, profile)
        assert profile.has_db is True

    def test_handles_missing_package_json(self):
        profile = ProjectProfile()
        _detect_js_deps(EMPTY_PROJECT, profile)
        assert profile.framework is None


class TestDetectPackageManager:
    """Test package manager detection."""

    def test_detects_uv_from_lock_file(self):
        profile = ProjectProfile()
        _detect_package_manager(FASTAPI_PROJECT, profile)
        assert profile.package_manager == "uv"

    def test_detects_pnpm_from_lock_file(self):
        profile = ProjectProfile()
        _detect_package_manager(NEXTJS_PROJECT, profile)
        assert profile.package_manager == "pnpm"

    def test_returns_none_for_no_lock_files(self):
        profile = ProjectProfile()
        _detect_package_manager(EMPTY_PROJECT, profile)
        assert profile.package_manager is None


class TestDetectDirectories:
    """Test directory detection."""

    def test_detects_src_directory(self):
        profile = ProjectProfile(language="python")
        _detect_directories(FASTAPI_PROJECT, profile)
        assert "src" in profile.src_dirs or any("src" in d for d in profile.src_dirs)

    def test_detects_app_directory_for_nextjs(self):
        profile = ProjectProfile(language="typescript")
        _detect_directories(NEXTJS_PROJECT, profile)
        # Directory detection should find app/ or include it in tree
        assert (
            "app" in profile.src_dirs
            or any("app" in d for d in profile.src_dirs)
            or "app" in profile.directory_tree
        )

    def test_generates_directory_tree(self):
        profile = ProjectProfile(language="python")
        _detect_directories(FASTAPI_PROJECT, profile)
        assert profile.directory_tree != ""
        assert "src" in profile.directory_tree or "main.py" in profile.directory_tree


class TestDetectProjectIntegration:
    """Integration tests for full project detection."""

    def test_detects_fastapi_project_completely(self):
        profile = detect_project(FASTAPI_PROJECT)

        assert profile.name == "test-fastapi-app"
        assert profile.language == "python"
        assert profile.framework == "FastAPI"
        assert profile.package_manager == "uv"
        assert profile.python_version == ">=3.11"
        assert profile.has_db is True
        assert profile.db_type == "postgresql"
        assert profile.preset_selected == "python-fastapi"

    def test_detects_nextjs_project_completely(self):
        profile = detect_project(NEXTJS_PROJECT)

        assert profile.name == "test-nextjs-app"
        assert profile.language in ("typescript", "javascript")
        assert profile.framework == "Next.js"
        assert profile.package_manager == "pnpm"
        assert profile.has_db is True  # Prisma
        assert profile.preset_selected == "nextjs"

    def test_detects_django_project(self):
        profile = detect_project(DJANGO_PROJECT)

        assert profile.name == "test-django-app"
        assert profile.language == "python"
        assert profile.framework == "Django"
        assert profile.has_db is True
        assert profile.db_type == "postgresql"
        assert profile.preset_selected == "python-django"
        assert "manage.py" in profile.entry_points

    def test_handles_empty_project_gracefully(self):
        profile = detect_project(EMPTY_PROJECT)

        # Should return minimal profile without errors
        assert profile.name == "empty_project"
        assert profile.preset_selected == "generic"
