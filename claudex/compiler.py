"""Agent file compiler — renders YAML role registries into individual .md agent files.

Reads implementers.yml and verifiers.yml from the ClaudeX agent registry and writes
one .md file per role into the target agents directory. Called by cli.py during
`claudex init --multi-agent`.
"""

from pathlib import Path

import yaml

_IMPLEMENTER_TEMPLATE = """\
# {name}

You are the **{name}** — a specialist implementer for this project.

## Your Responsibility

{description}

## Focus Areas

{focus_list}

## Files You Own

{files_owned_list}

## Files You Must NOT Touch

{must_not_touch_list}

## Working Style

- Follow the project's CLAUDE.md architecture rules at all times
- Write tests for all code you implement (see TESTING_GUIDELINES.md)
- Keep files \u2264300 lines (hard limit: 500 lines)
- Run lint and format before signaling completion
- Update `.claude/session/TASK_PROGRESS.md` when done
- Use `/context-handoff` to hand back to the orchestrator when complete

## Done Signal

When your work is complete, output:

```
DONE: [brief summary of what was implemented]
Files changed: [list]
Tests: [pass/fail count]
```
"""

_VERIFIER_TEMPLATE = """\
# {name}

You are the **{name}** — you run AFTER implementers complete to validate the work.

## Your Responsibility

{description}

## What to Check

{checks_list}

## Output

Write your findings to `{output}`.

Use this format:

```markdown
# {name} Report
_Checked: [date]_

## Summary
[PASS / FAIL with one-line explanation]

## Issues Found

### Critical
- [file:line] [description]

### Warnings
- [file:line] [description]

## Verdict
[MERGE_READY / NEEDS_FIXES / BLOCK_MERGE]
```

## Blocking Criteria

**Blocks merge on**: {blocks_merge_on} issues.

If you find blocking issues, recommend routing back to the relevant implementer.
"""


def compile_implementer_agents(agents_yml: Path, dest_dir: Path) -> list[str]:
    """Read implementers.yml and write one .md file per role.

    Returns list of created filenames (e.g. ['api-engineer.md', ...]).
    """
    if not agents_yml.exists():
        return []

    data = yaml.safe_load(agents_yml.read_text(encoding="utf-8"))
    created: list[str] = []

    for role in data.get("roles", []):
        role_id = role["id"]
        name = role.get("name", role_id)
        description = role.get("description", "")
        focus = role.get("focus", [])
        files_owned = role.get("files_owned", [])
        must_not_touch = role.get("must_not_touch", [])

        focus_list = "\n".join(f"- {item}" for item in focus) if focus else "- See CLAUDE.md"
        files_owned_list = (
            "\n".join(f"- `{p}`" for p in files_owned) if files_owned else "- Project-dependent"
        )
        must_not_touch_list = (
            "\n".join(f"- `{p}`" for p in must_not_touch) if must_not_touch else "- None specified"
        )

        content = _IMPLEMENTER_TEMPLATE.format(
            name=name,
            description=description,
            focus_list=focus_list,
            files_owned_list=files_owned_list,
            must_not_touch_list=must_not_touch_list,
        )

        out_path = dest_dir / f"{role_id}.md"
        out_path.write_text(content, encoding="utf-8")
        created.append(f"{role_id}.md")

    return created


def compile_verifier_agents(verifiers_yml: Path, dest_dir: Path) -> list[str]:
    """Read verifiers.yml and write one .md file per role.

    Returns list of created filenames (e.g. ['architecture-verifier.md', ...]).
    """
    if not verifiers_yml.exists():
        return []

    data = yaml.safe_load(verifiers_yml.read_text(encoding="utf-8"))
    created: list[str] = []

    for role in data.get("roles", []):
        role_id = role["id"]
        name = role.get("name", role_id)
        description = role.get("description", "")
        checks = role.get("checks", [])
        output = role.get("output", "verification/report.md")
        blocks_merge_on = role.get("blocks_merge_on", "critical")

        checks_list = "\n".join(f"- {c}" for c in checks) if checks else "- See project guidelines"

        content = _VERIFIER_TEMPLATE.format(
            name=name,
            description=description,
            checks_list=checks_list,
            output=output,
            blocks_merge_on=blocks_merge_on,
        )

        out_path = dest_dir / f"{role_id}.md"
        out_path.write_text(content, encoding="utf-8")
        created.append(f"{role_id}.md")

    return created
