"""Integration tests for claudex CLI via subprocess."""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    tmpdir = Path(tempfile.mkdtemp())
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def fastapi_project(temp_project):
    """Create a minimal FastAPI project structure."""
    (temp_project / "pyproject.toml").write_text("""
[project]
name = "test-project"
dependencies = ["fastapi"]
""")
    (temp_project / "src").mkdir()
    (temp_project / "src" / "main.py").write_text("from fastapi import FastAPI")
    return temp_project


def run_claudex(*args):
    """Run claudex CLI and return result."""
    result = subprocess.run(
        ["python", "-m", "claudex", *args],
        capture_output=True,
        text=True,
    )
    return result


class TestClaudexVersion:
    """Test version command."""

    def test_version_flag(self):
        result = run_claudex("--version")
        assert result.returncode == 0
        assert "claudex" in result.stdout
        assert "1." in result.stdout  # Version starts with 1.x

    def test_help_flag(self):
        result = run_claudex("--help")
        assert result.returncode == 0
        assert "claudex" in result.stdout
        assert "init" in result.stdout
        assert "info" in result.stdout


class TestClaudexInfo:
    """Test info command."""

    def test_info_on_fastapi_project(self, fastapi_project):
        result = run_claudex("info", str(fastapi_project))
        assert result.returncode == 0
        assert "Language:" in result.stdout
        assert "Framework:" in result.stdout or "FastAPI" in result.stdout

    def test_info_on_empty_directory(self, temp_project):
        result = run_claudex("info", str(temp_project))
        assert result.returncode == 0
        assert "unknown" in result.stdout or "generic" in result.stdout


class TestClaudexPresets:
    """Test presets command."""

    def test_lists_all_presets(self):
        result = run_claudex("presets")
        assert result.returncode == 0
        assert "python-fastapi" in result.stdout
        assert "python-django" in result.stdout
        assert "nextjs" in result.stdout
        assert "generic" in result.stdout


class TestClaudexInit:
    """Test init command."""

    def test_init_creates_claude_directory(self, temp_project):
        result = run_claudex("init", str(temp_project), "--yes")
        assert result.returncode == 0
        assert (temp_project / ".claude").exists()
        assert (temp_project / "CLAUDE.md").exists()

    def test_init_rejects_existing_claude_dir(self, temp_project):
        # First init
        run_claudex("init", str(temp_project), "--yes")

        # Second init without --force should fail
        result = run_claudex("init", str(temp_project), "--yes")
        assert result.returncode == 2
        assert "already exists" in result.stdout or "already exists" in result.stderr

    def test_init_with_force_overwrites(self, temp_project):
        # First init
        run_claudex("init", str(temp_project), "--yes")

        # Second init with --force should succeed
        result = run_claudex("init", str(temp_project), "--yes", "--force")
        assert result.returncode == 0


class TestClaudexValidate:
    """Test validate command."""

    def test_validate_passes_on_complete_setup(self, temp_project):
        # Initialize first
        run_claudex("init", str(temp_project), "--yes")

        # Then validate
        result = run_claudex("validate", str(temp_project))
        assert result.returncode == 0
        assert "PASS" in result.stdout

    def test_validate_fails_on_missing_claude_dir(self, temp_project):
        result = run_claudex("validate", str(temp_project))
        assert result.returncode == 1
        assert "FAIL" in result.stdout or "does not exist" in result.stdout
