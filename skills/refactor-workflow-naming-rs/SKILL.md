---
name: refactor-workflow-naming-rs
description: "Use when renaming the vocabulary and structure of one or more Rust crates — modules/folders, public types, files, functions, fields, features, log keys. Produces one batch table (batch | renames | why) covering every proposed rename plus the literal before/after previews for batch 1, applies exactly one approved batch, re-verifies every reviewed crate, then stops and names the next batch. The naming sibling of refactor-workflow-rs: same gates, but the input is ubiquitous language, not lint findings."
---

# Refactor Workflow — Naming (Rust)

Interactive, batched renaming with an explicit approval gate at **both** ends of every batch:
once to approve the plan, once to advance. **Never auto-carry into the next batch.**

## Invocation

- Command: `/refactor-workflow-naming-rs {crates}` → this skill, with `$ARGUMENTS` as the crate list.
- Run from the **build** agent. Applying edits is forbidden in plan mode.

## Phase −1 — CRITICAL setup (blocking)

Run `~/.config/opencode/skills/lele-rs/references/WORKFLOW_SETUP.md` in full before anything
else: load the listed skills, read RATIONALE.md + SMELLS.md + `lele-lint --rules-md` (+
`lele-bevy-lint --emit rules-md` for Bevy crates), run the **baseline** `just lint|bevy-lint|clippy`,
and open the first reply with the **Setup:** proof block. For naming also read in full
`lele-lint --explain` for LELE001, LELE011, LELE012, LELE022, LELE026, LELE027, LELE030 — every
rename moves files, types or delegate folders through these.

## Phase 0 — Resolve scope

- `crates` = the argument list. If empty, the user means the whole workspace.
- Enumerate crates deterministically: read `lele.toml` (respect `[lele.config] exclude`) and/or
  list directories containing `Cargo.toml`. Include any path-dependency crate that shares
  serialized types with the crate under review. Never invent a crate.
- Echo the resolved list back before auditing.

## Phase 1 — Inventory, then judge

Inventory per crate, reading each item's **definition and its users** — the meaning comes from the
code, not from the name:

- **Domains** — every top-level module under `src/` and every submodule folder.
- **Types** — every `pub struct` / `pub enum` / `pub type` (`grep -rhn '^pub \(struct\|enum\|type\)'`).
- **Also** — Cargo feature names, `tracing` `target:`s, log keys parsed by tests
  (`tests/common/*`), `#[macro_export]` macros, `bool` fields.
- For each item, record where it is *constructed* and where it is *read*.

Judge with RATIONALE §2 (one word per concept; every `bool` is named as the question it answers),
§12 (a newtype carries an invariant or a role, never a synonym) and §13 (a `struct` is an
object/noun, a `fn` is an action/verb, a `bool` is a question; wide scope = short name, narrow
scope = longer name, no cap) in front of you:

- **Abstraction level** — for each type/function: is the name the caller's *concept* (1–2
  words) or has the *mechanism* leaked in (more than two words on a wide-scope item)? A name
  whose body is at the same level of detail is a shallow abstraction (SMELLS S5) — a design
  change, not a rename: record it as `deepen` and keep it out of the rename batches. Do not
  propose `deepen` for `#[atomic_delegates]` shells, shape-only items (`From`, `Deref`, trait
  impls) or thin I/O adapters (RATIONALE §13 *Limits*).

- **Linter-compatible** — a name must not repeat its parent module (`LELE012`: `parse::ParseConfig`
  ✗, `parse::Config` ✓). Renaming a *module* can make existing types stutter — check both ways. If the
  user's preferred name violates a lint, say so and offer the compliant form.
- **Dead code** — "constructed but never read" counts as dead (a value stored at construction, a field
  written but never queried). Grep for reads, not just the name.
- **Synonym drift** — one concept under different words across code, log keys, feature flags, tracing
  targets and docs (the same idea as `alpha` in one module, `alpha_total` in a field, `alpha_store` in
  a feature flag). Propose ONE word and every place it must change.
- **Role vs. synonym** — a newtype that only restates its inner type is a `delete`/`merge` candidate;
  one that carries a role or an invariant (a value constructible only after a check) stays.
- **Merge sanity** — before folding A into B, confirm they share a source of truth. Data built from
  different inputs, or with fields that exist on only one side, is a *rename*, not a merge. Never
  replace one type with two fields that must agree (SMELLS §S3).
- **Wire / persisted types** — flag renames or field changes on serialized types (`serde`, `bincode`,
  a persisted schema). Re-keying is NOT a cost — just rebuild — but require a cross-crate round-trip
  test (serialize in one crate → deserialize in the other and back) and confirm every generated
  artifact (codegen output, checked-in fixtures, bundles) is rebuilt.
- **Log/parser coupling** — renaming a log key or tracing target means updating the test log parsers
  and env filters in the same batch.
- **Primitive fields** worth upgrading (`usize` count → `Vec<Item>` when the data is available
  upstream and thrown away) — handled by the type-shape batch in Phase 3.

## Phase 2 — Propose: batch table first, then batch 1 (NO EDITS)

**At most 5 batches per window.** If the audit yields more, stop the table at batch 5 and add one
line — `<n> more batches after these` — then present the next window only after batch 5 is green.

The first output MUST contain, in this order:

1. **Inventory** — the evidence, one row per item, the meaning taken from the code:
   `Name | Meaning (one line, from the code) | Verdict | Alternatives`. Mark a meaning inferred from
   fields alone, without reading users. Verdicts: `keep` · `rename` · `merge` · `delete (dead)` · `split` · `deepen`.
2. **Concept clusters** — groups that may be ONE concept (e.g. `Thing` / `ThingEntry` /
   `ThingRecord` / `store::Thing`). For each: what each member holds, whether they can merge, and if
   not, *why* (different source of truth, local vs. shared/persisted state, different role).
3. **Batch table** — **every** proposed rename, grouped into batches, highest-confusion first. Exactly
   three columns: the batch number, the renames as a bare `old -> new` list separated by line breaks,
   and a one-line reason. No bullets, no nested lists, no extra columns:

   | batch | renames | why |
   |---|---|---|
   | 1 | `Alpha` -> `Beta`<br>`alpha_count` -> `beta_count` | one concept under two words; `beta` is the word the rest of the crate already uses |
   | 1 | `gamma::GammaConfig` -> `gamma::Config` | the type repeats its parent module name (`LELE012`); the prefix is redundant inside `gamma` |
   | 2 | `DeltaRecord` (delete)<br>`delta_record` field (delete) | constructed but never read anywhere — dead |
   | 3 | `item_count: usize` -> `items: Vec<Item>` | the items are already in hand upstream and thrown away; the count is re-derived |

4. **Batch 1 preview** — the literal before/after code for every batch-1 item, including knock-on
   edits (imports, callers, tests, log parsers), per the global `CRITICAL: Code Snippets` rule.
5. Closing question: **"Proceed with batch 1, or re-scope?"**

Do **NOT** edit anything yet. Wait for the user's reply.

## Phase 3 — Apply exactly ONE batch

- Batch order (one family per batch, so a failure is attributable):
  1. pure renames (module, type, file, fn, field — keep atomic file names in sync with their item)
  2. dead-code deletions
  3. type-shape changes (`usize` → `Vec`, new newtypes)
  4. wire / persisted changes (+ round-trip test, regenerated artifacts)
  5. wording: features, tracing targets, log keys + parsers, docs/README
- Re-show the batch's before/after snippets, then apply only that batch. Prefer `git mv` for file
  renames; after a bulk `sed`, grep for leftovers of the old name (code, docs, tests, examples).
- Verify **EVERY** crate under review — not just the edited one: `just build|clippy|fmt|test|lint`
  (+ `bevy-lint` and any repo-specific recipe when present). Never pipe a task runner; always append
  `2>&1`.
- If red: **STOP**, fix only this batch, re-run. Never advance on red.

## Phase 4 — All-green gate → explicit next-batch prompt (MANDATORY STOP)

Only when EVERY reviewed crate is green, emit exactly this shape and STOP:

```
✅ All green: <crate1>, <crate2>

Applied (batch <n-1>):
  | From | To | Files touched |

Next batch (<n>):
  | batch | renames | why |
  |---|---|---|
  | <n> | <old -> new><br>… | <one-line reason> |

Batch <n> preview:
  <for EVERY item: file:line, then the literal `// before` / `// after` code block,
   including knock-on edits (imports, callers, tests, log parsers)>

Proceed with batch <n>, or change the batch? (reply yes / re-scope / stop)
```

**Code previews are mandatory at EVERY approval gate.** A list of renames is not a preview.

Do **NOT** auto-carry. Wait for the reply, then loop to Phase 2/3 with the next batch. When the
window's last batch is green, re-audit and present the next window the same way — never carry the old
table forward.

## Hard rules

- No editing before explicit approval of the specific renames.
- A batch missing before/after snippets for any item is invalid — fix it before presenting.
- Report meanings from the code you read; mark guesses as guesses.
- Do not add `#[allow(clippy::…)]` without explicit user sign-off.
- No commit, push, merge, or rebase. Agents never run `bacon`.
