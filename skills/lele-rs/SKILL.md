---
name: lele-rs
description: Use for ANY Rust work in this workspace. Always-loaded indexer - binds lele-syntax-rs, lele-lint-rs, devenv-rs, bevy-rs, libp2p, freenet and related skills. Enforces atomic files, thin delegates, E018/Deref, domain imports, thiserror, test_usage, and reproducible devenv environments.
---

# lele-rs — Rust Stack Indexer (ALWAYS LOADED)

This is the entrypoint for all Rust work. Read this file first, then load the leaf skill that matches your task. Add this skill to `opencode.json: instructions[]` so it is always loaded.

## Leaf Skills

| Task | Load |
|------|------|
| Rust syntax, file layout, delegates, imports, struct shape | `lele-syntax-rs` |
| Linter error codes E001-E020, how to fix violations | `lele-lint-rs` |
| Reproducible dev environment, Nix, languages, packages, tasks, services, hooks | `devenv-rs` |
| Bevy ECS Plugin/Component/System patterns (bevy 0.19, Rust) | `bevy-rs` |
| P2P networking SwarmBuilder, transports, stream protocols | `libp2p` |
| Freenet contracts, delegates, WebSocket clients, node modes | `freenet` |
| Freenet ring topology, gateways, peer discovery, hermetic meshes | `freenet-gateway` |
| Freenet contract state/delta/merge design, CRDT, G-counter | `freenet-contract-design` |
| Avian physics determinism caveat, rollback (Rust) | `avian-rs` |
| Git history, commits, branches, rebase, stash | `opencode-git-workflow` |
| Crate tag CI (test/build/release tag scheme) | `crate-tag-ci` (project skill `.opencode/skills/crate-tag-ci`) |
| Cargo nextest test runner, crate-local `cargo nextest run --all-targets` | `cargo-nextest-rs` |
| Extra iterator adaptors, `Itertools` trait, `iproduct!`/`izip!` | `itertools-rs` |
| Statistics-driven microbenchmarks, groups, `black_box`, `cargo bench` | `criterion-rs` |
| Data parallelism, `par_iter`, `join`/`scope`, thread pools | `rayon-rs` |
| Serialization, `Serialize`/`Deserialize`, `rename_all`/`flatten`, data formats | `serde-rs` |
| CLI parsing, `Parser`/`Args`/`Subcommand`/`ValueEnum`, `#[command]`/`#[arg]` | `clap-rs` |
| Date-time, `Zoned`/`Timestamp`/`Span`, time zones, Temporal format | `jiff-rs` |
| Function taxonomy — pure/impure vs honest/dishonest definitions, pseudocode | `definition-function-taxonomy` |

## Load Order

1. `lele-rs` (this file) — always.
2. `lele-syntax-rs` + `lele-lint-rs` — for any `src/` edit.
3. `devenv-rs` — when touching `devenv.nix`, `devenv.yaml`, packages, services, tasks, or git-hooks.
4. Domain skill (`bevy-rs`, `libp2p`, `freenet`, `avian-rs`, ...) — when the crate depends on that engine/protocol.

## Global Config Placement

- Global skills live in `~/.config/opencode/skills/<name>/SKILL.md`.
- Project filtering lives in `projects/opencode.json: permission.skill`. Pattern `*-rs` already allows `lele-rs`, `devenv-rs`, `cargo-nextest-rs`, `itertools-rs`, `criterion-rs`, `rayon-rs`, `serde-rs`, `clap-rs`, `jiff-rs`, `bevy-rs`, and `avian-rs`; no explicit allow needed. Bare-name tools (`libp2p`, `freenet`) require exact `allow`.
- Always-loaded binding is `opencode.json: instructions[]` — add `~/.config/opencode/skills/lele-rs/SKILL.md`, `~/.config/opencode/skills/itertools-rs/SKILL.md`, `~/.config/opencode/skills/criterion-rs/SKILL.md`, `~/.config/opencode/skills/rayon-rs/SKILL.md`, and related `*-rs` skills there. `serde-rs`, `clap-rs`, and `jiff-rs` are on-demand via this leaf table (not autoloaded). See `~/.config/opencode/AGENTS.md: Skill Loading (MUST)`.

## Build Verification (with devenv)

When `devenv-rs` is in use, prefer `devenv` tasks/git-hooks over raw cargo invocations in CI:

- `devenv tasks run` / `devenv test` replaces `cargo clippy -- -D warnings` + `cargo fmt -- --check` via `git-hooks.hooks.clippy` + `rustfmt`.
- Local equivalent: `cargo build --all-targets && cargo clippy -- -D warnings && cargo fmt -- --check && cargo nextest run --all-targets && bacon clippy -- -- -D warnings && cargo run --manifest-path ../lele_lint/Cargo.toml`.
- With devenv (per-crate): `devenv tasks run lele:verify` (build+clippy+fmt+nextest+bacon clippy+lint) and `devenv tasks run lele:bacon-clippy` (`bacon --headless clippy -- -- -D warnings`) separately; interactive `bacon clippy -- -- -D warnings` without `--headless` for TUI; `devenv shell -- cargo build --all-targets` etc. remain as manual fallbacks — raw `cargo …` is the fallback only when `devenv.nix` is absent.
- At the end of every non-trivial code change, run `devenv tasks run lele:bacon-clippy` (or `bacon clippy -- -- -D warnings` without devenv) before `lele_lint` (`devenv tasks run lele:lint` or `cargo run --manifest-path ../lele_lint/Cargo.toml`); fix `clippy -D warnings` first, then lint violations.

Path with spaces (e.g. `[AAI] Agentic AI`) — prepend `CARGO_TARGET_DIR=/tmp/frt-build` to all cargo commands; devenv sets this via `env.CARGO_TARGET_DIR` if needed.

## `#[allow(clippy::…)]` Gate — IMPORTANT — REALLY IMPORTANT

**No agent may add `#[allow(clippy::…)]` / `#![allow(clippy::…)]` for `clippy::pedantic` + `clippy::nursery` on its own.**

If `cargo clippy -- -D warnings` surfaces a `clippy::pedantic` or `clippy::nursery` lint:

1. Report the exact lint + `file:line` (`Cargo.toml: E021` / `clippy.toml: E022` context).
2. Propose the minimal fix: rewrite the code (`checked_add`, `try_from`, `Ipv4Addr::LOCALHOST`, `if let` vs `match`, etc.) as first choice; `#[allow]` only as last resort.
3. **Stop and ask the user** — do not insert `#[allow]` unless the user explicitly says “allow X at Y”. The user gates all existing `#[allow]` for usefulness and will remove any deemed useless.
4. Existing `#[allow]` in the codebase are not to be broadened or copied to new sites without the same explicit approval — flag them for review instead.

Rationale: `E021` forces `pedantic=deny` + `nursery=deny`; per-site `allow` defeats the deny. Only the user decides which pedantic/nursery lints are noise for this workspace. This gate also applies to file-level `#![allow]` and `Cargo.toml` global `allow` overrides — both need explicit user approval.

## Per-Crate devenv.nix — Always Read First

Before any `cargo build` / `cargo clippy` / `cargo nextest run` / `cargo run --manifest-path ../lele_lint/Cargo.toml` on a crate, read `<crate>/devenv.nix` (and `devenv.yaml` / `devenv.lock` if present). `tasks."lele:*"` there are the crate's canonical examples (`lele:verify`, `lele:nextest`, `lele:lint`, `lele:bacon-clippy` in `lele_lint:15-26`). **If `devenv.nix` defines tasks, always prefer `devenv tasks run <task>` over running the task's underlying `cargo …` command by hand**; fall back to raw `cargo nextest run --all-targets` / `cargo clippy -- -D warnings` only if `devenv.nix` is absent.

`devenv-rs` owns the per-crate `devenv.nix` template. Every Rust crate may have its own `devenv.nix` + `devenv.yaml` at the crate root; shared base can be imported via `imports = [ ../devenv.nix ]`. See `devenv-rs` for the template and composable/polyrepo pattern.
