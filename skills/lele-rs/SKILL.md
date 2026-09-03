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
- **Tool-skill auto-load rule:** If any crate in the workspace depends on a tool/crate for which a skill exists (`bevy-rs`, `libp2p`, `freenet`, `freenet-gateway`, `freenet-contract-design`, `avian-rs`, `serde-rs`, `clap-rs`, `jiff-rs`, `reqwest-rs`, `criterion-rs`, `rayon-rs`, `itertools-rs`, etc.), add that skill to `opencode.json: instructions[]` so it is always loaded. If no crate uses the tool, keep the skill only as `permission.skill: allow` and load it on demand via the leaf table — do not add to `instructions[]`.

## Build Verification (with devenv)

When `devenv-rs` is in use, prefer `devenv` tasks/git-hooks over raw cargo invocations in CI:

- `devenv tasks run` / `devenv test` replaces `cargo clippy -- -D warnings` + `cargo fmt -- --check` via `git-hooks.hooks.clippy` + `rustfmt`.
- Local equivalent: `cargo build --all-targets && cargo clippy -- -D warnings && cargo fmt -- --check && cargo nextest run --all-targets && cargo run --manifest-path ../lele_lint/Cargo.toml`.
- With devenv (per-crate): `devenv tasks run lele:build 2>&1`, `devenv tasks run lele:clippy 2>&1`, `devenv tasks run lele:fmt 2>&1`, `devenv tasks run lele:nextest 2>&1`, `devenv tasks run lele:lint 2>&1` — each leaf does one job; `devenv shell -- cargo build --all-targets 2>&1` etc. remain as manual fallbacks — raw `cargo …` is the fallback only when `devenv.nix` is absent. **Agents NEVER run `bacon` — `bacon clippy` is USER-ONLY (TUI).**
- At the end of every non-trivial code change, run `cargo clippy -- -D warnings` via `devenv tasks run lele:clippy 2>&1` before `lele_lint` (`devenv tasks run lele:lint 2>&1` or `cargo run --manifest-path ../lele_lint/Cargo.toml 2>&1`); fix `clippy -D warnings` first, then lint violations. Agents use `cargo clippy`, never `bacon`.

Path with spaces (e.g. `[AAI] Agentic AI`) — prepend `CARGO_TARGET_DIR=/tmp/frt-build` to all cargo commands; devenv sets this via `env.CARGO_TARGET_DIR` if needed.

## `#[allow(clippy::…)]` Gate — IMPORTANT — REALLY IMPORTANT

**No agent may add `#[allow(clippy::…)]` / `#![allow(clippy::…)]` for `clippy::pedantic` + `clippy::nursery` on its own.**

If `cargo clippy -- -D warnings` surfaces a `clippy::pedantic` or `clippy::nursery` lint:

1. Report the exact lint + `file:line` (`Cargo.toml: E021` / `clippy.toml: E022` context).
2. Propose the minimal fix: rewrite the code (`checked_add`, `try_from`, `Ipv4Addr::LOCALHOST`, `if let` vs `match`, etc.) as first choice; `#[allow]` only as last resort.
3. **Stop and ask the user** — do not insert `#[allow]` unless the user explicitly says “allow X at Y”. The user gates all existing `#[allow]` for usefulness and will remove any deemed useless.
4. Existing `#[allow]` in the codebase are not to be broadened or copied to new sites without the same explicit approval — flag them for review instead.

Rationale: `E021` forces `pedantic=deny` + `nursery=deny`; per-site `allow` defeats the deny. Only the user decides which pedantic/nursery lints are noise for this workspace. This gate also applies to file-level `#![allow]` and `Cargo.toml` global `allow` overrides — both need explicit user approval.

## Lele Rust Config — Canonical Crate Template (GENERAL)

**Template lives at `~/.config/opencode/skills/lele-rs/references/lele-rust-config/` — copy to any crate root, replacing `<crate>` with the crate name. Invoke `/lele-rust-config` to audit/fix or scaffold.**

**Nightly + pinned:** `languages.rust.channel = "nightly"` (via `fenix`, required for `lele:taxonomy_check` with `rustc-private`), `rust-toolchain.toml` mirrors it for non-devenv fallback, `Cargo.toml` pins every direct dep with `=version` (e.g. `thiserror = "=2.0.18"`, `derive_more = "=2.1.1"` — bump via `cargo update` then re-pin). `edition = "2024"` always.

| File | What it provides |
|------|-----------------|
| `Cargo.toml` | `edition 2024`, full `[lints.clippy]` E021 (pedantic+nursery deny + 13 denies), pinned `=version` deps |
| `clippy.toml` | E022 4× `true` (`allow-unwrap/expect/panic/indexing-in-tests`) |
| `devenv.nix` | nightly + `cargo-nextest`, `env.CARGO_TARGET_DIR`, 6 tasks `lele:build/clippy/fmt/nextest/lint/taxonomy_check` (`showOutput=true`), 4 git-hooks (task-composed `cd <crate> && devenv tasks run lele:* 2>&1`, `always_run`) |
| `devenv.yaml` | `nixpkgs` + `git-hooks` + `fenix` + `rust-overlay` |
| `rust-toolchain.toml` | nightly pin |
| `lele.toml` | `honesty` defaults (taxonomy) |
| `src/lib.rs`+`src/hello.rs` | minimal `Deref` newtype demo + `test_usage` |
| `.gitignore` | `.devenv/`, `target/`, `contract/target/` |

**Freenet overlay is NOT part of this template** — when `contract/Cargo.toml` or `dependencies.freenet` is present, overlay `freenet` skill on top (WASM targets, `gccStdenv`/clang/glibc `C_INCLUDE_PATH`, `contract:target` isolation, `freenet:*` tasks, `build.rs` contract builder). See `freenet: Freenet Devenv Overlay`.

**Command:** `/lele-rust-config [crate-path] [--check]` audits and patches toward this template; `/lele-rust-config create <name>` scaffolds from it.

## Per-Crate devenv.nix — Always Read First

Before any `cargo build` / `cargo clippy` / `cargo nextest run` / `cargo run --manifest-path ../lele_lint/Cargo.toml` on a crate, read `<crate>/devenv.nix` (and `devenv.yaml` / `devenv.lock` if present). `tasks."lele:*"` there are the crate's canonical examples (`lele:build`, `lele:clippy`, `lele:fmt`, `lele:nextest`, `lele:lint`, `lele:taxonomy_check` in `lele_lint:15-26`). **If `devenv.nix` defines tasks, you MUST run `devenv tasks run <task> 2>&1` — NEVER run the underlying `cargo …` by hand; NEVER pipe to `| tail`/`| head`; always append `2>&1`**; fall back to raw `cargo nextest run --all-targets 2>&1` / `cargo clippy -- -D warnings 2>&1` only if `devenv.nix` is absent. **Agents NEVER run `bacon` — it is USER-ONLY.**

`devenv-rs` owns the per-crate `devenv.nix` engine; this skill owns the canonical content. Every Rust crate may have its own `devenv.nix` + `devenv.yaml` at the crate root; shared base can be imported via `imports = [ ../devenv.nix ]`. See `devenv-rs` for the template and composable/polyrepo pattern.
