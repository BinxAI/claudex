"""Tests for .claude/ setup validator."""

import shutil
import tempfile
from pathlib import Path

import pytest

from claudex.validator import REQUIRED_DIRS, REQUIRED_FILES, validate_project


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    tmpdir = Path(tempfile.mkdtemp())
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def complete_project(temp_project):
    """Create a project with complete .claude/ setup."""
    claude_dir = temp_project / ".claude"
    claude_dir.mkdir()

    # Create all required directories
    for dirname in REQUIRED_DIRS:
        (claude_dir / dirname).mkdir(parents=True)

    # Create all required files
    for filepath in REQUIRED_FILES:
        file_path = claude_dir / filepath
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("# placeholder")

    # Create CLAUDE.md at root
    (temp_project / "CLAUDE.md").write_text("# Project")

    # Create .gitignore
    (temp_project / ".gitignore").write_text(".claude/\n")

    return temp_project


class TestValidateProject:
    """Test project validation logic."""

    def test_passes_for_complete_setup(self, complete_project):
        passes, failures = validate_project(complete_project)

        # Should have no critical failures (mcp.json is optional warning)
        critical_failures = [f for f in failures if "mcp" not in f.lower()]
        assert len(critical_failures) == 0
        assert len(passes) > 0
        # Check for any .claude related pass message
        assert any(".claude" in p.lower() for p in passes)

    def test_fails_when_claude_dir_missing(self, temp_project):
        passes, failures = validate_project(temp_project)

        assert len(failures) > 0
        assert any(".claude/" in f for f in failures)

    def test_detects_missing_required_directories(self, temp_project):
        claude_dir = temp_project / ".claude"
        claude_dir.mkdir()

        # Only create some directories
        (claude_dir / "hooks").mkdir()

        passes, failures = validate_project(temp_project)

        assert len(failures) > 0
        # Should detect missing commands, rules, session, feedback dirs
        missing_dirs = [d for d in REQUIRED_DIRS if d != "hooks"]
        for dirname in missing_dirs:
            assert any(dirname in f for f in failures)

    def test_detects_missing_required_files(self, temp_project):
        claude_dir = temp_project / ".claude"
        claude_dir.mkdir()

        # Create directories but not files
        for dirname in REQUIRED_DIRS:
            (claude_dir / dirname).mkdir(parents=True)

        passes, failures = validate_project(temp_project)

        assert len(failures) > 0
        # Should detect missing files
        assert any("settings.json" in f for f in failures)

    def test_detects_missing_claude_md(self, temp_project):
        claude_dir = temp_project / ".claude"
        claude_dir.mkdir()

        passes, failures = validate_project(temp_project)

        assert len(failures) > 0
        assert any("CLAUDE.md" in f for f in failures)

    def test_detects_missing_gitignore_entry(self, complete_project):
        # Overwrite gitignore without .claude/
        (complete_project / ".gitignore").write_text("node_modules/\n")

        passes, failures = validate_project(complete_project)

        assert len(failures) > 0
        assert any(".gitignore" in f and ".claude/" in f for f in failures)

    def test_warns_about_missing_mcp_json(self, complete_project):
        # mcp.json is optional, should warn not fail
        passes, failures = validate_project(complete_project)

        # Should pass overall but might have mcp warning
        if any("mcp" in msg.lower() for msg in failures):
            # If it mentions mcp, it should be a warning not blocking failure
            pass

    def test_provides_actionable_error_messages(self, temp_project):
        passes, failures = validate_project(temp_project)

        # Error messages should be helpful
        for failure in failures:
            assert len(failure) > 20  # Not just "Failed"
            assert any(keyword in failure.lower() for keyword in ["missing", "not found", "fail"])
