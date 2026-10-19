---
name: definition-functional-patterns
description: Use when writing, planning, or refactoring code to make it smaller and clearer with functional patterns — higher-order functions, iterator pipelines, functional core/imperative shell, transform-not-mutate, illegal states unrepresentable, combinators, declarative tables, composition, closures over state. Each pattern has a signal and an abuse warning. Works with any project, any language. Provides language-agnostic definitions and pseudocode.
---

# Functional Patterns (Definitions)

This skill is **definitions + pseudocode only**, with a one-line Rust note per pattern.
Purity/honesty of functions is covered by `definition-function-taxonomy`; this skill is about
**reshaping** code so it gets smaller AND clearer.

## Rule zero

Apply a pattern only if the result is **smaller AND clearer**, and still obeys the project's
rules (atomic files/delegates, naming). Less code that is harder to read is a regression.
When citing a pattern in a plan or review, use its id: `[FP1 higher-order]`.

## FP1 — Higher-order function

Two functions differ only in one step → one function taking that step as a parameter.

```
before: sum_even(xs) = fold xs where even(x)      sum_odd(xs) = fold xs where odd(x)
after:  sum_where(xs, keep) = fold xs where keep(x)
        sum_where(xs, even)  /  sum_where(xs, odd)
```
- **Signal:** near-identical bodies; copy-paste with one changed predicate/mapping/value.
- **Abuse:** >2 function parameters; a parameter always passed the same function (inline it);
  callers that need comments to explain which closure to pass.
- **Rust:** `fn sum_where(xs: &[i32], keep: impl Fn(i32) -> bool) -> i32`.

## FP2 — Iterator pipeline over manual loop

Loop that accumulates into a mutable collection → map/filter/fold/collect.

```
before: out = []; for x in xs: if ok(x): out.push(f(x))
after:  out = xs |> filter(ok) |> map(f) |> collect
```
- **Signal:** `mut` accumulator + `push` / counter / flag set inside a loop.
- **Abuse:** chains longer than ~5 steps (name an intermediate); side effects inside `map`;
  early-exit logic that reads clearer as a loop with `break`.
- **Rust:** `xs.iter().filter(ok).map(f).collect::<Vec<_>>()`; `try_fold`/`collect::<Result<_,_>>`
  for fallible steps.

## FP3 — Functional core, imperative shell

Pure decision logic in one function; I/O, ECS, network, clock in a thin wrapper around it.

```
core(state, input) -> (new_state, outputs)       // pure, unit-testable
shell: read input; (s, out) = core(s, input); perform(out)
```
- **Signal:** logic untestable without a runtime; decisions interleaved with reads/writes.
- **Abuse:** a "core" that only forwards to the shell (shallow); splitting trivial one-liners.
- **Rust:** pure fn + Bevy wrapper system (see bevy-rs core-logic + wrapper pattern).

## FP4 — Transform, don't mutate

Return a new/updated value instead of mutating through many helpers.

```
before: normalize(&mut cfg); clamp(&mut cfg); apply_defaults(&mut cfg)
after:  cfg = cfg |> normalize |> clamp |> apply_defaults
```
- **Signal:** `&mut` threaded through several helpers; hard to tell who changed what.
- **Abuse:** cloning large structs in hot paths; fighting a framework that is mutation-based (ECS).
- **Rust:** `fn clamp(self) -> Self` (consume + return) — no clone needed.

## FP5 — Make illegal states unrepresentable

Replace combinations of bools/Options with an enum or newtype; defensive checks disappear.

```
before: { connected: bool, peer: Option<Id>, error: Option<E> }   // 8 combos, 3 valid
after:  enum Conn { Idle, Connected(Id), Failed(E) }
```
- **Signal:** `if a && b.is_some()` guards; comments saying "only valid when …"; `unreachable!`.
- **Abuse:** type explosion for states nothing branches on.
- **Rust:** enum with data; single-field newtype with validation in the constructor.

## FP6 — Combinators over branching

Chain Option/Result operations instead of nested match / if-let.

```
before: match a { Some(x) => match f(x) { Ok(y) => Some(g(y)), Err(_) => None }, None => None }
after:  a |> and_then(f >> ok) |> map(g)
```
- **Signal:** pyramid of `match`/`if let` where each arm just forwards `None`/`Err`.
- **Abuse:** long combinator chains with closures that need reading twice — a `match` with
  named arms is clearer when arms do real work.
- **Rust:** `?`, `map`, `and_then`, `ok_or_else`, `unwrap_or_else`, `let … else`.

## FP7 — Declarative table

Repeated branches mapping an input to constants → one table/match + one generic function.

```
before: if k == A: return (1, "a") elif k == B: return (2, "b") elif ...
after:  TABLE = {A: (1, "a"), B: (2, "b"), ...};  lookup(k) = TABLE[k]
```
- **Signal:** same branch shape repeated, only literals differ.
- **Abuse:** tables of closures that are really separate behaviours (use enum methods / traits).
- **Rust:** exhaustive `match` returning a tuple/struct, or `const` array of structs.

## FP8 — Composition over flags

Small single-purpose functions chained by the caller instead of one function with mode flags.

```
before: render(doc, minify: bool, with_header: bool)
after:  doc |> render |> (with_header ? add_header : id) |> (minify ? minify : id)
```
- **Signal:** a `bool` / mode parameter that switches behaviour; `if flag` at the top of a body.
- **Abuse:** splitting so fine that the caller re-assembles the same chain everywhere (then keep
  one named composed function).
- **Rust:** separate fns, or a small builder; a bool param is a smell.

## FP9 — Closures over state

Capture configuration once, pass the resulting function, instead of threading the same args.

```
before: score(p, w1, w2, cap) called from 6 places with the same w1, w2, cap
after:  scorer = make_scorer(w1, w2, cap);  scorer(p)
```
- **Signal:** the same 2–3 arguments forwarded unchanged through many calls.
- **Abuse:** hidden state that callers need to see (prefer a named struct with a method when the
  config is a domain concept — that is often clearer in Rust).
- **Rust:** `fn make_scorer(cfg: ScoreCfg) -> impl Fn(&Peer) -> Score`, or `struct Scorer` + method.

## Quick pick

| You see                                   | Try   |
|-------------------------------------------|-------|
| two bodies differing in one step          | FP1   |
| mut accumulator in a loop                 | FP2   |
| logic you can't test without runtime      | FP3   |
| `&mut` passed through many helpers        | FP4   |
| bool/Option combos + guards               | FP5   |
| nested match forwarding None/Err          | FP6   |
| repeated branches differing in literals   | FP7   |
| bool mode parameter                       | FP8   |
| same args threaded everywhere             | FP9   |
