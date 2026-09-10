# Structural summary (per-tag vs scalar)

**Where from:** `SKILL.md §3` 0.2.101 nuance, `references/ATLAS_CONTRACT_STRUCTURE.md:47` `IndexSummary`, `RIVER_CONTRACT_STRUCTURE.md:43`.

**Description:** Summary is `map<key, version>` (`BTreeMap`) not scalar `total`. Byte-equality anti-entropy (`node.rs:2698`) would miss compensating divergence `{a:8}` vs `{a:4,b:4}` both total `8` with scalar summary. Structural catches it. Keeps delta path efficient.

**Memory cost:** `O(keys)` summary size, but small per key (`u64` version). Scalar `4-8B` vs structural `~keys×40B`. Summary `× peers` stored as interest.

**Speed:** `O(n)` serialize; delta per-key diff `O(n)`.

**Pros:** Detects divergence that scalar masks; enables per-key delta (only lagging keys).

**Cons:** Larger than scalar; still `O(keys)`.

**When to use:** Always for map/collection state unless scalar fully orders state (Website `version u32` LWW).

**Vulnerability:** `HashMap` iteration order non-canonical → different byte encodings for same logical state → spurious mismatch. Use `BTreeMap` + canonical `ciborium`/`bincode`.

**Example:**
```rust
fn summarize(state: &SiteState) -> StateSummary {
    let s: BTreeMap<PageId, u64> = state.pages.iter().map(|(id,p)|( *id, p.version)).collect();
    StateSummary(cbor(&s))
}
```

**Mapping:** Skill `§3`.

---
