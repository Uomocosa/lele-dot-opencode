---
name: lele-syntax-rs
description: Use for Rust code in this project. Enforces atomic file structure (snake_case files everywhere, structs/methods/system split), echo-rule naming, module flattening, thiserror error handling, inline testing, crate:: imports, no trivial accessors, and no positional fields.
---

# SYNTAX & ARCHITECTURE GUIDELINES

## Template Convention

All examples use template variables to remain project-agnostic:

| Variable | Meaning | Example replacement |
|---|---|---|
| `{{module}}` | Domain module path | `p2p`, `boxes`, `sync` |
| `{{Type}}` | PascalCase type name | `Config`, `Credentials` |
| `{{type}}` | snake_case type name (lowercase of `{{Type}}`) | `config`, `credentials` |
| `{{function}}` | snake_case function name | `authenticate`, `broadcast` |
| `{{submodule}}` | Subdirectory name (primarily `system`) | `system` |
| `{{crate}}` | Crate name (snake_case) | `my_crate`, `bevy_p2p` |

Replace these with actual names from your project. Never use template variables literally in code — the compiler will reject them.

## 1. Rule Priority
This file's rules override standard Rust conventions. Treat this file as the absolute source of truth for architecture, naming, file structure, and error handling.

## 2. Domain / Feature Mapping
The project is divided into isolated domain/feature modules. In these rules, we use `{{module}}` as a template variable meaning "your domain module path" (e.g., `p2p`, `boxes`, `sync`). **IMPORTANT: `{{module}}` is not valid Rust syntax. Never use it literally — you must replace it with the actual module name.**

## 3. Atomic File Structure & Naming (CRITICAL)

Every file must contain exactly **one** primary logic unit (one function, one struct, or one enum).
**Rule:** The filename MUST have the exact same name as the core item inside it.

### Three-Tree Layout

The crate source is split into three parallel trees:

```
src/
  lib.rs                      # pub mod structs; pub mod methods; pub mod system;
  structs/                    # type definitions only
    {{module}}/
      {{type}}.rs             # struct/enum definition + Default + thin delegates
  methods/                    # free function implementations of struct methods
    {{module}}/
      {{type}}/               # one directory per struct with methods
        mod.rs                # pub mod declarations + pub use flattening
        {{function}}.rs       # pub fn {{function}}(...) -> ...
  system/                     # Bevy systems and module-level free functions
    {{module}}/
      {{function}}.rs         # pub fn {{function}}(...)
```

**Sparse trees** — a module appears only in the trees where it has content. If a module has no structs, skip `structs/<module>/`. If it has no Bevy systems, skip `system/<module>/`.

### All Files Are snake_case

Every file and directory name in the crate MUST use snake_case. There is no PascalCase anywhere in the filesystem. Type names themselves (struct, enum, trait) are still PascalCase in Rust source code — the filename is the snake_case equivalent.

**No `#[path]` attributes, no `non_snake_case = "allow"`** — since all filenames are snake_case, `pub mod config;` naturally resolves to `config.rs` with no collision.

### File Naming Rules

- **Structs/Enums:** Filename is the snake_case of the type name (e.g., `config.rs` for `pub struct Config`, `peer_state.rs` for `pub struct PeerState`).
- **Functions:** Filename exactly matches the function name (e.g., `authenticate.rs` for `pub fn authenticate`).
- **Method directories:** Named as the snake_case of the struct type (e.g., `config/` for `Config`'s methods, `peer_state/` for `PeerState`'s methods).

### Struct Decomposition

**Mandatory for every struct with impls.** If a struct has any hand-written `impl` blocks (inherent or trait), you MUST decompose. `#[derive(...)]` macros do NOT trigger decomposition — only visible, hand-written `impl` blocks count.

**Structure:**
- `structs/{{module}}/{{type}}.rs` — struct definition, `impl Default` (if any, real body), associated constants (real bodies), plus ALL other `impl` blocks as **thin delegates** calling `crate::methods::{{module}}::{{type}}::{{function}}()`. No method bodies, no business logic, no tests.
- `methods/{{module}}/{{type}}/{{function}}.rs` — one free function per method, matching the method name exactly. Body and inline test live here.
- `methods/{{module}}/{{type}}/mod.rs` — module declarations plus `pub use` flattening so callers can write `config::new()` instead of `config::new::new()`.

> **Why `impl Default` is an exception:** `Default` is uniformly trivial (one-liner constructor or literal fields), exempt from testing as a trivial method (Rule 8), and `{{type}}.rs` with only `impl Default` + thin delegates is exempt from the struct-level `test_usage` requirement (Rule 8). Extracting `Default` would add a file for no architectural benefit.

> **`#[rustfmt::skip]` on thin delegate impl blocks:** Annotate every thin delegate `impl` block with `#[rustfmt::skip]` to preserve one-liner format. The `impl Default` block (real body) is NOT skipped.

> **Clarification — struct def goes in `structs/{{module}}/{{type}}.rs`, not in mod.rs:** The struct definition MUST live in its own `.rs` file under `structs/`. Never put it inside a `mod.rs`. This keeps mod.rs pure per Rule 6.

**Example (directory layout only):**
```
structs/p2p/
  config.rs             # struct Config + Default + thin delegate impl blocks
methods/p2p/
  config/
    mod.rs              # pub mod declarations + pub use flattening
    new.rs              # pub fn new() -> Config + tests
    coop.rs             # pub fn coop() -> Config + tests
    with_timeout.rs     # pub fn with_timeout(cfg: Config, ms: u64) -> Config + tests
```

**Thin delegate example:**
```rust
// structs/p2p/config.rs
use crate::methods::p2p::config as config_method;

pub struct Config {
    pub timeout_secs: u64,
}

impl Default for Config {
    fn default() -> Self { ... }
}

#[rustfmt::skip]
impl Config {
    pub fn new() -> Self { config_method::new() }
    pub fn coop() -> Self { config_method::coop() }
    pub fn with_timeout(self, ms: u64) -> Self { config_method::with_timeout(self, ms) }
}
```

> **Delegation call rule:** When a function in `methods/{{module}}/{{type}}/` delegates to another method of the same struct, it MUST call it through the struct's public API (e.g., `Config::coop()`), NOT directly by name. The struct method in `structs/{{module}}/{{type}}.rs` is the authoritative API surface. Example chain: `Config::lan_coop()` → delegate in `config.rs` → `config_method::lan_coop()` → calls `Config::coop()` → delegate in `config.rs` → `config_method::coop()`.

### Named Defaults

A "named default" is a preset constructor (e.g., `Config::coop()`, `Config::pvp()`). It follows the same decomposition rule — goes in `methods/{{module}}/{{type}}/` as a free function.

A method qualifies as a named default when ALL hold:
1. Returns `{{Type}}`, takes no `self` receiver
2. Return value is statically determined (literal field values, no params)
3. Purpose is to provide a preset configuration variant

Examples: `Config::coop()`, `Config::pvp()`
Counterexamples: `Config::new()` — generic constructor; `Config::with_auto_accept(mut self, ...)` — builder, takes self

**Benefits of this decomposition:**
- `structs/{{module}}/{{type}}.rs` shows every public method signature at a glance.
- Individual files can be `#[cfg(feature = "...")]`-gated.
- Each file carries its own self-contained test.
- The struct definition remains a minimal, readable declaration.

**Feature gating convention:** Do not add feature flags unless explicitly requested.

**Helper exception:** Small private helper functions used **exclusively by the file's single primary item** are permitted in the same file.

### Constants

#### Associated Constants (belonging to a struct type)

A constant meaningful only in the context of a **single** struct type MUST be an associated constant inside `structs/{{module}}/{{type}}.rs`:

```rust
// structs/{{module}}/{{type}}.rs
pub struct {{Type}} { pub inner: libp2p::gossipsub::IdentTopic }

impl {{Type}} {
    pub const GAME_TOPIC_STR: &str = "{{crate}}_p2p_game";
}
```

**Layout in `structs/{{module}}/{{type}}.rs` (in order):**
1. `struct` definition
2. `impl TypeName { pub const ... }` — associated constants, real bodies
3. `impl Default` — real body
4. All other `impl` blocks — thin delegates

**Criterion — associated vs. module-level:** An associated constant if **all** hold:
1. Its value is only meaningful for one specific struct type.
2. It is only referenced by that type's own methods.
3. No other type, function, or module reads it.

If any code outside the struct's own files references it, it MUST be a module-level constant in `constants.rs`.

#### Module-level Constants

A constant spanning multiple types or referenced by module-level functions goes in a grouped `constants.rs` file:

```
{{module}}/
  mod.rs                  # pub mod constants; pub use constants::*;
  constants.rs            # grouped pub const definitions
```

```rust
// {{module}}/constants.rs
pub const HASTE: Ability = Ability::Static { ... };
pub const VIGILANCE: Ability = Ability::Static { ... };
```

**No `test_usage` required** — pure value declarations are exempt from testing (Rule 8).

## 4. Contextual Naming (Zero Redundancy)

Items (files, functions, structs) inherently inherit the context of their parent directory and module path. **Never repeat parent folder or module names in the child filename, struct name, or function name.**

### Core Test

"If I drop the module name from this item's name, do I lose information that the module path doesn't already give me?"

| ✗ Wrong (redundant) | ✓ Correct | Why |
|---|---|---|
| `auth::logic::auth_user` | `auth::logic::authenticate` | Module says "auth"; function should say *what*, not *where* |
| `inventory::model::InventoryItem` | `inventory::model::Item` | Module says "inventory"; `Item` is unambiguous |
| `auth::AuthError` | `auth::Error` | Module says "auth"; `Error` suffices |
| `network::NetworkState` | `network::PeerState` | `Peer` clarifies *which* state; dropping the echo `Network` is what matters |

### Echo vs. Disambiguator

A qualifier is **redundant (echo)** when it repeats the same lexical root as the module name. A qualifier is a **disambiguator** when it distinguishes siblings using information not already in the module name.

- `network::PeerState` → not an echo. `Peer` distinguishes *which* state.
- `p2p::P2pPlugin` → echo. Use `p2p::Plugin`.
- `auth::AuthError` → echo. Use `auth::Error`.

### Common Misconceptions

1. **"`inventory::Item` is too vague!"** — It isn't. `use inventory::Item;` reads as "an inventory Item."
2. **"Multiple states in network!"** — Add a disambiguator: `PeerState`, `ConnectionState`. The qualifier describes *what kind* — it does NOT echo the module name.
3. **"Bevy `Plugin` trait collision?"** — Rust resolves traits and types independently. `impl bevy::prelude::Plugin for Plugin { ... }` works.

## 5. Module Exporting & Flattening (CRITICAL)

### A. Exporting (Inside `mod.rs`)
Flatten single-function and single-struct files in their parent `mod.rs` using `pub use` to prevent stutter.

**Struct files** in `structs/{{module}}/`:
```rust
// structs/{{module}}/mod.rs
pub mod {{type}};
pub use {{type}}::{{Type}};     // Flatten: structs::{{module}}::{{Type}} not structs::{{module}}::{{type}}::{{Type}}
```

**Function files** in `system/{{module}}/`:
```rust
// system/{{module}}/mod.rs
pub mod {{function}};
pub use {{function}}::{{function}};
```

**Method directories** in `methods/{{module}}/` are NOT re-exported at the module root. Methods are accessed exclusively through the struct's thin delegates.

**Exception — items in subdirectories under `methods/` (per-type dirs):**
```rust
// methods/{{module}}/config/mod.rs
pub mod new;
pub mod coop;

pub use new::new;     // flatten: config::new() not config::new::new()
pub use coop::coop;
```

**Subdirectory items that are not in flat files (e.g., domain submodules) are NOT re-exported:**
```rust
// ✓ Subdirectory declared — its contents are NOT re-exported
pub mod {{submodule}};   // consumers: {{module}}::{{submodule}}::{{Type}}
```

> **Exception — `constants.rs` glob re-export:** `pub use constants::*;` is safe because constants live in the value namespace. Do not extend to types or functions.

### B. Importing (Inside Consumer Files)

| What you're importing | Style | Example |
|---|---|---|
| **Types from `structs/`** | Import exact item | `use crate::structs::{{module}}::{{Type}};` |
| **Functions from `system/`** | Import parent module, call through it | `use crate::system::{{module}};` → `{{module}}::{{function}}()` |
| **Types from a domain submodule** | Import through full path | `use crate::{{module}}::{{submodule}}::{{Type}};` |

```rust
// ✓ Correct — types via structs/ tree
use crate::structs::{{module}}::{{Type}};

// ✓ Correct — system functions via module prefix
use crate::system::{{module}};

// ✗ Wrong — super:: breaks on directory moves
use super::{{Type}};
```

Methods are never imported directly — they are called through the struct's thin delegates.

## 6. `mod.rs` — Module Tree Only (No Logic, No Exceptions)

A `mod.rs` file builds the module tree and flattens exports. It must NOT contain any business logic, struct definitions, or data.

**Rule:** A `mod.rs` may contain ONLY:
- `pub mod` declarations
- `pub use` re-exports

Everything else is **strictly forbidden**:
- ❌ Struct/enum definitions
- ❌ `impl` blocks (methods, trait impls)
- ❌ Functions (including private helpers)
- ❌ Constants or statics
- ❌ `#[cfg(test)]` modules
- ❌ Trait definitions

✅ **Allowed — pure re-export:**
```rust
// structs/p2p/mod.rs
pub mod config;
pub use config::Config;

// No pub use from methods/ — methods are accessed through Config.rs thin delegates
```

## 7. Error Handling (Strict Constraints)
- **Never use `.unwrap()`, `.expect()`, or `panic!()`.** All errors must be gracefully propagated.
- **Always use `thiserror`.** Define strongly typed, domain-specific error enums.

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("Invalid credentials provided")]
    InvalidCredentials,
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Configuration error: {0}")]
    Config(String),
}
```

## 8. Testing Rules (Inline)

Tests must live in the exact same file as the core item. Do not create separate `tests/` directories or `test.rs` files. Append a `#[cfg(test)]` module at the bottom of the file.

Every file whose primary item is a non-trivial function (branching, arithmetic, I/O, or allocation) MUST contain a `test_usage` test that exercises the primary item in a way that mirrors real consumption.

**Exemption — type-only definitions:** Pure struct/enum with zero `impl` blocks → no `test_usage` required.

**Struct files with hand-written impl blocks — test_usage required:** A `structs/{{module}}/{{type}}.rs` with any hand-written `impl` block (beyond `impl Default` alone) MUST contain a `test_usage` test that:
1. Constructs the struct.
2. Exercises it through the primary integration path.
3. Asserts on an observable outcome.

**Exemption — thin-delegate struct files:** If `impl Default` is the only non-thin-delegate `impl` block, no `test_usage` required.

**Exemption — trivial methods:** One-liner accessor/delegating methods with no branching, arithmetic, or I/O are exempt.

**Exemption — constant-only definitions:** `constants.rs` is exempt.

**Context-dependent items (e.g., framework systems):** Construct a minimal working context inside the test. See framework-specific skills for patterns.

```rust
// methods/{{module}}/{{type}}/new.rs
use crate::structs::{{module}}::{{Type}};

pub fn new() -> {{Type}} { {{Type}}::default() }

#[cfg(test)]
mod tests {
    use super::new;

    #[test]
    fn test_usage() {
        let result = new();
        assert!(result.timeout_secs > 0);
    }
}
```

**Plugin test example:**
```rust
// structs/{{module}}/plugin.rs
pub struct Plugin;

#[rustfmt::skip]
impl bevy::prelude::Plugin for Plugin {
    fn build(&self, app: &mut App) { crate::methods::{{module}}::plugin::build(self, app) }
}

#[cfg(test)]
mod tests {
    use bevy::prelude::*;
    use super::Plugin;

    #[test]
    fn test_usage() {
        let mut app = App::new();
        app.add_plugins(Plugin);
    }
}
```

**Imports in tests:** Follow Rule 11. `super::` is allowed for same-file items.

## 9. Universal Code Style

- **No Comments:** Do not write comments. Code must be self-documenting.
- **Clarity over cleverness.**
- **Early returns:** Use `?` or `return` to reduce nesting.
- **Indentation:** 4 spaces.
- **Thin delegates `#[rustfmt::skip]`:** Every thin delegate `impl` block (Rule 3) MUST use `#[rustfmt::skip]`. `impl Default` blocks (real bodies) are NOT skipped.
- **Logging:** Use `tracing!` macros.
  ```rust
  tracing::debug!(target: "module_name", var_name = var.value);
  ```

## 10. Standard Build & Verification Routine

Verify changes with:
```bash
cargo build --all-targets
cargo clippy -- -D warnings
cargo fmt -- --check
cargo test --all-targets
```

## 11. Import Style — Absolute `crate::` Only (Strict)

Every `use` statement MUST start with `crate::` or an extern crate name. Relative paths (`super::`, `self::`) are banned in production code.

### Import by type

| What you're importing | Style | Example |
|---|---|---|
| **Types from `structs/`** | Import exact item | `use crate::structs::{{module}}::{{Type}};` |
| **Types from a domain submodule** | Import through full path | `use crate::{{module}}::{{submodule}}::{{Type}};` |
| **Functions from `system/`** | Import parent module, call through it | `use crate::system::{{module}};` → `{{module}}::{{function}}()` |
| **External crate types** | Import directly | `use extern_crate::Type;` |

```rust
// ✓ Correct — types via structs/ tree
use crate::structs::{{module}}::{{Type}};

// ✓ Correct — system functions via module prefix
use crate::system::{{module}};

// ✗ Wrong — super:: breaks on directory moves
use super::{{Type}};
```

### Test modules — `super::` allowed for same-file access

```rust
// ✓ Correct — super:: for same-file items, crate:: for external items
#[cfg(test)]
mod tests {
    use super::{{function}};
    use crate::structs::{{module}}::{{Type}};

    #[test]
    fn test_usage() { ... }
}
```

### Exception — `mod.rs` re-exports only

```rust
// ✓ This is a re-export, not a consumer import
pub mod {{function}};
pub use {{function}}::{{function}};
```

## 12. No Trivial Accessors (Getters/Setters)

A method that reads or writes a single `pub` field without any computation, validation, or side effect MUST be removed. Callers access the field directly.

### Mechanical Test

A method IS a trivial accessor when **all** hold:
1. Body is a single expression or assignment statement.
2. It reads or writes exactly one field of `self`.
3. That field is `pub`.
4. The method is not required by a trait implementation.

```
// ✗ WRONG — trivial getter, field is pub
fn tick(&self) -> u64 { self.0 }

// ✓ OK — trait impl
impl Deref for Wrapper {
    type Target = Inner;
    fn deref(&self) -> &Inner { &self.0 }
}

// ✓ OK — consuming builder (self → Self)
fn with_timeout(self, ms: u64) -> Self { Self { timeout: ms, ..self } }
```

## 13. No Positional Struct Field Access

Never access struct fields by position (`.0`, `.1`, ...). All struct definitions MUST use named fields.

### Exceptions
- Types from **external crates** (not under your control).
- **Anonymous tuples** — inherently positional.

```
// ✓ CORRECT — named field is self-documenting
pub struct PlayerId { pub value: u64 }
fn check(id: &PlayerId) -> bool { id.value == 0 }

// ✓ OK — external crate
text.0 = format!("{}", count);
```
