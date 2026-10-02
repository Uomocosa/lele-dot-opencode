---
name: avian-rs
description: Use when working with the Avian 2D/3D physics engine (Rust crate, Bevy). Covers the critical determinism caveat (Avian's integrator parallelizes over Bevy's process-global ComputeTaskPool, so two engine Apps in one process cannot be bit-identical) plus docs links and footguns.
---

# avian-rs — Avian (Bevy physics)

Deterministic-lockstep guidance for Avian. **Read the determinism section first.**

## Docs & examples

| Topic | URL |
|-------|-----|
| API docs (Avian2D) | `https://docs.rs/avian2d` |
| API docs (Avian3D) | `https://docs.rs/avian3d` |
| Book / user guide | `https://docs.rs/avian2d/latest/avian2d/#documentation` |
| Repository / examples | `https://github.com/avianphysics/avian` |
| Discussions (determinism Q&A) | `https://github.com/avianphysics/avian/discussions` |

## Determinism — read this FIRST

Avian integrates bodies with `Query::par_iter_mut`, drawing from **Bevy's process-global
`ComputeTaskPool`** regardless of the `parallel` cargo feature (that gates parry, not Bevy's
parallel query iterator).

- **A single engine App is deterministic.**
- **Two co-existing engine Apps in ONE process are NOT deterministic** — they interleave on the
  shared compute pool → nondeterministic float accumulation → divergent state hashes.
- **Separate processes ARE deterministic** (each has its own pool and one engine).

Fixes that do **not** work for in-process multi-engine determinism:

- Pinning `ComputeTaskPool` to 1 thread → deadlocks Avian's `TaskPool::scope`.
- Serializing engine `.step()` behind a process-wide `Mutex` → pools still diverge.

The correct model: **one engine per OS process**; validate determinism cross-process, never by
putting two engines in one test process. Full investigation:
`found_problems/compile-taskpool-nondeterminism.md`.

## Setup notes

```rust
app.add_plugins((
    MinimalPlugins,
    bevy::transform::TransformPlugin,
    PhysicsPlugins::default(),
));
```

- Enable the `enhanced-determinism` cargo feature for cross-platform `libm` math when determinism
  matters (with `parry*-f32`). It stabilizes arithmetic but does **not** fix the multi-engine pool
  issue.
- Avian already pins its `PhysicsSchedule` to a `SingleThreadedExecutor`; that is orthogonal.
- Force a fixed step with `TimeUpdateStrategy::ManualDuration(1 / TICKS_PER_SECOND)`, and prefer a
  **power-of-two** tick rate (`64`, `128`) over `60` — `1/60` is inexact in binary and the
  sub-step accumulator can occasionally skip/double a physics step.

## Footguns

- Two engines in one process (e.g. in-process "two-node" tests) is fundamentally
  non-deterministic — test cross-process instead.
- Keep velocities/gravity authored per-second, not per-tick, so the tick rate stays physics-neutral.
