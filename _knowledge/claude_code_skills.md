# Claude Code Skills (Slash Commands) - Complete Reference

Skills are reusable prompts that extend Claude's capabilities. They're `.md` files with optional YAML frontmatter that give Claude instructions for handling specific tasks. Invoke with `/skill-name` or Claude can load them automatically when relevant.

---

## File Structure

```
my-skill/
  SKILL.md           # Required: main instructions with frontmatter
  template.md        # Optional: template for Claude to fill in
  reference.md       # Optional: detailed docs
  scripts/           # Optional: executable scripts
  examples/          # Optional: example outputs
```

### SKILL.md Format

```markdown
---
name: my-skill
description: What this skill does (max 250 chars displayed)
argument-hint: "[component-name] [from] [to]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read Grep Edit Write Bash
model: claude-opus-4-6-20250514
effort: high
context: fork
agent: Explore
paths: "src/**/*.ts,lib/**/*.js"
---

Skill content / instructions here...

Use $ARGUMENTS for all args, or $0, $1, $2 for positional args.
```

---

## Frontmatter Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | No | string | Display name, uses directory name if omitted. Lowercase, numbers, hyphens (max 64 chars) |
| `description` | Recommended | string | What the skill does. Claude uses this to decide when to load it. Truncated at 250 chars |
| `argument-hint` | No | string | Shown during autocomplete. E.g. `[issue-number]` |
| `disable-model-invocation` | No | boolean | If true, only user can invoke via `/`. Default: false |
| `user-invocable` | No | boolean | If false, hides from `/` menu. Only Claude can invoke. Default: true |
| `allowed-tools` | No | string/list | Tools Claude can use without asking. Space-separated or YAML list |
| `model` | No | string | Override session model while skill is active |
| `effort` | No | enum | `low`, `medium`, `high`, `max` (Opus only) |
| `context` | No | enum | `fork` to run in isolated subagent context |
| `agent` | No | string | Subagent type when `context: fork`. E.g. `Explore`, `Plan` |
| `hooks` | No | object | Hooks scoped to this skill's lifecycle |
| `paths` | No | string/list | Glob patterns limiting when Claude loads this skill |
| `shell` | No | enum | `bash` (default) or `powershell` |

---

## File Locations and Scope

| Location | Path | Scope | Shareable |
|----------|------|-------|-----------|
| Enterprise | Managed settings | All users in org | Yes (admin) |
| Personal | `~/.claude/skills/<name>/SKILL.md` | All your projects | No |
| Project | `.claude/skills/<name>/SKILL.md` | This project only | Yes (git) |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | Where plugin enabled | Yes |

Priority: Enterprise > Personal > Project > Plugin

---

## Arguments

```bash
/fix-issue 123                    # $ARGUMENTS = "123", $0 = "123"
/migrate-component Foo React Vue  # $0 = "Foo", $1 = "React", $2 = "Vue"
```

Available substitution variables:
- `$ARGUMENTS` - all arguments as single string
- `$ARGUMENTS[N]` or `$N` - specific argument (0-based)
- `${CLAUDE_SESSION_ID}` - unique session ID
- `${CLAUDE_SKILL_DIR}` - path to skill's directory

---

## Built-in Skills

| Skill | Purpose |
|-------|---------|
| `/batch <instruction>` | Orchestrate large-scale changes across codebase (5-30 parallel agents) |
| `/claude-api` | Load Claude API reference and Agent SDK docs |
| `/debug [description]` | Enable debug logging for session |
| `/loop [interval] <prompt>` | Run a prompt repeatedly on interval |
| `/simplify [focus]` | Review changed files for code quality (3 parallel review agents) |

---

## Dynamic Context Injection

Use `` !`command` `` to inject live data before Claude sees the skill:

```markdown
---
name: deploy-status
---

Current commits:
!`git log --oneline -10`

Latest tag:
!`git describe --tags --latest`
```

Commands run immediately before Claude receives the prompt.

---

## Example Skills

### Commit Message Generator

```markdown
---
name: commit
description: Create a well-formatted git commit
disable-model-invocation: true
allowed-tools: Bash(git *)
---

Create a git commit following Conventional Commits format:
- feat: / fix: / docs: / refactor: / test: / chore:

1. Review staged changes: `git diff --cached`
2. Craft a clear message
3. Commit

Changes: $ARGUMENTS
```

### PR Summary (forked context)

```markdown
---
name: pr-summary
description: Summarize current pull request
context: fork
agent: Explore
allowed-tools: Bash(gh *)
disable-model-invocation: true
---

Fetch and summarize the current PR:
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`

Provide: what changed, why it matters, risks, what to test.
```

### Background Knowledge (auto-loaded)

```markdown
---
name: api-conventions
description: API design patterns for this project
user-invocable: false
---

All endpoints return JSON: {"data": ..., "meta": ..., "errors": null}
Use RESTful resource naming. Use HTTP verbs for actions.
```

---

## Skills vs Hooks

| Aspect | Skills | Hooks |
|--------|--------|-------|
| **Triggered by** | User (`/skill-name`) or Claude (auto) | System events |
| **Purpose** | Give Claude instructions | Automate deterministic actions |
| **Type** | Prompt-based (LLM reasoning) | Script-based (shell/HTTP) |
| **Decision** | LLM judged | Rule-based (exit codes) |
| **Side effects** | Anything Claude's tools allow | Anything a shell script can do |
| **Control** | Optional | Mandatory when conditions match |

---

## Best Practices

1. **Front-load descriptions** with the key use case (first 250 chars matter)
2. **Use `disable-model-invocation: true`** for skills with side effects (deploy, send messages)
3. **Restrict tool access** when possible with `allowed-tools`
4. **Keep SKILL.md under 500 lines** - move details to supporting files
5. **Use `context: fork`** for isolated research tasks
6. **Use supporting files** for templates and examples rather than inlining
7. **Name skills for direct invocation** - clear, actionable names (`/deploy`, `/review-pr`)
8. **Document argument expectations** with `argument-hint`
