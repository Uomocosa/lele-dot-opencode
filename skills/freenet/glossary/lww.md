# LWW (last-writer-wins)

**Where from:** `references/WEBSITE_CONTRACT_STRUCTURE.md:30` `version u32` LWW; Atlas `Record.version`; Raven `seq` LWW.

**Description:** Per-key resolve by higher `version` / `seq` wins. Deterministic, commutative, idempotent. Tie-break by serialized bytes when version equal so `merge(a,b)==merge(b,a)`.

**Memory cost:** `O(keys)` — one versioned value per key, constant width `u32/u64`. No history.

**Speed:** `O(1)` per key `max`.

**Pros:** Minimal, simple, no vector clocks; works for single-owner or per-key owner surfaces.

**Cons:** Concurrent writes at same version — one lost (higher bytes wins). Not suitable for multi-writer additive counters (use G-counter).

**When to use:** Single-writer blobs (Website), per-member `seq` (River), per-page `version` (Delta), Atlas per-subject `version`.

**Vulnerability:** Client forges higher `version` to overwrite — mitigated by signature on `version+payload` with owner key in `Parameters`.

**Example:**
```rust
if incoming.version > cur.version { cur = incoming; }
else if incoming.version == cur.version && incoming.bytes > cur.bytes { cur = incoming; }
```

**Mapping:** Skill `§2` max pattern, Website/Atlas.

---
