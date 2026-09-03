---
name: lele-syntax-rs
description: Use for Rust code in this project. Enforces atomic file structure (snake_case files everywhere, co-located domain folders), module flattening, thiserror error handling, inline testing, domain-prefix imports, no trivial accessors, and struct field shape (single-field structs are tuple newtypes with #[derive(Deref)]; multi-field structs use named fields).
---

# SYNTAX & ARCHITECTURE GUIDELINES

Conventions are enforced by `lele_lint` — see **lele-lint-rs** for the full error code reference,
how to run and fix violations.

Run linter after changes: `cargo run --manifest-path ../lele_lint/Cargo.toml`

## Template Convention

All examples use template variables:

| Variable | Meaning | Example replacement |
|---|---|---|
| `{{module}}` | Domain module path | `clicker`, `player`, `combat` |
| `{{Type}}` | PascalCase type name | `Config`, `Credentials` |
| `{{type}}` | snake_case version of `{{Type}}` | `config`, `credentials` |
| `{{function}}` | snake_case function name | `authenticate` |
| `{{subfolder}}` | User-chosen subfolder within a domain | `plugin` |

## 1. Rule Priority
This file's rules override standard Rust conventions.

## 2. Domain / Feature Mapping
Projects are divided into isolated domain modules. Each domain lives in a single folder
under `src/` (e.g., `src/clicker/`, `src/player/`). Structs, their methods, system
functions, and supporting types are all co-located in the domain folder. There is no
`structs/`/`methods/`/`system/` split.

Cross-cutting types that span domains may live in a dedicated module (e.g., `common/`).
Do not invent root modules.

## 3. Atomic File Structure

Every file contains exactly **one** primary logic unit (one function, one struct, or one enum).
The filename is the snake_case equivalent of the item's name.

```
src/
  lib.rs                         # pub mod {{module}}; + crate-level re-exports
  {{module}}/                    # domain folder
    mod.rs
    {{type}}.rs                  # struct definition + Default + thin delegates
    {{type}}_{{function}}.rs     # method free function + test_usage  (PRIVATE module)
    {{name}}.rs                  # pure enum / error type / message struct
    {{function}}.rs              # system function or domain-level free function  (PUBLIC)
    constants.rs                 # grouped module-level constants  (optional)
```

### Struct File (`{{module}}/{{type}}.rs`)
Contains struct definition, `impl Default` (real body), associated constants (real bodies),
plus ALL other `impl` blocks as **thin delegates** calling sibling method files.

Layout order: struct def → associated constants → `impl Default` → thin delegate `impl` blocks.

```rust
// {{module}}/config.rs
use super::config_new;

pub struct Config {
    pub timeout_secs: u64,
}

impl Default for Config {
    fn default() -> Self { Self { timeout_secs: 30 } }
}

#[rustfmt::skip]
impl Config {
    pub fn new() -> Self { config_new::new() }
    pub fn coop() -> Self { config_new::coop() }
}
```

### Method File (`{{module}}/{{type}}_{{function}}.rs`)
Contains a single free function matching the method name. The module is **PRIVATE**
(`mod` not `pub mod` in `mod.rs`). Method files are consumed exclusively through
the struct's thin delegates.

```rust
// {{module}}/config_new.rs
use super::config::Config;

pub fn new() -> Config { Config::default() }

#[cfg(test)]
mod tests {
    use super::new;

    #[test]
    fn test_usage() {
        let config = new();
        assert!(config.timeout_secs > 0);
    }
}
```

**Thin delegate dispatch:** The struct file imports `use super::config_new;` and the
delegate method calls `config_new::new()` — convention: 2-segment `super::` dispatch, no crate paths.

**Delegation call rule:** When a method file needs to call another method of the same
struct, route through the struct's public API (e.g., `Config::coop()`), not directly.

### Grouping (User-Directed)
The base structure is flat. When a domain grows, the user may introduce subfolders.
Method files inside subfolders keep the same `<struct>_<method>.rs` naming. Subfolder
items are NOT re-exported at the domain root; consumers access them through the
subfolder path (e.g., `crate::{{module}}::plugin::ClickerPlugin`).

### Bevy Systems
When using Bevy, system functions live in a `{{module}}/bevy_systems/` subfolder.
`bevy_systems/mod.rs` must flatten via `pub use` so consumers access them as
`{{module}}::bevy_systems::poll_events`. Systems are NOT re-exported at the domain root.

### Named Defaults
A preset constructor like `Config::coop()` goes in a method file `{{type}}_{{name}}.rs`.
Qualifies when: returns `{{Type}}`, no `self`, values are static, purpose is a preset variant.

### Constants
- **Associated:** A constant meaningful only for one struct type goes in the struct file.
- **Module-level:** A constant spanning multiple types goes in `constants.rs`.

### Helper exception
Small private helper functions used exclusively by the file's primary item are permitted
in the same file.

## 4. Type Naming — No Restrictions
Domain-prefix imports (Rule 6) provide full disambiguation, so no naming constraints needed.

## 5. Module Exporting & Flattening
Flatten single-function and single-struct files in `mod.rs` via `pub use` to prevent stutter.
Method files are NEVER re-exported.

```rust
// {{module}}/mod.rs
mod player;                     // struct module — private
mod player_new;                 // method module — PRIVATE
pub mod bevy_systems;           // declared, items NOT re-exported at root
pub mod constants;
pub use constants::*;           // safe glob for value namespace
pub use player::Player;         // flatten type
```

### mod.rs Boundary (CRITICAL)
A `mod.rs` may ONLY `pub use` items from its own directory. Cross-domain re-exports
(`pub use crate::other::Type`) must go in `lib.rs`.

## 6. `mod.rs` — Module Tree Only
A `mod.rs` may contain ONLY `pub mod`, `mod`, and `pub use`. No structs, impls,
functions, constants, or tests.

## 7. Error Handling
- **Never `.unwrap()`, `.expect()`, or `panic!()`.**
- **Always `thiserror`.** Define strongly typed, domain-specific error enums.

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("Invalid credentials provided")]
    InvalidCredentials,
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}
```

## 8. Testing Rules
Tests live in the same file as the primary item (no separate `tests/` directories under `src/`).

Every non-trivial file must contain a `test_usage` test. Add `// no test_usage necessary`
to opt out. Exemptions:
- **Type-only definitions:** Pure struct/enum with zero impl blocks beyond `Default`.
- **Thin-delegate struct files:** If `impl Default` is the only non-delegate impl block.
- **`constants.rs`** and pure `mod.rs` files.

## 9. Code Style
- **No comments** (code must be self-documenting).
- **Early returns:** Use `?` or `return` to reduce nesting.
- **Indentation:** 4 spaces.
- **Logging:** Use `tracing!` macros.

## 10. Build Routine
```
cargo build --all-targets
cargo clippy -- -D warnings
cargo fmt -- --check
cargo nextest run --all-targets
cargo run --manifest-path ../lele_lint/Cargo.toml
```
Via devenv (per-crate `devenv.nix`): `devenv tasks run lele:clippy 2>&1` etc. **Agents NEVER run `bacon` — `bacon clippy` is USER-ONLY (TUI).** `bacon clippy -- -- -D warnings` is the user's interactive tool only.

## 11. Import Style
| What | Style | Example |
|------|-------|---------|
| Domain items | Module prefix | `use crate::clicker;` → `clicker::Config` |
| Method file (in struct file) | `super::` | `use super::config_new;` |
| External crate types | Direct | `use bevy::prelude::*;` |

Thin delegates in struct files dispatch via `use super::{{type}}_{{function}};` → `{{type}}_{{function}}::{{function}}(self, ...)`. Convention: 2-segment `super::` path.

**`crate::` placement (E020):** `crate::` may only appear inside `use` items (e.g. `use crate::clicker;`), never inline in expression/type/signature positions — outside the crate root (`lib.rs`/`main.rs`) it is an E020 error. Cross-domain references go through a top-level `use crate::<module>;` import, not inline `crate::` paths.

## 12. Clippy Config (E021 + E022)
Every crate must have `[lints.clippy]` in `Cargo.toml` and `clippy.toml` at crate root — minimum defaults, may extend:
- `Cargo.toml`: `pedantic/nursery = { level="deny", priority=-1 }` + 13 `deny` lints (`unwrap_used`, `expect_used`, `indexing_slicing`, `arithmetic_side_effects`, `unreachable`, `unimplemented`, `unchecked_time_subtraction`, `todo`, `string_slice`, `panic_in_result_fn`, `panic`, `exit`, `as_conversions`) — `E021`.
- `clippy.toml`: `allow-unwrap-in-tests`, `allow-expect-in-tests`, `allow-panic-in-tests`, `allow-indexing-slicing-in-tests = true` — `E022`.
`workspace.lints.clippy` + `lints.workspace=true` also satisfies `Cargo.toml`.

## 13. Struct Field Shape (E018 + E009)
Field arity decides struct shape, enforced by `lele_lint`:
- **Exactly one field** → MUST be a **tuple newtype** `pub struct X(T)` **with `#[derive(…, Deref)]`** (from `derive_more`). Access via deref (`*x`, method calls), never `.0`.
- **Two or more fields** → MUST use **named fields** `{ a: A, b: B }`. Tuple structs with ≥2 fields are forbidden.
- **`DerefMut`** is optional — only when the type needs mutation through deref (`*counter += 1`).
- Positional access (`.0`, `.1`) is banned (E009); `Deref` makes it unnecessary.

## 14. Dummy `Default` for Process Handles (clippy `unwrap_used`/`panic`)

When a struct holds a `std::process::Child` (or similar handle that must be spawned), `Default` cannot `spawn().unwrap()` — `Cargo.toml` denies `unwrap_used`/`expect_used`/`panic` (E021). Prefer `Option<Child>` with `Default => None` and handle `Some` at the call site (`if let Some(c)=&mut guard.child { c.kill(); }`), as in `freenet_example/src/testing/terminal_guard.rs:6-19` — dummy `spawn("true").unwrap()` was replaced by `Option` to stay clippy-clean. Only add `#[allow(clippy::unwrap_used)]` with explicit user approval.

