---
name: avian
description: Use when working with the Avian 2D/3D physics engine (Rust, Bevy). Covers the critical determinism caveat — Avian's integrator parallelizes over Bevy's process-global ComputeTaskPool, so two engine Apps in one process cannot be bit-identical — plus plugin setup, fixed timestep, rollback sessions, and common footguns.
---

# Avian (Bevy physics)

Deterministic-lockstep and physics-integration guidance for Avian 2D/3D.

## 1. Determinism — read this FIRST

Avian integrates bodies with `Query::par_iter_mut`, which draws work from **Bevy's
process-global [`ComputeTaskPool`]**, regardless of whether the `parallel` cargo feature is enabled
(that feature gates parry, not Bevy's parallel query iterator).

Consequences:

- **A single engine App is deterministic.** Running the same inputs twice through one engine gives
  identical state (Bevy's fixed-step schedule is stable on one thread).
- **Two co-existing engine Apps in ONE process are NOT deterministic.** Their physics interleave on
  the shared compute pool → nondeterministic float accumulation → divergent state hashes, no matter
  how correctly the lockstep is driven.
- **Separate processes ARE deterministic.** Each process has its own compute pool and its own single
  engine, so two processes replaying the same inputs converge bit-identically.

### Fixes that do NOT work for in-process multi-engine determinism

```text
AVOID  Pinning ComputeTaskPool (and AsyncCompute/Io pools) to 1 thread
       → deadlocks avian's TaskPool::scope.

AVOID  Serializing engine .step() calls behind a process-wide Mutex
       → each engine still runs on its own thread with its own pool view; results still diverge.
```

### The correct model for deterministic lockstep

- **One engine per OS process.** This is what powers cross-process / mainnet determinism.
- Validate determinism **cross-process** (spawn a real game subprocess, or run real peers on the
  network), never by putting two engines in the same test process.
- For reproducible single-process checks, use an isolated single-engine trace (a
  {{module}} that steps one `Engine` and hashes each tick), which is deterministic.

Full write-up of the original investigation: `found_problems/compile-taskpool-nondeterminism.md`

## 2. Plugin setup

```rust
app.add_plugins((
    MinimalPlugins,
    bevy::transform::TransformPlugin,
    PhysicsPlugins::default(),
));
```

- Enable the `enhanced-determinism` cargo feature for cross-platform `libm` math when determinism
  matters (with `parry*-f32`). It does **not** by itself make multi-engine-in-one-process
  deterministic — it only stabilizes the arithmetic.
- Avian already sets its internal `PhysicsSchedule` to a `SingleThreadedExecutor`; the main Bevy
  schedule is single-threaded by default in recent Bevy. That is orthogonal to the `par_iter_mut`
  pool issue above.

## 3. Fixed timestep

- Force a fixed step with `TimeUpdateStrategy::ManualDuration(1 / {{ticks_per_second}})`.
- Prefer a **power-of-two** tick rate (`64`, `128`) rather than `60`: `1/60` is inexact in binary,
  and Bevy/Avian's sub-step accumulator can round over the residue and occasionally skip/double a
  physics step. A binary-exact step avoids that accumulation drift.

## 4. Rollback sessions

- Use one engine per session; the snapshot/restore model is the same as above — `step`, snapshot,
  restore must all be deterministic, so keep one session per process.

## 5. Footguns

- Two engines in one process (e.g. in-process "two-node" tests) is fundamentally non-deterministic —
  see §1; test cross-process instead.
- Changeable tick rate changes physics only via per-second quantities (velocities, gravity) staying
  frame-rate independent — keep speeds/gravity authored per-second, not per-tick.

## Sources

| Topic | URL |
|-------|-----|
| API docs (Avian2D 0.3+) | `https://docs.rs/avian2d` |
| Book / user guide | `https://docs.rs/avian2d/latest/avian2d/#documentation` |
| Repository / releases | `https://github.com/avianphysics/avian` |
| Discussions (determinism Q&A) | `https://github.com/avianphysics/avian/discussions` |

- `found_problems/` — problem reports and their root causes

{{project}}: a Rust/Bevy project using Avian. {{crate}}: the physics crate. {{module}}: the module
that builds/steps the engine.