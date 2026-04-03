# Claude Code MCP & Settings System - Complete Reference

## MCP (Model Context Protocol)

MCP is a standardized protocol that extends Claude Code by connecting it to external tools, databases, APIs, and services.

---

## MCP Server Configuration

### File Locations

- **Project scope**: `.claude/.mcp.json` (committed to git)
- **User scope**: `~/.claude/.mcp.json` (personal)
- **Local scope**: `.claude/.mcp-local.json` (gitignored)

### Configuration Format

```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio",
      "command": "node",
      "args": ["./mcp-server.js"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

### Server Types

| Type | Best For | How It Works |
|------|----------|---|
| **stdio** | Local programs, fast execution | Spawns process, communicates via stdin/stdout |
| **sse** | Managed services, team sharing | HTTPS connection with Server-Sent Events |
| **http** | Simple REST APIs (legacy) | HTTP polling (prefer sse) |

### stdio Example (PostgreSQL)

```json
{
  "mcpServers": {
    "postgres": {
      "type": "stdio",
      "command": "node",
      "args": ["./mcp-servers/postgres.js"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

### SSE Example (Sentry)

```json
{
  "mcpServers": {
    "sentry": {
      "type": "sse",
      "url": "https://api.sentry.io/mcp",
      "headers": {
        "Authorization": "Bearer ${SENTRY_API_TOKEN}"
      }
    }
  }
}
```

### Import from Claude Desktop

```bash
claude import-mcp-config
```

---

## Settings System

### Four-Tier Scope

| Scope | File Location | Shared? | Use Case |
|-------|---|---|---|
| **Managed** | System-level (IT deployment) | Organization-wide | Enforce policies |
| **User** | `~/.claude/settings.json` | Just you | Personal preferences |
| **Project** | `.claude/settings.json` | Team (git) | Team standards |
| **Local** | `.claude/settings.local.json` | Just you | Local overrides, secrets (gitignored) |

### Precedence (highest to lowest)

1. Managed settings (enforced, cannot override)
2. CLI flags
3. Local settings (gitignored)
4. Project settings (committed)
5. User settings

### Example: Project Settings

```json
{
  "defaultModel": "claude-opus-4-1",
  "effortLevel": "high",
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(git commit *)"
    ],
    "deny": [
      "Bash(rm -rf /)",
      "Bash(git push * --force)"
    ]
  }
}
```

### Example: Local Settings (secrets)

```json
{
  "env": {
    "GITHUB_TOKEN": "ghp_xxxxxxxxxxxx",
    "DATABASE_URL": "postgresql://localhost/dev"
  }
}
```

---

## Permission System

### Permission Modes

| Mode | Description |
|------|-------------|
| `default` | Prompt for each new tool on first use |
| `acceptEdits` | Auto-approve file edits, prompt for commands |
| `plan` | Read-only, no commands or edits |
| `auto` | Auto-approve safe actions (Research Preview) |
| `dontAsk` | Deny all tools unless pre-approved |
| `bypassPermissions` | Skip prompts (protected dirs still prompt) |

### Permission Rule Syntax

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Read(src/**)",
      "Edit(/config/*.json)",
      "WebFetch(domain:github.com)",
      "mcp__postgres__query_db",
      "Agent(Explore)"
    ],
    "deny": [
      "Bash(git push * --force)",
      "Bash(rm -rf /)",
      "Edit(.env)"
    ]
  }
}
```

---

## Environment Variables

### In settings.local.json (secrets)

```json
{
  "env": {
    "GITHUB_TOKEN": "ghp_xxxxx",
    "DATABASE_URL": "postgresql://...",
    "API_KEY": "sk-proj-xxxxx"
  }
}
```

### Variable Substitution in MCP configs

Use `${VAR_NAME}` syntax:

```json
{
  "mcpServers": {
    "postgres": {
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

---

## CLAUDE.md Files

Persistent instruction files Claude reads at session start.

### Locations

| Location | Scope | Shared? |
|----------|-------|---------|
| `./CLAUDE.md` or `./.claude/CLAUDE.md` | Project | Team (git) |
| `~/.claude/CLAUDE.md` | User | Personal |
| System-level CLAUDE.md | Managed (org) | Organization |
| `.claude/rules/*.md` | Project | Team (git) |
| `~/.claude/rules/*.md` | User | Personal |

### Loading Order

1. Managed policy CLAUDE.md
2. CLAUDE.md from ancestor directories (walking up from cwd)
3. CLAUDE.md in subdirectories (lazy-loaded when files accessed)
4. User-level CLAUDE.md
5. Rules in `.claude/rules/`

### Path-Specific Rules

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "lib/**/*.ts"
---

# Backend Rules
These rules apply only to TypeScript files under src/api/ or lib/.
```

### Importing External Files

```markdown
See @README for project overview.
@docs/development-setup.md
@~/.claude/company-security.md
```

---

## Popular MCP Servers

| Category | Server | Purpose |
|----------|--------|---------|
| **Database** | PostgreSQL MCP | Query databases, inspect schema |
| **Database** | MongoDB MCP | Query collections, manage indexes |
| **Version Control** | GitHub MCP | PRs, issues, repositories |
| **Error Monitoring** | Sentry MCP | Monitor errors, track performance |
| **Infrastructure** | AWS MCP | EC2, Lambda, S3 management |
| **Communication** | Slack MCP | Send messages, query history |
| **Communication** | Gmail MCP (built-in) | Read/manage email |
| **Communication** | Telegram MCP (built-in) | Send/receive messages |

---

## MCP Best Practices

1. **Never commit secrets** - use `.claude/settings.local.json` (gitignored)
2. **Use stdio for local ops** - lowest latency
3. **Use SSE for team-shared services** - shared, no local setup
4. **Minimize tool count** - more tools = more context overhead
5. **Use permission rules** for MCP tools: `"allow": ["mcp__postgres__query_db"]`
6. **Test connectivity** with `claude /mcp`

---

## Project Configuration Checklist

```bash
mkdir -p .claude
touch .claude/settings.json        # Team settings (git)
touch .claude/settings.local.json  # Local secrets (gitignored)
touch .claude/.mcp.json            # MCP servers
touch .claude/CLAUDE.md            # Project instructions

# Verify
claude /config --show
claude /mcp
```
