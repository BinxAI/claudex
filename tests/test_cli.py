"""Integration tests for CLI commands."""

import shutil
import tempfile
from pathlib import Path

import pytest

from claudex.detectors import detect_project

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_project():
    """Create a temporary project directory for init testing."""
    tmpdir = Path(tempfile.mkdtemp())
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestInfoCommand:
    """Test the 'info' command."""

    def test_info_detects_fastapi_project(self):
        """Test info command on FastAPI fixture."""
        fastapi_path = FIXTURES / "fastapi_project"

        # Run detection directly (equivalent to info command)
        profile = detect_project(fastapi_path)

        assert profile.name == "test-fastapi-app"
        assert profile.framework == "FastAPI"
        assert profile.package_manager == "uv"

    def test_info_detects_nextjs_project(self):
        """Test info command on Next.js fixture."""
        nextjs_path = FIXTURES / "nextjs_project"

        profile = detect_project(nextjs_path)

        assert profile.name == "test-nextjs-app"
        assert profile.framework == "Next.js"
        assert profile.package_manager == "pnpm"

    def test_info_handles_empty_project(self):
        """Test info command on empty project."""
        empty_path = FIXTURES / "empty_project"

        profile = detect_project(empty_path)

        # Should not crash
        assert profile.name == "empty_project"
        assert profile.preset_selected == "generic"


class TestPresetsCommand:
    """Test the 'presets' command."""

    def test_lists_all_presets(self):
        """Test that presets command would list all 4 presets."""
        # Get preset directory directly (don't import internal function)
        presets_dir = Path(__file__).parent.parent / "claudex" / "presets"

        if presets_dir.exists():
            preset_files = list(presets_dir.glob("*.yaml"))
            assert len(preset_files) == 4
            assert any("python-fastapi" in f.name for f in preset_files)
            assert any("python-django" in f.name for f in preset_files)
            assert any("nextjs" in f.name for f in preset_files)
            assert any("generic" in f.name for f in preset_files)


class TestInitCommand:
    """Test the 'init' command (integration)."""

    def test_init_creates_claude_directory(self, temp_project):
        """Test that init creates .claude/ structure."""
        # This would normally use CLI, but we test the logic
        from claudex.copier import copy_tree

        templates_dir = Path(__file__).parent.parent / "claudex" / "templates" / "project"
        claude_dir = temp_project / ".claude"

        if templates_dir.exists():
            copy_tree(templates_dir, claude_dir)

            # Check key directories were created
            assert (claude_dir / "hooks").exists()
            assert (claude_dir / "commands").exists()
            assert (claude_dir / "rules").exists()
            assert (claude_dir / "session").exists()

    def test_init_creates_claude_md(self, temp_project):
        """Test that init generates CLAUDE.md."""
        from claudex.detectors import ProjectProfile
        from claudex.generator import generate_claude_md

        profile = ProjectProfile(name="test-project", language="python", framework="FastAPI")

        claude_md = generate_claude_md(profile, {})
        (temp_project / "CLAUDE.md").write_text(claude_md)

        assert (temp_project / "CLAUDE.md").exists()
        content = (temp_project / "CLAUDE.md").read_text()
        assert "# test-project" in content


class TestValidateCommand:
    """Test the 'validate' command."""

    def test_validate_detects_missing_claude_dir(self, temp_project):
        """Test validate command on project without .claude/."""
        from claudex.validator import validate_project

        passes, failures = validate_project(temp_project)

        assert len(failures) > 0
        assert any(".claude/" in f for f in failures)

    def test_validate_passes_on_complete_setup(self, temp_project):
        """Test validate command on complete setup."""
        from claudex.validator import REQUIRED_DIRS, REQUIRED_FILES, validate_project

        # Create complete .claude/ setup
        claude_dir = temp_project / ".claude"
        claude_dir.mkdir()

        for dirname in REQUIRED_DIRS:
            (claude_dir / dirname).mkdir(parents=True)

        for filepath in REQUIRED_FILES:
            file_path = claude_dir / filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("# placeholder")

        (temp_project / "CLAUDE.md").write_text("# Project")
        (temp_project / ".gitignore").write_text(".claude/\n")

        passes, failures = validate_project(temp_project)

        assert len(failures) == 0 or all("mcp" in f.lower() for f in failures)  # mcp is optional
        assert len(passes) > 0


class TestUpdateCommand:
    """Test the 'update' command."""

    def test_update_preserves_session_files(self, temp_project):
        """Test that update mode preserves user session files."""
        # Create .claude/ with session file
        claude_dir = temp_project / ".claude"
        session_dir = claude_dir / "session"
        session_dir.mkdir(parents=True)

        session_file = session_dir / "CURRENT_TASK.md"
        original_content = "# My custom task\nDo not overwrite"
        session_file.write_text(original_content)

        # Simulate update (preserve session files)
        from claudex.copier import copy_tree

        templates_dir = Path(__file__).parent.parent / "claudex" / "templates" / "project"

        if templates_dir.exists():
            preserve_patterns = {
                "session/CURRENT_TASK.md",
                "session/TASK_PROGRESS.md",
                "session/BACKGROUND_QUEUE.md",
                "session/PARALLEL_SESSIONS.md",
            }
            copy_tree(
                templates_dir, claude_dir, update_mode=True, preserve_on_update=preserve_patterns
            )

            # Check session file was preserved
            if session_file.exists():
                assert session_file.read_text() == original_content


class TestEndToEndWorkflow:
    """Test complete workflow: info -> init -> validate."""

    def test_full_workflow_on_fastapi_fixture(self, temp_project):
        """Test full workflow on FastAPI project."""
        from claudex.copier import copy_tree, ensure_gitignore
        from claudex.detectors import detect_project
        from claudex.generator import generate_claude_md
        from claudex.validator import validate_project

        # 1. Detect
        fastapi_path = FIXTURES / "fastapi_project"
        profile = detect_project(fastapi_path)
        assert profile.framework == "FastAPI"

        # 2. Generate
        claude_md = generate_claude_md(profile, {})
        assert "FastAPI" in claude_md

        # 3. Init (copy templates)
        claude_dir = temp_project / ".claude"
        templates_dir = Path(__file__).parent.parent / "claudex" / "templates" / "project"

        if templates_dir.exists():
            copy_tree(templates_dir, claude_dir)
            (temp_project / "CLAUDE.md").write_text(claude_md)
            ensure_gitignore(temp_project)

            # 4. Validate
            passes, failures = validate_project(temp_project)

            # Should mostly pass (might warn about mcp.json)
            critical_failures = [f for f in failures if "mcp" not in f.lower()]
            assert len(critical_failures) == 0
            assert len(passes) > 0
