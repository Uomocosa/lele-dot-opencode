# Global OpenCode Architecture

This file documents the global skill/agent/command architecture. It applies to every opencode session.

## Skill Architecture

Skills live in `~/.config/opencode/skills/<name>/SKILL.md` and are organized into three tiers:

| Tier | Naming | Location | Loaded when |
|---|---|---|---|
| **General** | `opencode-*` | `~/.config/opencode/skills/` | Always (any project) |
| **Language-specific** | `*-py`, `*-rs`, `*-ts` | `~/.config/opencode/skills/` | Filtered per-project via permissions |
| **Project-specific** | Any valid name | `.opencode/skills/` in repo | That project only |

Tool-name skills (bare, no suffix) like `pixi`, `bevy`, ... are treated as general.

## Per-Project Filtering

Each project's `opencode.json` can select which global skills are visible:

```json
{
  "permission": {
    "skill": {
      "*": "deny",
      "opencode-*": "allow",
      "*-py": "allow",
      "pixi": "allow"
    }
  }
}
```

Last matching rule wins. Skills with `deny` are hidden from the agent entirely.

## Commands

Custom slash commands live in `~/.config/opencode/commands/<name>.md` and are available in every project. 

## Agents

Custom agents live in `~/.config/opencode/agents/<name>.md` and are available in every project.

## CRITICAL: Commit Authorization

**NEVER stage, commit, push, merge, rebase, or amend anything without an explicit command from the user.** An "explicit command" means a direct statement like "commit", "stage that file", "push to origin", or "merge the PR". Implied intent, "go ahead", or silence does NOT count. When in doubt, ask. This rule overrides all other instructions in this file.
