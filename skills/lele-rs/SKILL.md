---
name: lele-rs
description: Use for ANY Rust work in this workspace. Always-loaded indexer - binds lele-syntax-rs, rust-env-rs, bevy-rs, libp2p, freenet and related skills. Enforces atomic files, atomic delegates, E018/Deref, domain imports, thiserror, test_usage, and reproducible Rust environments.
---

# lele-rs — Rust Stack Indexer (ALWAYS LOADED)

This is the entrypoint for all Rust work. Read this file first, then load the leaf skill that matches your task. v2 has no `instructions[]` binding: `AGENTS.md` is the always-loaded content, and skills are advertised by `description` and loaded on demand via the `skill` tool.

## Leaf Skills

| Task | Load |
|------|------|
| Rust syntax, file layout, delegates, imports, struct shape, judgement rules | `lele-syntax-rs` (+ `references/RATIONALE.md`, `references/SMELLS.md`) |
| Rust dev env — toolchain, tasks, hooks, cargo config (preferred) | `rust-env-rs` |
| Nix/devenv dev env (LEGACY; opt-in only) | `devenv-rs-legacy` |
| Bevy ECS Plugin/Component/System patterns (bevy 0.19, Rust) | `bevy-rs` |
| P2P networking SwarmBuilder, transports, stream protocols | `libp2p` |
| Freenet contracts, delegates, WebSocket clients, node roles/ring, CRDT state design | `freenet` (+ its `glossary/`, `references/`) |
| Avian physics determinism caveat, rollback (Rust) | `avian-rs` |
| Git history, commits, branches, rebase, stash | `opencode-git-workflow` |
| Crate tag CI (test/build/release tag scheme) | `crate-tag-ci` (project skill `.opencode/skills/crate-tag-ci`) |
| Extra iterator adaptors, `Itertools` trait, `iproduct!`/`izip!` | `itertools-rs` |
| Statistics-driven microbenchmarks, groups, `black_box`, `cargo bench` | `criterion-rs` |
| Data parallelism, `par_iter`, `join`/`scope`, thread pools | `rayon-rs` |
| Serialization, `Serialize`/`Deserialize`, `rename_all`/`flatten`, data formats | `serde-rs` |
| CLI parsing, `Parser`/`Args`/`Subcommand`/`ValueEnum`, `#[command]`/`#[arg]` | `clap-rs` |
| Date-time, `Zoned`/`Timestamp`/`Span`, time zones, Temporal format | `jiff-rs` |
| Function taxonomy — pure/impure vs honest/dishonest definitions, pseudocode | `definition-function-taxonomy` |
| State machines — one `update` entrypoint, `State`/`Input`/`Output`, transitions `-> Output` | `definition-state-machine` + `lele-syntax-rs` (RATIONALE *State machines*) |

**`lele:taxonomy_check`** runs `lele_function_taxonomy` (a rustc-MIR driver). It checks only
`[[lele.boundary]]` folders with `require = "honest"`: every function physically inside must reach hidden
I/O (clock, fs, net, env, process, randomness, non-`Freeze` globals, `thread_local!`) only through its
signature. It exits instantly when no honest boundary is configured (so most crates pay nothing). Logging
(`tracing`/`log` callsites) is treated as honest. A finding is `TAX001`; bad config is `TAX002`.

## Load Order

1. `lele-rs` (this file) — always.
2. `lele-syntax-rs` — for any `src/` edit. The linter (`lele_lint`) enforces the mechanical
   rules; the full list is generated into `lele_lint/RULES.md`, and `lele_lint --explain E0xx`
   prints one rule with a bad/good example (`--checker-list` lists checkers). Judgement rules
   the linter cannot check live in `lele-syntax-rs/references/RATIONALE.md`.
3. `rust-env-rs` — when touching `rust-toolchain.toml`, `justfile`, `.githooks`, `.cargo/config.toml`, or the workspace/`lele.toml` layout. Legacy: `devenv-rs-legacy` for crates that still ship `devenv.nix`.
4. Domain skill (`bevy-rs`, `libp2p`, `freenet`, `avian-rs`, ...) — when the crate depends on that engine/protocol.

## Global Config Placement

- Global skills live in `~/.config/opencode/skills/<name>/SKILL.md`.
- Project filtering lives in `projects/opencode.json: permission.skill`. Pattern `*-rs` already allows `lele-rs`, `rust-env-rs`, `itertools-rs`, `criterion-rs`, `rayon-rs`, `serde-rs`, `clap-rs`, `jiff-rs`, `bevy-rs`, and `avian-rs`; no explicit allow needed. Bare-name tools (`libp2p`, `freenet`) and the `-legacy` skills (`devenv-rs-legacy`) require an exact `allow` rule (they are not matched by any glob).
- **Always-on vs on-demand (v2).** There is no `instructions[]` binding — v2 accepts the field but does not load its entries. Put always-on content in `AGENTS.md` (global or project); skills are advertised by `description` and loaded on demand via the `skill` tool, so the `description` is the only thing the model sees before loading. See `~/.config/opencode/AGENTS.md: Skill Loading (MUST)`.
- **Tool-skill visibility rule:** a skill whose crate dependency is present should be *permitted* (`permission.skill: allow` — `*-rs` matches by glob; bare tools like `libp2p`/`freenet` and `*-legacy` skills need an exact `allow`) so it is advertised when relevant. Do not try to force-load it via `instructions[]` (no effect in v2); to put content in every prompt, add it to `AGENTS.md`.

## Build Verification

Preferred (no Nix): `rust-toolchain.toml` provisions the toolchain; `just <recipe>` runs the tasks
(see `rust-env-rs`). Read the repo's `justfile` first and use `just build|clippy|fmt|test|lint`.

- Local equivalent: `cargo build --all-targets --all-features && cargo clippy --all-targets --all-features -- -D warnings && cargo fmt -- --check && cargo nextest run --all-targets --all-features && lele-lint --config lele.toml .`
- At the end of every non-trivial change run `cargo clippy --all-targets --all-features -- -D warnings` (`just clippy`) before the linter (`just lint` / `lele-lint --config lele.toml .`); fix `clippy -D warnings` first, then lint violations. **Agents NEVER run `bacon` — `bacon clippy` is USER-ONLY (TUI).**
- Legacy (crates that still ship `devenv.nix`): `devenv tasks run lele:clippy 2>&1`, `devenv tasks run lele:lint 2>&1` — each leaf does one job; raw `cargo … 2>&1` is the fallback only when neither `justfile` nor `devenv.nix` is present.

Path with spaces (e.g. `[AAI] Agentic AI`): set `[build] target-dir = "/tmp/frt-build"` (with `jobs = 6`) in `.cargo/config.toml`. `CARGO_TARGET_DIR` in the `[env]` table does NOT redirect cargo's target dir.

> **CRITICAL — NO PIPE:** never pipe a task runner (`devenv tasks run`, `just`) to `| tail`/`| head`/`| grep`. Pipes swallow output and hide diagnostics; always append `2>&1` on the caller.

## `#[allow(clippy::…)]` Gate — IMPORTANT — REALLY IMPORTANT

**No agent may add `#[allow(clippy::…)]` / `#![allow(clippy::…)]` for `clippy::pedantic` + `clippy::nursery` on its own.**

If `cargo clippy --all-targets --all-features -- -D warnings` surfaces a `clippy::pedantic` or `clippy::nursery` lint:

1. Report the exact lint + `file:line` (`Cargo.toml: E021` / `clippy.toml: E022` context).
2. Propose the minimal fix: rewrite the code (`checked_add`, `try_from`, `Ipv4Addr::LOCALHOST`, `if let` vs `match`, etc.) as first choice; `#[allow]` only as last resort.
3. **Stop and ask the user** — do not insert `#[allow]` unless the user explicitly says “allow X at Y”. The user gates all existing `#[allow]` for usefulness and will remove any deemed useless.
4. Existing `#[allow]` in the codebase are not to be broadened or copied to new sites without the same explicit approval — flag them for review instead.

Rationale: `E021` forces `pedantic=deny` + `nursery=deny`; per-site `allow` defeats the deny. Only the user decides which pedantic/nursery lints are noise for this workspace. This gate also applies to file-level `#![allow]` and `Cargo.toml` global `allow` overrides — both need explicit user approval.

## Lele Config Enforcement

`lele_enforce_config` and `lele_hook_resync` are retired (2026-10-10) — there is no floor-task
checker and no combined hook config. Config is a single `lele.toml` at the workspace root, consumed
via `lele-lint --config lele.toml <crate>`; the `justfile` + `.githooks` are the source of truth for
tasks and gates. The canonical template is at
`~/.config/opencode/skills/lele-rs/references/lele-rust-config/`; the freenet overlay is in the
`freenet` skill.

## Per-Repo Task Runner — Read First

Before any `cargo build` / `cargo clippy` / `cargo nextest run` / `lele-lint` on a repo, read its
`justfile` (legacy: `<crate>/devenv.nix`). If a `justfile` exists, run `just <recipe>`; only fall
back to raw `cargo nextest run --all-targets --all-features 2>&1` / `cargo clippy --all-targets --all-features -- -D warnings 2>&1` when neither exists. A workspace keeps `[profile.*]` and
`[workspace.dependencies]` at the root `Cargo.toml`, with crates under `crates/`. **Agents NEVER run `bacon` — it is USER-ONLY.**

Legacy: `devenv-rs-legacy` owns the per-crate `devenv.nix` engine (opt-in only — it is denied by
default; a project must add an exact `devenv-rs-legacy` allow). After editing `devenv.nix`, re-enter
`devenv shell` to regenerate hooks. Do not add `devenv.nix` to new repos — use `rust-env-rs`.
