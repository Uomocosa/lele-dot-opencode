---
name: lele-lint-fix-rs
description: Use when a Rust crate has lele-lint / lele-bevy-lint (LELE0xx / LELEBEVY0xx) errors to clear autonomously — loops one rule code at a time (structural first, cosmetic last), fixes every occurrence, rebuilds, re-lints, and hands back ONE clean, uncommitted change set; git is read-only. Behaviour-preserving only; never weakens rules or config. For user-approved refactor batches use refactor-workflow-rs instead.
---

# lele lint fix (Rust)

Clear every lele lint error in ONE crate, autonomously, without changing behaviour.

## Setup
Load the `lele-lint-rules-rs` skill and read it IN FULL before the first edit. A fix for one
rule must not break another: check every file you create or edit against its
"Every file you create or edit" list.

Every shell call that runs `just` or `lele-*` starts with:
`export PATH="/home/uomocosa/Syncthing/[R] Rust/bin:$HOME/.cargo/bin:$HOME/.local/bin:$PATH" &&`
Always append `2>&1` and read the WHOLE output: never add `| tail`, `| head` or `| grep` to a
lint, build or test command. The lint report ends with per-code counts; you need all of it.
To see one code's errors, use the linter's own filter: `<linter> --only <CODE> <crate>`.

Find the lint command: read the repo's `justfile` `lint:` recipe and run only the line(s) for
the target crate. Inside `lele-rust-linter` that is
`cargo run -q -p lele-lint -- --config lele.toml crates/<crate>` (and `-p lele-bevy-lint` for
Bevy crates); elsewhere it is the installed `lele-lint` / `lele-bevy-lint` binaries.
Explain a rule: `<linter> --explain <CODE>`.

Learn a rule ONLY from `--explain`, each error's `help:` line and the `lele-lint-rules-rs` skill.
Never read the linter's own source code (`lele-rust-linter/crates/...`) to work out what
passes the check: the goal is code that follows the rule, not code that slips past it.

## Loop
0. Once, before any edit: save `git status --short` to a scratch file (baseline).
1. Lint the crate. Count errors per code. 0 errors → **Done**.
2. Pick ONE code. Priority: structural/placement first (helpers or types in method files,
   atomic file, free functions, methods layout, delegates, re-exports), then naming/imports,
   then comments and impl ordering last. Ties → fewest errors first.
3. Read the code's `Fix:` line in the `lele-lint-rules-rs` skill and `--explain <CODE>` once;
   follow its Good example. Each error's `help:` line is the fix for that exact site.
4. Fix EVERY error of that code, same pattern each time. More than ~25 → one folder at a time.
   If a message says to run `--sync-methods`, run the repo's `just sync-methods`.
   Before saving each edit, check the file against the `lele-lint-rules-rs` "Every file you
   create or edit" list. Most often: a helper that becomes a method keeps at most 3
   statements inline (`#[rustfmt::skip]` block, no constructors in it); a longer one goes
   behind an empty shell in the type's `#[atomic_delegates]` block with its body and a
   `test_usage` test in `methods/<type>/<fn>.rs`.
   LELE031 (comments): never just delete a comment. First move what it says into the code:
   rename the item so its name says it, or, when it explains *why* (an edge case, a format
   quirk), add an assertion to the `test_usage` test that proves it. Then delete it.
5. `just build 2>&1` and `just test 2>&1`; repair anything you broke before continuing.
5b. **Regression check.** Lint again and compare per-code counts with step 1. If any code went
   up, or a new code appeared in a file you edited, your edit caused it: fix those errors now,
   before picking the next code. A code is finished only when the TOTAL went down.
6. Diff `git status --short` against the baseline: every path that is new or changed since
   the baseline must be under `<crate path>/src/` or `<crate path>/methods/`, or be a
   rename-follow edit in `<crate path>/tests|benches|examples/`. Anything else
   → STOP and report (do not revert it yourself).
   Exception: `Cargo.lock` changes made by `cargo`/`just` (dependency re-resolution) are
   expected. Never stop for them, never revert them; list them in the final report.
7. Back to 1 — fixes cascade, never trust the previous list.

## Hard rules
- **Git is read-only until Done.** Never run `git reset`, `git checkout`, `git restore`,
  `git stash`, `git clean`, `git rm`, `git mv` or `git add` during the loop. The working tree
  holds other people's uncommitted work; reverting a file you "broke" destroys it. To undo your
  own edit, re-edit the file by hand.
- **Write scope = `<crate path>/src/` and `<crate path>/methods/`**, plus the
  rename-following exception below. Never edit: the repo root (`Cargo.toml`, `lele.toml`,
  `justfile`, `README.md`, `prek.toml`),
  `lele-lint-test-crates/`, `expected.toml`, `RULES.md`/`SKILL.md` (only `just docs` may write
  them), or another crate.
- **Rename-following exception (`<crate path>/tests/`, `benches/`, `examples/`, doc tests).**
  When a fix renames or moves an item and these stop compiling, you MAY update only the
  `use` lines, paths and identifiers that name it, mirroring the rename exactly. Nothing else:
  no changes to assertions, expected values, test names, fixture/test-crate paths, control
  flow, or added/removed tests. Each such file goes in the final report as "rename-follow".
- **Failing tests are not yours to rewrite.** A test that compiles but FAILS after your edit
  means behaviour changed: fix your src edit, never the test. A test failing that your edits
  didn't touch → STOP and report it.
- Behaviour-preserving only. Never edit rule logic, `lele.toml` allow/exclude lists, clippy
  config, test-crate fixtures or `expected.toml` to make an error disappear.
- Same error survives 2 attempts, or a fix needs a forbidden change → STOP and report
  code, file, message and what you tried.

## Done
Run `just fmt`, `just clippy`, `just test` and the lint — all clean. Then do NOT commit:
report to the user and let them commit (the tree contains other uncommitted work you must
not sweep into your commit or lose). Report per-code counts fixed and the list of files you changed (rename-follow files
separately, with the old → new names).
