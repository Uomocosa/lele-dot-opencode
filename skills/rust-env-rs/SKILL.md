---
name: rust-env-rs
description: Use for the preferred non-Nix Rust dev environment — rust-toolchain.toml (toolchain), a justfile (tasks), .githooks via core.hooksPath (hooks), and .cargo/config.toml (target-dir/jobs). Covers workspace layout (crates/, root Cargo.toml) and one root lele.toml/clippy.toml per repo. Nix/devenv is legacy (see devenv-rs-legacy).
---

# rust-env-rs — Rust Dev Environment (no Nix)

The preferred, reproducible Rust environment: one toolchain file, one task file, one hook file
per repo. No Nix, no container, no `setup.sh` — `rustup` + `cargo` + `just` is the whole install.

## 1. Toolchain — `rust-toolchain.toml`

rustup provisions the channel, components and targets automatically the first time you run `cargo`.

```toml
[toolchain]
channel = "nightly"
components = ["rustc", "cargo", "clippy", "rustfmt"]
targets = ["wasm32-unknown-unknown"]   # only freenet/contract repos
```

## 2. Tasks — `justfile`

`just` is the single source of truth for tasks (replaces `devenv tasks`). Install once:
`cargo install just`.

```just
set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

build:  ; cargo build --all-targets --all-features
clippy: ; cargo clippy --all-targets --all-features -- -D warnings
fmt:    ; cargo fmt -- --check
test:   ; cargo nextest run --all-targets --all-features
lint:   ; lele-lint --config lele.toml .
hooks:  ; git config core.hooksPath .githooks && chmod +x .githooks/*
ci: build fmt clippy test
```

- Keep leaves independent (no `just a: b` chains for checks); `ci` is the only aggregate.
- In a workspace, run the linter once per crate: `lele-lint --config lele.toml crates/<name>`.

## 3. Hooks — `.githooks/` + `core.hooksPath`

No external hook runner (no `prek`). `just hooks` points git at the repo's tracked hooks dir.

```sh
#!/usr/bin/env sh
set -eu
just fmt && just clippy && just lint && just test
```

## 4. Cargo config — `.cargo/config.toml`

```toml
[build]
target-dir = "/tmp/frt-build"   # space-in-path workaround (tikv-jemalloc-sys rejects spaces)
jobs = 6                        # bound peak RAM on heavy bevy/freenet cold builds
```

`CARGO_TARGET_DIR` in the `[env]` table does **not** redirect cargo's own target dir — use
`[build] target-dir`.

## 5. Workspace layout

```
<repo>/
  Cargo.toml           # [workspace] members = ["crates/..."], [profile.*], [workspace.dependencies]
  rust-toolchain.toml  clippy.toml  lele.toml  justfile  .githooks/pre-commit
  crates/<name>/       # one crate per dir
```

`[profile.*]` is allowed only at the workspace root — members must drop it. Share versions via
`[workspace.dependencies]` and use `dep.workspace = true` in members.

## 6. One root config per repo

- `lele.toml` at the workspace root; run `lele-lint --config lele.toml <crate>`. Boundary
  `folders` are **workspace-relative** (the config file's directory is the base).
- `clippy.toml` (the four `allow-*-in-tests = true`) at the root; the linter finds it by walking up.

## 7. System libraries — README, not a script

Binaries that need OS packages document them in the repo `README` (no `setup.sh`, no container):

- Linux (bevy/freenet): `libasound2-dev libudev-dev libwayland-dev libxkbcommon-dev libx11-dev mesa-vulkan-drivers ffmpeg`
- macOS: `brew install ffmpeg`; Windows: `winget install Gyan.FFmpeg`
- Pure-Rust crates need none.

## Legacy

Crates that still carry `devenv.nix`/`devenv.yaml` use the opt-in `devenv-rs-legacy` skill. Do not
add `devenv.nix` to new repos.
