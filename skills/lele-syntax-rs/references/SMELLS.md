# SMELLS — anti-patterns `lele_lint` cannot check

Judgement only, with bad/good examples. The charter is in `SKILL.md` §4: read a definition
and ask *"does it let me understand what this represents?"* Anything mechanically
checkable belongs in `lele_lint`, not here.

Every example is **`single_field_newtype`-conformant**: one field is a tuple newtype (`#[derive(Deref)]`),
two or more are named fields. A newtype wraps a single **scalar** value (`single_field_newtype`) and never a
collection (`no_collection_newtype`); a collection is held directly — as a field, argument, or return type. A
type alias only earns its place for a long or noisy underlying type (e.g.
`HashMap<PathBuf, ModuleInfo>`), never for a short one like `Vec<Entry>`.

## S1. Primitive obsession (field level)

A field typed as a primitive (`String`, `u64`, `bool`) hides its domain meaning. Use the
narrowest type that carries it: `PathBuf`/`&Path` for paths, a newtype for a validated
value, an enum for a fixed set. The reader should understand the field from its type alone.

```rust
// BAD — every field is a primitive; the definition tells the reader nothing
struct Report {
    path: String,
    size: u64,
    format: String,
}

// GOOD — the type carries the meaning
struct Report {
    path: PathBuf,
    size: ByteCount,
    format: Format,
}
```

Judgement only; the newtype shape is **`single_field_newtype`**. Related: RATIONALE §5 parse, don't validate.
Ref: Fowler, [Primitive Obsession](https://refactoring.guru/smells/primitive-obsession).

## S2. Boolean blindness

A `bool` carries no meaning beyond its value; you must remember its provenance to use it.
A `bool` **field** is permitted but rare — usually it is derived state or a collapsed enum.
Before adding or keeping one, walk these three questions:

1. **Is it derivable from the other fields?** If the value follows from the rest of the
   state, delete the field and expose a **method returning `bool`**. Stored derived state
   drifts out of sync with its source.
2. **Are there other `bool` fields on the same axis?** If two or more flags are mutually
   exclusive or describe one state, replace them with an **enum** — separate `bool`s make
   impossible combinations (both true, both false) representable. Genuinely independent
   flags stay separate (a bitset only when there are many); several `bool`s that flip
   together are usually a flattened state machine (RATIONALE §10).
3. **Otherwise keep the field** — a single, genuinely independent flag — and name it as the
   question it answers (RATIONALE §2).

```rust
// BAD — two bools on one axis; both-true and both-false are representable
struct Job {
    id: JobId,
    png: bool,
    mp4: bool,
}

// GOOD — one enum; exactly one format
enum Format { Png, Mp4 }

struct Job {
    id: JobId,
    format: Format,
}
```

```rust
// BAD — `is_uploaded` follows from `uploaded_at`; two sources of truth that can disagree
struct Upload {
    uploaded_at: Option<Timestamp>,
    is_uploaded: bool,
}

// GOOD — the field is gone; the answer is computed where it is asked
struct Upload {
    uploaded_at: Option<Timestamp>,
}

impl Upload {
    pub fn is_uploaded(&self) -> bool { self.uploaded_at.is_some() }
}
```

Naming is RATIONALE §2: whatever its position, a `bool` is the question it answers —
`is_visible`, not `visible`; `do_all_jobs_have_an_owner`, not `all_jobs_have_an_owner`.

Judgement only.
Ref: Robert Harper, [Boolean Blindness](https://existentialtype.wordpress.com/2011/03/15/boolean-blindness/).

## S3. Parallel / kind-segmented collections

One conceptual set split by kind across two or more sibling collections. Prefer a single
collection of a sum type: each element is exactly one kind, so "present in both" becomes
unrepresentable. Match the decomposition of neighbouring fields — if the rest of the type
is collections of domain values, a struct of primitive collections stands out.

```rust
// BAD — one set, split by kind into parallel primitive collections
struct Catalog {
    primaries: HashMap<String, String>,
    secondaries: Vec<String>,
}

// GOOD — one collection of a sum type
enum Entry {
    Primary { name: Name, derived: Derived },
    Secondary(Name),
}

// (a) one field among several => named struct
struct Workspace {
    entries: Vec<Entry>,
    version: Version,
}
```

The collection stays a `Vec<Entry>` — a field, argument, or return type. No wrapper type,
and no alias for a type this short; only a long or noisy underlying type earns an alias.

Trigger: a set split across ≥2 sibling collections **by kind**, where each kind could carry
its own data. Counter-indication: the collections are genuinely independent (never iterated
or queried as one), or split by access pattern rather than kind.
Judgement only.
Refs: Jon Skeet, [Anti-pattern: parallel collections](https://codeblog.jonskeet.uk/2014/06/03/anti-pattern-parallel-collections/);
[Make illegal states unrepresentable](https://corrode.dev/blog/illegal-state/);
Wlaschin, [Designing with types](https://fsharpforfunandprofit.com/series/designing-with-types/).

## S4. Data parked in a tuple

A tuple with two or more fields is a positional type: the reader must remember the order to
know what `.0` and `.1` mean. Name it.

```rust
// BAD — every call site must know that .0 is the path, .1 the label, .2 the hash
fn render_states(scene: &Scene) -> Vec<(PathBuf, String, String)> { /* … */ }

for (path, label, pixels) in &rendered { /* … */ }

// GOOD — the field names are the documentation
struct RenderedState {
    path: PathBuf,
    label: String,
    pixel_hash: String,
}
```

Judgement only. Field **access** is **`no_positional`**, and the named-field shape is **`single_field_newtype`**. Note `no_positional`
cannot see inside `assert!`/`assert_eq!` macro bodies, so positional access hidden there is on
you. Related: RATIONALE §12.
