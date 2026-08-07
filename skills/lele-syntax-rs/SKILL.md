---
name: lele-syntax-rs
description: Use for Rust code in this project. Enforces atomic file structure (snake_case files everywhere, co-located domain folders), module flattening, thiserror error handling, inline testing, domain-prefix imports, no trivial accessors, and no positional fields.
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
cargo test --all-targets
cargo run --manifest-path ../lele_lint/Cargo.toml
```

## 11. Import Style
| What | Style | Example |
|------|-------|---------|
| Domain items | Module prefix | `use crate::clicker;` → `clicker::Config` |
| Method file (in struct file) | `super::` | `use super::config_new;` |
| External crate types | Direct | `use bevy::prelude::*;` |

Thin delegates in struct files dispatch via `use super::{{type}}_{{function}};` → `{{type}}_{{function}}::{{function}}(self, ...)`. Convention: 2-segment `super::` path.
