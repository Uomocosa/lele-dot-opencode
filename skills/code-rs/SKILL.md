---
name: code-rs
description: Use when the user invokes /code-rs <request> to add or change Rust code. Produces a PLAN ONLY (no edits) — understanding + assumptions, one card per new/changed code block with at least 3 naming alternatives, literal BEFORE/AFTER previews marked line-by-line with +/-/!, and a scoped code-size review (duplication, near-duplicates → higher-order functions). Edits only after the user says proceed.
---

# Code (Rust) — plan first

> **THIS IS A PLAN. NO EDITS YET.** Do not create, edit, move, or delete any file until the user
> explicitly says to proceed (e.g. "proceed", "go", "apply"). Questions, objections, and
> requested changes are NOT approval — re-plan instead.

## Invocation

`/code-rs <request>` — the request may be one line or a long spec. Treat it as the goal.

## 1. Setup (blocking)

Run `~/.config/opencode/skills/lele-rs/references/WORKFLOW_SETUP.md` in full and also load
`definition-abstraction` and `definition-functional-patterns`. Load domain skills the request touches (bevy-rs, freenet, libp2p, …).
Open the first reply with the **Setup:** proof block. Every planned line of code must already
follow the lele rules and lints — never list "lint risks"; fix the plan instead.

## 2. Read before planning

Read the code the request touches: the files to edit, their callers, and the types they use.
Search for existing code that already does (part of) the job. Meaning comes from code read, not
from names; mark guesses as guesses.

## 3. Plan (NO EDITS)

Emit the **Plan** template from `references/TEMPLATES.md`, in this order:

1. Banner — "PLAN ONLY — no edits until you say proceed."
2. Setup proof.
3. Understanding — goal, assumptions (A1…), open questions with the default assumed (Q1…).
   Short request → more assumptions; long precise spec → may be one line.
4. Blocks — one card per new or changed item (fn, method, type, trait impl, system, test, mod).
   **Names: at least 3**, each with a one-line tradeoff; mark the chosen one.
5. Previews — literal code for EVERY block (tests included), in the BEFORE/AFTER marker format.
   A table or card is never a preview.
6. Code-size review — scoped ONLY to the planned blocks plus their direct callers/callees:
   - Duplication: logic already existing at `file:line` → reuse it; logic shared between
     blocks → extract once.
   - Near-duplicates: items differing only in a value / predicate / mapping → one function
     taking `impl Fn(..)` (or a generic), with a preview of the merged version.
   - Propose a merge only if the result is smaller AND clearer (no closure soup; respect
     deep-vs-shallow and "wrong abstraction" from definition-abstraction).
   - Functional reshapes: apply `definition-functional-patterns` (FP1–FP9) to the same scope;
     cite the pattern id and show a preview. If nothing found, say "nothing to reduce".
7. End with: **"Proceed, or what should change?"**

## 4. Feedback rounds

On feedback, re-render only the sections/blocks that changed (say which), keeping block numbers
stable. Answer information questions directly. Still no edits.

## 5. Apply (only after explicit proceed)

- Apply exactly the approved plan; anything new discovered → stop and re-plan that part.
- Verify: `export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH" && just build 2>&1`, then
  `just clippy`, `just fmt`, `just test`, `just lint` (raw cargo if no justfile). Never pipe.
- Red → fix within the plan's scope, or stop and report. Never `#[allow(...)]` without sign-off.
- Report results, then stop. No commit, push, merge, or rebase.
