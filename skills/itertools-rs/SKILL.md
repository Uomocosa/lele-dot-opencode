---
name: itertools-rs
description: Use when working with the itertools crate (extra iterator adaptors, free functions, and iproduct!/izip! macros). Covers Itertools trait import, adaptor categories, collecting helpers, and feature flags vs std. Works with any Rust project.
---

# itertools-rs — Extra Iterator Adaptors (itertools)

Extra iterator adaptors, iterator methods, free functions, and macros for Rust. Import the `Itertools` trait to extend `Iterator`. Docs-only skill; no config file template is needed.

## Sources

| Topic | URL |
|-------|-----|
| Crate page (v0.15.0, downloads, dependents) | `https://crates.io/crates/itertools` |
| API docs (crate, trait, free fns, macros) | `https://docs.rs/itertools` |
| Trait `Itertools` (adaptors + regular methods) | `https://docs.rs/itertools/latest/itertools/trait.Itertools.html` |
| Crate features `use_std` / `use_alloc` | `https://docs.rs/itertools/latest/itertools/#crate-features` |
| Repository / CHANGELOG / releases | `https://github.com/rust-itertools/itertools` |
| All items (structs, free fns, macros) | `https://docs.rs/itertools/latest/itertools/all.html` |

## 1. Installation

```toml
# Cargo.toml
[dependencies]
itertools = "0.15.0"
```

Features (from `Cargo.toml: [features]`):

- `default = ["use_std"]` — enables `use_alloc` + `either/use_std`.
- `use_std` — hash maps and `std`-dependent items (`unique`, `counts`, `into_group_map`, etc.). Disable for `#![no_std]`.
- `use_alloc` — allocation-dependent items (`chunk_by`, `kmerge`, `join`, `chunks`, etc.). Required when `use_std` is off but alloc is available.

MSRV 1.63.0. No `devenv.nix` package needed — pure Rust crate.

## 2. Import

```rust
use itertools::Itertools;
```

Blanket impl: `impl<T: Iterator> Itertools for T`. All `Itertools` methods become available on any iterator. Free-function variants (`itertools::interleave`, `itertools::kmerge`, `itertools::chain`, etc.) and macros `iproduct!` / `izip!` are alternatives when the trait is not imported.

## 3. Adaptor Categories

Adaptors are lazy (`must_use` — do nothing until consumed). Grouped by intent:

| Category | Methods |
|----------|---------|
| Bridging / zipping | `interleave`, `interleave_shortest`, `intersperse` / `intersperse_with`, `zip_longest`, `zip_eq`, `merge` / `merge_by`, `kmerge` / `kmerge_by`, `merge_join_by` |
| Chunking / grouping | `chunk_by` (replaces deprecated `group_by` since 0.13), `chunks`, `group_map` / `into_group_map` (via `Itertools::into_group_map` on `Iterator<Item=(K,V)>`), `counts` / `counts_by`, `dedup` / `dedup_by` / `unique` |
| Windowing / tuples | `tuple_windows`, `circular_tuple_windows`, `tuples`, `array_windows` / `circular_array_windows`, `next_tuple`, `collect_tuple`, `next_array` |
| Sorting / ordering | `sorted` / `sorted_by` / `sorted_by_key` / `k_smallest` (all return iterators, not `Vec`) |
| Combinatorics | `permutations(k)`, `combinations(k)`, `combinations_with_replacement(k)`, `powerset`, `cartesian_product` / `multi_cartesian_product` (also `iproduct!` macro) |
| Coalescing / folding | `coalesce`, `batching`, `fold_while` / `tree_reduce`, `partition_map`, `process_results` |
| Result iterators | `map_ok`, `filter_ok`, `filter_map_ok`, `flatten_ok`, `process_results` |
| Misc | `tee`, `pad_using`, `with_position`, `positions`, `find_position`, `update`, `format` / `join` |

Free functions mirror many of the above: `itertools::chain`, `itertools::equal`, `itertools::assert_equal`, `itertools::kmerge`, etc. Macros: `iproduct!(a, b, c)` for cartesian products, `izip!(a, b, c)` for lockstep zipping (optimized wrapper over `.zip()`).

## 4. Pitfalls

- `group_by` is deprecated since 0.13 — use `chunk_by`. Both return `ChunkBy`/`IntoChunks` which are **iterable by reference** (`for (k, g) in &iter.chunk_by(...)`), not `Iterator` directly; call `.into_iter()` explicitly if needed.
- `sorted` family returns an iterator, not a `Vec`. Collect with `.collect::<Vec<_>>()` or iterate directly.
- Adaptors are lazy — forgetting to consume (`.collect()`, `for`, `.counts()`, etc.) yields no effect.
- `zip_longest` yields `EitherOrBoth<L,R>`; `zip_eq` panics on length mismatch.
- Disabling `use_std` removes `unique`, `counts`, `into_group_map`, `into_grouping_map`; disabling `use_alloc` removes `chunk_by`, `kmerge`, `join`, `chunks` and most adaptors.

## 5. Example

```rust
use itertools::Itertools;

let data = vec![1, 3, -2, -2, 1, 0, 1, 2];
let grouped: Vec<(bool, Vec<i32>)> = data
    .into_iter()
    .chunk_by(|x| *x >= 0)
    .into_iter()
    .map(|(k, g)| (k, g.collect()))
    .collect();
assert_eq!(grouped, vec![(true, vec![1, 3]), (false, vec![-2, -2]), (true, vec![1, 0, 1, 2])]);

let it = (1..5).tuple_windows::<(i32, i32)>();
itertools::assert_equal(it, vec![(1, 2), (2, 3), (3, 4)]);

let prod: Vec<(i32, i32)> = (1..3).cartesian_product(4..6).collect();
assert_eq!(prod, vec![(1, 4), (1, 5), (2, 4), (2, 5)]);
```
