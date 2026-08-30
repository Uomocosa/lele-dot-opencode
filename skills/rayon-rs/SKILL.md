---
name: rayon-rs
description: Use when parallelizing Rust code with Rayon. Covers par_iter/into_par_iter via rayon::prelude::*, ParallelIterator vs IndexedParallelIterator, join/scope, thread pools, and data-race-free guarantees. Works with any Rust project.
---

# rayon-rs — Data Parallelism (Rayon)

Data-parallelism library that converts sequential iterators into parallel ones with work-stealing and data-race-free guarantees. Two modes: parallel iterators and fork-join tasks. Docs-only skill; no config file template is needed.

## Sources

| Topic | URL |
|-------|-----|
| Crate page (v1.12.0, MSRV 1.85) | `https://crates.io/crates/rayon` |
| Crate docs (iterators, join, scope, pools) | `https://docs.rs/rayon` |
| Parallel iter traits (ParallelIterator, IndexedParallelIterator) | `https://docs.rs/rayon/latest/rayon/iter/index.html` |
| Thread pools + join/scope | `https://docs.rs/rayon/latest/rayon/struct.ThreadPool.html` |
| Repository / README / changelog | `https://github.com/rayon-rs/rayon` |

## 1. Installation

```toml
# Cargo.toml
[dependencies]
rayon = "1.12"
```

MSRV 1.85. Pure Rust crate — no `devenv.nix` package needed. WASM builds fall back to sequential; `wasm-bindgen-rayon` adapter required for multithreaded WASM. `CARGO_TARGET_DIR=/tmp/frt-build` (space-in-path fix) applies same as other cargo commands.

## 2. Import

```rust
use rayon::prelude::*;
```

Prelude imports `ParallelIterator`, `IndexedParallelIterator`, `IntoParallelIterator`, `ParallelSlice`, `ParallelString`, `IntoParallelRefIterator`, etc. Rayon mirrors `std` module layout (`rayon::slice`, `rayon::str`, `rayon::collections`).

```rust
use rayon::prelude::*;

fn sum_of_squares(input: &[i32]) -> i32 {
    input.par_iter().map(|&i| i * i).sum()
}
```

Convert sequential to parallel by changing `iter()` → `par_iter()` (or `iter_mut()` → `par_iter_mut()`, `into_iter()` → `into_par_iter()`).

## 3. Parallel Iterator Categories

Lazy like std iterators — execute on consumption (`for_each`, `collect`, `sum`, etc.).

| Category | Methods / Notes |
|----------|-----------------|
| Creation | `par_iter` / `par_iter_mut` / `into_par_iter`; slices `par_split` / `par_windows` / `par_chunks` via `ParallelSlice`; strings `par_split` / `par_lines` via `ParallelString`; `par_extend` / `collect` to grow collections |
| `ParallelIterator` (all) | `map` / `for_each` / `filter` / `filter_map` / `flat_map` / `flatten`, `fold` / `reduce` / `sum` / `product`, `try_for_each` / `try_fold` / `try_reduce`, `cloned` / `copied` / `inspect` / `update`, `take_any` / `skip_any` variants |
| `IndexedParallelIterator` (len known, random-access) | `zip` / `zip_eq` / `interleave`, `chunks` / `fold_chunks`, `enumerate` / `rev` / `step_by` / `skip` / `take`, `position_first` / `position_any` / `cmp` / `eq`, `with_min_len` / `with_max_len`, `collect_into_vec` / `unzip_into_vecs`, `by_uniform_blocks` / `by_exponential_blocks` |
| Reduction pattern | `fold` (per-thread) + `reduce`, or `map` + `sum`; identity `Fn() -> T` must be `Send + Sync` |

`Item: Send` and closures `Sync + Send` required. Methods requiring `Indexed` (e.g., `zip`, `enumerate`, `with_min_len`) become unavailable after unindexed ops like `filter`.

## 4. join / scope / Thread Pools

Alternative to iterators for irregular parallelism:

```rust
let (a, b) = rayon::join(|| expensive(1), || expensive(2));

rayon::scope(|s| {
    s.spawn(|_| work_a());
    s.spawn(|_| work_b());
});

let pool = rayon::ThreadPoolBuilder::new().num_threads(4).build().unwrap();
pool.install(|| data.par_iter().for_each(|x| process(x)));
```

Global pool auto-created on first use. Custom pools isolate tests or limit threads. `scope` can borrow stack data; `spawn` requires `'static`.

## 5. Pitfalls

- Results match sequential counterparts, but side-effect order is nondeterministic (see `avian` skill: Bevy integrator also parallelizes over global `ComputeTaskPool`).
- Small workloads may be slower — tune `with_min_len` / `with_max_len` to control splitting granularity.
- Non-`Send` types (`Rc`, `Cell` content) cannot use `par_iter`.
- WASM without `wasm-bindgen-rayon` runs sequentially on one core.
