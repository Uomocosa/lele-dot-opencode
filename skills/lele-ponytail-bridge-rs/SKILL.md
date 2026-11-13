---
name: lele-ponytail-bridge-rs
description: |
  Use whenever Ponytail, lazy-senior-dev, YAGNI, minimal-code, or "simplest solution"
  mode is active in a Rust crate checked by lele-lint. Applies Ponytail's read-reuse-test
  ladder only where it does not conflict with LELE0xx, RATIONALE, SMELLS, or the domain
  skill. The linter always wins.
license: MIT
---

# lele × Ponytail bridge

**Precedence:** `lele-lint` > `lele-syntax-rs` (`RATIONALE.md` + `SMELLS.md`) > domain
skill (`bevy-rs`, `libp2p`, `freenet`, `avian-rs`, ...) > Ponytail.

Use Ponytail as a **review/audit lens** and a **reading/reuse discipline**, never as a
licence to delete linter-mandated shape.

## Keep from Ponytail

- Read the code the change touches before editing; grep every caller; list callers,
  tests, fixtures, config, and exports.
- Reuse first: an existing helper, the standard library, a platform feature, or an
  installed dependency. Never add a dependency for a few lines.
- Fix the root cause once in the shared code, not in one caller.
- Never cut trust-boundary validation, error handling that prevents data loss, security,
  accessibility, or anything the user asked for.
- End a coding reply with what was skipped or not checked, and any risk.

## Drop or override from Ponytail in Rust

- **"No abstraction / wrapper / type conversion."** Linter-mandated shape is not
  unrequested abstraction. Keep `single_field_newtype` + `Deref`, `__basic__/` placement,
  `From`/`TryFrom`, `derive_more::From`, and `thiserror` enums.
- **"Shortest diff / deletion beats addition."** Keep atomic files, `#[atomic_delegates]`
  shells, `methods/<type>/<method>.rs`, `test_usage`, and boundary structure.
- **"One line if a reader gets it."** Obey `LELE017` (at most 3 statements inline) and
  `LELE030` (method body in `methods/`).
- **"Trivial changes need no test."** Obey `LELE009`: every non-trivial file ends with a
  `test_usage` test or `// no test_usage necessary`.
- **`shortcut:` comments.** `LELE031` bans comments in `src/` and `methods/`. Keep the
  ledger outside `src/`, or use a `///` note in `constants.rs` only.
- **"Lean" review findings.** Never delete `#[atomic_delegates]` shells, `__basic__` types,
  single-field newtypes, state-machine types (`State`/`Input`/`Output`/`update`), or
  `[[lele.boundary]]` structure. RATIONALE §13 *Limits* and SMELLS S5 exempt them.

## Safe use

- Run Ponytail's `/ponytail-review` and `/ponytail-audit` as **one-shot reports**; they
  change no code.
- Do not leave the Ponytail authoring persona always-on in a lele crate. If it is on,
  apply this bridge before editing.
- Before any edit, re-check the proposed shape against `lele-lint --explain <CODE>` or the
  repo's `RULES.md`. If the linter would reject it, the linter wins.
