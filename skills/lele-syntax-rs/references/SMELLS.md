# SMELLS — anti-patterns `lele_lint` cannot check

Judgement only, with bad/good examples. The charter is in `SKILL.md` §4: read a definition
and ask *"does it let me understand what this represents?"* Anything mechanically
checkable belongs in `lele_lint` (`E0xx`), not here.

Every example is **E018-conformant**: one field is a tuple newtype (`#[derive(Deref)]`),
two or more are named fields. A newtype wraps a single **scalar** value (E018) and never a
collection (E028); a collection is held directly — as a field, argument, or return type. A
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

Judgement only; the newtype shape is **E018**. Related: RATIONALE §5 parse, don't validate.
Ref: Fowler, [Primitive Obsession](https://refactoring.guru/smells/primitive-obsession).

## S2. Boolean blindness

A `bool` carries no meaning beyond its value; you must remember its provenance to use it.
Several `bool` fields that encode one axis leave the reader guessing and make impossible
combinations representable. Use an enum — or a bitset only when the flags are genuinely
independent.

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
