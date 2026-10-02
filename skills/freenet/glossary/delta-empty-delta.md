# Delta / empty delta

**Where from:** `references/DELTA_CONTRACT_STRUCTURE.md:44` empty-delta invariant, Ping `delta_against`.

**Description:** What a holder sends a lagging peer (`get_state_delta`). Must be **non-empty when behind**, **empty `vec![]` when converged** (not CBOR placeholder). Convergence check is `is_empty()` (`#5072`). Tombstones excluded from summary so delta not re-sent. Fallback: bad summary → whole-state delta.

**Memory cost:** Delta `O(lag)` per lagging peer; whole-state fallback `O(state)` when peer far behind.

**Speed:** `O(n)` diff.

**Pros:** Only lagging entries sent; idempotent via same merge as `State`.

**Cons:** Placeholder non-empty delta breaks `self_delta_empty` invariant — every heartbeat looks “behind”.

**When to use:** Always implement per-key diff; whole-state fallback is correct default.

**Vulnerability:** Returning whole state on every call when summary mismatched due to version drift → bandwidth blow-up; mitigate per-key diff.

**Example:**
```rust
fn delta(ours: &State, theirs: &Summary) -> StateDelta {
    if ours == theirs { return StateDelta(vec![]); }
    let missing = theirs.diff(ours); // S \ R
    if missing.is_empty() { StateDelta(vec![]) } else { StateDelta(cbor(&missing)) }
}
```

**Mapping:** Skill `§3`, Delta docs.

---
