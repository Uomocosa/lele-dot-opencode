---
description: Bring a crate up to the lele-rs canonical config (or scaffold new) — audits Cargo.toml/clippy.toml/devenv.* per lele-rs template
agent: primary
---

Audit or scaffold a Rust crate toward the `lele-rs` canonical template (`~/.config/opencode/skills/lele-rs/references/lele-rust-config/` + `freenet` overlay when needed).

**Usage:** `/lele-rust-config [crate-path] [--check]` — audit/fix in place. `/lele-rust-config create <name> [--with-freenet]` — scaffold new crate. `$ARGUMENTS` is raw args.

**Routing:**
- `create <name>` → Mode 2 (scaffold)
- otherwise Mode 1 (audit), `crate-path` defaults to `.` (cwd), `--check` = report only, `--with-freenet` forces `freenet` overlay, otherwise auto-detects `contract/Cargo.toml` or `dependencies.freenet`.

**Steps — Mode 1 Audit/Fix `[crate-path] [--check] [--with-freenet]`:**

1. Resolve `crate = <crate-path or .>`; verify `Cargo.toml` exists else error → suggest `create`.
2. Load canonical refs: `lele-rs/SKILL.md: Lele Rust Config` + `lele-rs/references/lele-rust-config/{Cargo.toml,clippy.toml,devenv.nix,devenv.yaml,rust-toolchain.toml,lele.toml,.gitignore}` + `AGENTS.md: Devenv Tasks MANDATORY` + `lele-lint-rs E021/E022` + `devenv-rs tasks/hooks` + `freenet: Freenet Devenv Overlay` if auto-detected or `--with-freenet`.
3. Audit (diff, do not yet write):
   - `Cargo.toml`: `edition = "2024"`, `lints.clippy` full E021 block (pedantic+nursery deny + 13 denies), pinned `=version` deps (flag unpinned/caret), `lints.workspace` alternative accepted. Propose patch toward template, preserving crate name/version/description.
   - `clippy.toml`: 4 allows (E022).
   - `rust-toolchain.toml`: `channel = "nightly"` (general default).
   - `devenv.nix`: `languages.rust.channel = "nightly"`, `cargo-nextest`, `env.CARGO_TARGET_DIR`, 6 tasks `lele:build/clippy/fmt/nextest/lint/taxonomy_check` with `showOutput=true`, `2>&1` caller-side, `after` never for leaves, 4 hooks task-composed `cd <crate> && devenv tasks run lele:* 2>&1` with `always_run=true` + `pass_filenames=false`. Flag drift (e.g. `stable` → `nightly`, missing tasks/hooks, `| tail`).
   - `devenv.yaml`: 4 inputs `nixpkgs/git-hooks/fenix/rust-overlay`.
   - `lele.toml`: required, honesty defaults.
   - `.gitignore`: `.devenv/` etc.
   - `src/` shape: `lib.rs` flattening quick check; run `cargo run --manifest-path ../lele_lint/Cargo.toml -- --scan-folder` if available.
   - Never add `bacon`, never `| tail`/`| head`, always `2>&1`.
4. If freenet detected (or `--with-freenet`): also audit `languages.rust.targets`, `gccStdenv/clang/glibc`, `C_INCLUDE_PATH`, `freenet:*` tasks, `build.rs` WASM isolation (`contract/target` not `CARGO_TARGET_DIR`).
5. Report unified diff summary. If `--check`, stop. Else ask to apply; on confirm, patch files (replace `<crate>` placeholder, keep crate identity), then **re-enter `devenv shell`** to regenerate `.pre-commit-config.yaml` (hooks) and provision `nightly` + `wasm32-unknown-unknown` via `fenix` (otherwise hooks stay stale — `freenet_example` showed 4 vs 5 hooks until `devenv shell`). Then verify: `devenv tasks run lele:clippy 2>&1` (or `CARGO_TARGET_DIR=/tmp/frt-build cargo clippy -- -D warnings 2>&1` fallback + `rustup target add wasm32-unknown-unknown --toolchain nightly` if not via `devenv`) + `cargo run --manifest-path ../lele_lint/Cargo.toml 2>&1`.

**Steps — Mode 2 Scaffold `create <name>`:**

1. Run `cargo new <name> --lib --edition 2024` (or `--bin` if `--bin` in args) in parent dir of `crate-path` or cwd.
2. Overlay template files from `references/lele-rust-config/` onto the new crate, replacing `<crate>` with `<name>` in `Cargo.toml`/`devenv.nix` hook entries.
3. If `--with-freenet` or contract requested, overlay `freenet` additions and create `contract/` stub + `build.rs` WASM builder.
4. `git init` if not already in repo, ensure `.gitignore`. Print next steps: `cd <name> && devenv tasks run lele:clippy 2>&1`.

**Safety:** General mode never injects freenet overlay unless detected/forced. Pinned `=version` uses template versions; user bumps via `cargo update` then re-pin.

**CRITICAL — NO PIPE on devenv tasks:** Never `| tail`/`| head`/`| grep` on `devenv tasks run … 2>&1` — tasks use `showOutput=true` and stream; pipes swallow output and `tail` blocks 120s with `(no output)` on fresh `cargo` builds (hides `cargo` stderr). Always bare `devenv tasks run <task> 2>&1`.
