# /new-spec — Interactive Spec Creator

Create a new feature specification through guided questions.

## Usage
```
/new-spec <feature-title>
```

## Process

### Step 1: Gather Requirements
Ask the user these questions (wait for answers before proceeding):

1. **Goal**: What problem does this feature solve? Who benefits?
2. **Scope**: What is explicitly OUT of scope for this spec?
3. **Inputs**: What data or events trigger this feature?
4. **Outputs**: What does the system produce or change?
5. **Constraints**: Any hard technical constraints? (performance, compatibility, security)
6. **Acceptance criteria**: How will you know it's done? (be specific and measurable)

### Step 2: Generate Spec File

Create `docs/specs/<slug>.md` with this structure:

```markdown
# Spec: <Feature Title>
_Created: <date> | Status: draft_

## Problem Statement
<1-2 sentences: what problem, who has it>

## Goal
<What success looks like — measurable if possible>

## Scope
### In scope
- <item>

### Out of scope
- <item>

## Functional Requirements
### FR-1: <requirement title>
<Description>
**Acceptance**: <testable criterion>

## Non-Functional Requirements
- **Performance**: <requirement or "none">
- **Security**: <requirement or "none">
- **Scalability**: <requirement or "none">

## Technical Approach
<High-level implementation strategy — 2-5 sentences>

## Open Questions
- [ ] <unresolved question>

## Implementation Plan
_To be filled by /implement-spec_
```

### Step 3: Create GitHub Issue

```bash
gh issue create \
  --title "feat: <feature-title>" \
  --body "Implements spec: docs/specs/<slug>.md" \
  --label "enhancement"
```

### Step 4: Update CURRENT_TASK.md

Set the task title, GitHub issue number, and done conditions from the spec's acceptance criteria.
