# Audit lenses

Load the full section for any rule a proposal touches (`lele-lint --explain <CODE>`). For the
`name` lens always read LELE001, LELE011, LELE012, LELE022, LELE026, LELE027, LELE030.

## `lint`

- Every finding cites its rule code; `judgement` when no rule covers it; prefix `baseline` for
  pre-existing ones.
- Passing only through an exemption (e.g. an unused `Serialize` derive silencing `LELE026`) is a
  finding, not a pass.

## `name` — vocabulary (RATIONALE §2, §12, §13)

Inventory per crate: modules/folders, `pub struct|enum|type`, Cargo features, `tracing` targets,
log keys parsed by tests, `#[macro_export]` macros, `bool` fields — with where each is
constructed and read.

- **Synonym drift** — one concept, several words across code, logs, features, docs. Pick ONE.
- **Stutter** — `parse::ParseConfig` → `parse::Config` (LELE012). Renaming a module can make its
  types stutter; check both ways. If the user's name violates a lint, offer the compliant form.
- **Questions** — every `bool` reads as the question it answers.
- **Dead** — constructed/written but never read. Grep for reads, not the name.
- **Role vs synonym** — a newtype restating its inner type is `delete`/`merge`; one carrying an
  invariant or role stays.
- **Merge sanity** — merge only if both share a source of truth; never replace one type with two
  fields that must agree (SMELLS S3).
- **Wire/persisted** — renames on serde/bincode types: re-keying is free, but require a
  cross-crate round-trip test and regenerate every artifact.
- **Log coupling** — renaming a log key/target updates test parsers and env filters in the same batch.

## `shape` — abstraction (`definition-abstraction`, SMELLS S5–S7)

- **Scope gradient** — wide scope: 1–2 word caller concept; narrow scope: as long as needed.
  A wide name that leaks the mechanism → rename or `deepen`.
- **Shallow / pass-through** — interface as complex as the body → `deepen` (absorb the caller's
  work) or inline. Exempt: `#[atomic_delegates]` shells, `From`/`Deref`/trait impls, thin I/O
  adapters.
- **Wrong abstraction** — grows parameters, flags, "just this once" branches → inline into callers,
  drop what each doesn't need, re-extract the surviving duplication.
- **Mixed levels** — a body mixing a high-level step with low-level detail → extract the detail.
- **False abstraction** — hides a decision callers actually depend on → expose it in the signature.
- **Premature** — an abstraction with one user and no hidden decision → inline.
- **Primitive fields** — `item_count: usize` when the items exist upstream → `items: Vec<Item>`.

Verdicts: `keep` · `rename` · `merge` · `delete` · `split` · `deepen` · `inline` · `out of scope`.
