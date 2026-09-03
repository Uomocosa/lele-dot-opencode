---
name: cargo-nextest-rs
description: Use when running Rust tests via cargo nextest. Covers installation via devenv packages or cargo install, crate-local invocation cargo nextest run --all-targets, profile handling, and how nextest replaces cargo test in the verification routine.
---

# cargo-nextest-rs — Rust Test Runner (cargo nextest)

Replaces `cargo test` with `cargo nextest run` for faster, isolated test execution. Docs-only skill; no `.config/nextest.toml` template is provided—configure only if a crate needs custom profiles.

## Sources

| Topic | URL |
|-------|-----|
| Home / book | `https://nexte.st/` |
| Installation & running | `https://nexte.st/docs/installation/pre-built-binaries/` + `https://nexte.st/docs/running/` |
| Configuration & profiles | `https://nexte.st/docs/configuration/` |
| Repository / releases | `https://github.com/nextest-rs/nextest` |
| Devenv package | `https://devenv.sh/packages/` (`pkgs.cargo-nextest`) |

## 1. Installation

Preferred (reproducible, per-crate):

```nix
# devenv.nix — per-crate
packages = with pkgs; [ cargo-nextest ];
```

Fallback (no devenv):

```bash
cargo install cargo-nextest --locked
```

`CARGO_TARGET_DIR=/tmp/frt-build` (space-in-path fix) is respected by nextest same as cargo.

## 2. Invocation — Crate-Local (Required)

This workspace uses **crate-local** invocations (no `--workspace`):

```bash
cargo nextest run --all-targets
```

Equivalents:

| `cargo test` | `cargo nextest run` |
|--------------|---------------------|
| `cargo test --all-targets` | `cargo nextest run --all-targets` |
| `cargo test -- --nocapture` | `cargo nextest run -- --nocapture` |
| `cargo test -p foo -- --ignored` | `cargo nextest run -p foo --run-ignored all -- --nocapture` or `cargo nextest run -p foo -- --ignored` (pass-through) |
| `cargo test --no-run` | `cargo nextest run --no-run` |

With devenv:

```bash
devenv shell -- cargo nextest run --all-targets
```

## 3. Verification Routine Position

`cargo nextest run --all-targets` occupies the same slot as `cargo test` in the standard routine:

```
cargo build --all-targets
cargo clippy -- -D warnings
cargo fmt -- --check
cargo nextest run --all-targets
cargo run --manifest-path ../lele_lint/Cargo.toml
```

At the end of every non-trivial change, `cargo clippy -- -D warnings` (via `devenv tasks run lele:clippy 2>&1`) runs before `lele_lint`; `nextest` is the test step before that. **Agents NEVER run `bacon` — it is USER-ONLY.**
