"""Tests for claudex.compiler — YAML registry → individual agent .md file compilation."""

import pytest
import yaml

from claudex.compiler import compile_implementer_agents, compile_verifier_agents


@pytest.fixture()
def implementers_yml(tmp_path):
    """Minimal implementers.yml with 2 roles."""
    data = {
        "version": "1.0",
        "roles": [
            {
                "id": "api-engineer",
                "name": "API Engineer",
                "description": "Builds REST endpoints.",
                "focus": ["REST design", "Pydantic validation"],
                "files_owned": ["src/api/**"],
                "must_not_touch": ["src/core/**"],
            },
            {
                "id": "database-engineer",
                "name": "Database Engineer",
                "description": "Manages ORM and migrations.",
                "focus": ["SQLAlchemy models", "Alembic migrations"],
                "files_owned": ["src/db/**", "alembic/**"],
                "must_not_touch": ["src/api/**"],
            },
        ],
    }
    yml_file = tmp_path / "implementers.yml"
    yml_file.write_text(yaml.dump(data), encoding="utf-8")
    return yml_file


@pytest.fixture()
def verifiers_yml(tmp_path):
    """Minimal verifiers.yml with 2 roles."""
    data = {
        "version": "1.0",
        "roles": [
            {
                "id": "architecture-verifier",
                "name": "Architecture Verifier",
                "description": "Checks layer boundaries.",
                "checks": ["Layer violations", "Circular imports"],
                "output": "verification/architecture-report.md",
                "blocks_merge_on": "critical",
            },
            {
                "id": "security-verifier",
                "name": "Security Verifier",
                "description": "OWASP Top 10 scan.",
                "checks": ["SQL injection", "Hardcoded secrets"],
                "output": "verification/security-report.md",
                "blocks_merge_on": "any",
            },
        ],
    }
    yml_file = tmp_path / "verifiers.yml"
    yml_file.write_text(yaml.dump(data), encoding="utf-8")
    return yml_file


class TestCompileImplementerAgents:
    def test_creates_one_file_per_role(self, implementers_yml, tmp_path):
        created = compile_implementer_agents(implementers_yml, tmp_path)
        assert created == ["api-engineer.md", "database-engineer.md"]
        assert (tmp_path / "api-engineer.md").exists()
        assert (tmp_path / "database-engineer.md").exists()

    def test_file_contains_role_name(self, implementers_yml, tmp_path):
        compile_implementer_agents(implementers_yml, tmp_path)
        content = (tmp_path / "api-engineer.md").read_text(encoding="utf-8")
        assert "API Engineer" in content

    def test_file_contains_description(self, implementers_yml, tmp_path):
        compile_implementer_agents(implementers_yml, tmp_path)
        content = (tmp_path / "api-engineer.md").read_text(encoding="utf-8")
        assert "Builds REST endpoints." in content

    def test_file_contains_focus_items(self, implementers_yml, tmp_path):
        compile_implementer_agents(implementers_yml, tmp_path)
        content = (tmp_path / "api-engineer.md").read_text(encoding="utf-8")
        assert "REST design" in content
        assert "Pydantic validation" in content

    def test_file_contains_files_owned(self, implementers_yml, tmp_path):
        compile_implementer_agents(implementers_yml, tmp_path)
        content = (tmp_path / "api-engineer.md").read_text(encoding="utf-8")
        assert "src/api/**" in content

    def test_file_contains_must_not_touch(self, implementers_yml, tmp_path):
        compile_implementer_agents(implementers_yml, tmp_path)
        content = (tmp_path / "api-engineer.md").read_text(encoding="utf-8")
        assert "src/core/**" in content

    def test_returns_empty_list_when_file_missing(self, tmp_path):
        result = compile_implementer_agents(tmp_path / "missing.yml", tmp_path)
        assert result == []

    def test_handles_empty_optional_fields(self, tmp_path):
        """Roles with no focus/files_owned/must_not_touch should not crash."""
        data = {
            "version": "1.0",
            "roles": [{"id": "minimal-agent", "name": "Minimal", "description": "Bare minimum."}],
        }
        yml = tmp_path / "minimal.yml"
        yml.write_text(yaml.dump(data), encoding="utf-8")
        created = compile_implementer_agents(yml, tmp_path)
        assert created == ["minimal-agent.md"]
        content = (tmp_path / "minimal-agent.md").read_text(encoding="utf-8")
        assert "Minimal" in content


class TestCompileVerifierAgents:
    def test_creates_one_file_per_role(self, verifiers_yml, tmp_path):
        created = compile_verifier_agents(verifiers_yml, tmp_path)
        assert created == ["architecture-verifier.md", "security-verifier.md"]
        assert (tmp_path / "architecture-verifier.md").exists()
        assert (tmp_path / "security-verifier.md").exists()

    def test_file_contains_verifier_name(self, verifiers_yml, tmp_path):
        compile_verifier_agents(verifiers_yml, tmp_path)
        content = (tmp_path / "architecture-verifier.md").read_text(encoding="utf-8")
        assert "Architecture Verifier" in content

    def test_file_contains_checks(self, verifiers_yml, tmp_path):
        compile_verifier_agents(verifiers_yml, tmp_path)
        content = (tmp_path / "architecture-verifier.md").read_text(encoding="utf-8")
        assert "Layer violations" in content
        assert "Circular imports" in content

    def test_file_contains_output_path(self, verifiers_yml, tmp_path):
        compile_verifier_agents(verifiers_yml, tmp_path)
        content = (tmp_path / "architecture-verifier.md").read_text(encoding="utf-8")
        assert "verification/architecture-report.md" in content

    def test_file_contains_blocks_merge_on(self, verifiers_yml, tmp_path):
        compile_verifier_agents(verifiers_yml, tmp_path)
        content = (tmp_path / "security-verifier.md").read_text(encoding="utf-8")
        assert "any" in content

    def test_returns_empty_list_when_file_missing(self, tmp_path):
        result = compile_verifier_agents(tmp_path / "missing.yml", tmp_path)
        assert result == []


class TestCompilerWithRealRegistries:
    """Integration tests using the actual YAML registries from the package templates."""

    def test_compiles_all_eight_implementers(self, tmp_path):
        from claudex.copier import PROJECT_TEMPLATE

        agents_yml = PROJECT_TEMPLATE / "agents" / "implementers.yml"
        created = compile_implementer_agents(agents_yml, tmp_path)
        expected_ids = [
            "api-engineer",
            "database-engineer",
            "ui-designer",
            "testing-engineer",
            "devops-engineer",
            "security-engineer",
            "data-engineer",
            "docs-engineer",
        ]
        assert len(created) == 8
        for role_id in expected_ids:
            assert f"{role_id}.md" in created
            assert (tmp_path / f"{role_id}.md").exists()

    def test_compiles_all_four_verifiers(self, tmp_path):
        from claudex.copier import PROJECT_TEMPLATE

        verifiers_yml = PROJECT_TEMPLATE / "agents" / "verifiers.yml"
        created = compile_verifier_agents(verifiers_yml, tmp_path)
        expected_ids = [
            "architecture-verifier",
            "security-verifier",
            "quality-verifier",
            "test-verifier",
        ]
        assert len(created) == 4
        for role_id in expected_ids:
            assert f"{role_id}.md" in created
            assert (tmp_path / f"{role_id}.md").exists()

    def test_all_agent_files_are_valid_markdown(self, tmp_path):
        from claudex.copier import PROJECT_TEMPLATE

        compile_implementer_agents(PROJECT_TEMPLATE / "agents" / "implementers.yml", tmp_path)
        compile_verifier_agents(PROJECT_TEMPLATE / "agents" / "verifiers.yml", tmp_path)

        for md_file in tmp_path.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            assert content.startswith("#"), f"{md_file.name} must start with a heading"
            assert len(content) > 100, f"{md_file.name} is suspiciously short"
