# Claude Code Hooks - Complete Reference

Claude Code hooks are **user-defined shell commands, HTTP endpoints, or LLM prompts that execute at specific lifecycle points** in your Claude Code workflow. They provide deterministic control over Claude Code's behavior, ensuring certain actions always happen rather than relying on the LLM to choose to run them.

## Key Characteristics

- **Event-driven**: Fire at specific lifecycle points (before/after tool use, on session start, on permission prompts, etc.)
- **Deterministic**: Always execute when conditions match (not at LLM discretion)
- **Filterable**: Use matchers to narrow execution to specific tools/events
- **Decision-capable**: Can allow, deny, block, or modify actions

When an event fires, all matching hooks run **in parallel** (identical commands are deduplicated). For decisions, the **most restrictive** answer wins (deny > ask > allow).

---

## Hook Events

### Core Session Events

| Event | When It Fires | Can Block? |
|-------|---------------|-----------|
| `SessionStart` | Session begins or resumes | No |
| `SessionEnd` | Session terminates | No |
| `InstructionsLoaded` | CLAUDE.md or rules file loaded | No |
| `UserPromptSubmit` | User submits a prompt (before Claude processes it) | Yes |

### Tool Execution Events

| Event | When It Fires | Can Block? | Tool Matcher? |
|-------|---------------|-----------|---------------|
| `PreToolUse` | Before a tool call executes | Yes | Yes |
| `PostToolUse` | After a tool call succeeds | No | Yes |
| `PostToolUseFailure` | After a tool call fails | No | Yes |
| `PermissionRequest` | Permission dialog appears | Yes | Yes |
| `PermissionDenied` | Tool blocked by auto mode | Yes | Yes |

### Decision/Control Events

| Event | When It Fires | Can Block? |
|-------|---------------|-----------|
| `Stop` | Claude finishes responding (turn complete) | Yes |
| `StopFailure` | Session ends due to API error | No |
| `TaskCreated` | Task created via TaskCreate | Yes |
| `TaskCompleted` | Task marked as completed | Yes |

### Agent/Team Events

| Event | When It Fires | Can Block? |
|-------|---------------|-----------|
| `SubagentStart` | Subagent is spawned | No |
| `SubagentStop` | Subagent finishes | No |
| `TeammateIdle` | Teammate about to go idle | Yes |

### Context & File Change Events

| Event | When It Fires | Can Block? |
|-------|---------------|-----------|
| `PreCompact` | Before context compaction | No |
| `PostCompact` | After context compaction | No |
| `FileChanged` | Watched file changes on disk | No |
| `CwdChanged` | Working directory changes | No |
| `ConfigChange` | Config file changes during session | Yes |

### MCP & Worktree Events

| Event | When It Fires | Can Block? |
|-------|---------------|-----------|
| `Elicitation` | MCP server requests user input | Yes |
| `ElicitationResult` | User responds to MCP elicitation | No |
| `Notification` | Claude Code sends a notification | No |
| `WorktreeCreate` | Worktree created for subagent isolation | Yes |
| `WorktreeRemove` | Worktree removed at session end | No |

---

## Configuration

### File Locations

```
~/.claude/settings.json                 -> Global (all projects)
.claude/settings.json                   -> Project (shareable, committed to git)
.claude/settings.local.json             -> Project (local only, gitignored)
Managed policy settings                 -> Organization-wide (admin-controlled)
```

### Structure

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "pattern-to-filter",
        "hooks": [
          {
            "type": "command",
            "command": "shell command to run"
          }
        ]
      }
    ]
  }
}
```

Three levels: **Event** -> **Matcher Group** -> **Hook Handler**

### Hook Handler Types

1. **command** - Shell command
2. **http** - HTTP endpoint
3. **agent** - LLM subagent
4. **prompt** - LLM prompt evaluation

---

## Matchers

| Event Type | Matcher Field | Example Values | Pattern Type |
|-----------|---|---|---|
| Tool events | tool name | `Bash`, `Edit|Write`, `mcp__github__.*` | Regex |
| SessionStart | how started | `startup`, `resume`, `clear`, `compact` | Exact |
| Notification | notification type | `permission_prompt`, `idle_prompt` | Exact |
| SubagentStart/Stop | agent type | `Explore`, `Plan` | Exact |
| FileChanged | filename | `.env`, `package.json` | Exact/Regex |

### Advanced: Filter by Tool Arguments with `if`

```json
{
  "type": "command",
  "if": "Bash(git *)",
  "command": "check-git-policy.sh"
}
```

---

## Hook Command Execution

### Environment Variables

```bash
CLAUDE_SESSION_ID              # Unique session ID
CLAUDE_PERMISSION_MODE         # Current mode
CLAUDE_PROJECT_DIR             # Absolute path to project root
CLAUDE_ENV_FILE                # Write env vars here to persist them
```

### Stdin JSON (all events)

```bash
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')
```

### Exit Codes

| Exit Code | Meaning | Effect |
|-----------|---------|--------|
| 0 | Success | Parse JSON from stdout, continue |
| 2 | Block/Deny | Use stderr as feedback to Claude, block action |
| Other | Non-blocking error | Stderr logged, action continues |

---

## Practical Examples

### Auto-format on file edit (PostToolUse)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write"
          }
        ]
      }
    ]
  }
}
```

### Block dangerous commands (PreToolUse)

```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')
if echo "$COMMAND" | grep -qE 'rm\s+-rf|drop table'; then
  echo "Destructive command blocked" >&2
  exit 2
fi
exit 0
```

### Re-inject context after compaction (SessionStart)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Important: Use uv for packages. Always run tests before committing.'"
          }
        ]
      }
    ]
  }
}
```

### Verify tests before stopping (Stop)

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate whether all requested tasks are complete. Return {\"ok\": true} if complete, or {\"ok\": false, \"reason\": \"what still needs doing\"}."
          }
        ]
      }
    ]
  }
}
```

### Desktop notification (Notification)

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Claude needs your attention'"
          }
        ]
      }
    ]
  }
}
```

### Reload env on directory change (CwdChanged)

```json
{
  "hooks": {
    "CwdChanged": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "direnv export bash >> \"$CLAUDE_ENV_FILE\""
          }
        ]
      }
    ]
  }
}
```

---

## Hooks vs Skills

| Aspect | Hooks | Skills |
|--------|-------|--------|
| **Trigger** | Automatic on lifecycle events | Manual `/skill-name` or Claude auto-invokes |
| **Control** | Deterministic, always execute | LLM decides when to use |
| **Purpose** | Enforce rules, automate workflow | Extend capabilities with instructions |
| **Blocking** | Can block tool calls | Cannot block actions |

---

## Common Gotchas

1. **Hook not firing**: Check matcher case sensitivity and event type (before vs after)
2. **JSON parse error**: Shell profile has unconditional `echo` statements - wrap in `if [[ $- == *i* ]]`
3. **Stop hook infinite loop**: Check `stop_hook_active` field and exit early if true
4. **Permission rules override hook approvals**: Deny rules always take precedence
5. **Hook timeout**: 10 minutes default (configurable with `timeout` field)
6. **PostToolUse cannot undo**: Action already executed; hook can only react
