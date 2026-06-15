---
name: opencode-create-commands
description: Create custom opencode slash commands (/command) for repetitive tasks. Covers markdown and JSON config, template placeholders ($ARGUMENTS, $1-$N), shell injection (!`cmd`), file references (@file), and agent/model routing. Works with any opencode project.
---

# Opencode Command Craft

Teaches how to create and manage custom opencode commands.

## 1. What Custom Commands Are

Custom commands are user-defined slash commands that send a prompt template to the LLM when invoked in the TUI:

```
/my-command
```

They're useful for repetitive tasks: running tests, creating components, reviewing changes, etc.

## 2. File Placement

Create markdown files in a `commands/` directory. The filename (without `.md`) becomes the command name.

- Global: `~/.config/opencode/commands/<name>.md`
- Per-project: `.opencode/commands/<name>.md`

## 3. Frontmatter Reference

```yaml
---
description: Run tests with coverage    # shown in TUI autocomplete
agent: build                            # optional, which agent executes (default: current)
model: anthropic/claude-sonnet-4-20250514  # optional, override model
subtask: true                           # optional, force subagent invocation
---
```

The body of the markdown file becomes the prompt template.

### Example

`~/.config/opencode/commands/review.md`:

```markdown
---
description: Review recent changes for issues
agent: plan
---

Review the recent changes in this diff and flag any issues:
- Potential bugs or regressions
- Performance concerns
- Security implications
- Style or maintainability problems
```

Usage: `/review`

## 4. JSON Configuration

Commands can also be defined in `opencode.json`:

```jsonc
{
  "command": {
    "test": {
      "template": "Run the full test suite and report failures.\nSuggest fixes for any failing tests.",
      "description": "Run tests with coverage",
      "agent": "build",
      "model": "anthropic/claude-sonnet-4-20250514"
    }
  }
}
```

## 5. Template Placeholders

### Arguments

| Placeholder | Expands to |
|-------------|-----------|
| `$ARGUMENTS` | All arguments passed after the command name |
| `$1`, `$2`, `$3`... | Individual positional arguments |

Example — `.opencode/commands/component.md`:

```markdown
---
description: Create a new React component
---

Create a new React component named $1 with TypeScript support.
Include proper typing, a test file, and Stories.
```

Usage: `/component Button` → `$1` becomes `Button`

### Shell Output Injection

Use `` !`command` `` to inject the output of a bash command into the prompt:

```markdown
---
description: Analyze test failures
---

Current test failures:

!`your-project test --with-args 2>&1 | tail -50`

Analyze these failures and suggest fixes.
```

Commands run in the project root directory.

### File References

Use `@filename` to include file contents:

```markdown
---
description: Review a specific component
---

Review the component in @path/to/your/file.ext.
Check for performance issues, accessibility problems, and suggest improvements.
```

## 6. Agent Routing

- If `agent` is a **subagent**, the command triggers a subagent invocation by default.
- Set `subtask: false` to disable this and run in the current agent instead.
- Set `subtask: true` to force subagent invocation even for primary agents.

## 7. Overriding Built-in Commands

Custom commands can override built-in commands (like `/init`, `/help`) by using the same name. Use with caution.

## 8. Common Mistakes

- **Leading slash in filename:** Not needed. The command name is the filename without `.md`. The `/` is added automatically in the TUI.
- **Missing `$ARGUMENTS` or `$1`:** If your command expects arguments but the template doesn't reference them, the args are silently ignored.
- **Shell injection without quoting:** `` !`command` `` captures stdout. For multi-line output, pipe or redirect inside the backticks.
- **Agent name typo:** If the agent specified in frontmatter doesn't exist, the command defaults to the current agent with no error.
- **`subtask: true` on non-subagent:** Forces a subagent session for the command, keeping the primary context clean.
- **`mode` is invalid in command frontmatter:** `mode` (`primary`/`subagent`/`all`) is for **agents only**, not commands. The JSON schema rejects unknown command fields (`additionalProperties: false`). Use `subtask: true` to force subagent invocation, or set `agent` to a subagent.
