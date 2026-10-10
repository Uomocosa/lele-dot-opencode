# Global OpenCode Architecture

This file documents the global skill/agent architecture (opencode v2). It applies to every opencode session.

## Skill Loading (MUST)

Skills are auto-discovered from `~/.config/opencode/skills/` and `.opencode/skills/` and
advertised by their `description`; load them on demand with the `skill` tool. Nothing is
preloaded — v2 accepts `instructions[]` in the config but does **not** load it; always-on
content lives in `AGENTS.md`.

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
| **Legacy (superseded)** | `*-legacy` | `~/.config/opencode/skills/` | Hidden by default; requires an exact `allow` |
| **Project-specific** | Any valid name | `.opencode/skills/` in repo | Listed for that project only |

**Naming rules:**

* **General — opencode (`opencode-*`):** General opencode workflow/tooling skills (e.g., `opencode-git-workflow`, `opencode-mcp`, `opencode-create-skill`). Always general, never language-specific.
* **General — definitions (`definition-*`):** General language-agnostic definitions and pseudocode (e.g., `definition-function-taxonomy`). Always general, never language-specific.
* **Language-specific (`*-rs`, `*-py`, `*-ts`):** Any skill whose content is tied to a single language MUST carry the suffix — this includes language-specific tools/crates (e.g., `bevy-rs`, `avian-rs` are Rust crates) and convention skills (e.g., `lele-syntax-rs`). A language-specific skill without a suffix is a violation.
* **Language-agnostic tool (bare `{{tool_name}}`):** A tool available independent of language (protocol, platform, or cross-language tool) MUST be bare with no suffix (e.g., `libp2p`, `freenet`). Adding `-rs`/`-py`/`-ts` to a language-agnostic tool is a violation. Main example: `libp2p` stays `libp2p`, not `libp2p-rs`.
* **Legacy (`*-legacy`):** A superseded skill kept for old crates (e.g. `devenv-rs-legacy`). The name matches no allow glob, so it is hidden by default and must be listed by exact name to be loaded — this keeps stale tooling out of new work.

No `*-(language_fullname)` multi-variant pattern — if a tool ships as a Rust crate, it is `*-rs`; the agnostic protocol is the bare name.

**Tool permission rule:** Language-agnostic bare tools (`libp2p`, `freenet`, `pixi`) and `*-legacy` skills are NOT matchable by glob patterns. They must be listed by their exact full name as `skill` rules in `permissions`:
```json
{ "action": "skill", "resource": "libp2p", "effect": "allow" }
```
Only the `opencode-*`, `definition-*`, and `*-rs`/`*-py`/`*-ts` patterns support glob matching. This prevents accidental inclusion of unrelated tool skills.

## Per-Project Filtering

Each project's `opencode.json` can select which global skills are visible:

```json
{
  "permissions": [
    { "action": "skill", "resource": "*", "effect": "deny" },
    { "action": "skill", "resource": "opencode-*", "effect": "allow" },
    { "action": "skill", "resource": "definition-*", "effect": "allow" },
    { "action": "skill", "resource": "*-py", "effect": "allow" },
    { "action": "skill", "resource": "pixi", "effect": "allow" }
  ]
}
```

Last matching rule wins. Skills with `deny` are hidden from the agent entirely.

## Agents

Custom agents live in `~/.config/opencode/agents/<name>.md` and are available in every project.

## Past Conversations

Past important conversation summaries are saved repo-wide in `projects/.opencode/summaries/` as `YYYY_MM_DD_HH_MM-<slug>.md` (autosorted). Read the most recent file there (`ls -t projects/.opencode/summaries/ | head -1`) for context. Writing a summary never commits.

## CRITICAL: Commit Authorization

**NEVER stage, commit, push, merge, rebase, or amend anything without an explicit command from the user.** An "explicit command" means a direct statement like "commit", "stage that file", "push to origin", or "merge the PR". Implied intent, "go ahead", or silence does NOT count. When in doubt, ask. This rule overrides all other instructions in this file.

## CRITICAL: Task Runner — NO PIPE

**NEVER pipe a task runner (`just`, `devenv tasks run`) to `| tail`, `| head`, `| grep`, or any pipe.** Legacy devenv tasks use `showOutput = true` and stream correctly via bare `devenv tasks run <task> 2>&1`; `just` streams too. Pipes swallow output; `tail` on a fresh `cargo` task (zero `stdout` lines until `Finished`) blocks the full 120s timeout with `(no output)` and hides diagnostics (`cargo` writes to `stderr`, caller must add `2>&1`). Always append `2>&1` on the caller — never `| tail`/`| head`.

## CRITICAL: Git Hooks

**If any git hook fails (pre-commit, pre-push, commit-msg, etc.), STOP immediately.** Do not retry, amend, or bypass the failure. Inspect the hook output, identify the root cause, and **propose a concrete solution** for the failure before proceeding. **NEVER run with `--no-verify` / `-n` (or `SKIP=*`) to bypass hooks unless explicitly prompted to do so by the user.** Bypassing is only allowed on direct user instruction, and must be confirmed.

## CRITICAL: Code Snippets — ALWAYS SHOW CODE (DEFAULT-ON, NON-NEGOTIABLE)

Whenever ANY response discusses code, behavior, structure, or a fix — in MOST conversations — you MUST include a concrete fenced code snippet. Prose alone is a violation. This rule overrides any instinct to summarize. The code preview IS the deliverable — a description of an edit is not a substitute for the edit.
- Preview rule: before proposing or making ANY edit, show the literal code the user will receive — not a diff sketch, not a TODO, not "I'll extract X".
- Before/after is mandatory when editing or proposing: every change = a fenced block with BEFORE then AFTER, each citing `path/to/file.rs:line` (from your own `Read`/`Grep`, never from memory). A proposal without before/after is INVALID.
- Coverage: if a change touches N sites, show all N — or one representative plus the exact count and every location. No silent edits.
- Trigger: mentioning a function, file, type, pattern, bug, fix, plan, or review → show code. Only pure non-code chat (scheduling, opinions with no code referent) is exempt, and then say nothing about code.
- Format: fenced block with language tag (```rust, ```toml, ```nix, ```bash), minimal and copy-pasteable. Show real code, never a hypothetical sketch.
- Grounding: new code is labelled `proposed` + target path.
- No-snippet responses about code are forbidden. If you cannot show code, you MUST name the exact file you would need to read first and stop.
