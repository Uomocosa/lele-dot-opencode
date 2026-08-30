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
| E012 | thin_delegates | 1-stmt methods require `#[rustfmt::skip]` on impl block. >3 stmt inherent methods must be extracted to `<type>_<method>.rs`. Trait impls with >3 stmts are skipped. |
| E013 | constructor_no_skip | `impl Default` and constructor methods must NOT use `#[rustfmt::skip]`. |
| E015 | helper_count | Max 2 unannotated private helpers. Mark each with `// needed helper:` above. |
| E016 | single_caller_type | Type with 1 caller and 0 thin delegates → define in the caller's file. |
| E017 | method_file_co_location | `<type>_<method>.rs` must reside in the same directory as `<type>.rs`. |
| E018 | single_field_newtype | 1 field → tuple newtype `X(T)` with `#[derive(Deref)]`; ≥2 fields → named `{ a, b }`; ≥2-field tuple forbidden. |
| E019 | mod_rs_purity | `mod.rs` may only declare `mod`/`pub mod` + `pub use`; no private `use`, impls, fns, or `#[cfg(test)]` modules. |
| E020 | no_crate_paths | `crate::` may only appear inside `use` items (e.g. `use crate::module;`); any `crate::` in expression/type/signature position outside `lib.rs`/`main.rs` is an error. |
| E021 | clippy_config_cargo | `Cargo.toml` must have `[lints.clippy]` with `pedantic/nursery = {level="deny",priority=-1}` + 13 `deny` lints (minimum). |
| E022 | clippy_config_clippy | `clippy.toml` must have `allow-unwrap-in-tests`, `allow-expect-in-tests`, `allow-panic-in-tests`, `allow-indexing-slicing-in-tests = true`. |

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

**Fix:** Change to `mod <type>_<method>;` (private) and remove any `pub use` of it. Method files are consumed exclusively through the struct's thin delegates.

### E004 — no_cross_domain_reexport

**Triggers when:** `mod.rs` contains `pub use crate::other_domain::Type`.

**Fix:** Move the re-export to `lib.rs`. `mod.rs` may only re-export items from its own directory.

### E006 — test_usage

**Triggers when:** A non-exempt file has no `test_usage` function inside a `#[cfg(test)] mod tests` block.

**Exempt:** `main.rs`, `mod.rs`/`lib.rs` (pure module trees), `constants.rs`, `tests/` directories. Struct files with thin delegates may also be exempt.

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

### E012 — thin_delegates

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

### E015 — helper_count

**Triggers when:** A file has more than 2 private, unannotated helper functions. `pub` functions and `impl` methods don't count.

**Fix:** Add `// needed helper:` on the line above each private helper function, or extract reusable helpers into proper thin delegate files.

### E016 — single_caller_type

**Triggers when:** A type (struct/enum) defined in its own file is referenced by exactly 1 other file, and has no thin delegate methods. A thin delegate method counts as a separate caller (the method file is also a caller).

**Fix:** Move the type definition into the caller's file, or add a thin delegate method to justify the separate file.

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

### E019 — mod_rs_purity

**Triggers when:** A `mod.rs` contains anything other than `mod`/`pub mod` declarations and `pub use` re-exports — e.g. private `use` imports, structs, fns, impls, consts, or `#[cfg(test)] mod tests` blocks.

**Fix:** Declare submodules with `mod`/`pub mod` and re-export only with `pub use`. Move private imports into function files, and move `#[cfg(test)]` test modules into the file they test.

### E020 — no_crate_paths

**Triggers when:** A `crate::` path appears anywhere other than the path of a `use` item — e.g. `own_id: crate::boxes::PlayerId` in a type position, `crate::foo()` in an expression, a thin delegate dispatching via `crate::module::fn` — in any file that is not the crate root (`lib.rs`/`main.rs`). `pub(crate)` visibilities are exempt.

**Fix:** Add a top-level `use crate::<module>;` import and reference `<module>::Item` inline, or use a `super::`-relative path for same-domain items. Keep `crate::` out of expression/type/signature positions entirely.

### E021 — clippy_config_cargo

**Triggers when:** `Cargo.toml` lacks `[lints.clippy]` or any of `pedantic`/`nursery = {level="deny",priority=-1}` or the 13 `deny` lints (`unwrap_used`, `expect_used`, `indexing_slicing`, `arithmetic_side_effects`, `unreachable`, `unimplemented`, `unchecked_time_subtraction`, `todo`, `string_slice`, `panic_in_result_fn`, `panic`, `exit`, `as_conversions`).

**Fix:** Add the minimum block to `Cargo.toml` (extendable). `workspace.lints.clippy` + `lints.workspace=true` also satisfies.

### E022 — clippy_config_clippy

**Triggers when:** `clippy.toml` missing at crate root or lacks `allow-unwrap-in-tests`, `allow-expect-in-tests`, `allow-panic-in-tests`, `allow-indexing-slicing-in-tests = true`.

**Fix:** Create `clippy.toml` with the four `true` entries. Extra keys are allowed.

---

## Build Routine

```
cargo build --all-targets
cargo clippy -- -D warnings
cargo fmt -- --check
cargo nextest run --all-targets
bacon clippy -- -- -D warnings
cargo run --manifest-path ../lele_lint/Cargo.toml
```

Via devenv (per-crate `devenv.nix` with `packages = [ cargo-nextest bacon ]`):

```
devenv shell -- cargo build --all-targets
devenv shell -- cargo clippy -- -D warnings
devenv shell -- cargo fmt -- --check
devenv shell -- cargo nextest run --all-targets
devenv shell -- bacon clippy -- -- -D warnings
cargo run --manifest-path ../lele_lint/Cargo.toml
```

Via tasks (per-crate):

```
devenv tasks run lele:verify       # build+clippy+fmt+nextest+lint (without bacon)
devenv tasks run lele:bacon-clippy # bacon separately (requires TTY)
devenv tasks run lele:nextest
devenv tasks run lele:lint
```

Always run after making changes. At the end of every non-trivial change run `bacon clippy` before `lele_lint`; fix `clippy -D warnings` first, then lint violations. Test both direct and `devenv shell --` invocations when devenv is present.
