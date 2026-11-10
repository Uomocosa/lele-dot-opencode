---
name: lele-syntax-rs
description: Use for Rust code in this project — naming, design review, atomic files, LELE0xx/LELEBEVY0xx lint. Read references/RATIONALE.md and references/SMELLS.md in full before naming/designing/reviewing/editing.
---

# lele syntax and architecture

> **MANDATORY FIRST ACTION — before naming, designing, or reviewing anything:**
> `read` `references/RATIONALE.md` and `references/SMELLS.md` (both, in full).
> The `skill` tool does not inline them; this file is not a substitute.

`lele_lint` enforces every rule that can be checked; each diagnostic carries a code —
`LELE0xx` from `lele-lint`, `LELEBEVY0xx` from `lele-bevy-lint` (`lele-lint --rule-list`,
`lele-bevy-lint --rule-list`). The old `E0xx` scheme is retired. This file is the mental
model plus how to use the linter. Do not memorise rules: ask the linter, and read
`references/RATIONALE.md` for the rules it cannot check.

## 1. Mental model

- **Domain folders.** One folder per feature under `src/` (`src/stock/`). Types, method
  bodies and systems co-locate there; there is no `structs/`/`__methods__/` split.
- **Atomic files.** One primary item per file, named after it (`config.rs` holds
  `pub struct Config`). A free `pub fn` in `src/` is an error (`no_free_functions`): make it
  a method of its first argument's type or of its return type (a newtype if neither is a
  crate type); `__bevy_systems__/` and `[[lele.lint.entry_points]]` are exempt.
- **Struct + delegate shells.** `<type>.rs` holds the struct, its `impl Default`, and the
  empty-bodied shells; bodies live in the crate-root `__methods__/<type_snake>/<method>.rs`
  (`LELE030` — mounted in `lib.rs` as `#[path = "../__methods__/mod.rs"] mod methods;`,
  private and never re-exported — bodies are reached through their type's methods, never
  `methods::…`; a single-statement body is inlined under `#[rustfmt::skip]` instead). One
  `#[atomic_delegates]` block per `impl_item_order` group — constructor shells, `pub`
  shells, `pub(crate)` shells; no block mixes groups and `new` is never delegated (`LELE032`)
  — so hand-written impls sit between the blocks in the fixed order constructors →
  trait impls → `pub` fns:

```rust
// src/clicker/click_counter.rs
#[atomic_delegates]
impl ClickCounter {
    pub fn increment(&mut self) {}
}

// __methods__/click_counter/increment.rs
pub fn increment(counter: &mut ClickCounter) {
    let next = *counter + 1;
    *counter = next;
}
```

```rust
// src/stock/unix_time.rs — shells split by group; trait impls slot between them
#[atomic_delegates]
impl UnixTime {
    pub fn from_parts(seconds: u64, nanos: u32) -> Self {}
}

#[rustfmt::skip]
impl std::fmt::Display for UnixTime {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result { write!(formatter, "{}s", self.seconds) }
}

#[atomic_delegates]
impl UnixTime {
    pub fn seconds_since(&self, earlier: &UnixTime) -> u64 {}
}
```

- **Dunder folders** are linter-enforced layout folders (`LELE038`: mounted with
  `#[path = ".../mod.rs"]` and named without the dunders everywhere in code — `basic`,
  never `__basic__`). One public path per item: `basic` items are re-exported flat from
  the domain (`RATIONALE` §4); traits and systems keep the folder in their path and are
  never re-exported (`LELE038`/`LELEBEVY001`). Two kinds; the code dunders are fully
  linted and hold one item per file:
  - **`__basic__/` (container)** — behaviour-free types by role (plain
    structs/enums/newtypes/aliases/markers), mounted `#[path = "__basic__/mod.rs"]
    mod basic;` (private) with each item re-exported flat from the domain `mod.rs`
    (`pub use basic::enums::HelloKind;` → `domain::HelloKind`; the path survives the type
    graduating to its own `hello_kind.rs`). No code, no tests; a type that gets any
    `impl` graduates to its own file.
  - **`__traits__/` (code)** — one trait per file `<trait_snake>.rs` (`LELE041`), mounted
    `#[path = "__traits__/mod.rs"] pub mod traits;` (or `pub(crate)`) and never
    re-exported — callers write `domain::traits::Greetable` and import it with
    `use crate::domain::traits::Greetable;` to call its methods (`pub use traits::…;` is a
    `LELE038` error); never a `Trait` suffix — the folder says it.
  - **`__bevy_systems__/` (code)** — Bevy systems (`LELEBEVY002`), mounted
    `#[path = "__bevy_systems__/mod.rs"] pub mod bevy_systems;` (or `pub(crate)`) and
    never re-exported (`LELEBEVY001`); Rust paths stay
    `{{module}}::bevy_systems::poll_events`.
- **Trait impls co-locate with the type** (`LELE042`): `impl Trait for LocalType` lives in
  the file that defines the type (`cfg(feature)` impls included); blanket impls and impls
  for foreign types live in the trait's `__traits__/` file. A `__basic__` type is a
  container item and keeps no impls — graduate it to its own `<type>.rs` first.
- **Imports.** Import the domain and qualify: `use crate::stock;` then `stock::Item`.
  The one exception is a trait: import it with `use crate::stock::traits::Greetable;`
  so its methods are callable. `super::` is allowed only inside `#[cfg(test)]`;
  `crate::` appears only in `use` items.
- **Struct shape.** Exactly one field means a tuple newtype with `#[derive(Deref)]`, read
  through deref; two or more means named fields. Positional `.0` is banned. A newtype
  wraps one **scalar** value; it never wraps a collection (`no_collection_newtype`) — a collection is held
  directly as a field. A type alias only earns its place when the underlying type is long
  or noisy (`type ModuleInfoMap = HashMap<PathBuf, ModuleInfo>;`); aliasing a short type
  (`type Entries = Vec<Entry>;`) is just repetition. Alias → name a long type only;
  newtype → distinct scalar with an invariant; struct → two or more fields. Need
  `X::from(...)`? Derive it with `derive_more::From` (`#[from(forward)]` to accept `Into`
  types); never on a type with an invariant — see RATIONALE §9.
- **Errors.** `thiserror` enums; never `unwrap`/`expect`/`panic`. Keep a caught error as a
  `#[source]`/`#[from]` field, never its text (`no_stringified_errors`), and never print the
  source in the variant's message (`error_message_omits_source`); a binary prints the chain.
- **Tests.** Each non-trivial file carries an inline `test_usage` (or `// no test_usage necessary`).
- **No comments** in `src/`/`__methods__/` except the final `// no test_usage necessary` opt-out.
- **Helpers are methods.** No private `fn` anywhere (`helpers_are_methods`): a helper is a
  `pub(crate)` method or associated fn of the type it serves — an `#[atomic_delegates]` shell
  (body in `__methods__/`) or an inline one-liner. In every impl block the `pub` methods come first,
  then the `pub(crate)` ones (`pub_before_crate`). A `__methods__/<type>/<method>.rs` file holds only
  `use`s, private `const`s, `pub fn <method>` and its tests (`methods_are_delegates`); internal
  types (visitors, hit records) live in `src/` as `pub(crate)`.
- **Recursion.** A tree walk lives in an inner `fn recursion(...)` inside its public function;
  the public function owns the accumulator and returns it (RATIONALE §11). It is the only inner
  `fn` allowed (`no_inner_fns`).
- **Newtype purpose.** Wrap a scalar to carry an *invariant* or a *role*, never a synonym; a
  path (`PathBuf`) is already typed, so don't wrap it just to restate that (RATIONALE §12).
- **Abstraction level.** A `struct`/`enum` name is a noun (the object), a `fn` name is a verb
  (the action), a `bool` is a question; only a *domain concept* name is short (1–2 words);
  internal machinery — even `pub`, which atomic files make almost everything — is named as
  long as needed to say what one value holds / one call does (3–7 words is normal, no cap)
  (RATIONALE §13).

## 2. Working with the linter

```bash
just lint                 # or: lele-lint --config lele.toml <crate>
```

- Install the linter from `github.com/Uomocosa/lele-rust-linter`; in a workspace run it once per
  crate (`lele-lint --config lele.toml crates/<name>`).
- Every finding is an error with a code. Explain one with `lele-lint --explain <name-or-code>`
  (prints the rule with a bad/good example).
- The rule index, one line per rule with the fix to apply, is the generated
  `lele-lint-rules-rs` skill. Load it whenever you clear lint errors.
- `RULES.md` is per-repo (`crates/lele-lint/RULES.md`); never copy rule text here.
- One root `lele.toml` + `clippy.toml` per workspace; boundary `folders` are workspace-relative
  (the config file's directory is the base).
- `--sync-methods` (or `just sync-methods`) regenerates the `__methods__/mod.rs` indexes after you add delegates.
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
