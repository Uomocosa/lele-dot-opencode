---
name: itertools-rs
description: Use when working with the itertools crate (extra iterator adaptors, iproduct!/izip!). Docs links, examples, and gotchas.
---

# itertools-rs — Extra Iterator Adaptors

Blanket `impl<T: Iterator> Itertools for T` adds adaptors and free functions; `iproduct!` /
`izip!` macros for cartesian products and lockstep zipping.

## Docs & examples

| Topic | URL |
|-------|-----|
| API docs | `https://docs.rs/itertools` |
| `Itertools` trait (all adaptors) | `https://docs.rs/itertools/latest/itertools/trait.Itertools.html` |
| All items (structs, fns, macros) | `https://docs.rs/itertools/latest/itertools/all.html` |
| Feature flags | `https://docs.rs/itertools/latest/itertools/#crate-features` |
| Repository / examples | `https://github.com/rust-itertools/itertools` |

`Cargo.toml`: `itertools = "0.15"` (default `use_std`).

## Minimal example

```rust
use itertools::Itertools;

let grouped: Vec<(bool, Vec<i32>)> = vec![1, 3, -2, -2, 1]
    .into_iter()
    .chunk_by(|x| *x >= 0)
    .into_iter()
    .map(|(k, g)| (k, g.collect()))
    .collect();

assert_eq!((1..5).tuple_windows().collect_tuple(), Some((1, 2, 3, 4)));
let prod: Vec<(i32, i32)> = (1..3).cartesian_product(4..6).collect();
```

## Gotchas

- `group_by` is deprecated since 0.13 — use `chunk_by`. Both are iterable **by reference**
  (`for (k, g) in &iter.chunk_by(...))`); call `.into_iter()` when needed.
- `sorted` / `sorted_by*` return iterators, not `Vec` — collect if you need one.
- Adaptors are lazy: nothing runs until consumed.
- Disabling `use_std` drops `unique`, `counts`, `into_group_map`; disabling `use_alloc` drops
  `chunk_by`, `kmerge`, `join`.
