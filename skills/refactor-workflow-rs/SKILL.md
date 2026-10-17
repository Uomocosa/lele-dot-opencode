---
name: refactor-workflow-rs
description: Use when refactoring one or more Rust crates batch-by-batch with user approval — audits the named crates (or the whole repo when none are named) against the loaded convention skills, presents a manifest table of at most 5 batches plus the literal before/after snippets for batch 1, applies exactly one approved batch, re-verifies every reviewed crate, then stops and names the next batch.
---

# Refactor Workflow (Rust)

Interactive, batched refactoring with an explicit approval gate at **both** ends of every
batch: once to approve the plan, once to advance. **Never auto-carry into the next batch.**

## Invocation

- Command: `/refactor-workflow-rs {crates}` → this skill, with `$ARGUMENTS` as the crate list.
- Run from the **build** agent. Applying edits is forbidden in plan mode.

## Phase −1 — CRITICAL setup (blocking)

Run `~/.config/opencode/skills/lele-rs/references/WORKFLOW_SETUP.md` in full before anything
else: load the listed skills, read RATIONALE.md + SMELLS.md + `lele-lint --rules-md` (+
`lele-bevy-lint --emit rules-md` for Bevy crates), run the **baseline** `just lint|bevy-lint|clippy`,
and open the first reply with the **Setup:** proof block. Lint findings are this skill's whole
input, so every proposed fix cites its `LELE0xx`/`LELEBEVY0xx` code from the generated rules.

## Phase 0 — Resolve scope

- `crates` = the argument list. If empty, the user means the whole workspace.
- Enumerate crates deterministically: read `lele.toml` (respect `[lele.config] exclude`) and/or
  list directories containing `Cargo.toml`. Never invent a crate.
- Echo the resolved list back before auditing.

## Phase 1 — Audit

1. Confirm Phase −1 is done. Do not re-derive it here.
2. Audit each crate's `src/` against the loaded rule sets. Record every finding as
   `crate | file:line | change | why`; mark baseline findings as such.

## Phase 2 — Propose: manifest table, then batch 1 (NO EDITS)

**At most 5 batches per window.** If the audit yields more, stop the manifest at batch 5 and add one
line — `<n> more batches after these` — then present the next window only after batch 5 is green.

First output MUST contain, in this order:

1. **Manifest** — every proposed edit in the current window, one row per finding, grouped by batch:

   | batch | change | why |
   |---|---|---|
   | 1 | `alpha` `src/parse.rs:41` `parse::ParseConfig` -> `parse::Config`<br>`alpha` `src/emit.rs:7` `emit::EmitJob` -> `emit::Job` | LELE012 — the type repeats its parent module |
   | 2 | `beta` `src/store.rs:112` drop the unused `Serialize` derive | LELE026 — the derive is unused, it only silences the rule |
   | 3 | `beta` `src/methods/plugin/mod.rs:1` move `methods/plugin/` under `Plugin` | LELE030 — the delegate folder is keyed by type name |

   The `change` cell carries the crate, the `file:line` and the edit, so no row is ambiguous about where
   it lands. `why` starts with the rule code, or `judgement` when no rule covers the finding; a baseline
   finding is prefixed `baseline`.
2. **Batch 1 preview** — the literal before/after code for every batch-1 row (per the global
   `CRITICAL: Code Snippets` rule).
3. A closing question: **"Proceed with batch 1, or re-scope?"**

Do **NOT** edit anything yet. Wait for the user's reply.

## Phase 3 — Apply exactly ONE batch

- A batch is ONE coherent rule family so a failure is attributable. Order batches:
  mechanical / lint-enforced (`LELE0xx` / `LELEBEVY0xx`) → structural → design / judgement.
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

Applied (batch <n-1>):
  | change | files touched |
  |---|---|

Next batch (<n>):
  | batch | change | why |
  |---|---|---|
  | <n> | <crate> <file:line> <one-line change> | <rule> — <one-line reason> |

Batch <n> preview:
  <for EVERY item: file:line, then the literal `// before` / `// after` code block,
   including knock-on edits (now-unused imports, callers, tests)>

Proceed with batch <n>, or change the batch? (reply yes / re-scope / stop)
```

**CRITICAL — code previews are mandatory at EVERY approval gate**, not only for batch 1.
The next-batch prompt is invalid without the literal before/after snippets for every item;
a table of one-line changes is NOT a preview. The user approves code, not summaries.

Do **NOT** auto-carry. Wait for the reply, then loop to Phase 2/3 with the next batch. When the
window's last batch is green, re-audit and present the next window the same way — never carry the old
manifest forward.

## Hard rules

- No editing before explicit batch approval.
- A batch missing before/after snippets for any item is invalid — fix it before presenting.
- Do not add `#[allow(clippy::…)]` without explicit user sign-off.
- No commit, push, merge, or rebase. Agents never run `bacon`.
