---
name: lele-syntax-rs
description: Use for Rust code in this project — naming, design review, atomic files, LELE0xx/LELEBEVY0xx lint. Read references/RATIONALE.md and references/SMELLS.md in full before naming/designing/reviewing/editing.
---

# lele syntax and architecture

> **MANDATORY FIRST ACTION — before naming, designing, or reviewing anything:**
> `read` `references/RATIONALE.md` and `references/SMELLS.md` (both, in full).
> The `skill` tool does not inline them; this file is not a substitute.

`lele_lint` enforces every rule that can be checked; each diagnostic carries a code —
`LELE0xx` from `lele-lint`, `LELEBEVY0xx` from `lele-bevy-lint` (`lele-lint --checker-list`,
`lele-bevy-lint --checker-list`). The old `E0xx` scheme is retired. This file is the mental
model plus how to use the linter. Do not memorise rules: ask the linter, and read
`references/RATIONALE.md` for the rules it cannot check.

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
  through deref; two or more means named fields. Positional `.0` is banned. A newtype
  wraps one **scalar** value; it never wraps a collection (`no_collection_newtype`) — a collection is held
  directly as a field. A type alias only earns its place when the underlying type is long
  or noisy (`type ModuleInfoMap = HashMap<PathBuf, ModuleInfo>;`); aliasing a short type
  (`type Entries = Vec<Entry>;`) is just repetition. Alias → name a long type only;
  newtype → distinct scalar with an invariant; struct → two or more fields. Need
  `X::from(...)`? Derive it with `derive_more::From` (`#[from(forward)]` to accept `Into`
  types); never on a type with an invariant — see RATIONALE §9.
- **Errors.** `thiserror` enums; never `unwrap`/`expect`/`panic`.
- **Tests.** Each non-trivial file carries an inline `test_usage` (or `// no test_usage necessary`).
- **No comments** in `src/`/`methods/` except `// needed helper: <why>` and the test opt-out.
- **Recursion.** A tree walk lives in an inner `fn recursion(...)` inside its public function;
  the public function owns the accumulator and returns it (RATIONALE §11).
- **Newtype purpose.** Wrap a scalar to carry an *invariant* or a *role*, never a synonym; a
  path (`PathBuf`) is already typed, so don't wrap it just to restate that (RATIONALE §12).
- **Abstraction level.** A `struct`/`enum` name is a noun (the object), a `fn` name is a verb
  (the action), a `bool` is a question; a wide-scope name is short (1–2 words) and the body
  with its narrow-scope helpers carries the mechanism (two, three, four words or more — no
  cap) (RATIONALE §13).

## 2. Working with the linter

```bash
just lint                 # or: lele-lint --config lele.toml <crate>
```

- Install the linter from `github.com/Uomocosa/lele-rust-linter`; in a workspace run it once per
  crate (`lele-lint --config lele.toml crates/<name>`).
- Every finding is an error with a code. Explain one with `lele-lint --explain <name-or-code>`
  (prints the rule with a bad/good example).
- `RULES.md` is per-repo (`crates/lele-lint/RULES.md`); never copy rule text here.
- One root `lele.toml` + `clippy.toml` per workspace; boundary `folders` are workspace-relative
  (the config file's directory is the base).
- `--sync-methods` (or `just sync-methods`) regenerates the `methods/mod.rs` indexes after you add delegates.
- A `[[lele.boundary]]` has two checks: imports (`cannot_use`; `boundary_imports`) and honesty
  (`require = "honest"`; `lele_function_taxonomy`). Ubiquitous language is guidance
  only — the linter does not check names.

## 3. `#[allow(clippy::…)]` gate

Never add `#[allow]`/`#[expect]` for `clippy::pedantic`/`clippy::nursery` — including
`Cargo.toml` global allows or file-level `#![allow]` — without explicit user approval.
When clippy objects, rewrite the code; if you cannot, stop and ask. Existing `#[allow]`
are user-gated: do not broaden them or copy them to new sites.

## 4. What the linter cannot check — READ BOTH FILES

`lele_lint` covers mechanical shape (`LELE0xx`; `LELEBEVY0xx` for Bevy — see each repo's
generated `RULES.md`: `crates/lele-lint/RULES.md`, `crates/lele-bevy-lint/RULES.md`).
Everything it cannot check lives in two reference files, and reading both is mandatory
before you design or review code:

- `references/RATIONALE.md` — **principles**: positive design rules (do this).
- `references/SMELLS.md` — **smells**: anti-patterns with bad/good examples (avoid this).

Together they are the written form of how this workspace is built — representation,
decomposition, naming. Most of "the way I program" lives in these two files.

Boundary rule: **if a smell can be detected mechanically, it does not belong in either
file — it becomes a `lele_lint` rule (`LELE0xx`; `LELEBEVY0xx` for Bevy).** Every entry
names the `LELE0xx`/`LELEBEVY0xx` that enforces part of it, or says "judgement only". Read
both before designing.
