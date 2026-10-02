---
name: criterion-rs
description: Use when benchmarking Rust code with Criterion.rs. Docs links, upstream examples, and gotchas.
---

# criterion-rs — Microbenchmarks

Statistics-driven benchmarking with sampling, confidence intervals, and comparison against a
saved baseline.

## Docs & examples

| Topic | URL |
|-------|-----|
| API docs | `https://docs.rs/criterion` |
| User guide (book) | `https://criterion-rs.github.io/book/` |
| Getting started | `https://criterion-rs.github.io/book/getting_started.html` |
| Repository / examples | `https://github.com/criterion-rs/criterion.rs` |

`Cargo.toml`:

```toml
[dev-dependencies]
criterion = { version = "0.8", features = ["html_reports"] }

[[bench]]
name = "my_benchmark"
harness = false
```

## Minimal example

```rust
use std::hint::black_box;
use criterion::{criterion_group, criterion_main, Criterion};

fn bench(c: &mut Criterion) {
    c.bench_function("fib 20", |b| b.iter(|| fibonacci(black_box(20))));
}

criterion_group!(benches, bench);
criterion_main!(benches);
```

Run: `cargo bench` (baseline in `target/criterion/`; HTML at `target/criterion/report/index.html`).

## Gotchas

- `harness = false` is required — otherwise it conflicts with the libtest harness.
- Black-box inputs (`std::hint::black_box`); sub-nanosecond times signal the optimizer elided work.
- `throughput()` exists only on `benchmark_group`, not `bench_function`.
- Call `group.finish()` explicitly (summary pages are incomplete otherwise).
