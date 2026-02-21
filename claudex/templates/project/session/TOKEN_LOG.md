# Token Budget Log

Tracks cumulative token spend per session. Written by the `token-budget.py` PreToolUse hook.

**Format**: one row per tool call that crosses a threshold checkpoint.

---

## Log

| Timestamp (UTC) | Tool | Estimated Tokens | Session Total | % of Budget |
|-----------------|------|-----------------|---------------|-------------|
| _auto-populated by token-budget.py_ | | | | |

---

## Budget Configuration

Edit `.claude/hooks/token-budget.py` to change thresholds:

```python
WARN_THRESHOLD = 0.80   # Warn at 80% of budget
BLOCK_THRESHOLD = 1.00  # Block at 100% of budget
SESSION_BUDGET = 200000 # Tokens per session (adjust to your plan)
```

---

## Reading This File

- **Session Total**: cumulative tokens since the current session started
- **% of Budget**: total / SESSION_BUDGET * 100
- When % reaches WARN_THRESHOLD: hook prints a warning in tool output
- When % reaches BLOCK_THRESHOLD: hook blocks the tool call and outputs a stop message

Reset by deleting the log rows below the header (the hook appends new rows on each run).
