"""Tests for claudex.layer_configs and copier.patch_layer_config."""

import shutil

import pytest

from claudex.copier import patch_layer_config
from claudex.layer_configs import PRESETS, get_preset


class TestGetPreset:
    def test_returns_fastapi_preset(self):
        cfg = get_preset("python-fastapi")
        assert "src/core/" in cfg["layer_config"]
        assert "sqlalchemy" in cfg["layer_config"]["src/core/"]

    def test_returns_django_preset(self):
        cfg = get_preset("python-django")
        assert "apps/" in cfg["layer_config"]

    def test_returns_nextjs_preset(self):
        cfg = get_preset("nextjs")
        assert "src/lib/" in cfg["layer_config"]
        assert "src/components/" in cfg["layer_config"]

    def test_returns_generic_preset(self):
        cfg = get_preset("generic")
        assert cfg["layer_config"] == {}
        assert cfg["sibling_blocks"] == {}

    def test_unknown_preset_falls_back_to_generic(self):
        cfg = get_preset("unknown-stack")
        assert cfg == PRESETS["generic"]

    def test_all_presets_have_required_keys(self):
        for name, cfg in PRESETS.items():
            assert "layer_config" in cfg, f"{name} missing layer_config"
            assert "sibling_blocks" in cfg, f"{name} missing sibling_blocks"
            assert "layer_file_blocks" in cfg, f"{name} missing layer_file_blocks"


class TestPatchLayerConfig:
    @pytest.fixture()
    def claude_dir(self, tmp_path):
        """Set up a minimal .claude/ with a pre-tool-use.py containing template placeholders."""
        from claudex.copier import PROJECT_TEMPLATE

        hooks_dir = tmp_path / ".claude" / "hooks"
        hooks_dir.mkdir(parents=True)
        src = PROJECT_TEMPLATE / "hooks" / "pre-tool-use.py"
        shutil.copy2(src, hooks_dir / "pre-tool-use.py")
        return tmp_path / ".claude"

    def test_fastapi_writes_layer_config(self, claude_dir):
        patch_layer_config(claude_dir, "python-fastapi")
        content = (claude_dir / "hooks" / "pre-tool-use.py").read_text(encoding="utf-8")
        assert "src/core/" in content
        assert "sqlalchemy" in content

    def test_fastapi_writes_sibling_blocks(self, claude_dir):
        patch_layer_config(claude_dir, "python-fastapi")
        content = (claude_dir / "hooks" / "pre-tool-use.py").read_text(encoding="utf-8")
        assert "from src.api" in content

    def test_fastapi_writes_layer_file_blocks(self, claude_dir):
        patch_layer_config(claude_dir, "python-fastapi")
        content = (claude_dir / "hooks" / "pre-tool-use.py").read_text(encoding="utf-8")
        assert "llm" in content

    def test_nextjs_writes_component_rule(self, claude_dir):
        patch_layer_config(claude_dir, "nextjs")
        content = (claude_dir / "hooks" / "pre-tool-use.py").read_text(encoding="utf-8")
        assert "src/lib/" in content
        assert "src/components/" in content

    def test_generic_leaves_file_unchanged(self, claude_dir):
        original = (claude_dir / "hooks" / "pre-tool-use.py").read_text(encoding="utf-8")
        patch_layer_config(claude_dir, "generic")
        after = (claude_dir / "hooks" / "pre-tool-use.py").read_text(encoding="utf-8")
        assert original == after

    def test_unknown_preset_leaves_file_unchanged(self, claude_dir):
        original = (claude_dir / "hooks" / "pre-tool-use.py").read_text(encoding="utf-8")
        patch_layer_config(claude_dir, "unknown-stack")
        after = (claude_dir / "hooks" / "pre-tool-use.py").read_text(encoding="utf-8")
        assert original == after

    def test_missing_hook_file_does_not_raise(self, tmp_path):
        empty_claude = tmp_path / ".claude"
        empty_claude.mkdir()
        # No hooks/ subdirectory — should silently return
        patch_layer_config(empty_claude, "python-fastapi")

    def test_result_is_valid_python(self, claude_dir):
        import ast

        patch_layer_config(claude_dir, "python-fastapi")
        content = (claude_dir / "hooks" / "pre-tool-use.py").read_text(encoding="utf-8")
        ast.parse(content)  # raises SyntaxError if invalid
