# /orchestrate — Route Any Task to the Right Specialist

Analyze a task and automatically route it to the correct implementer agent.
No manual agent selection required.

## Usage
```
/orchestrate <task-description>
```
Examples:
- `/orchestrate "add a POST /users endpoint with email validation"`
- `/orchestrate "fix the slow query on the orders table"`
- `/orchestrate "write unit tests for the payment service"`

## Process

### Step 1: Classify

Read the task description. Determine:
- **Primary type**: build / fix / refactor / test / docs / research / ops
- **Domain**: api / database / ui / infrastructure / security / data / docs
- **Scope**: single-agent or multi-agent?

### Step 2: Route

**Single-agent tasks** (most tasks):
- Use `/expert-backend` for: API, database, business logic, worker tasks
- Use `/expert-frontend` for: UI components, styling, client-side state
- Use `/expert-devops` for: CI/CD, Docker, deployment, monitoring
- Use `/expert-qa` for: tests, coverage, test strategy
- Use `/expert-architect` for: system design, architecture decisions

**Multi-agent tasks** (2+ distinct concerns):
- Use `/implement-spec` workflow (generates full agent plan)
- Threshold: route to implement-spec when task touches 3+ files OR 2+ layers

### Step 3: Generate Context

Before handing off to the specialist:
1. Generate `/context-handoff orchestrator <target-agent> "<task>"`
2. Include the handoff document as context for the specialist

### Step 4: Execute

Present the specialist with:
1. The context handoff document
2. The task instructions

### Step 5: Verify

After the specialist returns:
- Check if the done conditions are met
- If not: clarify and re-delegate
- If yes: confirm completion and update TASK_PROGRESS.md

## Quick-Route Table

| Task contains | Route to |
|---------------|----------|
| "endpoint", "API", "route", "REST" | expert-backend |
| "database", "schema", "migration", "query" | expert-backend |
| "component", "page", "UI", "style", "CSS" | expert-frontend |
| "test", "coverage", "spec", "mock" | expert-qa |
| "deploy", "CI", "Docker", "pipeline", "infra" | expert-devops |
| "design", "architecture", "refactor entire" | expert-architect |
| "document", "README", "ADR" | docs-engineer via expert-backend |
| multiple of the above | implement-spec |
