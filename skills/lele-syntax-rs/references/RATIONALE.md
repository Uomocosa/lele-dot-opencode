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

Judgement only; the folder shape rules (**E001**, **E017**, **E029**) enforce the mechanics.

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
