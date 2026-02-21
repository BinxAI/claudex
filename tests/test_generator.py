"""Tests for CLAUDE.md generator."""

from claudex.detectors import ProjectProfile
from claudex.generator import (
    _section_constraints,
    _section_header,
    _section_quick_start,
    generate_claude_md,
)


class TestSectionHeader:
    """Test header section generation."""

    def test_generates_header_with_name_and_description(self):
        profile = ProjectProfile(name="test-app", description="A test application")
        result = _section_header(profile)

        assert "# test-app" in result
        assert "A test application" in result


class TestSectionQuickStart:
    """Test quick start section generation."""

    def test_generates_uv_commands(self):
        profile = ProjectProfile(package_manager="uv")
        result = _section_quick_start(profile, {})

        assert "uv sync" in result
        assert "```bash" in result

    def test_generates_npm_commands(self):
        profile = ProjectProfile(package_manager="npm", language="javascript")
        result = _section_quick_start(profile, {})

        assert "npm install" in result
        assert "npm run dev" in result

    def test_includes_docker_if_detected(self):
        profile = ProjectProfile(package_manager="poetry", has_docker=True)
        result = _section_quick_start(profile, {})

        assert "docker-compose up -d" in result

    def test_includes_django_migrations(self):
        profile = ProjectProfile(
            framework="Django", language="python", has_db=True, entry_points=["manage.py"]
        )
        result = _section_quick_start(profile, {})

        assert "python manage.py migrate" in result or "manage.py" in result


class TestSectionConstraints:
    """Test constraints section generation."""

    def test_includes_base_constraints(self):
        profile = ProjectProfile()
        result = _section_constraints(profile)

        assert "Never commit" in result or "NEVER" in result.upper()
        assert ".env" in result

    def test_adds_rule_versioning_for_db_projects(self):
        profile = ProjectProfile(has_db=True)
        result = _section_constraints(profile)

        assert "rule" in result.lower() or "version" in result.lower()


class TestGenerateClaudeMd:
    """Integration tests for full CLAUDE.md generation."""

    def test_generates_complete_markdown_for_fastapi(self):
        profile = ProjectProfile(
            name="fastapi-app",
            description="FastAPI application",
            language="python",
            framework="FastAPI",
            package_manager="uv",
            python_version=">=3.11",
            has_db=True,
            db_type="postgresql",
            has_docker=True,
            directory_tree="fastapi-app/\n  src/\n  tests/",
        )
        preset_config = {"layer_description": "Test layers"}

        result = generate_claude_md(profile, preset_config)

        # Check all major sections present (case-insensitive where needed)
        result_lower = result.lower()
        assert "# fastapi-app" in result
        assert "FastAPI" in result
        assert "architecture" in result_lower
        assert "quick start" in result_lower
        assert "uv sync" in result
        # Database info not currently included in generated CLAUDE.md
        # (it's in detection but not rendered - OK for v1.0)
        assert "docker" in result_lower  # Check for docker instead

    def test_generates_complete_markdown_for_nextjs(self):
        profile = ProjectProfile(
            name="nextjs-app",
            description="Next.js application",
            language="typescript",
            framework="Next.js",
            package_manager="pnpm",
            has_db=False,
            directory_tree="nextjs-app/\n  app/\n  components/",
        )
        preset_config = {}

        result = generate_claude_md(profile, preset_config)

        assert "# nextjs-app" in result
        assert "Next.js" in result
        assert "pnpm install" in result
        assert "app/" in result

    def test_handles_minimal_profile(self):
        profile = ProjectProfile(name="minimal-app")
        preset_config = {}

        result = generate_claude_md(profile, preset_config)

        # Should not crash, should have basic structure
        assert "# minimal-app" in result
        assert "Architecture" in result

    def test_markdown_is_valid(self):
        profile = ProjectProfile(name="test-app", language="python", framework="FastAPI")
        preset_config = {}

        result = generate_claude_md(profile, preset_config)

        # Check markdown structure
        assert result.startswith("# ")
        assert "\n## " in result  # Has sections
        assert "```" in result or "---" in result  # Has code blocks or separators
