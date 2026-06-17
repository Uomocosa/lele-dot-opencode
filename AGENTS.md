# Global OpenCode Architecture

This file documents the global skill/agent/command architecture. It applies to every opencode session.

## Skill Architecture

Skills live in `~/.config/opencode/skills/<name>/SKILL.md` and are organized into three tiers:

| Tier | Naming | Location | Visibility |
|---|---|---|---|
| **General** | `opencode-*` | `~/.config/opencode/skills/` | Always listed, never auto-loaded |
| **Language-specific** | `*-py`, `*-rs`, `*-ts` | `~/.config/opencode/skills/` | Listed per-project via permissions |
| **Multi-language tool** | `*-(language_fullname)` e.g. `grpc-rust`, `grpc-python` | `~/.config/opencode/skills/` | Listed per-project via permissions |
| **Project-specific** | Any valid name | `.opencode/skills/` in repo | Listed for that project only |

Tool-name skills (bare, no suffix) like `pixi`, `bevy`, ... are treated as general.

The `*-(language_fullname)` pattern is for tools available in multiple languages. Unlike the compact `*-rs`/`*-py` suffixes, use the full language name so the tool name is distinct.

**Disambiguation rule:** The `-{{language_fullname}}` suffix is mandatory when the same tool has two or more language-specific skills in this project's `<available_skills>` (e.g., both `grpc-rust` and `grpc-python` exist). If only one variant of a tool exists in this project, the bare name is mandatory — do NOT add a gratuitous suffix (e.g., `libp2p`, `pixi`, `bevy` are bare because each has exactly one skill). The `<available_skills>` list is the sole authority for this determination — external implementations in other languages are irrelevant.

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
