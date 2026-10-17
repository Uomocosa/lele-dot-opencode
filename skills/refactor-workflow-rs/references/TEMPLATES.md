# Output templates

## Proposal (first output after Setup)

1. **Findings table** — every change in the window, grouped by batch:

   | batch | lens | change | why |
   |---|---|---|---|
   | 1 | lint | `alpha` `src/parse.rs:41` `parse::ParseConfig` -> `parse::Config` | LELE012 — repeats its module |
   | 2 | name | `beta` `src/store.rs:112` `DeltaRecord` (delete) | written, never read — dead |
   | 3 | shape | `beta` `src/load.rs:9` inline `read_cfg` into its 2 callers | pass-through: same signature as `parse_file` |

   `change` carries crate, `file:line` and the edit. `why` starts with a rule code, or a one-line
   judgement; `baseline` prefix for pre-existing findings.

2. **Concept clusters** (only if the `name` lens found any) — e.g. `Thing` / `ThingEntry` /
   `store::Thing`: what each holds, merge or not, and why.

3. **Out of scope** — findings needing a behaviour change, one line each.

4. **Batch 1 preview** — for every row: `file:line`, then literal `// before` / `// after` code,
   including knock-on edits (imports, callers, tests, log parsers).

5. **"Proceed with batch 1, or re-scope?"**

## Next batch (after each green batch)

```
✅ All green: <crate1>, <crate2>

Applied (batch <n-1>):
  | change | files touched |
  |---|---|

Next batch (<n>):
  | batch | lens | change | why |
  |---|---|---|---|

Batch <n> preview:
  <for EVERY item: file:line, then literal `// before` / `// after` code,
   including knock-on edits>

Proceed with batch <n>, or change the batch? (reply yes / re-scope / stop)
```
