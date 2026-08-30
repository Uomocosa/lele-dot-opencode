---
name: criterion-rs
description: Use when benchmarking Rust code with Criterion.rs. Covers dev-dependency setup, bench harness (harness=false), Criterion/Bencher groups, throughput, bench_with_input, black_box, and cargo bench invocation. Works with any Rust project.
---

# criterion-rs — Statistics-Driven Microbenchmarks (Criterion.rs)

Statistics-driven microbenchmarking on stable Rust. Detects regressions with confidence intervals, sampling, and comparison vs previous runs. Docs-only skill; no config file template is needed.

## Sources

| Topic | URL |
|-------|-----|
| Crate page (v0.8.2, MSRV 1.86) | `https://crates.io/crates/criterion` |
| API docs (Criterion, Bencher, BenchmarkGroup, Throughput) | `https://docs.rs/criterion` |
| Struct `Criterion` + measurement phases | `https://docs.rs/criterion/latest/criterion/struct.Criterion.html` |
| User Guide (book, groups, throughput, inputs) | `https://criterion-rs.github.io/book/` |
| Getting started + bench harness | `https://criterion-rs.github.io/book/getting_started.html` |
| Repository / changelog / extensions | `https://github.com/criterion-rs/criterion.rs` |

## 1. Installation

```toml
# Cargo.toml
[dev-dependencies]
criterion = { version = "0.8", features = ["html_reports"] }

[[bench]]
name = "my_benchmark"
harness = false
```

`harness = false` disables libtest harness — required. Features: `html_reports` + `plotters` are default (via `cargo_bench_support`); gnuplot optional fallback. MSRV 1.86; supports last 3 stable. `CARGO_TARGET_DIR=/tmp/frt-build` (space-in-path fix) applies to `cargo bench` same as `cargo build`.

## 2. Bench File

```rust
// benches/my_benchmark.rs
use std::hint::black_box;
use criterion::{criterion_group, criterion_main, Criterion};

fn fibonacci(n: u64) -> u64 {
    match n {
        0 | 1 => 1,
        n => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

fn criterion_benchmark(c: &mut Criterion) {
    c.bench_function("fib 20", |b| b.iter(|| fibonacci(black_box(20))));
}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);
```

`Criterion` is the benchmark manager (warm-up → measurement → analysis → comparison). `criterion_group!` defines a group; `criterion_main!` generates `main`. Benches compile as separate crates — only `pub` items are benchable.

## 3. Groups, Inputs, Throughput

Use `benchmark_group` when comparing implementations or sweeping inputs. `Throughput` is group-only.

```rust
use criterion::{BenchmarkId, Criterion, Throughput};
use std::hint::black_box;

fn bench_group(c: &mut Criterion) {
    let mut group = c.benchmark_group("from_elem");
    for size in [1024, 2048, 4096].iter() {
        group.throughput(Throughput::Bytes(*size as u64));
        group.bench_with_input(BenchmarkId::from_parameter(size), size, |b, &size| {
            b.iter(|| (0..size).collect::<Vec<u32>>());
        });
    }
    group.finish();
}
```

- `group.throughput(Throughput::Bytes(n))` / `Throughput::Elements(n)` adds `thrpt:` line (MiB/s or elements/s); not available on bare `bench_function`.
- `bench_with_input` + `BenchmarkId::from_parameter` / `BenchmarkId::new` groups related benches for comparison plots/HTML.
- Sampling tuning per group: `group.sample_size(100)`, `measurement_time`, `warm_up_time`, `sampling_mode(SamplingMode::Auto)` (default; `Linear`/`Flat` for long benches). Defaults: sample 100, warm-up 3s, measure 5s, bootstrap 100k, noise 1%, confidence 0.95.

## 4. Running

```bash
cargo bench
cargo bench -- "fib 20"
cargo bench -- --save-baseline before
cargo bench -- --baseline before
```

First run establishes baseline in `target/criterion/`; second run reports change with confidence interval and outlier analysis. HTML report (with `html_reports`) at `target/criterion/report/index.html`. Filter by substring after `--`; bench flags follow second `--`.

## 5. Pitfalls

- Missing `harness = false` conflicts with libtest harness.
- Missing `std::hint::black_box` on inputs lets LLVM constant-fold/DCE the code — sub-ns times signal elision. Criterion auto-black-boxes `b.iter` return, but discarded intermediates need explicit `black_box`. `criterion::black_box` is deprecated — use `std::hint::black_box`.
- Forget `group.finish()` — summary pages incomplete (auto-called on drop, but call explicitly).
- Benches report time per iteration `[lower estimate upper]` + outliers; throughput only appears when `throughput` is set.
