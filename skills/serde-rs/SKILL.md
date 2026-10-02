---
name: serde-rs
description: Use when serializing/deserializing Rust data with Serde. Docs links, upstream examples, and a few gotchas.
---

# serde-rs — Serialization Framework

Trait-based `Serialize`/`Deserialize` with derive macros; data formats (`serde_json`, `bincode`,
`toml`, …) supply the `Serializer`/`Deserializer`.

## Docs & examples

| Topic | URL |
|-------|-----|
| Overview | `https://serde.rs` |
| Derive setup | `https://serde.rs/derive.html` |
| Attributes (container/field/variant) | `https://serde.rs/attributes.html` / `https://serde.rs/container-attrs.html` / `https://serde.rs/field-attrs.html` |
| API docs | `https://docs.rs/serde` |
| Repository / examples | `https://github.com/serde-rs/serde` |

## Minimal example

```rust
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
struct Point { x: i32, y: i32 }

let point = Point { x: 1, y: 2 };
let json = serde_json::to_string(&point)?;
let back: Point = serde_json::from_str(&json)?;
```

`Cargo.toml`: `serde = { version = "1.0", features = ["derive"] }` + a format crate
(`serde_json`, `bincode`, …).

## Gotchas

- Missing `features = ["derive"]` → the derive macros are not found.
- `deny_unknown_fields` is incompatible with `flatten` (and interacts poorly with `skip`).
- `rename_all` accepts: `lowercase`, `UPPERCASE`, `PascalCase`, `camelCase`, `snake_case`,
  `SCREAMING_SNAKE_CASE`, `kebab-case`, `SCREAMING-KEBAB-CASE`.
- Duplicate serde major versions in the tree cause trait errors — `cargo tree -d` to dedupe.
