# CRDT / G-counter

**Where from:** `SKILL.md §4`, `references/reconciliation-and-scaling.md:89`.

**Description:** State = `map<key, count>` (or `map<subject, version>` for Atlas), merge = element-wise `max` (or `union` for sets), total = `sum(values)` or per-key LWW. Commutative+associative+idempotent. Replay of same `{key: V}` is no-op. Concurrent writers to different keys both survive (`N+M` not `N-overwrites-M`). Never evict a key if exact per-key retention is required.

**Memory cost:** `O(keys)` — one `version`/`count` (`u32`/`u64` + key bytes) per distinct key. Replication multiplies by peer count. `O(1)` per key's further updates (value widens in place, no new entry) — contrast `O(actions)` for per-action logs.

**Speed:** `O(n)` merge per delta, `O(n)` summary/delta.

**Pros:** Convergent shared aggregate; exact per-key retention; simple — the canonical CRDT for “how many / who has what”.

**Cons:** `Ω(N)` information bound — cannot keep exact per-key figure cheaper than one slot per key. Must shard or window to scale.

**When to use:** Shared total or per-subject registry where `N` fits in state (Atlas subjects, River members). For `O(S)` bounded total see **Sharding**, for churn see **Window / cap**.

**Vulnerability:** Client inflates own `count` — `max` accepts any monotonic value. Mitigated by `window` bound (`value ≤ cur + 1`) + `allow-list` + signature (Atlas root auth, River signed ops), but `+1` spam remains.

**Example:**
```rust
// pseudocode — generic G-counter / Atlas-like per-subject version
type State = BTreeMap<Key, u64>;
fn merge(mut a: State, b: State) -> State {
    for (k, v) in b {
        let cur = a.get(&k).copied().unwrap_or(0);
        a.insert(k, cur.max(v));
    }
    a
}
```

**Mapping:** Skill `§4`, `§5` Ω(N).

---
