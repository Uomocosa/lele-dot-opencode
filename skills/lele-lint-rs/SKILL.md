# lele-lint-rs — Linter Error Code Reference

How to run, interpret, and fix `lele_lint` violations.

## Run

```bash
cargo run --manifest-path ../lele_lint/Cargo.toml
```
Run from any project directory. `lele_lint` scans every `.rs` file under `src/` (finds the
nearest `Cargo.toml` and requires a `src/`).

### `--scan-folder` (scan specific folders)

```bash
# scan only the given folder(s) instead of src/ (one flag, comma-separated)
cargo run --manifest-path ../lele_lint/Cargo.toml -- --scan-folder=/src,/contract
```

- Values are **relative to the invocation directory** (a leading `/` is stripped and treated as
  root-relative). Keeps the default `find_cargo_root` behaviour when the flag is omitted.
- Scans are **aggregated into one run/report/exit-code** (one module tree; diagnostics use the
  real file paths).
- **Skips** `target/`, `.git/`, `node_modules/` directories during the walk — so pointing it at a
  cargo crate dir (e.g. `/contract`) does not descend into build artifacts.
- A listed folder that is **missing or not a directory** is an error (`NoScanFolder`); a folder
  that exists but has no `.rs` files is accepted (no diagnostics).
- Useful when the invocation root has no `Cargo.toml`/`src/` but contains sub-crates to lint
  (e.g. a workspace of contracts).

## Opt-outs

| Mechanism | Applies to | Where |
|-----------|-----------|-------|
| `// no test_usage necessary` | E006 | Last non-empty line of file |
| `// needed helper:` | E015 | Line directly above the function definition |

## Error Codes

| Code | Name | Checks |
|------|------|--------|
| E001 | atomic_file | One primary public item per file. Stem must match item's snake_case. |
| E002 | snake_case_files | All `.rs` filenames and directories under `src/` are `snake_case`. |
| E003 | method_visibility | Method files must be `mod` (private), never `pub mod` or `pub use`. |
| E004 | no_cross_domain_reexport | `pub use crate::other::Type` in `mod.rs` forbidden; use `lib.rs`. |
| E006 | test_usage | Non-exempt files need `test_usage` test or `// no test_usage necessary`. |
| E007 | test_inline | No `tests/` directories under `src/`. Tests go in the file they test. |
| E009 | no_positional | No `.0` / `.1` field access. Define structs with named fields. |
| E010 | no_trivial_accessors | Remove getters/setters that just return a `pub` field. |
| E011 | domain_import | `use crate::module;` → `module::Type`. Not `use crate::module::Type`. |
| E012 | atomic_delegates | 1-stmt methods require `#[rustfmt::skip]` on impl block. >3 stmt inherent methods must be extracted to `<type>_<method>.rs`. Trait impls with >3 stmts are skipped. |
| E013 | constructor_no_skip | `impl Default` and constructor methods must NOT use `#[rustfmt::skip]`. |
| E015 | helper_count | Max 2 unannotated private helpers. Mark each with `// needed helper:` above. |
| E016 | single_caller_type | Type with 1 caller and 0 atomic delegates → define in the caller's file. |
| E017 | method_file_co_location | `<type>_<method>.rs` must reside in the same directory as `<type>.rs`. |
| E018 | single_field_newtype | 1 field → tuple newtype `X(T)` with `#[derive(Deref)]`; ≥2 fields → named `{ a, b }`; ≥2-field tuple forbidden. Exempt: structs deriving `Serialize`/`Deserialize`/`Parser`/`Args`/`Subcommand`/`ValueEnum` (wire-shape derives). |
| E019 | mod_rs_purity | `mod.rs` may only declare `mod`/`pub mod` + `pub use`; no private `use`, impls, fns, or `#[cfg(test)]` modules. |
| E020 | no_crate_paths | `crate::` may only appear inside `use` items (e.g. `use crate::module;`); any `crate::` in expression/type/signature position outside `lib.rs`/`main.rs` is an error. |
| E021 | clippy_config_cargo | `Cargo.toml` must have `[lints.clippy]` with `pedantic/nursery = {level="deny",priority=-1}` + 13 `deny` lints (minimum). |
| E022 | clippy_config_clippy | `clippy.toml` must have `allow-unwrap-in-tests`, `allow-expect-in-tests`, `allow-panic-in-tests`, `allow-indexing-slicing-in-tests = true`. |
| E023 | no_allow_attributes | `#[allow(..)]` and `#[expect(..)]` attributes (outer and inner `#![..]`) are banned. Default on; opt out per crate with `no_allow_attributes = false` in `lele.toml [lele.lint.checkers]`. |
| E024 | root_reexport | Crate-root flattening: stutter type in `pub mod` file needs `pub use` in `lib.rs`; stutter fn-file needs private `mod` + `pub use`. |
| E025 | no_stuttered_path | No `module::Type` path where the type repeats a root-file stem — import the type once, use it bare. |
| E027 | no_stuttered_type | A `pub` type whose snake_case starts with `<parent_dir>_` must drop the prefix (e.g. `freenet::FreenetClient` → `freenet::Client`). Exempt: exact stem==dir matches (`cli::Cli`), short suffixes (<3 chars, e.g. `net_id::NetworkId`), crate-root types. |

## Per-Code Detail

### E001 — atomic_file

**Triggers when:** A file contains multiple public items (struct + function + enum), or the filename doesn't match its primary item's snake_case name.

**Fix:**
- One file per item. Name matches snake_case of the item (`PlayerEvent` → `player_event.rs`).
- If a file has a struct AND a free function, extract the function into its own file.

### E002 — snake_case_files

**Triggers when:** Filename or directory uses PascalCase (e.g. `ClickerError.rs`, `FreenetClientMethod/`).

**Fix:** Rename to `snake_case` (`clicker_error.rs`, `freenet_client_method/`).

### E003 — method_visibility

**Triggers when:** A method file (`<type>_<method>.rs`) is declared `pub mod` or re-exported via `pub use` in `mod.rs`.

**Fix:** Change to `mod <type>_<method>;` (private) and remove any `pub use` of it. Method files are consumed exclusively through the struct's atomic delegates.

### E004 — no_cross_domain_reexport

**Triggers when:** `mod.rs` contains `pub use crate::other_domain::Type`.

**Fix:** Move the re-export to `lib.rs`. `mod.rs` may only re-export items from its own directory.

### E006 — test_usage

**Triggers when:** A non-exempt file has no `test_usage` function inside a `#[cfg(test)] mod tests` block.

**Exempt:** `main.rs`, `mod.rs`/`lib.rs` (pure module trees), `constants.rs`, `tests/` directories. Type-only files (struct/enum with no inherent impls beyond `impl Default`) are also exempt. Struct files with atomic delegates are NOT exempt — they need `test_usage` or the opt-out comment.

**Fix:** Add a `test_usage` test or append `// no test_usage necessary` as the file's last non-empty line.

### E007 — test_inline

**Triggers when:** A `tests/` directory exists under `src/`.

**Fix:** Move tests into the source file they test, inside `#[cfg(test)] mod tests { ... }`. Delete the `tests/` directory.

### E009 — no_positional

**Triggers when:** `.0`, `.1` etc. field access on tuple types (including `Err(e)` in match arms, though the second field of Result is exempt).

**Fix:** Define structs with named fields instead of tuple structs.

### E010 — no_trivial_accessors

**Triggers when:** A method just returns/clones a `pub` field (e.g. `fn name(&self) -> &str { &self.name }`).

**Fix:** Delete the method. Callers access the `pub` field directly.

### E011 — domain_import

**Triggers when:** Importing a domain type directly (`use crate::clicker::Config`).

**Fix:** Import the module (`use crate::clicker;`) and use `clicker::Config`.

**Exception (paired with E025):** the direct stutter import
`use crate::{stem}::{Type};` (e.g. `use crate::test_log::TestLog;`) is
allowed — it is the required fix for an E025 hit.

### E012 — atomic_delegates

**Triggers when:**
- An impl block has 1-statement methods but no `#[rustfmt::skip]` → add `#[rustfmt::skip]`.
- An inherent impl block has methods with >3 statements → extract each into `<type>_<method>.rs`.
- Trait impls (e.g. `From`, `Display`) with >3 stmt bodies are silently skipped.

**Fix:**
- 1-stmt: add `#[rustfmt::skip]` above the impl.
- >3 inherent: extract each method body into a file `<type>_<method>.rs`, replace with a one-liner delegate.

### E013 — constructor_no_skip

**Triggers when:** `#[rustfmt::skip]` on `impl Default` or a constructor impl block (methods named `new`, `from_*`, `with_*`).

**Fix:** Remove `#[rustfmt::skip]` from the impl block. Constructors and `Default` impls carry real bodies and should be wrapped by rustfmt.

**Exempt:** pure atomic-delegate blocks — when every method in the block is a
1-statement sibling dispatch, the block is skipped by this check even if a
delegate is named `new` (e.g. `#[rustfmt::skip] impl Config {
pub fn new() -> Self { config_new::new() } }` satisfies E012 and is exempt
from E013). Only blocks containing a real (non-delegate) constructor body or
`impl Default` are flagged.

### E015 — helper_count

**Triggers when:** A file has more than 2 private, unannotated helper functions. `pub` functions and `impl` methods don't count.

**Fix:** Add `// needed helper:` on the line above each private helper function, or extract reusable helpers into proper atomic delegate files.

### E016 — single_caller_type

**Triggers when:** A type (struct/enum) defined in its own file is referenced by exactly 1 other file, and has no atomic delegate methods. A atomic delegate method counts as a separate caller (the method file is also a caller).

**Fix:** Move the type definition into the caller's file, or add a atomic delegate method to justify the separate file.

### E017 — method_file_co_location

**Triggers when:** A file named `<type_snake>_<method>.rs` does not reside in the same directory as `<type>.rs`.

**Fix:** Move the method file into the same directory as its type file. Method files are always co-located with their struct.

### E018 — single_field_newtype

**Triggers when:** A struct's field arity doesn't match the required shape:
- 1 field but defined as a **named** struct (e.g. `pub struct X { pub value: u64 }`).
- 1 field as a tuple newtype **without** `#[derive(Deref)]`.
- 2+ fields as a **tuple** struct (e.g. `pub struct Pair(pub String, pub u32)`).

**Fix:** 
- 1 field → `pub struct X(T)` with `#[derive(…, Deref)]` (from `derive_more`). Access via deref (`*x`, method calls); `DerefMut` optional.
- 2+ fields → named fields `{ a: A, b: B }`. Never use a 2+-field tuple struct.
- **Exempt:** structs deriving a wire-shape derive (`Serialize`, `Deserialize`, `Parser`, `Args`, `Subcommand`, `ValueEnum`, incl. `serde::`/`clap::`-pathed forms) keep named fields regardless of arity — field names come from the format (TOML keys / CLI flags), so the positional-access rationale doesn't apply.

### E019 — mod_rs_purity

**Triggers when:** A `mod.rs` contains anything other than `mod`/`pub mod` declarations and `pub use` re-exports — e.g. private `use` imports, structs, fns, impls, consts, or `#[cfg(test)] mod tests` blocks.

**Fix:** Declare submodules with `mod`/`pub mod` and re-export only with `pub use`. Move private imports into function files, and move `#[cfg(test)]` test modules into the file they test.

### E020 — no_crate_paths

**Triggers when:** A `crate::` path appears anywhere other than the path of a `use` item — e.g. `own_id: crate::boxes::PlayerId` in a type position, `crate::foo()` in an expression, a atomic delegate dispatching via `crate::module::fn` — in any file that is not the crate root (`lib.rs`/`main.rs`). `pub(crate)` visibilities are exempt.

**Fix:** Add a top-level `use crate::<module>;` import and reference `<module>::Item` inline, or use a `super::`-relative path for same-domain items. Keep `crate::` out of expression/type/signature positions entirely.

### E021 — clippy_config_cargo

**Triggers when:** `Cargo.toml` lacks `[lints.clippy]` or any of `pedantic`/`nursery = {level="deny",priority=-1}` or the 13 `deny` lints (`unwrap_used`, `expect_used`, `indexing_slicing`, `arithmetic_side_effects`, `unreachable`, `unimplemented`, `unchecked_time_subtraction`, `todo`, `string_slice`, `panic_in_result_fn`, `panic`, `exit`, `as_conversions`).

**Fix:** Add the minimum block to `Cargo.toml` (extendable). `workspace.lints.clippy` + `lints.workspace=true` also satisfies.

### E022 — clippy_config_clippy

**Triggers when:** `clippy.toml` missing at crate root or lacks `allow-unwrap-in-tests`, `allow-expect-in-tests`, `allow-panic-in-tests`, `allow-indexing-slicing-in-tests = true`.

**Fix:** Create `clippy.toml` with the four `true` entries. Extra keys are allowed.

### E023 — no_allow_attributes

**Triggers when:** Any `#[allow(..)]` or `#[expect(..)]` attribute appears — outer (on items, fields, variants, fns) or inner (`#![allow(..)]` at file/module top). String literals containing that text (e.g. test fixtures) are not attributes and don't trigger.

**Fix:** Remove the attribute and fix the underlying lint. There is no in-code suppression — not even `#[expect]`, which would otherwise become the unsanctioned hatch. The only relief is per-crate opt-out: `no_allow_attributes = false` in `lele.toml [lele.lint.checkers]`. Default on.

**Config:** `lele_lint` reads `<crate>/lele.toml` `[lele.lint]` (`checkers` map, same shape as the retired `lele_lint.toml`). Missing file or section → all checkers on.

### E024 — root_reexport

Two sub-rules, both about `src/*.rs` files at the crate root:

1. **Stutter type:** a `pub` struct/enum/type/alias whose snake_case equals its
   file stem (e.g. `Guard` in `guard.rs`) in a file declared `pub mod` in
   `lib.rs` must add `pub use {stem}::{Type};` to `lib.rs`. Files declared
   private `mod` are skipped by this half of the check.
2. **SHAPE-F (stutter fn-file):** a file `stem.rs` holding `pub fn stem`
   (fn snake == stem, e.g. `send_text.rs` holding `pub fn send_text`) must be
   declared **private** `mod {stem};` in `lib.rs` (never `pub mod`) **plus**
   `pub use {stem}::{name};`. Method files (`<type>_<method>.rs`, fn name !=
   stem) need only the private `mod`, no `pub use`.

**Fix:** match the file kind — struct files get `pub mod` + `pub use`;
stutter fn-files get private `mod` + `pub use`; method files get private
`mod` only.

### E025 — no_stuttered_path

**Triggers when:** a path contains adjacent `module::Type` segments where
`module` is a crate-root file stem and the type repeats the module
(e.g. `test_log::TestLog::open`). `crate::`-rooted and `::`-leading paths
are ignored here (they belong to E011/E020).

**Fix:** import the type once and use it bare. The sanctioned import is the
direct stutter form, which E011 explicitly exempts:

```rust
use crate::test_log::TestLog;

let log = TestLog::open("smoke");
```

### E027 — no_stuttered_type

**Triggers when:** A `pub`/`pub(crate)` struct or enum that is its file's E001 primary item has a snake_case name starting with `<parent_dir>_` — e.g. `FreenetClient` in `freenet/freenet_client.rs`, `P2PEvents` in `p2p/p2p_events.rs`.

**Fix:** Strip the directory prefix from the type name (`freenet::FreenetClient` → `freenet::Client`, `p2p::P2PEvents` → `p2p::Events`); the domain import (`use crate::freenet;`) already disambiguates, so the prefix adds no information.

**Exempt:** exact stem==dir matches (`cli::Cli`, `roster::Roster` — nothing to strip, rename manually if desired); stripped suffixes under 3 chars (`net_id::NetworkId` stays); types at the crate root (no parent module); non-`pub` types.

---

## Build Routine

```
cargo build --all-targets
cargo clippy -- -D warnings
cargo fmt -- --check
cargo nextest run --all-targets
cargo run --manifest-path ../lele_lint/Cargo.toml
```

Via devenv (per-crate `devenv.nix`):

```
devenv shell -- cargo build --all-targets 2>&1
devenv shell -- cargo clippy -- -D warnings 2>&1
devenv shell -- cargo fmt -- --check 2>&1
devenv shell -- cargo nextest run --all-targets 2>&1
cargo run --manifest-path ../lele_lint/Cargo.toml 2>&1
```

Via tasks (per-crate):

```
devenv tasks run lele:build 2>&1
devenv tasks run lele:clippy 2>&1
devenv tasks run lele:fmt 2>&1
devenv tasks run lele:nextest 2>&1
devenv tasks run lele:lint 2>&1
```

Always run after making changes. At the end of every non-trivial change run `cargo clippy -- -D warnings` via `devenv tasks run lele:clippy 2>&1` before `lele_lint`; fix `clippy -D warnings` first, then lint violations. **Agents NEVER run `bacon` — it is USER-ONLY.** Test both direct and `devenv shell --` invocations when devenv is present. **If `devenv.nix` defines tasks, you MUST use `devenv tasks run <task> 2>&1` — never raw `cargo`; never pipe to `| tail`/`| head`; always append `2>&1`.**
