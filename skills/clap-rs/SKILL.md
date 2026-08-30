---
name: clap-rs
description: Use when parsing command-line arguments with Clap. Covers derive (Parser/Args/Subcommand/ValueEnum), Builder API, attributes (command/arg), subcommands, defaults, and testing. Works with any Rust project.
---

# clap-rs — Command Line Argument Parser (Clap)

Full-featured CLI parser with derive (proc-macro) and builder APIs. Prefer derive for declarative CLIs; use builder when args must be constructed at runtime. Docs-only skill; no config file template is needed.

## Sources

| Topic | URL |
|-------|-----|
| Crate page (v4.6.6) | `https://crates.io/crates/clap` |
| API docs (Parser, Command, Arg) | `https://docs.rs/clap` |
| Derive reference + tutorial | `https://docs.rs/clap/latest/clap/_derive/` / `https://docs.rs/clap/latest/clap/_derive/_tutorial/` |
| Book / FAQ / cookbook | `https://docs.rs/clap/latest/clap/` (concepts, cookbook, FAQ) |
| Repository / releases / examples | `https://github.com/clap-rs/clap` |

## 1. Installation

```toml
# Cargo.toml
[dependencies]
clap = { version = "4.6", features = ["derive"] }
```

Feature flags: `derive` (pulls `clap_derive`), `env`, `cargo` (reads `CARGO_*` vars), `color`/`help`/`usage`/`error-context`/`suggestions` (default), `wrap_help`, `unicode`, `string`. MSRV follows `clap_builder`. No `devenv.nix` package needed.

```bash
cargo add clap --features derive
```

## 2. Derive API

```rust
use clap::{Parser, Subcommand, ValueEnum};

/// Simple program to greet a person
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// Name of the person to greet
    #[arg(short, long)]
    name: String,

    /// Number of times to greet
    #[arg(short, long, default_value_t = 1)]
    count: u8,

    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// does testing things
    Test {
        /// lists test values
        #[arg(short, long)]
        list: bool,
    },
}

#[derive(ValueEnum, Clone, Debug)]
enum Mode { Fast, Slow }

fn main() {
    let args = Args::parse();
    println!("{args:?}");
}
```

Traits: `Parser` (top-level `parse()`/`try_parse()`/`parse_from` + `CommandFactory`/`FromArgMatches`), `Args` (reusable flattened groups), `Subcommand` (enum of subcommands), `ValueEnum` (unit-enum values), `Args`/`Subcommand` can be hand-implemented and flattened into derive via `#[command(flatten)]` / `#[command(subcommand)]`.

## 3. Attributes

| Level | Attribute | Maps to |
|-------|-----------|---------|
| Command (`#[command(...)]`) | `version`, `about`, `long_about`, `author`, `propagate_version`, `next_help_heading`, `flatten` (for `Args`), `subcommand` (for `Subcommand`) | `Command::about`, `Command::version`, etc. Doc comment fills `about`/`long_about` unless overridden |
| Arg (`#[arg(...)]`) | `short`, `long`, `value_name`, `default_value`/`default_value_t`, `value_enum`, `value_parser`, `action`, `help`, `conflicts_with`, `requires`, `group`, `flatten` | `Arg::short`, `Arg::value_parser`, `ArgAction::Set`/`Append`/`Count` |
| ValueEnum variant | `#[value(...)]` | `PossibleValue` builder |

Type inference drives behavior: `bool` → `ArgAction::SetTrue`, `Option<T>` → optional, `T` → required, `Vec<T>` → `Append` (multiple occurrences), `u8` count → `ArgAction::Count`.

## 4. Testing & Validation

```rust
use clap::Parser;

#[test]
fn verify_cli() {
    use clap::CommandFactory;
    Args::command().debug_assert();
}

#[test]
fn parse_ok() {
    let args = Args::try_parse_from(["prog", "--name", "Bob"]).unwrap();
    assert_eq!(args.name, "Bob");
}
```

`Command::debug_assert()` catches duplicate flags / conflicting relations in tests. Prefer `try_parse_from` in tests over `parse()` (which exits on error).

## 5. Pitfalls

- Missing `features = ["derive"]` → `Parser` derive not found.
- `Vec<T>` implies `Append`; forgetting `Option<Vec<T>>` vs `Vec<T>` changes requiredness.
- Mixing `derive` and `builder`: use `Args::augment_args` / `Subcommand::augment_subcommands` to combine — see `_derive` docs section "Mixing Builder and Derive APIs".
- `#[command(flatten)]` only supports `next_help_heading` on the flattened field (see clap#3269).
