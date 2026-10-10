# lele-rust-config — Canonical Rust Crate Template

Two variants:

- **Non-Nix (preferred)** — `rust-toolchain.toml` + `justfile` + `.githooks` + `.cargo/config.toml`.
  See the `rust-env-rs` skill.
- **Nix/devenv (legacy, opt-in)** — `devenv.nix` + `devenv.yaml`. See the `devenv-rs-legacy` skill.

Copy these files to a crate (or workspace) root, replacing `<crate>` with the crate name:

- `Cargo.toml` — edition 2024, full `lints.clippy` (E021), pinned `=version` deps. In a workspace,
  move `[profile.*]` and `[workspace.dependencies]` to the root `Cargo.toml` and use `dep.workspace = true`.
- `clippy.toml` — 4 `allow-*-in-tests` (E022); one per workspace root.
- `lele.toml` — honesty defaults + boundary examples; one per workspace root. Boundary `folders` are
  workspace-relative (crate-relative only when the crate is the repo root).
- `rust-toolchain.toml` — nightly channel + components (add `targets = ["wasm32-unknown-unknown"]` for freenet).
- `justfile` — `build`/`clippy`/`fmt`/`test`/`lint`/`hooks`/`ci` recipes (replaces `devenv tasks`).
- `.githooks/pre-commit` — composes the `just` recipes; install with `just hooks` (`core.hooksPath`).
- `.cargo/config.toml` — optional `[build] target-dir` (space-in-path) + `jobs`.
- `src/lib.rs` / `src/hello.rs` — minimal demo for the E018 `Deref` newtype.
- `.gitignore` — `target/`, `.devenv/`, etc.
- **(legacy)** `devenv.nix` / `devenv.yaml` — only for crates that still use Nix.

Invoke `/lele-rust-config` to audit/fix an existing crate or `/lele-rust-config create <name>` to scaffold.
