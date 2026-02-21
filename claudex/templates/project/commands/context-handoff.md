# /context-handoff — Structured Agent-to-Agent Context Transfer

Generate a structured context handoff document when transitioning work
between agents. Prevents context loss and ensures agents have everything
they need to continue without asking redundant questions.

## Usage
```
/context-handoff <source-agent> <target-agent> <task-description>
```
Example: `/context-handoff orchestrator api-engineer "implement POST /auth/login endpoint"`

## Handoff Document Format

Generate `verification/handoff-<target-agent>.md`:

```markdown
# Context Handoff: <source> → <target>
_Generated: <date>_

## Task
<Specific, actionable task description — not the full spec>

## Completed Work
<What has already been done — be precise about file paths and decisions>
- None (first agent in chain)
  OR
- <file.py>: <what was done>

## Your Pending Work
<Explicit list of what THIS agent needs to do>
1. <action 1>
2. <action 2>

## Decision Log
<Architectural and approach decisions already made — the target agent must honor these>
- <decision 1>: <brief rationale>

## Files to Touch
<Expected file paths this agent will read or write>
- CREATE: <path> — <purpose>
- MODIFY: <path> — <what changes>
- READ: <path> — <why>

## Files NOT to Touch
<Files owned by other agents or that must not change>
- <path> — <owned by: role>

## Gotchas
<Known pitfalls, constraints, or non-obvious requirements>
- <gotcha 1>

## Done Condition
<How the target agent knows it's finished>
- [ ] <criterion 1>
- [ ] <criterion 2>

## Hand Back To
<Next agent in chain, or "orchestrator" if this is the last agent>
```

## When to Use This

- Before any agent-to-agent task transfer in `/implement-spec`
- When switching from one specialist to another mid-feature
- When resuming work after a session break (handoff from "previous session" → "current agent")
- When splitting a task between parallel background agents

## What Makes a Good Handoff

1. **Specific files** — list exact paths, not vague descriptions
2. **Decision log** — what was decided AND why, so the next agent doesn't re-litigate
3. **Explicit boundaries** — what NOT to touch is as important as what to touch
4. **Testable done condition** — the agent can self-verify completion
