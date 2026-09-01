# Found problem: two Avian engine Apps in one process cannot be deterministic

**Status:** investigated, root-caused, and concluded. Not a bug in the app — it is an inherent
Avian/Bevy behavior. Write-up preserved so the same time is not spent twice.

## Symptom

A test that ran **two engine `App`s in a single OS process** (each simulating the same world from
the same per-tick input) asserted identical state hashes but consistently diverged.

- Posts showed **byte-identical step sequences**: both engines stepped exactly ticks 1..N, in the
  same order, with the same ordered inputs — yet their positions/hashes differed.
- The divergence was **uniaxial** at first (only the vertical/gravity axis differed while horizontal
  stayed equal), and once established it was a **fixed one-substep offset** between the two engines.

## Root cause

Avian's integrator runs

```rust
bodies.par_iter_mut() // Query::par_iter_mut over the physics bodies
```

which iterates in parallel over Bevy's **process-global `ComputeTaskPool`**
(`ComputeTaskPool::get()`), NOT a per-app pool.

- A **single engine alone** is deterministic: the fixed-step schedule is stable and the pool's work
  executes in a reproducible order.
- When **two engine apps co-exist in one process** (each on its own worker thread), their
  `par_iter_mut` work **interleaves on the same shared pool threads**, so float reduction order
  varies → nondeterministic results → divergent hashes.
- The Avian `parallel` cargo feature does not help here — it only gates parry2d; Bevy's
  `Query::par_iter_mut` parallelizes regardless.
- Two **separate OS processes** each have their own pool + single engine → deterministic and
  bit-identical for identical inputs. This is the production / mainnet model.

## Approaches that failed (do not retry)

| Attempt | Result |
|---|---|
| Pin `ComputeTaskPool` (and `AsyncComputeTaskPool`/`IoTaskPool`) to 1 thread so `par_iter` serializes | **Deadlocks** Avian's `TaskPool::scope` on 1 thread. |
| Serialize each engine's `app.update()` behind a process-wide `Mutex` | No deadlock, **no effect** — each engine still runs on its own thread with its own view of the shared pool; results still diverge. |

## Conclusion / correct guidance

- **Deterministic Avian physics requires ONE engine per OS process.**
- Validate determinism **cross-process**: spawn a real game subprocess (or real peers on the
  network) and compare state hashes across the wire, or assert a single-engine trace is reproducible.
- Do not write "two-node" tests that put two `App` instances in one process and expect identical
  hashes; that is unrepresentative of any real deployment and will be flaky regardless of code.