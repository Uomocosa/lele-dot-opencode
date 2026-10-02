# Tombstone

**Where from:** `references/DELTA_CONTRACT_STRUCTURE.md:21` `deleted_pages: BTreeMap<PageId, SignedPageDeletion>`; Ping `retain(|_,v| !v.is_empty())`.

**Description:** A **recorded negative fact**: “page `42` was deleted at `version 7` by owner”. Stored in a grow-only set/map, never expired. Deletion is not “remove key” but “add tombstone”. Merge keeps `max(version)` per tombstone and drops the live entry.

**Memory cost:** `O(deletions)` forever. Never pruned, else a peer that never saw the deletion re-adds the live entry and merge resurrects it. Replication × peers.

**Speed:** Merge `O(log n)` insert into `BTreeMap`; delta filter `O(tombstones)` per peer.

**Pros:** Makes delete commutative/idempotent; concurrent add+delete resolves deterministically (tombstone wins).

**Cons:** Unbounded growth in tombstone set; summary/delta must handle it. Summary **excludes** tombstones (Delta `compute_delta` filters `!pages.contains_key`) else every heartbeat re-sends whole tombstone set. Fallback whole-state delta still carries them.

**When to use:** Any delete that must survive partitions. Avoid if you can use TTL/window expiry instead of explicit delete.

**Vulnerability:** Resurrection if tombstone pruned; blow-up if many deletes. Mitigation: epoch rotation — fork `ContractKey` with new empty tombstone set and migrate live entries; or never prune.

**Example:**
```rust
struct SiteState { pages: BTreeMap<PageId, Page>, deleted: BTreeMap<PageId, Deletion> }
fn merge(a: SiteState, b: SiteState) -> SiteState {
    let deleted = max_union(a.deleted, b.deleted); // grow-only
    let pages = max_union(a.pages, b.pages).into_iter()
        .filter(|(id,_)| !deleted.contains_key(id)).collect();
    SiteState{ pages, deleted }
}
```

**Mapping:** Delta docs tombstone safety, skill `§2` idempotent.

---
