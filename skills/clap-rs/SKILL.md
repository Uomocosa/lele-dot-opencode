---
name: clap-rs
description: Use when parsing command-line arguments with Clap. Docs links, upstream examples, and a few gotchas.
---

# clap-rs — Command Line Argument Parser

Derive (proc-macro) and builder APIs. Prefer derive for declarative CLIs; builder for args built
at runtime.

## Docs & examples

| Topic | URL |
|-------|-----|
| API docs | `https://docs.rs/clap` |
| Derive tutorial/reference | `https://docs.rs/clap/latest/clap/_derive/` |
| Cookbook / FAQ | `https://docs.rs/clap/latest/clap/` |
| Repository / examples | `https://github.com/clap-rs/clap/tree/master/examples` |

## Minimal example

```rust
use clap::{Parser, Subcommand, ValueEnum};

#[derive(Parser, Debug)]
#[command(version, about)]
struct Args {
    #[arg(short, long)]
    name: String,
    #[arg(short, long, default_value_t = 1)]
    count: u8,
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand, Debug)]
enum Commands { Test { #[arg(short, long)] list: bool } }

#[derive(ValueEnum, Clone, Debug)]
enum Mode { Fast, Slow }
```

`Cargo.toml`: `clap = { version = "4.6", features = ["derive"] }`.

## Gotchas

- Missing `features = ["derive"]` → `Parser` derive not found.
- Type inference drives behavior: `bool` → `SetTrue`, `Option<T>` → optional, `Vec<T>` → `Append`,
  integer → `Count`.
- Tests: prefer `Args::try_parse_from([...])` over `parse()` (which exits), and call
  `Args::command().debug_assert()` to catch flag conflicts.
- Mixing derive and builder needs `Args::augment_args` / `Subcommand::augment_subcommands`.
