# TTL (time to live)

**Where from:** `references/PING_CONTRACT_STRUCTURE.md:48` — `Ping::merge` `reference = max(values in union)` + `retain_history`; skill `§5`.

**Description:** How long a piece of state is allowed to live without being refreshed. After TTL the entry is evicted/aged out. In pure contracts TTL **must not** use wall clock (`Utc::now()` inside `merge`) because two nodes merging the same states at different real times would compute different `reference` and diverge. Instead TTL uses a **logical clock**: `reference = max(values in union)` (the newest timestamp already in the data). TTL then means `value older than reference - TTL`.

**Memory cost:** `O(active)` bounded. Ping keeps `max(10, in-window)` per peer: ~ `peers × (10 + write_rate × TTL)` live, frozen state stops ageing. Without TTL: `O(peers × history)` unbounded.

**Speed:** Merge prune `O(n log n)` sort + dedup + retain; summarize/delta `O(n)`. One extra `max` scan per merge.

**Pros:** Bounds growth deterministically; keeps merge pure and commutative across TTL boundaries.

**Cons:** Unauthenticated future timestamp can pin `reference` a year ahead and truncate every peer's history to 10. Needs `validate_state` to reject implausible timestamps.

**When to use:** High-churn per-key history where you want “recent window” not hard cap (chat, ping, presence). Use hard **Window / cap** when you need absolute bound.

**Vulnerability:** Future-dated write pins logical clock — mitigated by `validate_state: if timestamp > reference + max_skew { Err }` (read clock at write/validate, not merge).

**Example:**
```rust
fn merge(a: Ping, b: Ping, ttl: Duration) -> Ping {
    let mut u = union(a, b);
    let reference = u.values().flatten().max().copied().unwrap_or(now_at_write);
    u.retain(|_, vs| {
        vs.sort(); vs.dedup();
        vs.into_iter().rev().take(10).chain(vs.into_iter().filter(|t| *t + ttl >= reference)).collect()
    });
    u
}
```

**Mapping:** Skill `§5` scaling, `§0` pure reducer.

---
