---
name: refactor-workflow-rs
description: Use when refactoring one or more Rust crates batch-by-batch with user approval — audits the named crates (or the whole workspace) through three lenses (lint findings, naming/vocabulary, abstraction depth), presents one table of at most 5 batches plus literal before/after code for batch 1, applies exactly one approved behaviour-preserving batch, re-verifies every reviewed crate, then stops and names the next batch. To clear lint errors autonomously (no approval) use lele-lint-fix-rs.
---

# Refactor Workflow (Rust)

Goal: code that stays easy to understand over time — honest names, deep abstractions, lint-clean.
Every batch is a small, behaviour-preserving step with an approval gate at **both** ends.
**Never auto-carry into the next batch.**

## Invocation

- `/refactor-workflow-rs {crates} [--lens lint|name|shape]` — default: all three lenses.
- Run from the **build** agent. Applying edits is forbidden in plan mode.

## 1. Setup (blocking)

Run `~/.config/opencode/skills/lele-rs/references/WORKFLOW_SETUP.md` in full, and also load
`definition-abstraction` and `definition-functional-patterns`. Open the first reply with its **Setup:** proof block.

## 2. Scope

- `crates` = the argument list; empty means the whole workspace.
- Enumerate from `lele.toml` (respect `[lele.config] exclude`) and/or dirs with `Cargo.toml`. Add
  any path-dependency crate that shares serialized types. Never invent a crate. Echo the list.

## 3. Audit — three lenses

Read each item's **definition and its users**; meaning comes from the code, not the name. Tag
every finding `crate | file:line | lens | change | why`. Checklists: `references/LENSES.md`.

- `lint` — `LELE0xx` / `LELEBEVY0xx` / clippy findings, cited by code.
- `name` — vocabulary: one word per concept, stutter, bools as questions, dead (written but never
  read), wire types, log keys.
- `shape` — abstraction: shallow pass-through → deepen, wrong abstraction → inline, mixed levels
  in one body, false abstraction, primitive fields hiding thrown-away data.

A finding that needs a **behaviour change** is listed as `out of scope`, never batched.

## 4. Propose (NO EDITS)

Use the **Proposal** template in `references/TEMPLATES.md`: one table of at most 5 batches
(`<n> more batches after these` if more), concept clusters only when the `name` lens found any,
the literal before/after code for every batch-1 row, then **"Proceed with batch 1, or re-scope?"**

## 5. Apply exactly ONE batch

- One change family per batch so a failure is attributable. Order:
  1. lint (mechanical) 2. pure renames 3. dead-code deletions 4. abstraction (deepen/inline)
  5. type-shape 6. wire/persisted (+ cross-crate round-trip test, regenerated artifacts)
  7. wording (features, tracing targets, log keys + parsers, docs)
- Re-show the batch's snippets, then apply only that batch. Use `git mv` for file renames; after a
  bulk `sed`, grep for leftovers of the old name (code, docs, tests, examples).
- Verify **EVERY** reviewed crate: `just build|clippy|fmt|test|lint` (+ `bevy-lint` / repo
  recipes; raw `cargo` if no `justfile`). PATH prefix, `2>&1`, never piped. Green = no finding
  beyond baseline.
- Red: **STOP**, fix only this batch. If the fix keeps growing, revert the batch and propose the
  smaller prerequisite step first (Mikado). Never advance on red.

## 6. Gate (MANDATORY STOP)

Emit the **Next batch** template from `references/TEMPLATES.md` and stop. When the window's last
batch is green, re-audit and present a fresh window — never carry the old table forward.

## Hard rules

- No edit before explicit approval of that batch.
- Literal before/after code for every item at **every** gate; a table is not a preview.
- Never mix refactoring with behaviour change.
- Report meanings from code you read; mark guesses as guesses.
- No `#[allow(...)]` without explicit user sign-off.
- No commit, push, merge, or rebase. Agents never run `bacon`.
