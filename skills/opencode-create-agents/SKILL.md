---
name: opencode-create-agents
description: Create, configure, and manage opencode agents — primary (Build, Plan) and subagents invoked via @mention or Task tool. Covers frontmatter fields, permissions, file placement, and creation workflow. Works with any opencode project.
---

# Opencode Agent Operations

Teaches how agents work in opencode and how to create/customize them.

## 1. Agent Types

| Type | Usage | Invocation |
|------|-------|------------|
| **Primary** | Main assistant you interact with directly | Tab key to cycle; `switch_agent` keybind |
| **Subagent** | Specialized assistant for subtasks | `@mention` in chat, or auto-invoked by primary via Task tool |

Built-in primary agents: `build` (all tools), `plan` (read-only with `ask` permissions).
Built-in subagents: `general`, `explore` (read-only), `scout` (external docs).

## 2. File Placement

Agents are defined as markdown files. The filename (without `.md`) becomes the agent name.

- Global: `~/.config/opencode/agents/<name>.md`
- Per-project: `.opencode/agents/<name>.md`

## 3. Frontmatter Reference

```yaml
---
description: Reviews code for quality and best practices    # required
mode: subagent                                             # primary | subagent | all (default)
model: anthropic/claude-sonnet-4-20250514                  # optional, overrides global
temperature: 0.1                                           # 0.0-1.0; lower = more focused
steps: 10                                                  # max agentic iterations
top_p: 0.9                                                 # alternative to temperature
color: "#ff6b6b"                                           # hex or theme color (primary, accent, etc.)
hidden: true                                               # hide from @ autocomplete (subagent only)
disable: true                                              # disable the agent
permission:                                                # tool access control
  edit: deny
  bash: deny
  webfetch: deny
---
```

### Permission key reference

| Key | Tools it gates |
|-----|---------------|
| `read` | `read` |
| `edit` | `write`, `edit`, `apply_patch` |
| `glob` | `glob` |
| `grep` | `grep` |
| `list` | `list` |
| `bash` | `bash` |
| `task` | `task` |
| `webfetch` | `webfetch` |
| `websearch` | `websearch` |
| `lsp` | `lsp` |
| `skill` | `skill` |

Each permission key accepts: `"allow"` (no prompt), `"ask"` (prompt user), `"deny"` (disabled).

### Bash command-level permissions

```yaml
permission:
  bash:
    "*": ask
    "git status *": allow
    "grep *": allow
```

Patterns use glob matching; last matching rule wins.

## 4. Creating Agents

### Interactive command

```bash
opencode agent create
```

Prompts for: save location (global/project), description, generates system prompt, selects permissions, creates markdown file.

### Manual creation

Create a markdown file at one of the paths in §2 with frontmatter + body. The body becomes the system prompt:

```markdown
---
description: Audits code for security vulnerabilities
mode: subagent
permission:
  edit: deny
---

You are a security expert. Focus on:
- Input validation vulnerabilities
- Authentication and authorization flaws
- Data exposure risks
```

### Via opencode.json

```json
{
  "agent": {
    "code-reviewer": {
      "description": "Reviews code for best practices",
      "mode": "subagent",
      "permission": { "edit": "deny" }
    }
  }
}
```

## 5. Prompt from File

Reference an external prompt file with `{file:./path/to/prompt.txt}` (path relative to config location):

```yaml
---
prompt: "{file:./prompts/review.txt}"
---
```

## 6. Task Permissions (subagent invocation control)

Control which subagents a primary agent can invoke via the Task tool:

```yaml
permission:
  task:
    "*": deny
    "orchestrator-*": allow
    "code-reviewer": ask
```

- `deny` removes the subagent from the Task tool description entirely.
- Users can still invoke any subagent directly via `@mention`.

## 7. Subagent Navigation

- `session_child_first` (default: `<Leader>+Down`) — enter first child session
- `session_child_cycle` (default: `Right`) — next child
- `session_child_cycle_reverse` (default: `Left`) — previous child
- `session_parent` (default: `Up`) — return to parent

## 8. Common Mistakes

- **Missing `description`:** Required field; without it the agent won't work.
- **`mode` not set:** Defaults to `all`, which makes it both primary and subagent. Set explicitly.
- **Overly permissive permissions:** Start with `deny` and open only what's needed.
- **Prompt file path wrong:** `{file:...}` is relative to the config file location, not the working directory.
- **Hidden without mode subagent:** `hidden: true` only applies to `mode: subagent`.
