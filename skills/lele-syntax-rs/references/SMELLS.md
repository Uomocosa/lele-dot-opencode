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

## S5. Shallow abstraction (pass-through name)

A name that claims to abstract away the code, but whose body is at the same level of detail
as the name: a `pub fn` that only forwards its arguments to another item with a similar
signature, a wrapper that adds no invariant and no role. The interface is not much simpler
than the implementation, so the caller reads through it anyway. It is a layer, not an
abstraction (Ousterhout's *shallow module*).

```rust
// BAD — the name tells the caller nothing the body does not
pub fn read_config(path: &Path) -> Result<Config, Error> {
    parse_file(path)
}

// GOOD — the name is the concept; the body holds the detail
pub fn read_config(path: &Path) -> Result<Config, Error> {
    let text = fs::read_to_string(path)?;
    parse_config(&text)
}
```

Trigger: `pub` item whose body is a single call at the same abstraction level; a wrapper with
no invariant and no role. Counter-indication — do **not** flag: `#[atomic_delegates]` shells
(one-line by design; `method_file_co_location` mandates the split — RATIONALE §13 *Limits*),
a thin adapter at an I/O boundary (RATIONALE §3), a shape-only item (`impl From`, `Deref`,
trait impl), or a deliberate seam for a `[[lele.boundary]]`.

Judgement only. No lint rule is planned for this — a mechanical check ("`pub fn` whose sole
statement calls an item with an identical parameter list") was considered and rejected as too
noisy against legitimate thin adapters. Related: RATIONALE §13.
Ref: Ousterhout, *A Philosophy of Software Design* (shallow module; pass-through method).

## S6. False abstraction (leaky interface)

A name that hides a decision the caller actually depends on, so the caller reads the body
anyway. Unlike S5 this one has depth — but the wrong boundary: it hides something that
*matters to the caller* instead of something that may change (Parnas; RATIONALE §3).

```rust
// BAD — hides the deletion rule the UI must display; callers read the body to find out
impl Text {
    pub fn backspace(&mut self) {}
}

// GOOD — the decision is in the interface, where the caller needs it
impl Text {
    pub fn delete_previous_grapheme(&mut self) {}
}
```

Judgement only. Related: RATIONALE §3, §13.
Refs: Ousterhout, *A Philosophy of Software Design* (false abstraction; information leakage);
Spolsky, *The Law of Leaky Abstractions*; Parnas 1972.

## S7. Abstraction-level mismatch in a name

A name written at the wrong level for its scope: a wide-scope item named for its mechanism
(`write_bytes_then_flush` as a public API), or a single-caller helper named for a concept
broader than it performs (Ousterhout's *vague name*). The wide-scope name is the concept
(one or two words); the mechanism belongs in the body and in its narrow-scope names — two,
three, four words or more, with **no cap**. This is §2 read for nouns and verbs instead of
`bool`s.

```rust
// BAD — the public name states the mechanism, and its order
pub fn handshake_write_bytes_and_flush(stream: &mut Stream) -> Result<(), Error>

// GOOD — the public name is the concept; the mechanism is the body
pub fn handshake(stream: &mut Stream) -> Result<(), Error>
```

Judgement only; a name-length or word-count lint would repeat the retired `vocabulary`
mistake (RATIONALE §2). Related: RATIONALE §13.
Refs: Ousterhout, *A Philosophy of Software Design* (vague names; "hard to pick a name" is a
design signal); the Ousterhout–Martin discussion (scope vs. name length).

## S8. Jargon instead of description

A technique's term of art (`digest`, `fingerprint`, `shard`, `blob`, `envelope`, `frame`)
names how something is done, not what the value is. Describe the value instead.

```rust
// BAD:  the reader must know the technique to decode the name
struct Digest(u64);
// GOOD: the name says what it holds
struct FileContentHash(u64);
```

One word, one meaning: never give a word already used in the codebase a second meaning.

Judgement only. Related: RATIONALE §2 (ubiquitous language), §13 (two kinds of wide-scope
name), S7.
