---
name: plan-remove-dead-code-rs
description: "Use when searching for Rust files whose primary pub item has zero internal consumers in a crate's src/. Searches for internal use references, then presents candidates for user evaluation."
---

## Goal
Find and report files whose primary `pub` item has zero internal consumers in the codebase.

## Phase −1 — CRITICAL setup (blocking)
Run `~/.config/opencode/skills/lele-rs/references/WORKFLOW_SETUP.md` in full before searching:
load the listed skills, read RATIONALE.md + SMELLS.md + `lele-lint --rules-md` (+
`lele-bevy-lint --emit rules-md` for Bevy crates), run the **baseline** `just lint|bevy-lint|clippy`,
and open the first reply with the **Setup:** proof block. The lele layout changes what a
"consumer" is: `mod.rs` `pub use` flattening, `__basic__/` re-exports, `bevy_systems/` systems
registered only in a plugin, and `methods/` delegate bodies reached through `#[atomic_delegates]`
shells are all normal — none of them proves an item is used, and none proves it is dead.

## Also dead
A value that is **constructed but never read** — a resource inserted and written but never
queried, a config field stored but never consumed, a constant defined but never referenced —
is a removal candidate even though its name has references. Grep for *reads*.

## Detection Method
For each `.rs` file in `src/` containing a `pub struct`, `pub enum`, `pub fn`, or `pub type`:

1. Identify the item name.
2. Search `src/` for all of these patterns:
   - `use crate::` references to that name.
   - `pub use` re-exports of that name (in any `mod.rs` or `lib.rs`).
   - `mod` declarations that reference the file (in any `mod.rs` or `lib.rs`).
   - Imports guarded by `#[cfg(test)]` or `#[cfg(feature = "...")]` blocks.
3. Exclude the file's own `mod.rs` declaration and its own `pub use` re-export.
4. If zero external references remain, the file is a removal candidate.
5. Before finalizing, check for string-based references (e.g., `"Module::Item"` or `"item_name"` in type registries, plugin names, or reflection patterns) — flag these for user review rather than skipping automatically.

## Exemptions
- Items explicitly intended as public API for external crate consumers. Determine this by checking:
  - Is the item re-exported from `lib.rs` or a top-level `mod.rs`?
  - Does the item appear in the crate's public doc examples or README?
  - When uncertain, ask the user rather than assuming.
- Do not remove public API surface without explicit confirmation.

## Dry-Run Mode
Before any deletion, list all candidates and present them for confirmation:
- Show file path, primary item name, and zero-consumer count.
- Present all candidates together as a group and require explicit user approval before proceeding.
- Skipping user approval is a violation.

## Verification
After removal, run:
```
[[AGENTS.md::RUN_ALL_TESTS]]
```
(Resolved from `## Project Commands` in AGENTS.md.)
