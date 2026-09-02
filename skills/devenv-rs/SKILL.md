---
name: devenv-rs
description: Use when creating or editing devenv.nix/devenv.yaml for Rust crates. Covers languages.rust nightly/stable, packages, scripts, env, enterShell, git-hooks, tasks, processes, services, tests, containers, and poly/monorepo composable imports. Always loaded via lele-rs.
---

# devenv-rs — Rust devenv Configuration (ALWAYS LOADED via lele-rs)

Reproducible Rust environment via `devenv` (Nix). This skill is Rust-only; for other languages extend `devenv` generically. Bound via `lele-rs` indexer — add `~/.config/opencode/skills/devenv-rs/SKILL.md` to `opencode.json: instructions[]` alongside `lele-rs`.

## 1. Scaffold

```bash
devenv init          # creates devenv.nix, devenv.yaml, .gitignore
devenv shell         # activate
devenv up            # start processes
devenv tasks run <task>
devenv test          # enterTest with processes
devenv container build|copy|run <name>
devenv search <pkg>
devenv update        # pin devenv.yaml -> devenv.lock
```

## 2. Per-Crate Example Config (template — copy to each crate root)

Per-crate `devenv.nix` is the source of truth; `devenv.yaml` pins inputs. Example lives per crate (e.g. `freenet_libp2p_bevy_example_1/devenv.nix`). Shared base may be imported.

```nix
# devenv.nix — https://devenv.sh/getting-started/ + https://devenv.sh/reference/options/
{ pkgs, lib, config, inputs, ... }: {
  # https://devenv.sh/languages/rust/
  languages.rust = {
    enable = true;
    channel = "nightly";
    components = [ "rustc" "cargo" "clippy" "rust-analyzer" ];
  };

  # https://devenv.sh/packages/
  packages = with pkgs; [
    cargo-nextest
    cargo-seek
    cargo-generate
  ];

  # https://devenv.sh/scripts/
  scripts.watcher = {
    exec = ''
      watchexec -c -e rs \
      "cargo clippy && cargo nextest run --all-targets && cargo run"
    '';
    packages = [ pkgs.watchexec ];
  };

  # https://devenv.sh/basics/ — env
  env.LD_LIBRARY_PATH = lib.makeLibraryPath [
    pkgs.zlib
  ];
  env = {
    DATABASE_URL = "postgres://user:pass@localhost/dbname";
  };

  # https://devenv.sh/basics/ — enterShell (runs before shell + before devenv up)
  enterShell = ''
    echo "Crates ready to update with 'cargo update':"
    cargo update -n
  '';

  # https://devenv.sh/git-hooks/ — replaces cargo clippy/fmt in CI
  git-hooks.hooks = {
    clippy.enable = true;
  };
}
```

```yaml
# devenv.yaml — https://devenv.sh/inputs/
inputs:
  nixpkgs:
    url: github:NixOS/nixpkgs/nixos-unstable
  git-hooks:
    url: github:cachix/git-hooks.nix
  fenix:                          # needed for channel = "nightly"/"stable"/"beta"
    url: github:nix-community/fenix
    follows: nixpkgs
```

## 3. Capability Map (what each source has)

| Capability | Option surface | URL | Notes for Rust |
|------------|---------------|-----|----------------|
| **Languages** | `languages.rust.*` | `https://devenv.sh/languages/rust/` | `enable`, `channel` (`nixpkgs`/`stable`/`beta`/`nightly`), `version`, `components`, `targets = ["wasm32-unknown-unknown"]` for contracts, `toolchainFile`, `rustflags`, `mold`/`lld` |
| **Packages** | `packages` | `https://devenv.sh/packages/` | 100k+ nixpkgs pkgs; `pkgs.bacon`, `cargo-nextest`, `cargo-generate`, plus `pkgs.watchexec` for scripts |
| **Scripts** | `scripts.<name>.exec` | `https://devenv.sh/scripts/` | Shell snippets with own `packages`; callable directly in `enterShell`/`tasks` |
| **Env / Basics** | `env.*`, `enterShell` | `https://devenv.sh/basics/` | `env.LD_LIBRARY_PATH`, `env.DATABASE_URL`, `CARGO_TARGET_DIR=/tmp/frt-build` when path has spaces — **must not be reused as WASM `target-dir` in `build.rs`** (see §4 WASM isolation). |
| **Tasks (DAG)** | `tasks."ns:name".exec/before/after` | `https://devenv.sh/tasks/` | DAG via `before`/`after` for `processes` readiness (`after = ["devenv:processes:db@ready"]`) and `devenv:enterShell`/`devenv:enterTest` lifecycle — **avoid `after` for leaf check tasks** (turns `fmt` into `build+clippy+fmt`, hits LLM timeout + `Blocking waiting for file lock` on shared `CARGO_TARGET_DIR`). Prefer independent leaves; chain only in a single CI `exec` if needed. `devenv tasks run` streams task output, but caller needs `2>&1` to surface `cargo` stderr (see §4). Use `showOutput = true` so fresh `cargo` tasks that print `Finished` still stream. |
| **Processes** | `processes.<name>.exec` | `https://devenv.sh/processes/` | Native manager, supervision, readiness probes, socket activation, `after = ["devenv:processes:db@ready"]`, `devenv up [-d]` |
| **Services** | `services.<name>.enable` | `https://devenv.sh/services/` | 42 prebuilt services over processes: `services.postgres.enable`, `services.redis.enable`, `initialDatabases` |
| **Git Hooks** | `git-hooks.hooks.<name>` | `https://devenv.sh/git-hooks/` | Via `git-hooks.nix`; `clippy`, `rustfmt`, `cargo-check`; custom `entry`; default runner `pkgs.prek`; `git-hooks.hooks.clippy.settings.allFeatures = true` |
| **Tests** | `enterTest` | `https://devenv.sh/tests/` | `enterTest = '' wait_for_port 8080; cargo nextest run ''`; processes auto-started; guard with `config.devenv.isTesting` |
| **Containers (OCI)** | `containers.<name>.*` | `https://devenv.sh/containers/` | `devenv container build shell|processes`, `startupCommand`, `copyToRoot`, `registry` |
| **Poly/Monorepo Composable** | `imports`, `inputs`, `outputs` | `https://devenv.sh/guides/polyrepo/` + `https://devenv.sh/inputs/` + `https://devenv.sh/outputs/` | `imports = [ ../shared/devenv.nix ]`, `devenv.yaml` inputs, `outputs.app = config.languages.rust.import ./app {}` (crate2nix), `config.lib.tryGetInput` |

## 4. Tasks — Starlark-like DAG

> **Rule — prefer tasks over raw commands:** When a crate has `devenv.nix` with `tasks`, always run `devenv tasks run <task> 2>&1` (e.g. `devenv tasks run lele:clippy 2>&1`, `devenv tasks run lele:nextest 2>&1`) instead of invoking the task's underlying command by hand (`cargo clippy`, `cargo nextest run`, `cargo fmt`, …). `devenv tasks run` streams the task's output as it runs, but `cargo` writes to stderr — the caller must add `2>&1` (documented caller-side, not inlined in `exec`) so the LLM/tool sees the full stream. Read `devenv.nix` first to discover the canonical task; raw `cargo …` is the fallback only when `devenv.nix` is absent. Tasks should be independent leaves; `after` is for `processes` readiness, not for chaining leaf checks.

```nix
# https://devenv.sh/tasks/
tasks = {
  "lele:build" = { exec = "cargo build --all-targets --features dev"; showOutput = true; };
  "lele:clippy" = { exec = "cargo clippy --all-targets --features dev -- -D warnings"; showOutput = true; };
  "lele:fmt" = { exec = "cargo fmt -- --check"; showOutput = true; };
  "lele:nextest" = { exec = "cargo nextest run --all-targets --features dev"; showOutput = true; };
  "lele:lint" = { exec = "cargo run --manifest-path ../lele_lint/Cargo.toml"; showOutput = true; };
  "lele:taxonomy_check" = { exec = "cargo run --manifest-path ../lele_function_taxonomy/Cargo.toml --features rustc-private -- --manifest-path ./Cargo.toml"; showOutput = true; };
  "freenet:contract-harness" = { exec = "cargo test --manifest-path ../freenet_contract_harness/Cargo.toml -- --nocapture"; showOutput = true; };
  # no after, no verify sink — each leaf does one job; use a single CI exec if chaining is needed
};
```

Leaf tasks need `showOutput = true` so `devenv-tasks` (PR #2231) streams `stdout` via `println!` instead of capturing until failure — without it `cargo` `Finished` on fresh builds is swallowed and `| tail` on the caller hangs waiting for lines that never flush. Use `showOutput` not `| tail`; `tail` on fresh tasks blocks 120s timeout with `(no output)`.

WASM isolation: when `env.CARGO_TARGET_DIR="/tmp/frt-build"` is set for space-in-path, `build.rs` must NOT reuse it for `contract/target`. Isolate:
```rust
// build.rs — DO NOT use CARGO_TARGET_DIR for wasm
let wasm_target_dir = "contract/target".to_string();
build_contract("contract/Cargo.toml", "contract.wasm", &wasm_target_dir, out);
```
Otherwise host `cargo` holds `/tmp/frt-build/.cargo-lock` while `build.rs` spawns inner `cargo --target-dir /tmp/frt-build` that `Blocking waiting for file lock`s itself → LLM timeout. `needs_build` mtime check hides it until `contract/src/lib.rs` is touched, so the bug appears intermittent.
```

Leaf tasks are **independent** — `devenv tasks run lele:fmt 2>&1` runs only `cargo fmt` (<1s), not `build+clippy+fmt`. The old `after` chain (`lele:fmt.after=["lele:clippy"].after=["lele:build"]` → `lele:verify` sink, plus `lele:bacon-clippy` via `bacon --headless`) made every leaf pay the full pipeline cost (2-5min, `Blocking waiting for file lock` on shared `CARGO_TARGET_DIR=/tmp/frt-build`, LLM 120s timeout) and is now an anti-pattern — deleted. `bacon` is TUI-only (`bacon clippy` interactive); it has no better clippy output than `cargo clippy` and `bacon --headless` hangs in tasks — do not add it to `packages` for tasks. Single-line `exec = "cargo ..."` streams cleanly; avoid `set -e; echo ">>> ..."; ...; echo "done"` wrappers and duplicate `cargo clippy --tests` (`--all-targets` already covers it). Processes are tasks too: `devenv:processes:web-server`. Dependency states: `after = ["devenv:processes:db@ready"]` (default) vs `@completed`. See `https://devenv.sh/tasks/#dependency-states`.

## 5. Git Hooks — Blocking pre-commit via task composition (freenet_example template)

This is the canonical template — keep the four-hook freenet example. Each hook composes an existing `tasks` leaf (single source of truth, no `cargo` duplication) and blocks unless all checks pass.

```nix
# https://devenv.sh/git-hooks/ — requires devenv.yaml git-hooks input
# freenet_example/devenv.nix — four separate hooks so prek names the failing one
git-hooks.hooks = {
  lele-clippy = {
    enable = true;
    name = "clippy (freenet_example)";
    entry = "bash -c 'cd freenet_example && devenv tasks run lele:clippy 2>&1'";
    pass_filenames = false;
    always_run = true;
  };
  lele-fmt = {
    enable = true;
    name = "fmt (freenet_example)";
    entry = "bash -c 'cd freenet_example && devenv tasks run lele:fmt 2>&1'";
    pass_filenames = false;
    always_run = true;
  };
  lele-lint = {
    enable = true;
    name = "lele_lint (freenet_example)";
    entry = "bash -c 'cd freenet_example && devenv tasks run lele:lint 2>&1'";
    pass_filenames = false;
    always_run = true;
  };
  lele-taxonomy = {
    enable = true;
    name = "taxonomy_check (freenet_example)";
    entry = "bash -c 'cd freenet_example && devenv tasks run lele:taxonomy_check 2>&1'";
    pass_filenames = false;
    always_run = true;
  };
};
```

Rules:
* **Compose, don’t duplicate** — `entry` calls `devenv tasks run <task> 2>&1` (the leaf `exec = "cargo ..."` stays the single source of truth). Changing the task automatically changes the hook.
* **`cd <crate> &&` is required** — `.git/hooks/pre-commit` (`prek hook-impl --config=.../freenet_example/.pre-commit-config.yaml`) runs from the repo root (`/projects`). Without `cd freenet_example &&`, `devenv tasks run` fails `File devenv.nix does not exist`.
* **`always_run = true`, not `types = ["rust"]`** — `types`/`files` with `always_run=false` skips the hook when `devenv.nix` (or any non-`rust` file) is the only staged file (`clippy (no files to check) Skipped`), so a broken `devenv.nix` could be committed. `always_run=true` makes the gate blocking on every `git commit`.
* **`pass_filenames = false`** — `cargo` ignores filenames; `prek` must not append them.
* Simple `clippy.enable = true` / `rustfmt.enable = true` still exists for trivial crates, but for `freenet_example` they are wrong: they run `cargo fmt --all` from repo root → `cargo metadata could not find Cargo.toml in /projects`.

Hooks install via `prek` (`devenv shell` regenerates `freenet_example/.pre-commit-config.yaml` symlink + `.git/hooks/pre-commit` wrapper). Do not commit `.pre-commit-config.yaml` or `.pre-commit-config.json` — they are generated. `crate-tag-ci` tag pipeline still uses raw `cargo` as fallback when `devenv` is absent.

## 6. Processes & Services

```nix
# https://devenv.sh/processes/ + https://devenv.sh/services/
services.postgres = {
  enable = true;
  initialDatabases = [{ name = "app"; }];
};
services.redis.enable = true;
processes.api.exec = "secretspec run -- cargo run";
processes.watcher.exec = "${lib.getExe pkgs.watchexec} -c -e rs -- cargo nextest run --all-targets";
```

Ready probes, `after` dependencies, automatic port allocation prevent parallel-env collisions. Alternative managers (`process-compose`, `overmind`) via `process.manager`.

## 7. Tests & Containers

```nix
# https://devenv.sh/tests/
enterTest = ''
  wait_for_port 8080
  curl -s localhost:8080 | grep "Hello"
'';

# https://devenv.sh/containers/
containers.processes = {
  name = "myapp";
  startupCommand = config.processes.api.exec;
};
```

`devenv test` starts processes, runs `enterTest`, tears down. Condition on `config.devenv.isTesting` to exclude heavy frontend processes during tests.

## 8. Poly/Monorepo Composable

```nix
# crate-root devenv.nix — https://devenv.sh/guides/polyrepo/
{ pkgs, ... }: {
  imports = [ ../shared/devenv.nix ];
  languages.rust.targets = [ "wasm32-unknown-unknown" ];
  outputs.contract = config.languages.rust.import ./contract {};
}
```

Shared devenv at workspace root, per-crate overrides for `targets`, `channel`, extra `packages`. `devenv.yaml` at each level composes via `inputs`.

## 9. Rust Nightly Detail

`channel = "nightly"` requires `fenix` input (see `devenv.yaml` above). Example: `https://github.com/cachix/devenv/blob/main/examples/rust/devenv.nix`. Without `fenix`, use `channel = "nixpkgs"`.

## 10. Do Not

- Do not run `rustup` inside devenv — toolchain comes from `languages.rust`.
- Do not commit `.pre-commit-config.yaml` or `.devenv/` to git.
 - Do not rebuild WASM per user for Freenet — ship canonical `contract.wasm` via `include_bytes!` (see `freenet` skill).
 - When project path has spaces, set `env.CARGO_TARGET_DIR = "/tmp/frt-build"` in devenv.nix or prefix cargo calls.
 - When `env.CARGO_TARGET_DIR` is set, `build.rs` must NOT reuse it for WASM `contract/target` — use isolated `wasm_target_dir = "contract/target"` (see §4 WASM isolation) to avoid `Blocking waiting for file lock` self-deadlock.
 - Always set `showOutput = true` on `tasks` leaves — without it `devenv-tasks` captures `stdout` and fresh `cargo` (`Finished` only) appears as `{}` with no streaming. **NEVER add `| tail`, `| head`, `| grep` or any pipe to `devenv tasks run`** — pipes swallow the streams and mask the hang (fresh `cargo` with zero lines blocks `tail` until 120s timeout with `(no output)`). Use `showOutput = true` and bare `devenv tasks run <task> 2>&1` instead.
- Do not add `#[allow(clippy::pedantic)]` / `#[allow(clippy::nursery)]` (or `Cargo.toml` global `allow` for them) without explicit user approval — see `lele-rs` `#[allow(clippy::…)]` Gate.
- Do not add `bacon` / `bacon --headless` as a task (`lele:bacon-clippy`) — `bacon` is interactive TUI only (`bacon clippy`), headless hangs; `cargo clippy` already satisfies `-D warnings`.
- Do not chain leaf tasks with `after` (e.g. `lele:fmt.after=["lele:clippy"]`) — it makes every LLM call pay the full pipeline and hit `Blocking waiting for file lock` / 120s timeout. Keep leaves independent; delete the `lele:verify` sink.
- Do not duplicate `cargo clippy --tests` when `cargo clippy --all-targets` is used.
- When calling tasks from an LLM/tool, always add `2>&1` (`devenv tasks run <task> 2>&1`) — `cargo` writes diagnostics to stderr and the tasks stream is caller-side merged; do not inline `2>&1` into `exec`.
- Do not make blocking hooks with `types = ["rust"]` alone — `always_run=false` skips when only `devenv.nix` etc. is staged (`no files to check` skips gating). Use `always_run = true` for gate hooks.
- Do not run `devenv tasks run` from a hook without `cd <crate> &&` — hook CWD is repo root, not the crate dir (`File devenv.nix does not exist`).
- Do not duplicate `cargo` strings in hooks — compose `devenv tasks run <leaf> 2>&1` (single source of truth).
- Do not rewrite public history with `reset`/`push --force-with-lease` — use forward `revert`/fix commits; force needs explicit user “force” command (per `opencode-git-workflow`).
