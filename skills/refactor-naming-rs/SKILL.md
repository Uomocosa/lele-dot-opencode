---
name: refactor-naming-rs
description: Use when reviewing or refactoring the NAMES and STRUCTURE of one or more Rust crates — domains (modules/folders), public types, features, log keys. Produces a reviewable report (Domains table, Types table, concept clusters, prioritized renames — each with meaning, verdict and alternatives), then applies approved renames batch-by-batch with before/after previews, re-verifying every crate, never auto-carrying.
---

# Refactor Naming (Rust)

The naming sibling of `refactor-workflow-rs`: same approval gates, but the audit target is
**vocabulary and structure** (ubiquitous language), not lint findings. Output is a report the
user can review at a glance; edits happen only after explicit approval, one batch at a time.
**Never auto-carry into the next batch.**

## Invocation

- Command: `/refactor-naming-rs {crates}` → this skill, with `$ARGUMENTS` as the crate list.
- Run from the **build** agent. Applying edits is forbidden in plan mode.

## Phase 0 — Resolve scope

- `crates` = the argument list. If empty, the user means the whole workspace.
- Enumerate crates deterministically: read `lele.toml` (respect `[lele.config] exclude`) and/or
  list directories containing `Cargo.toml`. Include path-dependency crates the crate shares wire
  types with (e.g. a Freenet `contract/` crate). Never invent a crate.
- Echo the resolved list back before auditing.

## Phase 1 — Load rules, then inventory

1. `lele-rs` (always), then `lele-syntax-rs` and **read in full** its `references/RATIONALE.md`
   (§2 ubiquitous language, §9 `From`, §12 newtype purpose) and `references/SMELLS.md`.
2. Load the domain skills the crate depends on (`bevy-rs`, `libp2p`, `freenet`, `serde-rs`, …).
3. Read the repo's `justfile` FIRST — its recipes are the canonical verifiers.
4. Inventory, per crate:
   - **Domains**: every top-level module under `src/` and every submodule folder.
   - **Types**: every `pub struct` / `pub enum` / `pub type` (`grep -rhn '^pub \(struct\|enum\|type\)'`).
   - **Also**: Cargo feature names, `tracing` `target:`s, log keys parsed by tests
     (`tests/common/*`), `#[macro_export]` macros, and `bool` fields.
5. For each item read the **definition and its users** — the meaning comes from the code, not
   from the name. Record where it is *constructed* and where it is *read*.

## Phase 2 — Report (NO EDITS)

First output MUST contain, in this order:

1. **Domains table** — `Name | Meaning (one line, from the code) | Verdict | Alternatives`.
2. **Types table** — same columns. Mark meanings inferred from fields only, without reading users.
3. **Concept clusters** — groups that may be ONE concept (e.g. `Room` / `RoomEntry` /
   `RoomRecord` / `roster::Room`). For each: what each member holds, whether they can merge,
   and if not, *why* (different source of truth, local vs. shared/persisted state, different role).
4. **Recommended renames**, priority-ordered (highest-confusion first).
5. Closing question: **"Which renames should I apply?"**

Verdicts: `keep` · `rename` · `merge` · `delete (dead)` · `split`.

### Checks to run before proposing a name

- **Linter-compatible**: the name must not repeat its parent module (`LELE012`: `freenet::FreenetClient`
  ✗, `lobby::Lobby` ✗). Renaming a *module* can make existing types stutter — check both ways.
  If the user's preferred name violates a lint, say so and offer the compliant form.
- **Dead code**: "constructed but never read" counts as dead (a resource inserted, a config field
  stored, never consumed). Grep for reads, not just the type name.
- **Synonym drift**: one concept under different words across code, log keys, feature flags,
  tracing targets, docs (`catalogue` vs `lobby` vs `rooms`; feature `room_lobby` vs module
  `discovery`). Propose ONE word and every place it must change.
- **Role vs. synonym** (RATIONALE §12): a newtype that only restates its inner type is a
  `delete`/`merge` candidate; one that carries a role or invariant (`ActiveRoom`) stays.
- **Merge sanity**: before proposing to fold type A into B, confirm they share a source of truth.
  Data built from different inputs (lobby vs. handshakes) or with local-only fields (link status)
  is a *rename*, not a merge. Never replace one type with two fields that must agree
  (SMELLS S3, parallel collections).
- **Wire / contract types**: flag renames or field changes on serialized types (serde/bincode,
  Freenet contract state). Contract re-keying is NOT a cost — just rebuild — but require a
  cross-crate round-trip test (`serialize` crate type → `deserialize` contract type and back) and
  confirm the embedded wasm is rebuilt.
- **Log/parser coupling**: renaming a log key or tracing target means updating the test log
  parsers and env filters in the same batch.
- **Primitive fields** worth upgrading (`usize` count → `Vec<Item>` when the data is available
  upstream and thrown away).

## Phase 3 — Apply exactly ONE batch

- Batch order (one family per batch, so a failure is attributable):
  1. pure renames (module, type, file, fn, field — keep atomic file names in sync with items)
  2. dead-code deletions
  3. type-shape changes (`usize` → `Vec`, new newtypes)
  4. wire / contract changes (+ round-trip test, contract rebuild + harness)
  5. wording: features, tracing targets, log keys + parsers, docs/README
- Re-show the batch's before/after snippets, then apply only that batch. Prefer `git mv` for file
  renames; after a bulk `sed`, grep for leftovers of the old name (code, docs, tests, examples).
- Verify **EVERY** crate under review: `just build|clippy|fmt|test|lint` (+ `bevy-lint`,
  `contract`, harness recipes when present). Never pipe a task runner; always append `2>&1`.
- If red: **STOP**, fix only this batch, re-run. Never advance on red.

## Phase 4 — All-green gate → explicit next-batch prompt (MANDATORY STOP)

Only when EVERY reviewed crate is green, emit exactly this shape and STOP:

```
✅ All green: <crate1>, <crate2>

Applied (batch <n-1>):
  | From | To | Files touched |

Next batch (<n> of <total>):
  - <old name → new name: where — why>

Batch <n> preview:
  <for EVERY item: file:line, then the literal `// before` / `// after` code block,
   including knock-on edits (imports, callers, tests, log parsers)>

Proceed with batch <n>, or change the batch? (reply yes / re-scope / stop)
```

**Code previews are mandatory at EVERY approval gate.** A list of renames is not a preview.

## Hard rules

- No editing before explicit approval of the specific renames.
- Report meanings from the code you read; mark guesses as guesses.
- Do not add `#[allow(clippy::…)]` without explicit user sign-off.
- No commit, push, merge, or rebase. Agents never run `bacon`.
