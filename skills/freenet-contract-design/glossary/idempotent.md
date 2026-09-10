# Idempotent (max/union, never +1)

**Where from:** `SKILL.md §2`, `§0` pure reducer.

**Description:** `apply(state, data) == apply(apply(state,data), data)` and `apply(a, b) == apply(b, a)`. Achieved by `max`/`union` from `data`, never `state + 1`. Update must carry its **monotonic value** so replay is no-op. Duplicate delivery and reordering are normal.

**Memory cost:** `O(1)` extra (store value).

**Speed:** `O(1)` per key.

**Pros:** Stateless contract tolerates re-delivery; no history.

**Cons:** The carried monotonic value is what attacker inflates — idempotent is necessary but not sufficient for anti-cheat.

**When to use:** Every contract. If you need `+1` semantics, carry `value = cur+1` in update, don’t increment from state.

**Vulnerability:** `state+1` double-counts on replay — canonical freenet bug. Test `update_reads_data_not_state_plus1`.

**Example:**
```rust
// correct
let cur = state.get(&k).copied().unwrap_or(0);
if value > cur { state.insert(k, value.max(cur)); }
// broken
state.insert(k, cur + 1);
```

**Mapping:** Skill `§0`, `§2`.

---
