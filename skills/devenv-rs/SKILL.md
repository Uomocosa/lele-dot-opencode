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
    bacon
    cargo-seek
    cargo-nextest
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
| **Env / Basics** | `env.*`, `enterShell` | `https://devenv.sh/basics/` | `env.LD_LIBRARY_PATH`, `env.DATABASE_URL`, `CARGO_TARGET_DIR=/tmp/frt-build` when path has spaces |
| **Tasks (DAG)** | `tasks."ns:name".exec/before/after` | `https://devenv.sh/tasks/` | DAG via `before`/`after`, suffix `@ready`/`@completed`, `devenv:enterShell` + `devenv:enterTest` lifecycle, `devenv tasks run` |
| **Processes** | `processes.<name>.exec` | `https://devenv.sh/processes/` | Native manager, supervision, readiness probes, socket activation, `after = ["devenv:processes:db@ready"]`, `devenv up [-d]` |
| **Services** | `services.<name>.enable` | `https://devenv.sh/services/` | 42 prebuilt services over processes: `services.postgres.enable`, `services.redis.enable`, `initialDatabases` |
| **Git Hooks** | `git-hooks.hooks.<name>` | `https://devenv.sh/git-hooks/` | Via `git-hooks.nix`; `clippy`, `rustfmt`, `cargo-check`; custom `entry`; default runner `pkgs.prek`; `git-hooks.hooks.clippy.settings.allFeatures = true` |
| **Tests** | `enterTest` | `https://devenv.sh/tests/` | `enterTest = '' wait_for_port 8080; cargo nextest run ''`; processes auto-started; guard with `config.devenv.isTesting` |
| **Containers (OCI)** | `containers.<name>.*` | `https://devenv.sh/containers/` | `devenv container build shell|processes`, `startupCommand`, `copyToRoot`, `registry` |
| **Poly/Monorepo Composable** | `imports`, `inputs`, `outputs` | `https://devenv.sh/guides/polyrepo/` + `https://devenv.sh/inputs/` + `https://devenv.sh/outputs/` | `imports = [ ../shared/devenv.nix ]`, `devenv.yaml` inputs, `outputs.app = config.languages.rust.import ./app {}` (crate2nix), `config.lib.tryGetInput` |

## 4. Tasks — Starlark-like DAG

> **Rule — prefer tasks over raw commands:** When a crate has `devenv.nix` with `tasks`, always run `devenv tasks run <task>` (e.g. `devenv tasks run lele:verify`, `devenv tasks run lele:nextest`) instead of invoking the task's underlying command by hand (`cargo clippy`, `cargo nextest run`, `cargo fmt`, `bacon clippy`, …). Read `devenv.nix` first to discover the canonical task; raw `cargo …` is the fallback only when `devenv.nix` is absent.

```nix
# https://devenv.sh/tasks/
tasks = {
  "myapp:setup".exec = "cargo build --all-targets";
  "myapp:check".exec = "cargo clippy -- -D warnings && cargo fmt -- --check";
  "myapp:test".exec = "cargo nextest run --all-targets";
  "lele:verify".exec = ''
    cargo build --all-targets
    cargo clippy -- -D warnings
    cargo fmt -- --check
    cargo nextest run --all-targets
    bacon --headless clippy -- -- -D warnings
    cargo run --manifest-path ../lele_lint/Cargo.toml
  '';
  "lele:nextest".exec = "cargo nextest run --all-targets";
  "lele:bacon-clippy".exec = "bacon --headless clippy -- -- -D warnings";
  "lele:lint".exec = "cargo run --manifest-path ../lele_lint/Cargo.toml";
  "devenv:enterShell".after = [ "myapp:setup" ];
  "devenv:enterTest".after = [ "lele:verify" ];
};
```

`lele:verify` is the crate-local smoke including `bacon --headless clippy` before `lele_lint` (bacon also available separately via `lele:bacon-clippy`; interactive use is `bacon clippy -- -- -D warnings` without `--headless`). Run `devenv tasks run lele:verify` for the full chain, `devenv tasks run lele:nextest` for nextest only — do not run `cargo nextest run --all-targets` or `cargo clippy -- -D warnings` directly when `devenv tasks run lele:*` exists. Processes are tasks too: `devenv:processes:web-server`. Dependency states: `after = ["devenv:processes:db@ready"]` (default) vs `@completed`. See `https://devenv.sh/tasks/#dependency-states`.

## 5. Git Hooks — Replaces clippy/fmt in CI

```nix
# https://devenv.sh/git-hooks/ — requires devenv.yaml git-hooks input
git-hooks.hooks = {
  clippy.enable = true;
  clippy.settings.allFeatures = true;
  rustfmt.enable = true;
  cargo-check.enable = true;
};
```

CI note: when this is enabled, `crate-tag-ci` test gate may run `devenv test` / `devenv tasks run myapp:check` instead of raw `cargo clippy -- -D warnings && cargo fmt -- --check`. Keep raw commands as fallback when `devenv` is not present. Hooks install via `prek` by default; `.pre-commit-config.yaml` is a symlink to the store — do not commit it.

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
- Do not add `#[allow(clippy::pedantic)]` / `#[allow(clippy::nursery)]` (or `Cargo.toml` global `allow` for them) without explicit user approval — see `lele-rs` `#[allow(clippy::…)]` Gate.
