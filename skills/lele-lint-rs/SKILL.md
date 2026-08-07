# lele-lint-rs — Linter Error Code Reference

How to run, interpret, and fix `lele_lint` violations.

## Run

```bash
cargo run --manifest-path ../lele_lint/Cargo.toml
```
Run from any project directory. `lele_lint` scans every `.rs` file under `src/`.

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

---

## Build Routine

```
cargo build --all-targets
cargo clippy -- -D warnings
cargo fmt -- --check
cargo test --all-targets
cargo run --manifest-path ../lele_lint/Cargo.toml
```

Always run after making changes. Fix violations before committing.
