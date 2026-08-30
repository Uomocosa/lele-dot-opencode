---
name: serde-rs
description: Use when serializing/deserializing Rust data with Serde. Covers serde derive (Serialize/Deserialize), container/field/variant attributes, rename_all, flatten, data-format crates, and trait-based zero-cost model. Works with any Rust project.
---

# serde-rs — Serialization Framework (Serde)

Framework for serializing and deserializing Rust data structures generically via `Serialize`/`Deserialize` traits. Derive macros generate impls at compile time with zero reflection overhead; data formats (e.g., `serde_json`, `bincode`) provide `Serializer`/`Deserializer`. Docs-only skill; no config file template is needed.

## Sources

| Topic | URL |
|-------|-----|
| Crate page (v1.0.229, MSRV 1.56) | `https://crates.io/crates/serde` |
| Derive crate | `https://crates.io/crates/serde_derive` |
| Overview + derive setup | `https://serde.rs` / `https://serde.rs/derive.html` |
| API docs (Serialize/Deserialize) | `https://docs.rs/serde` |
| Attributes (container/field/variant) | `https://serde.rs/attributes.html` |
| Container / field attrs (rename_all, flatten, etc.) | `https://serde.rs/container-attrs.html` / `https://serde.rs/field-attrs.html` |
| Repository / releases | `https://github.com/serde-rs/serde` |

## 1. Installation

```toml
# Cargo.toml
[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0" # data format — separate crate (or bincode, postcard, toml, etc.)
```

Features: `derive` (pulls `serde_derive`), `std` (default; disable for `no_std` + `alloc` via `alloc` feature), `rc`, `unstable`. Split into `serde_core` + `serde_derive` since 1.0. No `devenv.nix` package needed.

## 2. Derive & Traits

```rust
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
struct Point {
    x: i32,
    y: i32,
}

let point = Point { x: 1, y: 2 };
let json = serde_json::to_string(&point).unwrap();
let back: Point = serde_json::from_str(&json).unwrap();
```

Serde is trait-based, not reflection-based — `Serialize`/`Deserialize` impls can be fully optimized away for a given struct+format pair. Import `Serialize`/`Deserialize` in the same module as `#[derive]`. Format crates provide `Serializer`/`Deserializer`. Out-of-box support for `String`, `&str`, `Vec`, `HashMap`, `Option`, etc.

## 3. Attributes

Three levels (`serde.rs/attributes.html`); each may carry multiple `#[serde(...)]`:

| Level | Key Attributes |
|-------|----------------|
| Container (`struct`/`enum`) | `rename`, `rename_all = "camelCase"` (8 cases: `lowercase`, `UPPERCASE`, `PascalCase`, `camelCase`, `snake_case`, `SCREAMING_SNAKE_CASE`, `kebab-case`, `SCREAMING-KEBAB-CASE`), `deny_unknown_fields`, `default`, `transparent`, `tag`/`content`/`untagged` (enum) |
| Field | `rename`, `alias` (repeatable), `default`, `skip`, `skip_serializing_if = "Option::is_none"`, `flatten`, `serialize_with`/`deserialize_with`, `borrow` |
| Variant | `rename`, `alias`, `skip`, `other` |

```rust
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct User {
    id: String,
    #[serde(rename_all = "camelCase")]
    user_name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    email: Option<String>,
    #[serde(flatten)]
    extra: std::collections::HashMap<String, serde_json::Value>,
}
```

`flatten` inlines map/struct keys into the parent; useful for capturing unknown fields. `alias` deserializes from alternate names; `rename` changes both directions.

## 4. Pitfalls

- Missing `features = ["derive"]` → `Serialize`/`Deserialize` derive not found.
- `deny_unknown_fields` is incompatible with `flatten` (neither outer nor inner flattened struct may use it) and interacts poorly with `skip` (skipped field seen as unknown if present) — see `serde.rs/container-attrs.html` and issue #2121. Use `serde::de::IgnoredAny` or `serde_ignored` crate to detect unknowns instead.
- Version mismatch `serde 0.9 vs 1.0` trait errors — run `cargo tree -d` to deduplicate.
- Derive requires Rust 1.56+; ensure toolchain matches.
