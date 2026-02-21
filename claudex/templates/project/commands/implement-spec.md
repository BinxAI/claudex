# /implement-spec — 5-Phase Spec Implementation

Implements a spec through a structured multi-agent workflow.

## Usage
```
/implement-spec <spec-file-path>
```
Example: `/implement-spec docs/specs/user-auth.md`

## Phase 1: Plan Subagent Assignments

Read the spec file. Identify all implementation concerns. For each concern:
- Select the appropriate implementer role from `agents/implementers.yml`
- Estimate scope (files to touch, rough complexity)
- Identify dependencies between agents (execution order)

Output `verification/task-assignments.yml`:

```yaml
spec: <spec-path>
created: <date>

assignments:
  - id: "assign-1"
    role: api-engineer
    task: "<specific task description>"
    files: ["src/api/routes/auth.py", "src/api/schemas/auth.py"]
    depends_on: ["assign-2"]

  - id: "assign-2"
    role: database-engineer
    task: "<specific task description>"
    files: ["src/db/models/user.py", "alembic/versions/xxx_add_users.py"]
    depends_on: []
```

## Phase 2: Context Handoff

For each agent in execution order, generate a context handoff document
using `/context-handoff`. This ensures agents receive structured context,
not raw task descriptions.

Each handoff is saved to `verification/handoff-<role>.md`.

## Phase 3: Delegate to Implementers

In execution order (respecting `depends_on`):

1. Present the handoff document to the appropriate specialist command
   (e.g., `/expert-backend`, `/expert-devops`)
2. The implementer works and returns results
3. Record completion status in `task-assignments.yml`

For parallel-safe assignments (no shared files, no dependencies), these
can be run as background agents — see `agents/` directory.

## Phase 4: Delegate to Verifiers

After all implementers complete, run each applicable verifier
from `agents/verifiers.yml`:

- Always run: architecture-verifier, quality-verifier, test-verifier
- Run if security changes: security-verifier

Each verifier writes its report to `verification/<type>-report.md`.

## Phase 5: Final Verification

Review all verifier reports. Check:
- [ ] Zero critical issues across all reports
- [ ] All acceptance criteria from the spec are met
- [ ] All tests pass
- [ ] Lint and format clean

If issues found: route back to the relevant implementer (Phase 3).
If clean: write `verification/final-verification.md` and close the GitHub issue.

```markdown
# Final Verification: <spec title>
_Completed: <date>_

## Acceptance Criteria
- [x] <criterion 1>
- [x] <criterion 2>

## Verifier Reports
- Architecture: ✅ clean
- Quality: ✅ clean
- Security: ✅ clean
- Tests: ✅ 95% coverage

## Ready to merge: YES
```
