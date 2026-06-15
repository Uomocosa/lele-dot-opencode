---
name: plan-remove-dead-code-rs
description: Find .rs files whose primary pub item has zero internal consumers in src/. Detects removal candidates by searching for use crate:: references, then presents them for user evaluation.
disable-model-invocation: true
---

## Goal
Find and report files whose primary `pub` item has zero internal consumers in the codebase.

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
