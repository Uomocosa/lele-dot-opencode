# RATIONALE — the rules `lele_lint` cannot check

`lele_lint` covers mechanical shape (`E0xx`, see `../lele_lint/RULES.md`). The rules
below are judgement: read them before designing, not before linting. Each names the
lele rule that enforces part of it, or says "judgement only".

## 1. One function, one job

When a fragment of code does one nameable thing, extract it into a function with that
name and a colocated test. The name, arguments and return type are the documentation
(hence no comments). When two functions differ in one inner step, pass that step as a
parameter (`impl Fn`).

Limits: pass behaviour, not a flag/enum that switches branches; at most one behaviour
parameter (more means separate functions, or a trait if the behaviours belong together);
the passed function is a named `fn` with its own test; do not merge when the shared part
is two statements or fewer; undo the merge as soon as callers bend to fit it.

```rust
// judgement: two callers differing in one inner step -> parameterize it
fn apply(items: &mut [Item], strategy: impl Fn(&mut Item)) {
    for item in items {
        strategy(item);
    }
}
```

Enforced in part by **E015 `helper_count`** (one public function per file, at most two
unnamed private helpers). Everything else is judgement.

Refs: Fowler, [Extract Function](https://refactoring.com/catalog/extractFunction.html) and
[Parameterize Function](https://refactoring.com/catalog/parameterizeFunction.html);
Fowler, [FunctionLength](https://martinfowler.com/bliki/FunctionLength.html);
the Rust Book, [closures and iterators](https://doc.rust-lang.org/book/ch13-00-functional-features.html);
Sandi Metz, [The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction)
(only for the "undo the merge" limit). Do **not** present "rule of three" or AHA as the rule.

## 2. Ubiquitous language

Pick exactly one word per concept and use it everywhere — files, folders, types,
functions, fields. When a synonym creeps in, rename to the canonical word. State the
canonical term and a one-line domain definition in the crate's own docs, and list the
synonyms you have seen drifting in.

This one is **guidance, not a lint**: `lele_lint` cannot check it. An earlier `E035
vocabulary` rule tried, matching banned words as contiguous sub-words of every declared
identifier and path component — so `banned = ["index"]` flagged `snapshot_index` and
`peer_index`, which have nothing to do with the concept. It was retired (2026-10-04);
`[[lele.vocabulary]]` is no longer part of `lele.toml`.

Ref: Fowler, [UbiquitousLanguage](https://martinfowler.com/bliki/UbiquitousLanguage.html).

## 3. Functional core, imperative shell (Sans-IO, ports and adapters)

Put the decisions in a pure core that receives inputs and returns outputs/commands, and
keep I/O, clocks, sockets and frameworks in a thin shell that drives the core and executes
its commands. Core folders are named after the domain; adapter folders are named after
the technology they talk to. A `[[lele.boundary]]` has **two** checks: lele_lint **E036**
forbids the imports in `cannot_use`, and `lele_function_taxonomy` proves the folder's
functions are honest (`require = "honest"` — no hidden I/O reached through local calls).

Enforced by **E036** (imports) and the taxonomy (honesty).

Refs: Gary Bernhardt, [Boundaries](https://www.destroyallsoftware.com/talks/boundaries);
Firezone, [sans-IO](https://www.firezone.dev/blog/sans-io);
[Sans I/O](https://sans-io.readthedocs.io/);
Cockburn, [Hexagonal architecture](https://alistair.cockburn.us/hexagonal-architecture/).

## 4. Group by feature (screaming architecture)

The top-level source tree should name the features of the system, not the framework that
delivers it. `src/stock/`, `src/roster/`; never `src/handlers/`, `src/models/`. The three
deliberate exceptions in this workspace are `methods/` (hide delegate bodies until they
are needed), `__basic__/` (behaviour-free types do not each need a file and a test), and
`bevy_systems/` (all systems of a domain are found in one place).

Judgement only; the folder shape rules (**E001**, **E017**, **E040**) enforce the mechanics.

Ref: Robert C. Martin, [Screaming Architecture](https://blog.cleancoder.com/uncle-bob/2011/09/30/Screaming-Architecture.html).

## 5. Parse, don't validate

When a value has an invariant, make the invalid state unrepresentable: a private field
plus `FromStr`/`TryFrom`, a newtype over a checked value. A function that validates and
returns `()` throws the knowledge away; a function that parses returns a type carrying the
proof, so callers never re-check.

```rust
// judgement: a checked newtype replaces a validate() call
pub struct Port(u16);

impl TryFrom<u16> for Port {
    type Error = Error;
    fn try_from(raw: u16) -> Result<Self, Self::Error> {
        if raw == 0 { Err(Error::ZeroPort) } else { Ok(Self(raw)) }
    }
}
```

Judgement only; not enforced. The Rust shape of the newtype is **E018**.

Ref: Alexis King, [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/).

## 6. End-to-end tests: Screenplay pattern and turmoil

E2E tests read as a script: actors with goals, attempts as reusable tasks, questions for
assertions. In Rust, give the app a plain `async` handle whose methods are the tasks, and
let the test own the timeouts via `run.step(name, future)`. For a sans-IO core, test it
in-process with `turmoil`: simulated hosts, network and time make a distributed system
deterministic on one thread.

Judgement only.

Refs: Serenity/JS, [Screenplay Pattern](https://serenity-js.org/handbook/design/screenplay-pattern/);
[turmoil docs](https://docs.rs/turmoil); Tokio, [Announcing turmoil](https://tokio.rs/blog/2023-01-03-announcing-turmoil).

## 7. Test vocabulary

- **unit test** — Rust's name for the inline `#[cfg(test)]` tests; lives with the code.
- **usage test** (`test_usage`) — this workspace's required per-file test that exercises
  the item once, proving it is usable.
- **doctest** — a snippet in `///` docs; compiled and run by `cargo test`.
- **integration test** — a test in `tests/` using the crate as a dependency.
- **smoke test** — the narrowest run that proves the app starts and responds.
- **characterization test** — records current behaviour before a refactor.
- **snapshot / golden test** — asserts exact output against a checked-in file.
- **property-based test** — asserts an invariant over generated inputs.

Enforced in part by **E007** (inline tests only), **E034** (no tests in `__basic__/`), and
**E006** (`test_usage` every file).

## 8. Dummy `Default` for process handles

A struct that owns a spawned handle (`std::process::Child`, a socket, a task) cannot
`spawn().unwrap()` in `Default` — this workspace denies `unwrap`/`expect`/`panic` (E021).
Prefer `Option<Child>` with `Default => None` and handle `Some` at the call site. Only add
`#[allow(clippy::unwrap_used)]` with explicit user approval (see SKILL.md §3).

Judgement only; the lint gate is enforced by **E021**.

## 9. Constructors come from `derive_more::From`

When a type needs a `::from()` / `.into()` constructor, derive it with `derive_more`
(enable its `from` feature) instead of writing `impl From` by hand or spelling the
wrapping out at every call site. This holds for any wrapped type, not only `String`:

- **Newtype, same type in:** `#[derive(From)]` gives `From<T>`.
- **Newtype, convertible types in:** add `#[from(forward)]` to get
  `impl<U: Into<T>> From<U>` — `&str` into a `String` newtype, `u32` into a `u64`
  newtype, `&str` into a `PathBuf` newtype.
- **Sum type:** `#[derive(From)]` on an enum gives one `From` per single-field variant, so
  `.into()` picks the variant from the value's type. Unit variants are skipped; two
  variants holding the same type conflict (E0119) — mark all but one `#[from(skip)]`.

```rust
// judgement: derive the constructor; call sites name the value, not the wrapping
#[derive(Debug, Clone, PartialEq, Eq, Deref, From)]
#[from(forward)]
pub struct Username(pub String);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deref, From)]
#[from(forward)]
pub struct Millis(pub u64);

#[derive(Debug, Clone, PartialEq, Eq, Deref, From)]
#[from(forward)]
pub struct ConfigPath(pub PathBuf);

let user = Username::from("ada");            // was Username("ada".to_string())
let timeout = Millis::from(250u32);          // was Millis(u64::from(250u32))
let path = ConfigPath::from("config.toml");  // was ConfigPath(PathBuf::from("config.toml"))

#[derive(Debug, Clone, PartialEq, From)]
pub enum Shape {
    Circle(Circle),
    Square(Square),
    Empty,
}

let shape: Shape = circle.into();            // was Shape::Circle(circle)
```

Limit: **only for types without an invariant.** `From` is infallible and public, so
deriving it on a checked newtype hands every caller a way around the check. A type with an
invariant gets `TryFrom`/`FromStr` instead (§5) and never derives `From`. Do not derive
`From` speculatively either: add it when a caller needs the conversion.

Judgement only; not enforced. The newtype shape itself is **E018**.

Ref: [derive_more `From`](https://docs.rs/derive_more/2.1.1/derive_more/derive.From.html).

## 10. State machines — the Rust shape

The concrete Rust realization of §3 (functional core) and the taxonomy. A domain that models a
protocol or session as a machine keeps it in one folder, `{{domain}}::state_machine`:

- **`State`** — `state.rs`, `pub struct State`. Fields are data only: no `outputs` field, no I/O
  handles, no clock. Time and dependencies arrive as parameters.
- **`Input` / `Output`** — `__basic__/enums.rs`, `pub enum Input { ... }` (every event in) and
  `pub enum Output { ... }` (every effect out; e.g. `Notify(Event)` + `NetCommand(NetCommand)`).
- **`update`** — `update.rs`, the single entrypoint:
  `pub fn update(state: &mut State, input: Input, now: EpochSecs) -> Vec<Output>`.
- **Every transition returns its outputs.** `handle_command`, `handle_net_event`, `handle_lobby`,
  `tick`, `dial_candidates`, `send_hello`, ... are all `... -> Vec<Output>` (or `-> Output` for an
  always-single effect). A `outputs: &mut Vec<Output>` parameter is **not** used.
- **Pure readers return values**, not outputs: `fn snapshot(&State) -> Snapshot`,
  `fn hello(&State) -> Hello`, `fn publish_target(&State) -> Option<PublishTarget>`.
- **Other types are allowed** inside `state_machine/` (per-domain enums/structs such as `Hello`,
  `PublishTarget`) — only `State`/`Input`/`Output`/`update` are fixed.
- The folder stays an honest boundary: a `[[lele.boundary]]` with `require = "honest"` and
  `cannot_use = ["tokio", "libp2p", "bevy", "std::net", "std::fs", "std::time"]`.

Worked example: `freenet_libp2p_bevy_plugin/src/discovery/state_machine/`. Language-agnostic
rules: `definition-state-machine`.

Judgement only. A `lele_lint` rule could later enforce "a `state_machine/` folder has `state.rs`
+ `update.rs` and no `&mut Vec<Output>` transition parameter" — add it if the pattern recurs.

## 11. Recursion lives in an inner `fn`

A function that must walk a tree should not recurse as the public function, and should not thread
an accumulator **and** a behaviour parameter through its public signature. Put the walk in an
inner `fn recursion(...)` declared inside the public function; the public function owns the
accumulator, calls `recursion` once, and returns it.

```rust
pub fn matching_names(root: &Node, keep: impl Fn(&str) -> bool) -> Vec<String> {
    fn recursion(node: &Node, keep: &impl Fn(&str) -> bool, out: &mut Vec<String>) {
        if keep(&node.name) {
            out.push(node.name.clone());
        }
        for child in &node.children {
            recursion(child, keep, out);
        }
    }

    let mut out = Vec::new();
    recursion(root, &keep, &mut out);
    out
}
```

**Why:** the public signature stays "behaviour in, output out" (`impl Fn(&str) -> bool` →
`Vec<String>`) instead of leaking the recursion's `&mut` accumulator or its `&keep` borrow. An
inner `fn` cannot capture its environment, so it must take everything it needs — including
`&keep` — as parameters; that is the point: what the recursion needs is visible in its own
signature, the caller-facing API is not. When one inner step differs between callers, pass that
step as the behaviour parameter (§1).

**Limits:** use this for genuinely tree-shaped walks. A flat scan is clearer as a `for`/iterator;
a graph that can revisit nodes needs an explicit stack/queue plus a visited set — follow the data
structure. E015 counts only top-level functions, and no `E0xx` rule descends into a function body,
so the inner `recursion` is invisible to the linter and needs **no** `// needed helper:` marker.

Judgement only; not enforced.

## 12. When a newtype earns its place — and why `PathBuf` usually doesn't

A newtype wraps one scalar to make an implicit meaning explicit: `Milliseconds(u64)`,
`Username(String)`. It earns its place when the underlying type is **untyped enough that the
domain meaning is lost** — a bare `u64` could be bytes, seconds or a count; a bare `String`
could be a name, a token or free text. The newtype says which.

`PathBuf`/`Path` is different: the underlying type is **already the domain abstraction**. It
means "a file or directory on this machine" and nothing else, so wrapping it purely to restate
that ("`ScanFolder(PathBuf)` so you know it's a folder") adds a name without removing an
ambiguity. This is SMELLS S1 read the other way: for paths, `PathBuf`/`&Path` is already the
narrowest honest type.

A newtype over a path still earns its place for the two things a bare path cannot express —
an **invariant** or a **role**, never a restatement:

```rust
// BAD — restates "this is a path"; the reader already knows from `PathBuf`
pub struct ConfigPath(pub PathBuf);

// GOOD — an invariant the path itself does not carry (built only after the check)
pub struct ExistingDir(pub PathBuf);

// GOOD — a role, so two paths cannot be swapped at a call site
pub fn copy(from: Source, to: Destination) { /* … */ }
```

The same test applies to every wrapped type, `String` and integers included: wrap to carry an
**invariant** or a **role**, never just a synonym. `Milliseconds(u64)` and `Username(String)`
pass because the bare type was ambiguous; `ScanFolder(PathBuf)` fails because `PathBuf` was not.

Judgement only; not enforced. The newtype shape itself is **E018**; primitive obsession is
**SMELLS S1**; the invariant-constructor is **§5**; the infallible `From` is **§9**.
