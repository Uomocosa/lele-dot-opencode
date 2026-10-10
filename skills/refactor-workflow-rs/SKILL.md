---
name: refactor-workflow-rs
description: Use when refactoring one or more Rust crates batch-by-batch with user approval — audits the named crates (or the whole repo when none are named) against the loaded convention skills, presents a manifest of ALL proposed edits plus the first batch as before/after snippets, applies exactly one approved batch, re-verifies every reviewed crate, then stops and names the next batch.
---

# Refactor Workflow (Rust)

Interactive, batched refactoring with an explicit approval gate at **both** ends of every
batch: once to approve the plan, once to advance. **Never auto-carry into the next batch.**

## Invocation

- Command: `/refactor-workflow-rs {crates}` → this skill, with `$ARGUMENTS` as the crate list.
- Run from the **build** agent. Applying edits is forbidden in plan mode.

## Phase 0 — Resolve scope

- `crates` = the argument list. If empty, the user means the whole workspace.
- Enumerate crates deterministically: read `lele.toml` (respect `[lele.config] exclude`) and/or
  list directories containing `Cargo.toml`. Never invent a crate.
- Echo the resolved list back before auditing.

## Phase 1 — Load rules, then audit

1. `lele-rs` (always), then `lele-syntax-rs` (+ `references/RATIONALE.md`, `references/SMELLS.md`).
2. Per crate: if its `Cargo.toml` depends on a tool with a skill (`bevy-rs`, `serde-rs`, `clap-rs`,
   `jiff-rs`, `rayon-rs`, `criterion-rs`, `itertools-rs`, `reqwest-rs`, or a bare tool `libp2p` /
   `freenet` / `pixi`), load it.
3. `rust-env-rs` when touching `rust-toolchain.toml`, `justfile`, `.githooks`, `.cargo/config.toml`
   (legacy: `devenv-rs-legacy` for crates that still ship `devenv.nix`).
4. Read the repo's `justfile` FIRST for every repo under review — its recipes are the
   canonical verifiers (legacy: `<crate>/devenv.nix` `lele:*` tasks).
5. Audit each crate's `src/` against the loaded rule sets. Record every finding as
   `crate | file:line | rule | proposed change`.

## Phase 2 — Propose: manifest first, then batch 1 (NO EDITS)

First output MUST contain, in this order:

1. **Manifest** — a table of *every* proposed edit, grouped into batches:
   `batch | crate | file:line | rule | one-line change`.
2. **Batch 1 preview** — the literal before/after code for batch-1 items (per the global
   `CRITICAL: Code Snippets` rule).
3. A closing question: **"Proceed with batch 1, or re-scope?"**

Do **NOT** edit anything yet. Wait for the user's reply.

## Phase 3 — Apply exactly ONE batch

- A batch is ONE coherent rule family so a failure is attributable. Order batches:
  mechanical / lint-enforced (`E0xx`) → structural → design / judgement.
- Re-show the batch's before/after snippets (per the global snippet rule), then apply only that batch.
- Then verify **EVERY** crate under review — not just the edited one:
  - `just build|clippy|fmt|test|lint` per repo (`[[AGENTS.md::RUN_ALL_TESTS]]`), or raw
    `cargo …` when no `justfile` exists (legacy: `devenv tasks run <crate>:clippy|nextest|lint 2>&1`).
  - Never pipe a task runner (`just`, `devenv tasks run`) to `| tail` / `| head`; always append `2>&1`.
- If red: **STOP**, fix only this batch, re-run. Never advance on red.

## Phase 4 — All-green gate → explicit next-batch prompt (MANDATORY STOP)

Only when EVERY reviewed crate is green, emit exactly this shape and STOP:

```
✅ All green: <crate1>, <crate2>, <crate3>

Next batch (<n> of <total>):
  - <item a: file:line — one-line change>
  - <item b: file:line — one-line change>
  - <item c: file:line — one-line change>

Batch <n> preview:
  <for EVERY item: file:line, then the literal `// before` / `// after` code block,
   including knock-on edits (now-unused imports, callers, tests)>

Proceed with batch <n>, or change the batch? (reply yes / re-scope / stop)
```

**CRITICAL — code previews are mandatory at EVERY approval gate**, not only for batch 1.
The next-batch prompt is invalid without the literal before/after snippets for every item;
a bullet list of one-line changes is NOT a preview. The user approves code, not summaries.

Do **NOT** auto-carry. Wait for the reply, then loop to Phase 2/3 with the next batch.

## Hard rules

- No editing before explicit batch approval.
- A batch missing before/after snippets for any item is invalid — fix it before presenting.
- Do not add `#[allow(clippy::…)]` without explicit user sign-off.
- No commit, push, merge, or rebase. Agents never run `bacon`.
