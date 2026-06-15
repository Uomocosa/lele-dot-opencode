# Global OpenCode Architecture

This file documents the global skill/agent/command architecture. It applies to every opencode session.

## Skill Architecture

Skills live in `~/.config/opencode/skills/<name>/SKILL.md` and are organized into three tiers:

| Tier | Naming | Location | Loaded when |
|---|---|---|---|
| **General** | `opencode-*` | `~/.config/opencode/skills/` | Always (any project) |
| **Language-specific** | `*-py`, `*-rs`, `*-ts` | `~/.config/opencode/skills/` | Filtered per-project via permissions |
| **Multi-language tool** | `*-(language_fullname)` e.g. `grpc-rust`, `grpc-python` | `~/.config/opencode/skills/` | Filtered per-project via permissions |
| **Project-specific** | Any valid name | `.opencode/skills/` in repo | That project only |

Tool-name skills (bare, no suffix) like `pixi`, `bevy`, ... are treated as general.

The `*-(language_fullname)` pattern is for tools available in multiple languages. Unlike the compact `*-rs`/`*-py` suffixes, use the full language name so the tool name is distinct.

**Disambiguation rule:** Only use the `-{{language_fullname}}` suffix when a tool exists in two or more languages (e.g., `grpc-rust`, `grpc-python`). If a tool only has a single implementation, use the bare name (e.g., `libp2p`, `pixi`, `bevy`).

**Tool permission rule:** Tool skills — both bare-name (`pixi`, `libp2p`) and multi-language (`grpc-rust`) — are NOT matchable by glob patterns. They must be listed by their exact full name in `permission.skill`:
```json
{ "pixi": "allow", "libp2p": "allow", "grpc-rust": "allow" }
```
Only the `opencode-*` and `*-py`/`*-rs`/`*-ts` patterns support glob matching. This prevents accidental inclusion of unrelated tool skills.

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
