# Global OpenCode Architecture

This file documents the global skill/agent/command architecture. It applies to every opencode session.

## Skill Loading (MUST)

Before answering any question, proposing a plan, or modifying code:
1. Review `<available_skills>` in your system prompt
2. Load every skill whose description overlaps with the current topic
3. Proceed only after loading matching skills

When in doubt, load it — an irrelevant skill costs little context; a skipped
skill costs correctness.

## Skill Architecture

Skills live in `~/.config/opencode/skills/<name>/SKILL.md` and are organized into three tiers:

| Tier | Naming | Location | Visibility |
|---|---|---|---|
| **General — opencode** | `opencode-*` | `~/.config/opencode/skills/` | Always listed, never auto-loaded |
| **General — definitions** | `definition-*` | `~/.config/opencode/skills/` | Always listed, never auto-loaded |
| **Language-specific** | `*-rs`, `*-py`, `*-ts` | `~/.config/opencode/skills/` | Listed per-project via permissions |
| **Language-agnostic tool** | `{{tool_name}}` (bare, no suffix) | `~/.config/opencode/skills/` | Always listed, never auto-loaded |
| **Project-specific** | Any valid name | `.opencode/skills/` in repo | Listed for that project only |

**Naming rules:**

* **General — opencode (`opencode-*`):** General opencode workflow/tooling skills (e.g., `opencode-git-workflow`, `opencode-mcp`, `opencode-create-skill`). Always general, never language-specific.
* **General — definitions (`definition-*`):** General language-agnostic definitions and pseudocode (e.g., `definition-function-taxonomy`). Always general, never language-specific.
* **Language-specific (`*-rs`, `*-py`, `*-ts`):** Any skill whose content is tied to a single language MUST carry the suffix — this includes language-specific tools/crates (e.g., `bevy-rs`, `avian-rs` are Rust crates) and convention skills (e.g., `lele-syntax-rs`). A language-specific skill without a suffix is a violation.
* **Language-agnostic tool (bare `{{tool_name}}`):** A tool available independent of language (protocol, platform, or cross-language tool) MUST be bare with no suffix (e.g., `libp2p`, `freenet`). Adding `-rs`/`-py`/`-ts` to a language-agnostic tool is a violation. Main example: `libp2p` stays `libp2p`, not `libp2p-rs`.

No `*-(language_fullname)` multi-variant pattern — if a tool ships as a Rust crate, it is `*-rs`; the agnostic protocol is the bare name.

**Tool permission rule:** Language-agnostic bare tools (`libp2p`, `freenet`, `pixi`) are NOT matchable by glob patterns. They must be listed by their exact full name in `permission.skill`:
```json
{ "pixi": "allow", "libp2p": "allow", "freenet": "allow" }
```
Only the `opencode-*`, `definition-*`, and `*-rs`/`*-py`/`*-ts` patterns support glob matching. This prevents accidental inclusion of unrelated tool skills.

## Per-Project Filtering

Each project's `opencode.json` can select which global skills are visible:

```json
{
  "permission": {
    "skill": {
      "*": "deny",
      "opencode-*": "allow",
      "definition-*": "allow",
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
