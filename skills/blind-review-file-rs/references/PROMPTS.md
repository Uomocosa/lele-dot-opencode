# Prompts for the `blind-reader`

Paste these verbatim, filling the `<…>` slots.

## Primer (start of round 1)

```
You are reviewing ONE file from a Rust crate you cannot see. Conventions of this codebase:
- One file holds one primary item; the file is named after it (snake_case of the type/fn).
- `__basic__/` holds behavior-free types; `mod.rs` holds only `mod` / `pub use`.
- `#[atomic_delegates] impl T { fn f(..) {} }` is a shell: each empty body forwards to
  `methods/<t_snake>/<f>.rs`, where the real body lives as a free function.
- Domain-concept names are short; internal-machinery names (even `pub`) are as long as needed.
  A `bool` is named as the question it answers.
Answer only from what you are shown. Do not guess what you cannot see; say it is unclear.
```

## Round 1

```
<primer>

File: `<relative path>`
```rust
<file text>
```

Answer in this shape:
1. Responsibility — 1–3 sentences: what this file is responsible for.
2. Items — one line per public type / fn / field: what you think it means.
3. Confidence — 1–5 (5 = certain).
4. Confusing names — each name that slowed you down, with why (vague, misleading, too
   mechanical, synonym of another name, …). "none" if none.
```

## Round 2

```
Here is more context: the definitions of the crate types this file uses and, if it is a
delegate shell, the method bodies behind it.

<context.py output>

Answer again in the same 4-part shape, then add:
5. Changed — what changed from your first answer and which piece of context caused it.
```
