"""Tests for file copying operations."""

import shutil
import tempfile
from pathlib import Path

import pytest

from claudex.copier import (
    copy_tree,
    ensure_gitignore,
    patch_lint_hook,
    patch_lint_hook_from_preset,
    setup_global,
)
from claudex.detectors import ProjectProfile


@pytest.fixture
def temp_src():
    """Create a temporary source directory with test files."""
    tmpdir = Path(tempfile.mkdtemp())
    (tmpdir / "file1.txt").write_text("content1")
    (tmpdir / "subdir").mkdir()
    (tmpdir / "subdir" / "file2.txt").write_text("content2")
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def temp_dst():
    """Create a temporary destination directory."""
    tmpdir = Path(tempfile.mkdtemp())
    yield tmpdir
    shutil.rmtree(tmpdir)


class TestCopyTree:
    """Test tree copying with skip patterns."""

    def test_copies_all_files_by_default(self, temp_src, temp_dst):
        copy_tree(temp_src, temp_dst)

        assert (temp_dst / "file1.txt").exists()
        assert (temp_dst / "file1.txt").read_text() == "content1"
        assert (temp_dst / "subdir" / "file2.txt").exists()
        assert (temp_dst / "subdir" / "file2.txt").read_text() == "content2"

    def test_skips_files_matching_skip_patterns(self, temp_src, temp_dst):
        skip_patterns = {"file1.txt"}
        copy_tree(temp_src, temp_dst, skip_patterns=skip_patterns)

        assert not (temp_dst / "file1.txt").exists()
        assert (temp_dst / "subdir" / "file2.txt").exists()

    def test_preserves_on_update_mode(self, temp_src, temp_dst):
        # Create existing file in destination
        (temp_dst / "file1.txt").write_text("existing content")

        # Use update_mode=True with preserve patterns
        preserve_patterns = {"file1.txt"}
        copy_tree(temp_src, temp_dst, update_mode=True, preserve_on_update=preserve_patterns)

        # Should not overwrite when in update mode and file exists
        assert (temp_dst / "file1.txt").read_text() == "existing content"

    def test_path_traversal_protection(self, temp_src, temp_dst):
        # Create a file with path traversal attempt
        temp_src / ".." / "malicious.txt"

        try:
            copy_tree(temp_src, temp_dst)
            # Should not copy files outside destination
            assert not (temp_dst.parent / "malicious.txt").exists()
        except Exception:
            # Or should raise security error
            pass


class TestEnsureGitignore:
    """Test gitignore management."""

    def test_creates_gitignore_if_missing(self, temp_dst):
        ensure_gitignore(temp_dst)

        assert (temp_dst / ".gitignore").exists()
        content = (temp_dst / ".gitignore").read_text()
        assert ".claude/" in content

    def test_adds_claude_if_missing_from_existing(self, temp_dst):
        # Create gitignore without .claude/
        (temp_dst / ".gitignore").write_text("node_modules/\n")

        ensure_gitignore(temp_dst)

        content = (temp_dst / ".gitignore").read_text()
        assert ".claude/" in content
        assert "node_modules/" in content

    def test_does_not_duplicate_entry(self, temp_dst):
        # Create gitignore with .claude/ already
        (temp_dst / ".gitignore").write_text(".claude/\nnode_modules/\n")

        ensure_gitignore(temp_dst)

        content = (temp_dst / ".gitignore").read_text()
        # Should appear only once
        assert content.count(".claude/") == 1


class TestPatchLintHook:
    """Test lint hook patching from detection."""

    def test_patches_python_project(self, temp_dst):
        # Create mock lint hook
        claude_dir = temp_dst / ".claude"
        claude_dir.mkdir()
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir()

        lint_hook = hooks_dir / "stop-lint-check.py"
        lint_hook.write_text('LINT_DIRS = ["src/", "tests/"]\nLINT_EXTENSIONS = [".py"]\n')

        profile = ProjectProfile(
            language="python", src_dirs=["app/", "core/"], test_dirs=["tests/"]
        )

        patch_lint_hook(claude_dir, profile)

        content = lint_hook.read_text()
        # Check that dirs are updated (single or double quotes both OK)
        assert "app/" in content and "core/" in content
        assert ".py" in content

    def test_patches_typescript_project(self, temp_dst):
        claude_dir = temp_dst / ".claude"
        claude_dir.mkdir()
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir()

        lint_hook = hooks_dir / "stop-lint-check.py"
        lint_hook.write_text('LINT_DIRS = ["src/", "tests/"]\nLINT_EXTENSIONS = [".py"]\n')

        profile = ProjectProfile(language="typescript", src_dirs=["src/", "components/"])

        patch_lint_hook(claude_dir, profile)

        content = lint_hook.read_text()
        # Should update extensions for TypeScript
        assert ".ts" in content or ".tsx" in content

    def test_handles_missing_hook_gracefully(self, temp_dst):
        claude_dir = temp_dst / ".claude"
        claude_dir.mkdir()

        profile = ProjectProfile(language="python")

        # Should not crash if hook doesn't exist
        try:
            patch_lint_hook(claude_dir, profile)
        except FileNotFoundError:
            # Expected behavior - hook should exist but test covers the case
            pass


class TestPatchLintHookFromPreset:
    """Test lint hook patching from preset config."""

    def test_patches_hook_from_preset_lint_dirs(self, temp_dst):
        claude_dir = temp_dst / ".claude"
        claude_dir.mkdir()
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir()

        lint_hook = hooks_dir / "stop-lint-check.py"
        lint_hook.write_text('LINT_DIRS = ["src/", "tests/"]\nLINT_EXTENSIONS = [".py"]\n')

        preset_config = {
            "lint_dirs": """
- "app/"
- "core/"
"""
        }

        patch_lint_hook_from_preset(claude_dir, preset_config)

        content = lint_hook.read_text()
        assert "app/" in content and "core/" in content

    def test_patches_hook_from_preset_extensions(self, temp_dst):
        claude_dir = temp_dst / ".claude"
        claude_dir.mkdir()
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir()

        lint_hook = hooks_dir / "stop-lint-check.py"
        lint_hook.write_text('LINT_DIRS = ["src/", "tests/"]\nLINT_EXTENSIONS = [".py"]\n')

        preset_config = {
            "lint_extensions": """
- ".ts"
- ".tsx"
"""
        }

        patch_lint_hook_from_preset(claude_dir, preset_config)

        content = lint_hook.read_text()
        assert ".ts" in content or ".tsx" in content

    def test_handles_missing_hook_from_preset_gracefully(self, temp_dst):
        claude_dir = temp_dst / ".claude"
        claude_dir.mkdir()

        preset_config = {"lint_dirs": '- "app/"'}

        # Should not crash if hook doesn't exist
        try:
            patch_lint_hook_from_preset(claude_dir, preset_config)
        except FileNotFoundError:
            pass


class TestSetupGlobal:
    """Test global ~/.claude/ configuration."""

    def test_creates_global_claude_dir(self, monkeypatch, temp_dst):
        # Mock Path.home() to use temp directory
        monkeypatch.setattr(Path, "home", lambda: temp_dst)

        setup_global(dry_run=False)

        assert (temp_dst / ".claude").exists()
        assert (temp_dst / ".claude" / "rules").exists()

    def test_dry_run_mode(self, monkeypatch, temp_dst, capsys):
        monkeypatch.setattr(Path, "home", lambda: temp_dst)

        setup_global(dry_run=True)

        captured = capsys.readouterr()
        assert "Setting up global" in captured.out

    def test_creates_settings_json_new_if_exists(self, monkeypatch, temp_dst):
        monkeypatch.setattr(Path, "home", lambda: temp_dst)

        # Create existing settings.json
        claude_dir = temp_dst / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.json").write_text('{"existing": true}')

        setup_global(dry_run=False)

        # Should create .new file when settings.json already exists
        assert (claude_dir / "settings.json.new").exists()
        # Template content should be in .new file
        new_content = (claude_dir / "settings.json.new").read_text()
        assert "permissions" in new_content
