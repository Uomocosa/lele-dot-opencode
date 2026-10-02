---
name: rayon-rs
description: Use when parallelizing Rust code with Rayon. Docs links, upstream examples, and gotchas.
---

# rayon-rs — Data Parallelism

Turns sequential iterators into parallel ones (`par_iter` / `into_par_iter`) with work-stealing,
plus fork-join (`join` / `scope`) for irregular parallelism.

## Docs & examples

| Topic | URL |
|-------|-----|
| API docs | `https://docs.rs/rayon` |
| Parallel iter traits | `https://docs.rs/rayon/latest/rayon/iter/index.html` |
| Thread pools / join / scope | `https://docs.rs/rayon/latest/rayon/struct.ThreadPool.html` |
| Repository / examples | `https://github.com/rayon-rs/rayon` |

`Cargo.toml`: `rayon = "1.12"`.

## Minimal example

```rust
use rayon::prelude::*;

let squares: Vec<i32> = (1..=10).into_par_iter().map(|i| i * i).collect();
let sum: i32 = squares.par_iter().sum();

let (a, b) = rayon::join(|| expensive(1), || expensive(2));
```

## Gotchas

- Lazy like `std` iterators — nothing runs until consumed (`collect`, `for_each`, `sum`, …).
- Results equal the sequential version, but side-effect order is nondeterministic.
- `Item: Send` and closures `Sync + Send` are required (`Rc`, `Cell` contents won't work).
- Indexed-only methods (`zip`, `enumerate`, `with_min_len`) are unavailable after `filter`.
- Small workloads can be slower — tune with `with_min_len` / `with_max_len`.
- WASM without `wasm-bindgen-rayon` runs on one core.
