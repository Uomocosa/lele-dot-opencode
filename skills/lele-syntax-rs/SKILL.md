---
name: lele-syntax-rs
description: Use for Rust code in this project. Enforces atomic file structure (snake_case files everywhere, co-located domain folders), echo-rule naming, module flattening, thiserror error handling, inline testing, crate:: imports, no trivial accessors, and no positional fields.
---

# SYNTAX & ARCHITECTURE GUIDELINES

## Template Convention

All examples use template variables to remain project-agnostic:

| Variable | Meaning | Example replacement |
|---|---|---|
| `{{module}}` | Domain module path | `clicker`, `player`, `combat` |
| `{{Type}}` | PascalCase type name | `Config`, `Credentials` |
| `{{type}}` | snake_case type name (lowercase of `{{Type}}`) | `config`, `credentials` |
| `{{function}}` | snake_case function name | `authenticate`, `broadcast` |
| `{{subfolder}}` | User-chosen subfolder within a domain | `plugin`, `gui` |
| `{{crate}}` | Crate name (snake_case) | `my_crate`, `bevy_p2p` |

Replace these with actual names from your project. Never use template variables literally in code — the compiler will reject them.

## 1. Rule Priority
This file's rules override standard Rust conventions. Treat this file as the absolute source of truth for architecture, naming, file structure, and error handling.

## 2. Domain / Feature Mapping
The project is divided into isolated domain/feature modules. Each domain lives in a single folder under `src/` (e.g., `src/clicker/`, `src/player/`). Structs, their methods, system functions, and supporting types are all co-located in the domain folder. There is no `structs/`/`methods/`/`system/` split — everything for a domain lives together. In these rules, we use `{{module}}` as a template variable meaning "your domain folder path" (e.g., `clicker`, `player`). **IMPORTANT: `{{module}}` is not valid Rust syntax. Never use it literally — you must replace it with the actual module name.**

Cross-cutting types that span domains may live in a dedicated module (e.g., `common/`). Do not invent root modules.

## 3. Atomic File Structure & Naming (CRITICAL)

Every file must contain exactly **one** primary logic unit (one function, one struct, or one enum).
**Rule:** The filename MUST have the exact same name as the core item inside it.

### Domain Layout (Co-located)

All code for a domain module lives in a single flat folder:

```
src/
  lib.rs                         # pub mod {{module}}; + crate-level re-exports
  {{module}}/                    # domain folder — structs, methods, systems, types all co-located
    mod.rs
    {{type}}.rs                  # struct definition + Default + thin delegates
    {{type}}_{{function}}.rs     # method free function + test_usage  (PRIVATE module)
    {{name}}.rs                  # pure enum / error type / message struct
    {{function}}.rs              # system function or domain-level free function  (PUBLIC)
    constants.rs                 # grouped module-level constants  (optional)
```

**All filenames are snake_case.** Every file and directory name in the crate MUST use snake_case. Type names (struct, enum, trait) are still PascalCase in Rust source code — the filename is the snake_case equivalent. No `#[path]` attributes, no `non_snake_case = "allow"` — since all filenames are snake_case, `pub mod config;` naturally resolves to `config.rs` with no collision.

### Struct File (`{{module}}/{{type}}.rs`)

Contains struct definition, `impl Default` (real body, if any), associated constants (real bodies), plus ALL other `impl` blocks as **thin delegates** calling sibling method files. No method bodies, no business logic, no tests.

> **Why `impl Default` is an exception:** `Default` is uniformly trivial (one-liner constructor or literal fields), exempt from testing as a trivial method (Rule 8), and `{{type}}.rs` with only `impl Default` + thin delegates is exempt from the struct-level `test_usage` requirement (Rule 8).

> **`#[rustfmt::skip]` on thin delegate impl blocks:** Annotate every thin delegate `impl` block with `#[rustfmt::skip]` to preserve one-liner format. The `impl Default` block (real body) is NOT skipped.

> **Clarification — struct def goes in `{{module}}/{{type}}.rs`, not in mod.rs:** The struct definition MUST live in its own `.rs` file. Never put it inside a `mod.rs`. This keeps mod.rs pure per Rule 6.

**Layout (in order):**
1. `struct` definition
2. `impl TypeName { pub const ... }` — associated constants, real bodies
3. `impl Default` — real body
4. All other `impl` blocks — thin delegates

**Example:**

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

Contains a single free function matching the method name exactly. The module is **PRIVATE** — declared with `mod` (not `pub mod`) in `mod.rs`. Method files are never imported directly; they are consumed exclusively through the struct's thin delegates.

The filename follows the pattern `<struct_name>_<method>.rs` so that method files of the same struct sort together alphabetically in the flat domain folder.

```rust
// {{module}}/config_new.rs
use super::config::Config;

pub fn new() -> Config { Config::default() }

#[cfg(test)]
mod tests {
    use super::new;
    use crate::{{module}}::Config;

    #[test]
    fn test_usage() {
        let config = new();
        assert!(config.timeout_secs > 0);
    }
}
```

**Thin delegate dispatch from struct file:**

```rust
// {{module}}/config.rs
use super::config_new;

#[rustfmt::skip]
impl Config {
    pub fn new() -> Self { config_new::new() }    // 2 segments
}
```

Both files are siblings in `{{module}}/`. The struct file imports the method module with `use super::config_new;` and calls it as `config_new::new()`. No deep crate paths.

### Method Files Are Private

Method modules are declared with `mod` (private) in the domain `mod.rs`. They are NOT re-exported. Only the struct type and system functions are public:

```rust
// {{module}}/mod.rs
mod config;                     // struct module — private
mod config_new;                 // method module — PRIVATE
mod config_coop;                // method module — PRIVATE
pub mod increment;              // system function — PUBLIC

pub use config::Config;         // type is public
pub use increment::increment;   // system is public
```

External consumers can only call `config.new()` through the struct's public thin delegate. `crate::{{module}}::config_new::new()` is a private module and will not compile.

### Grouping (User-Directed)

The base structure is flat. Method files and struct files are siblings in one folder. When a domain grows, the user may introduce subfolders. Method files inside subfolders keep the same `<struct>_<method>.rs` naming:

```
{{module}}/
  mod.rs
  plugin/
    mod.rs
    plugin.rs
    plugin_build.rs
  state/
    mod.rs
    state.rs
    state_new.rs
    state_increment.rs
  command.rs                     # stays flat
  event.rs                       # stays flat
  increment.rs                   # stays flat
```

No automated threshold triggers grouping — the user decides. The only rules are:
- Method filenames always use `<struct>_<method>.rs`, even inside subfolders
- Subfolder items are NOT re-exported at the domain root; consumers access them through the subfolder path
- `mod.rs` in every directory follows Rule 6 (module tree only)

```rust
// {{module}}/plugin/mod.rs
mod plugin;                     // struct — private, but pub use below
mod plugin_build;               // method — PRIVATE

pub use plugin::ClickerPlugin;  // type is public
```

Consumer path: `use crate::{{module}}::plugin::ClickerPlugin;`

> **Delegation call rule:** When a method file calls another method of the same struct, it MUST route through the struct's public API (e.g., `Config::coop()`), not call the other method file directly. The struct's thin delegates are the authoritative API surface. Example chain: `Config::lan_coop()` → thin delegate → `config_lan_coop::lan_coop()` → calls `Config::coop()` → thin delegate → `config_coop::coop()`.

### Systems Subfolder

Bevy system functions (functions registered via `app.add_systems()`) live in a `systems/` subfolder within the domain. This prevents filename collisions between Component types and system functions (e.g., `IncrementButton` Component at `increment_button.rs` vs a system that would share the same filename).

```
{{module}}/
  systems/
    mod.rs
    poll_events.rs              # system function  (PUBLIC)
    handle_input.rs             # system function  (PUBLIC)
  increment_button.rs           # Component struct
  plugin.rs                     # Plugin struct
  plugin_build.rs               # plugin build method (PRIVATE)
```

Non-system functions (core logic, method files, plugin builds) stay flat in the domain folder. Systems in `systems/` may be re-exported at the domain root via `pub use` in `mod.rs` to keep consumer imports concise.

### Named Defaults

A "named default" is a preset constructor (e.g., `Config::coop()`, `Config::pvp()`). It follows the same decomposition rule — goes in a method file `{{type}}_{{name}}.rs`.

A method qualifies as a named default when ALL hold:
1. Returns `{{Type}}`, takes no `self` receiver
2. Return value is statically determined (literal field values, no params)
3. Purpose is to provide a preset configuration variant

Examples: `Config::coop()`, `Config::pvp()`
Counterexamples: `Config::new()` — generic constructor; `Config::with_auto_accept(mut self, ...)` — builder, takes self

**Benefits of this decomposition:**
- `{{module}}/{{type}}.rs` shows every public method signature at a glance.
- Individual files can be `#[cfg(feature = "...")]`-gated.
- Each file carries its own self-contained test.
- The struct definition remains a minimal, readable declaration.

**Feature gating convention:** Do not add feature flags unless explicitly requested.

**Helper exception:** Small private helper functions used **exclusively by the file's single primary item** are permitted in the same file.

### Constants

#### Associated Constants (belonging to a struct type)

A constant meaningful only in the context of a **single** struct type MUST be an associated constant inside `{{module}}/{{type}}.rs`:

```rust
// {{module}}/{{type}}.rs
pub struct {{Type}} { pub inner: libp2p::gossipsub::IdentTopic }

impl {{Type}} {
    pub const GAME_TOPIC_STR: &str = "{{crate}}_p2p_game";
}
```

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

### How It Applies to Files

Filenames follow the same rule.

- `auth/auth_error.rs` → `auth/error.rs` ✓
- `inventory/inventory_item.rs` → `inventory/item.rs` ✓

### Common Misconceptions

1. **"`inventory::Item` is too vague!"** — It isn't. `use inventory::Item;` reads as "an inventory Item."
2. **"Multiple states in network!"** — Add a disambiguator: `PeerState`, `ConnectionState`. The qualifier describes *what kind* — it does NOT echo the module name.
3. **"Bevy `Plugin` trait collision?"** — Rust resolves traits and types independently. `impl bevy::prelude::Plugin for Plugin { ... }` works.

> **After flattening:** When the user eliminates subfolders through flattening, the former folder-based prefixes become leaf-level disambiguators, not echoes. A type like `CliPlugin` in a flat `clicker/` domain is a **disambiguator** (distinguishes from the main `Plugin`), not an echo — because the `cli/` subfolder no longer exists. The test is: *does a folder with that name still exist in the current module hierarchy?* If the folder is gone, the prefix is a valid disambiguator.

## 5. Module Exporting & Flattening (CRITICAL)

### A. Exporting (Inside `mod.rs`)

Flatten single-function and single-struct files in their parent `mod.rs` using `pub use` to prevent stutter. Method files are NEVER re-exported — they are private modules.

**Struct types** (public):

```rust
// {{module}}/mod.rs
pub mod {{type}};
pub use {{type}}::{{Type}};     // Flatten: {{module}}::{{Type}} not {{module}}::{{type}}::{{Type}}
```

**System functions / free functions** (public):

```rust
// {{module}}/mod.rs
pub mod {{function}};
pub use {{function}}::{{function}};
```

**Method files** (PRIVATE):

```rust
// {{module}}/mod.rs
mod {{type}}_{{function}};      // private — no pub, no pub use
```

**User-chosen subfolders:**

```rust
// {{module}}/mod.rs
pub mod {{subfolder}};          // declared — items inside NOT re-exported
```

Items inside subfolders are accessed through their folder path (e.g., `{{module}}::plugin::ClickerPlugin`). Do NOT re-export them at the domain root.

**`constants.rs`:**

```rust
// {{module}}/mod.rs
pub mod constants;
pub use constants::*;           // constants live in the value namespace — safe glob
```

### B. Importing (Inside Consumer Files)

| What you're importing | Style | Example |
|---|---|---|
| **Structs / pure enums** | Import exact item | `use crate::{{module}}::{{Type}};` |
| **System functions** | Import parent domain, call through it | `use crate::{{module}};` → `{{module}}::{{function}}()` |
| **Items in user subfolder** | Import through full module path | `use crate::{{module}}::{{subfolder}}::{{Type}};` |
| **External crate types** | Import directly | `use extern_crate::Type;` |

```rust
// ✓ Correct — types via direct import
use crate::{{module}}::{{Type}};

// ✓ Correct — system functions via domain prefix
use crate::{{module}};

// ✓ Correct — subfolder items via full path
use crate::{{module}}::{{subfolder}}::{{Type}};

// ✗ Wrong — importing a PRIVATE method module
use crate::{{module}}::{{type}}_{{function}};
```

Methods are never imported directly — they are called through the struct's thin delegates.

## 6. `mod.rs` — Module Tree Only (No Logic, No Exceptions)

A `mod.rs` file builds the module tree and flattens exports. It must NOT contain any business logic, struct definitions, or data.

**Rule:** A `mod.rs` may contain ONLY:
- `pub mod` declarations
- `mod` declarations (for private method files)
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
// {{module}}/mod.rs
pub mod config;
pub use config::Config;

mod config_new;            // method file — PRIVATE
mod config_coop;           // method file — PRIVATE
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

**Struct files with hand-written impl blocks — test_usage required:** A `{{module}}/{{type}}.rs` with any hand-written `impl` block (beyond `impl Default` alone) MUST contain a `test_usage` test that:
1. Constructs the struct.
2. Exercises it through the primary integration path.
3. Asserts on an observable outcome.

**Exemption — thin-delegate struct files:** If `impl Default` is the only non-thin-delegate `impl` block, no `test_usage` required.

**Exemption — trivial methods:** One-liner accessor/delegating methods with no branching, arithmetic, or I/O are exempt.

**Exemption — constant-only definitions:** `constants.rs` is exempt.

**Context-dependent items (e.g., framework systems):** Construct a minimal working context inside the test. See framework-specific skills for patterns.

```rust
// {{module}}/{{type}}_{{function}}.rs
use super::{{type}}::{{Type}};

pub fn {{function}}() -> {{Type}} { {{Type}}::default() }

#[cfg(test)]
mod tests {
    use super::{{function}};
    use crate::{{module}}::{{Type}};

    #[test]
    fn test_usage() {
        let result = {{function}}();
        assert!(result.timeout_secs > 0);
    }
}
```

**Plugin test example:**

```rust
// {{module}}/plugin.rs
use super::plugin_build;
use bevy::prelude::*;

pub struct Plugin;

#[rustfmt::skip]
impl bevy::prelude::Plugin for Plugin {
    fn build(&self, app: &mut App) { plugin_build::build(self, app) }
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

**Imports in tests:** Follow Rule 11. `super::` is allowed for same-file items. Cross-domain types use `crate::`.

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

## 11. Import Style

Production code imports follow two rules:
1. **Same-domain imports:** Use `super::` for files sharing the same domain folder. All files in a domain folder move together, so `super::` paths survive refactoring safely.
2. **Cross-domain imports:** Use `crate::` for anything outside the current domain folder.

### Import by type

| What you're importing | Style | Example |
|---|---|---|
| **Struct/enum in same domain** | `super::` path | `use super::config::Config;` |
| **Struct/enum in other domain** | `crate::` path | `use crate::clicker::Config;` |
| **System fn in same domain** | `super::` path | `use super::increment;` |
| **System fn in other domain** | Module prefix | `use crate::clicker;` → `clicker::increment()` |
| **External crate types** | Import directly | `use bevy::prelude::*;` |

```rust
// ✓ Same-domain: struct from domain, method sibling
// In {{module}}/{{type}}_{{function}}.rs:
use super::{{type}}::{{Type}};

// ✓ Same-domain: struct file calling method
// In {{module}}/{{type}}.rs:
use super::{{type}}_{{function}};

// ✓ Cross-domain: consuming a type from another domain
use crate::combat::Damage;

// ✓ Cross-domain: calling a system from another domain
use crate::combat;
combat::apply_damage();
```

```rust
// ✗ Wrong — crate:: for same-domain siblings (unnecessarily verbose)
use crate::{{module}}::{{type}}::{{Type}};  // use super::{{type}}::{{Type}} instead

// ✗ Wrong — super:: crossing domain boundaries
use super::clicker::Config;  // use crate::clicker::Config instead
```

### Imports in thin delegates

Thin delegates in the struct file use `use super::{{type}}_{{function}};` to import sibling method modules:

```rust
// {{module}}/{{type}}.rs
use super::{{type}}_{{function}};

#[rustfmt::skip]
impl {{Type}} {
    pub fn {{function}}() -> Self { {{type}}_{{function}}::{{function}}() }
}
```

The dispatch call is always `module_name::function_name(self, ...)` — 2 segments.

### Test modules — `super::` allowed for same-file access

```rust
// ✓ Correct — super:: for same-file items, crate:: for external
#[cfg(test)]
mod tests {
    use super::{{function}};            // same-file item
    use crate::{{module}}::{{Type}};    // cross-domain type
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
