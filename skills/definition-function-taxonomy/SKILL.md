---
name: definition-function-taxonomy
description: Use when classifying, designing, or reviewing functions by purity or honesty — determinism, hidden state, signature completeness, local reasoning, testability, infectious dishonesty. Works with any project, any language. Provides language-agnostic definitions and pseudocode.
---

# Function Taxonomy — Pure / Impure and Honest / Dishonest (Definitions)

Source idea from Logan Smith "How to write the perfect function" — reframing the traditional `pure vs impure` split into `honest vs dishonest`. This skill is **definitions + pseudocode only**. No language-specific code, no toolchain.

## 1. At a Glance

| Taxonomy | Question it answers | Honest equivalent? |
|---|---|---|
| **Pure** | Same inputs -> same outputs? No visible mutation? No hidden reads? | Subset of honest (over-constrained) |
| **Impure** | Does it depend on or affect hidden state? | Maps to dishonest |
| **Honest** | Can the caller control all inputs/outputs via the signature? | Covers pure + disciplined mutation |
| **Dishonest** | Does the signature lie about real inputs/outputs? | Includes impure + sneaky reads |

Honest is the preferred mental model: it keeps the benefits of pure while allowing disciplined mutation (e.g., in-place sort), and correctly flags read-only but hidden-input functions (e.g., clock read) as dishonest.

## 2. Pure vs Impure

### 2.1 Pure — definition

A function is **pure** when all three hold:

1. **Deterministic** — same arguments always produce same observable result.
2. **No visible mutation** — it does not modify arguments in a caller-visible way, nor any shared/global state.
3. **No hidden reads** — it does not read mutable shared/global state (including hidden `this` if applicable).

Consequences: local reasoning (body alone suffices), freely testable, freely cacheable/reorderable in abstract semantics.

### 2.2 Impure — definition

A function is **impure** when it violates any pure criterion: reads hidden state, mutates visible state, or is nondeterministic.

Consequences: requires global reasoning, tests need environment setup, order-sensitive.

### 2.3 Pseudocode — pure

```
// pure: deterministic, no mutation, no hidden reads
function add(a, b) -> c
    return a + b

// pure: returns derived value, no mutation
function format_name(first, last) -> string
    return first + " " + last

// pure accessor: returns view/copy of input without hidden reads
function first_element(items) -> element
    return items[0]
```

### 2.4 Pseudocode — impure (classic)

```
// impure: reads hidden global
function get_time() -> timestamp
    return read_system_clock()   // hidden input: wall time

// impure: mutates global / performs I/O
function draw_to_screen(pixels)
    write_framebuffer(pixels)

// impure: mutates argument visibly (by traditional strict definition)
function sort_in_place(items)
    reorder items ascending       // visible mutation -> impure under strict pure
```

### 2.5 Why strict pure over-constrains

Two counter-examples motivate the honest reframing:

```
// Counter-example A: mutates but is otherwise well-behaved
function sort_in_place(items)
    reorder items ascending
// Deterministic, testable, locally reasoned, only touches given arg.
// Strict pure says "impure", but caller can fully control it.

// Counter-example B: no mutation yet misbehaves
function get_time() -> timestamp
    return read_system_clock()
// No mutation, no arguments, yet nondeterministic and untestable in isolation.
// Strict pure might call it "pure-ish" — misleading.
```

## 3. Honest vs Dishonest

### 3.1 Honest — definition

A function is **honest** when:

> It **only accesses the outside world through its signature**. Every input it reads and every output/effect it produces is reachable via an explicit parameter or return value. No hidden reads, no hidden writes.

The caller can **fully control** the function's behavior by choosing arguments. Includes true pure functions **and** disciplined mutating functions that only mutate what they were given.

Properties: local reasoning, testable, composable. Lives at **leaves** of the call tree.

### 3.2 Dishonest — definition

A function is **dishonest** when:

> Its **signature is an incomplete description** of its real inputs/outputs. It reads or writes state not visible in the signature.

Caller cannot fully control or predict it from arguments alone. Always involves hidden coupling (global registry, clock, filesystem, RNG state, framebuffer, etc.).

Properties: global reasoning required, fragile tests, **infectious** (see §4), but **necessary** at I/O boundaries — abstract machine cannot affect the world without dishonesty.

### 3.3 Pseudocode — honest

```
// honest, pure
function add(a, b) -> c
    return a + b

// honest, mutates only what was given (disciplined mutation)
function clear(vector)
    set vector.size = 0          // keeps capacity, deterministic outcome
    // returns via mutation channel; no hidden state

// honest, two output channels: mutation + return value
function remove_if(items, predicate) -> index
    // reorders items so matching elements are at front
    // returns boundary index so caller can erase remainder
    return boundary

// honest, explicit dependency injection (PRNG example)
function populate(world, rng, count)
    repeat count times
        p = create_particle(rng.next())
        world.add(p)
// Caller may seed rng with clock (random) or fixed value (reproducible/tests)
// Contrast with dishonest variant that conjures global rng internally.
```

### 3.4 Pseudocode — dishonest

```
// dishonest accessor: name suggests pure lookup, but filters via hidden global
function get_unloaded_assets(names) -> list
    all = lookup_registry(names)              // registry is global
    return filter(all, a -> not is_loaded(a)) // is_loaded reads global asset manager
// Same args can return different results depending on prior loads.

// dishonest: hidden input (clock)
function get_time() -> timestamp
    return read_system_clock()

// dishonest: hidden output (screen) — useful but still dishonest
function draw_to_screen(pixels)
    write_framebuffer(pixels)

// dishonest: hidden read+write of shared RNG (global PRNG anti-pattern)
function populate_global(world, count)
    rng = get_global_rng()       // hidden read
    rng.seed(read_system_clock())// hidden input + hidden write
    repeat count times
        p = create_particle(rng.next())
        world.add(p)
// Beats above? No local reasoning, order/thread-sensitive, not reproducible.

```

### 3.5 Allowed dishonesty — I/O boundaries

Dishonesty is not always bad. The honest abstract machine ends at the program boundary; beyond it (`screen`, `file`, `network`, `clock`) you **must** be dishonest. Treat dishonest I/O as valuable but **toothed**: isolate it, keep it small, and keep it at the top.

```
function bounce(normal, velocity) -> new_velocity
    // honest: requires invariant via type — see §6
    return reflect(velocity, normal)

function render_frame(world, screen)   // dishonest boundary
    pixels = render(world)             // honest
    draw_to_screen(pixels, screen)     // dishonest leaf at top
```

Backward / framework hooks (e.g., `update` called by engine, `main`) abstract the **call site** rather than the implementation — keep their bodies minimal and delegate immediately to honest functions.

## 4. Infectious Property and Call-Tree Shape

> **If a function calls a dishonest function, it becomes dishonest.**

Therefore in any call tree:

* Honest functions occupy **leaves** (and interior built only from honest leaves).
* Dishonest functions occupy **roots / edges** near I/O.
* Honesty flows upward only through honest calls.

Design rule (Logan Smith): **maximize honest leaves, inject dishonesty at the topmost possible level.** Build core logic honest; wrap it with a thin dishonest skin.

Pseudocode — refactoring toward honesty:

```
// Before: intermingled (hard to test)
function main()
    name = read_console()                // dishonest
    perms = all_permutations(name)       // honest-ish but tangled with I/O
    for p in perms
        write_console(p)                 // dishonest

// After: honest core + thin dishonest shell (testable)
function all_permutations(input) -> list
    // pure/honest: builds data structure, no I/O
    return permutations_of(input)

function for_each_permutation(input, action)
    // honest, allocation-free alternative: caller controls effect via callback/iterator
    for p in permutations_of(input)
        action(p)

function main()
    name = read_console()                // dishonest at top
    // option A: materialized list
    perms = all_permutations(name)       // honest
    for p in perms
        write_console(p)                 // dishonest at top
    // option B: injection, no big allocation
    for_each_permutation(name, p -> write_console(p))
```

Same shape applies to PRNG:

```
// dishonest: hidden RNG
function populate_global(world, count)  // see §3.4

// honest: injected RNG — caller decides seeding policy
function populate(world, rng, count)    // see §3.3
function main()
    rng = make_rng(seed = read_system_clock()) // dishonest seeding at top
    populate(world, rng, 100)                  // honest core
    // for reproducibility/tests:
    // rng = make_rng(seed = 42); populate(world, rng, 100)
```

## 5. Decision Checklist (use in reviews)

For any `function f`:

1. List every read and write in `f`'s body.
2. Is each read from a parameter (or transitively from one)? If any read is from global/clock/filesystem/registry not passed in -> **dishonest**. Under strict pure: -> **impure**.
3. Is each write to a parameter or return value only? If any write goes to global/screen/file not returned/passed -> **dishonest** (and impure).
4. Same inputs (including explicit RNG/state params) -> same observable result? If no -> impure and likely dishonest.
5. Can you write a deterministic unit test by only choosing arguments? If yes -> honest (often pure). If you must set up global state / time / filesystem first -> dishonest.

Quadrant cheat sheet:

| Deterministic? | Visible mutation? | Hidden I/O? | Verdict |
|---|---|---|---|
| yes | no | no | pure & honest |
| yes | only given args | no | **not pure (strict) but honest** — prefer honest label (`sort`, `clear`, `remove_if`) |
| yes/no | no | yes (read) | impure & dishonest (`get_time`, `get_unloaded_assets`) |
| any | yes to global / screen | yes | impure & dishonest (`draw_to_screen`, `populate_global`) |

## 6. Signature Honesty and Invariants (types as honesty)

A dishonest signature invites misuse. Strengthen honesty via types when a precondition must hold:

```
// Weak (dishonest): caller may pass any vector, but bounce requires unit normal
function bounce(velocity, normal) -> velocity
    // must re-normalize or branch on zero-length — error handling leaks in

// Strong (honest): invariant encoded in type; illegal states unconstructable
type NormalizedVector   // invariant: length == 1, constructible only via checked constructor
function bounce(velocity, normal: NormalizedVector) -> velocity
    // no re-check, no failure path; caller normalizes once at call site or reuses stored value
    return reflect(velocity, normal)
```

Applies generally: when a parameter has an invariant (non-empty, sorted, normalized, locked mutex proof), encode it so the signature tells the truth.

## 7. Common Mistakes

* Calling hidden-state reads "pure because no mutation" — hidden reads are dishonest.
* Calling disciplined in-place mutation "dishonest" — if it only touches given args and is deterministic, it is honest.
* Letting dishonest helpers leak into core: `get_unloaded_assets` looks like `get_required_assets` but hides a filter; name and signature should reveal the dependency or take it as a parameter (`is_loaded` predicate / registry handle).
* Seeding/using a global PRNG inside core logic instead of injecting `rng` — sacrifices reproducibility and testability with no benefit.
* Encoding every invariant as a type — dishonest to over-constrain where not needed; balance caller's flexibility vs. safety.
