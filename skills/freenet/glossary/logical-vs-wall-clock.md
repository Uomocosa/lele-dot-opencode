# Logical clock vs wall clock

**Where from:** `references/PING_CONTRACT_STRUCTURE.md:48-49`, `types/src/lib.rs:146-191`, skill `§0`.

**Description:** **Logical:** `reference = max(values in union)` derived from state itself. **Wall:** `Utc::now()` read during `merge`. Wall makes `merge(A,B)` at `T1` differ from same `merge(A,B)` at `T2` when TTL boundary crossed — breaks commutativity. Rule: read clock at **write** (insert) to stamp data; **never** at merge. Merge is pure function of inputs.

**Memory cost:** None.

**Speed:** `O(n)` max scan.

**Pros:** Deterministic, convergent across time and nodes.

**Cons:** Logical TTL pinning (see TTL).

**When to use:** Any TTL/window merge. Stamp `now` into `UpdateData` at client `tick`, let merge use `reference`.

**Vulnerability:** Wall in merge → divergent replicas even with identical updates.

**Example:**
```rust
// write
let ts = Utc::now(); update = Ping{ from: {me: vec![ts]} };
// merge — no clock
let reference = union.values().flatten().max().unwrap();
```

**Mapping:** Skill `§0`, Ping docs.

---
