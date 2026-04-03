# Claude Code Agents & Subagents - Complete Reference

Subagents are specialized AI assistants that handle specific tasks within a Claude Code session. Each runs in its own **separate context window** with custom system prompt, tool restrictions, and focused instructions.

---

## Why Subagents

- **Context preservation**: Research subagent uses its own context, main stays clean
- **Specialization**: Different agents for different tasks (security, data, etc.)
- **Parallelism**: Multiple agents working simultaneously (with worktree isolation)
- **Reusability**: Define once, use across all projects

---

## Built-In Agent Types

| Agent Type | Purpose | Tools |
|---|---|---|
| **general-purpose** | Complex multi-step tasks | All tools |
| **Explore** | Research, codebase exploration | Read, Glob, Grep, WebFetch, WebSearch (read-only) |
| **Plan** | Analysis and planning | Read, Glob, Grep (no modifications) |

---

## Defining Custom Agents

Create `.claude/agents/{agent-name}/AGENT.md`:

```markdown
---
description: >
  Expert database query validator. Reviews SQL queries for performance,
  security, and correctness.

tools:
  - Read
  - Bash
  - Glob
  - Grep

model: claude-opus-4-1
permission_mode: plan

system_prompt: |
  You are a senior database engineer specializing in SQL optimization.
  Focus on: performance, security, correctness, best practices.
---

# Database Query Validator

This agent specializes in reviewing database queries.
```

### Agent File Locations

- **Project level**: `.claude/agents/` (shared with team)
- **User level**: `~/.claude/agents/` (available in all projects)
- **Plugin level**: Packaged with a plugin

### Frontmatter Fields

```yaml
description: |                          # When Claude should use this agent
tools: [Read, Edit, Bash, Glob, Grep]  # Available tools
model: claude-opus-4-1                  # Override model
permission_mode: plan                   # Permission level
system_prompt: |                        # Custom instructions
isolation: worktree                     # Run in isolated worktree
```

---

## Agent Isolation (Worktree)

Worktree isolation creates a separate copy of the repository for each subagent:

```yaml
---
description: Parallel refactoring agent
isolation: worktree
tools: [Read, Edit, Bash, Glob]
---
```

How it works:
1. Creates `.claude/worktrees/<agent-name>/` with fresh checkout
2. Branch named `worktree-<agent-name>`
3. Changes isolated from other sessions
4. Auto-cleaned up if no changes made

### .worktreeinclude

Fresh worktrees don't include gitignored files. Create `.worktreeinclude` to copy them:

```
.env
.env.local
config/secrets.json
```

---

## Background vs Foreground

- **Foreground** (default): Main agent waits for results before continuing. Use when you need the result to proceed.
- **Background** (`run_in_background: true`): Agent runs independently, you're notified on completion. Use for independent parallel work.

---

## Agent Communication

### Subagents (within a session)
- Subagent -> Main Agent: Results returned as summary
- Main Agent -> Subagent: Instructions via spawn prompt
- Subagent <-> Subagent: No direct communication

### Agent Teams (experimental)
Enable with: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

- Direct messaging between teammates
- Broadcast to all teammates
- Shared task coordination
- Multiple agents working in parallel

---

## Agent Tool Restrictions

### Per-agent tools
```yaml
tools: [Read, Glob, Grep]  # No Edit or Bash - safe for analysis
```

### Permission rules for agents
```json
{
  "permissions": {
    "allow": ["Agent(Explore)", "Agent(code-reviewer)"],
    "deny": ["Agent(dangerous-agent)"]
  }
}
```

---

## Agent SDK (Programmatic)

Build production AI agents in Python or TypeScript without Claude Code CLI.

```bash
pip install claude-agent-sdk       # Python
npm install @anthropic-ai/claude-agent-sdk  # TypeScript
```

### Basic Usage

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find and fix bugs in auth.py",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Bash"],
            permission_mode="acceptEdits",
            model="claude-opus-4-1"
        )
    ):
        print(message)

asyncio.run(main())
```

### Message Types
- `SystemMessage`: Agent initialization
- `AssistantMessage`: Claude's reasoning and tool calls
- `ToolResultMessage`: Tool output
- `ResultMessage`: Final results

### Session Resumption

```python
# Turn 1
session_id = None
async for msg in query(prompt="Read auth module", options=opts):
    if isinstance(msg, SystemMessage):
        session_id = msg.data["session_id"]

# Turn 2 - continues with full context
async for msg in query(prompt="Now fix the bug", options=ClaudeAgentOptions(resume=session_id)):
    print(msg)
```

---

## When to Use What

| Scenario | Approach |
|---|---|
| Quick file edit | Direct tools |
| Research before implementing | Explore subagent |
| Code review while implementing | Subagent (parallel, specialized) |
| Multiple hypotheses to investigate | Agent teams |
| CI/CD automation | Agent SDK |
| Parallel refactoring | Worktree-isolated agents |

---

## Limitations

1. **No inter-subagent communication** (use agent teams for that)
2. **Results are summarized** when returned to main context
3. **No persistent state** between sessions (unless using persistent memory)
4. **Agent teams are experimental** (require env flag)
5. **Context window limits** still apply per-agent
6. **No nested teams** - teammates cannot spawn their own teams
7. **File conflicts without worktrees** - always use worktrees for parallel agents
