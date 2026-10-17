# Report format

## Table

| file | round 1 (conf) | round 2 (conf) | grade 1 / 2 | confusing names |
|---|---|---|---|---|
| `src/parse/config.rs` | "Loads settings from disk" (3) | "Parses a TOML config into `Config`, defaults for missing keys" (5) | 🟡 / ✅ | `cfg_raw` (mechanical), `ok` (bool, not a question) |

- `round N` = the reader's responsibility sentence, verbatim (trimmed), plus its confidence.
- Below the table, one evidence line per grade: `file — grade 1: <why>; grade 2: <why>`.

## Grading

| grade | meaning |
|---|---|
| ✅ correct | Matches what the file's users rely on it for. |
| 🟡 partial | Right area, wrong or missing a key responsibility. |
| ❌ wrong | Describes a different responsibility. |

Reading the pattern:
- ❌/🟡 → ✅: names are weak but the abstraction is fine → `name` lens edits.
- ✅ → ✅ with low round-1 confidence: names work but feel vague → consider a clearer name.
- ❌ → ❌ or 🟡 → 🟡: the abstraction itself is unclear → `shape` lens edits (deepen, split, inline).
- ✅ → ❌: context contradicts the names → a misleading name; highest priority.
