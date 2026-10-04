---
name: lele-syntax-rs
description: Use for Rust code in this project. Atomic files, domain folders, #[atomic_delegates] bodies in methods/, __basic__/ containers, bevy_systems/, domain-prefix imports, test_usage, thiserror, struct field shape. lele_lint enforces these; this skill is the mental model and the linter workflow, with judgement rules in references/RATIONALE.md.
---

# lele syntax and architecture

`lele_lint` enforces every rule that can be checked; each diagnostic carries an `E0xx`
code. This file is the mental model plus how to use the linter. Do not memorise rules:
ask the linter, and read `references/RATIONALE.md` for the rules it cannot check.

## 1. Mental model

- **Domain folders.** One folder per feature under `src/` (`src/stock/`). Types, method
  bodies and systems co-locate there; there is no `structs/`/`methods/` split.
- **Atomic files.** One primary item per file, named after it (`greet.rs` holds
  `pub fn greet`; `config.rs` holds `pub struct Config`).
- **Struct + delegate shells.** `<type>.rs` holds the struct, its `impl Default`, and one
  `#[atomic_delegates]` shell block; method bodies live in `methods/<type_snake>/<method>.rs`
  (a single-statement body is inlined under `#[rustfmt::skip]` instead).

```rust
// src/clicker/click_counter.rs
#[atomic_delegates]
impl ClickCounter {
    pub fn increment(&mut self) {}
}

// methods/click_counter/increment.rs
pub fn increment(counter: &mut ClickCounter) {
    let next = *counter + 1;
    *counter = next;
}
```

- **`__basic__/`** holds behaviour-free types (plain structs/enums/newtypes/aliases/markers),
  surfaced as the domain's `basic` module via `#[path = "__basic__/mod.rs"]`. A type with
  any `impl` graduates to its own file.
- **`bevy_systems/`** holds Bevy systems, flattened with `pub use`, so callers write
  `{{module}}::bevy_systems::poll_events`.
- **Imports.** Import the domain and qualify: `use crate::stock;` then `stock::Item`.
  `super::` is allowed only inside `#[cfg(test)]`; `crate::` appears only in `use` items.
- **Struct shape.** Exactly one field means a tuple newtype with `#[derive(Deref)]`, read
  through deref; two or more means named fields. Positional `.0` is banned.
- **Errors.** `thiserror` enums; never `unwrap`/`expect`/`panic`.
- **Tests.** Each non-trivial file carries an inline `test_usage` (or `// no test_usage necessary`).
- **No comments** in `src/`/`methods/` except `// needed helper: <why>` and the test opt-out.

## 2. Working with the linter

```bash
devenv tasks run lele:lint 2>&1
```

- Every finding is an error with a code. Explain one with
  `devenv shell -- cargo run --manifest-path ../lele_lint/Cargo.toml -- --explain E0xx`
  (prints the rule with a bad/good example).
- The full list is generated into `../lele_lint/RULES.md`; never copy rule text here.
- `--sync-methods` regenerates the `methods/mod.rs` indexes after you add delegates.
- A `[[lele.boundary]]` has two checks: imports (`cannot_use`; E036) and honesty
  (`require = "honest"`; `lele_function_taxonomy`). Ubiquitous language is guidance
  only — the linter does not check names.

## 3. `#[allow(clippy::…)]` gate

Never add `#[allow]`/`#[expect]` for `clippy::pedantic`/`clippy::nursery` — including
`Cargo.toml` global allows or file-level `#![allow]` — without explicit user approval.
When clippy objects, rewrite the code; if you cannot, stop and ask. Existing `#[allow]`
are user-gated: do not broaden them or copy them to new sites.

## 4. What the linter cannot check

Judgement rules live in `references/RATIONALE.md`: one function one job, ubiquitous
language, functional core / imperative shell, group by feature, parse don't validate,
Screenplay E2E and turmoil, test vocabulary. Read it before designing, not before linting.
