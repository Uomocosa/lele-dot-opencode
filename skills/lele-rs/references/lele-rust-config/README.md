# lele-rust-config — Canonical General Rust Crate Template

GENERAL template (nightly, pinned deps, 6 lele tasks, 4 hooks). For Freenet contracts, overlay `freenet` skill — see `freenet/SKILL.md: Freenet Devenv Overlay`.

Copy these files to a crate root, replacing `<crate>` with the crate name:

- `Cargo.toml` — edition 2024, full `lints.clippy` (E021), pinned `=version` deps
- `clippy.toml` — 4 allows (E022)
- `devenv.nix` — `languages.rust channel nightly`, `cargo-nextest`, `CARGO_TARGET_DIR`, 6 `lele:*` tasks, 4 git-hooks (task-composed, `cd <crate> &&`, `always_run`)
- `devenv.yaml` — nixpkgs + git-hooks + fenix + rust-overlay
- `rust-toolchain.toml` — nightly pin for non-devenv fallback
- `lele.toml` — honesty defaults
- `src/lib.rs` / `src/hello.rs` — minimal demo for E018 `Deref` newtype
- `.gitignore` — `.devenv/` etc.

Invoke `/lele-rust-config` to audit/fix an existing crate or ` /lele-rust-config create <name>` to scaffold.
