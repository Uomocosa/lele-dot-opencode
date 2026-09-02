# Delta — Contract Structure Reference

Source: `freenet/delta` @ `HEAD f0257f2c` (2026-08-30) — **no tag; main branch head**, WIP delta month cadence (#83)
Path: `contracts/site-contract/src/lib.rs`, `common/src/{lib.rs,state.rs}`
Crate: `site-contract` (contract) + `delta-core` (pure Rust, `#[composable]`-like manual)
Serialization: CBOR (`ciborium`) for state/summary/delta and `SiteParameters`
Parameters: `SiteParameters { prefix: String }` — 10-char base58 prefix of owner's `VerifyingKey` (`pubkey_to_prefix = bs58(owner)[..10]`). Contract key = `Blake3(code_hash || prefix_bytes)`. Anyone knowing the 10-char prefix can reconstruct the contract key.
Build: `cargo build -p site-contract --target wasm32-unknown-unknown --features freenet-main-contract`

## State shape

`SiteState` (`common/src/state.rs:30`):

```rust
pub struct SiteState {
    pub owner: VerifyingKey,                          // pinned at creation; placeholder zero-key when default
    pub config: SignedConfig,                         // site name etc., owner-signed, versioned
    pub pages: BTreeMap<PageId, Page>,                // PageId = u64 monotonic (next_page_id)
    pub next_page_id: PageId,                         // never reused, only increases
    pub deleted_pages: BTreeMap<PageId, SignedPageDeletion>, // tombstones — prevents re-add on merge
}
impl Default for SiteState { owner: placeholder_owner (zero-key), next_page_id: 1 }
```

`Page { id, title, content, version: u64, signature, ... }`, `SignedPageDeletion { page_id, tombstone_version, signature }`, `SiteParameters { prefix }`. `BTreeMap` for canonical encoding (same reason as Ping).

## Four functions

### validate_state (`contracts/site-contract/src/lib.rs:12`)
- Empty → `Valid`. Otherwise `ciborium::from_reader::<SiteState>` + `from_reader::<SiteParameters>` → `site_state.verify(&params)` (checks `params.matches_owner(&state.owner)` prefix + signature validity per page/config) → `Valid` else `InvalidUpdateWithInfo`.

### update_state (`src/lib.rs:35`)
- Empty state → `SiteState::default()`. Folds each `UpdateData`:
  - `State(bytes)` → `SiteState` + `site_state.merge(&params, &other)` — verifies `other`'s signatures then per-field join
  - `Delta(bytes)` → skip if empty (`continue`) else `SiteStateDelta` + `site_state.apply_delta(&delta, &params)`
  - `_ => {}` (ignores Related)
- CBOR serialize → `UpdateModification::valid`. **Idempotent**: `merge` is max-union per page/tombstone.

### summarize_state (`src/lib.rs:81`)
- Empty → default `SiteStateSummary` CBOR. Otherwise `site_state.summarize()` (`common/src/state.rs:summarize`) → CBOR `StateSummary`. Summary is **structural** (per-page version digests), not scalar version — tombstones are *excluded* from summary (so `summarize` never reflects `deleted_pages`).

### get_state_delta (`src/lib.rs:100`)
- Empty state → `delta_core::SiteState` default fallback, then `compute_delta(&peer_summary)`. Deserializes `peer_summary: SiteStateSummary`. `site_state.compute_delta(&peer_summary)` returns `Option<SiteStateDelta>`.
- **Empty-delta invariant**: `None` → `StateDelta(vec![])` (0 bytes), NOT CBOR placeholder (~39 bytes of field names). `Some(d) → CBOR(d)`. Commentary at `:117-123`: convergence check tests `is_empty()`, so placeholder would break it. Tests pin `self_delta_empty` (`self_delta_against_own_summary_is_empty`, `self_delta_is_empty_for_a_state_that_has_deleted_pages`) and deletion healing (`get_state_delta_carries_a_pending_deletion_and_heals_a_stale_peer`).

## Merge laws

`SiteState::merge(&params, &other)` and `apply_delta` — per-page LWW by `version` (monotonic `u64` per page), tombstone set is grow-only union by `SignedPageDeletion.version`. `next_page_id = max(self, other)`. `owner`/`config` are LWW by signature+version. Commutative/associative/idempotent. Deletion is **recorded negative fact** — `deleted_pages` entry is tombstone, not expiry; re-adding a deleted `PageId` is rejected during merge (retry would violate §7 tombstone rule noted in Ping docs: "expiring a tombstone resurrects").

## Tombstone subtlety

`compute_delta` must NOT re-emit tombstones whose `PageId` the peer no longer has listed in `pages`. Summary excludes `deleted_pages`, so a converged site with a tombstone diffs empty (`summary.pages.contains_key(id)` filter). Without that filter, every heartbeat would re-send whole tombstone set forever. Test `self_delta_is_empty_for_a_state_that_has_deleted_pages` catches it; `compute_delta` comment explains.

## Scaling

State = O(pages + tombstones + config). `pages` bounded by site author (owner-writes only — single writer per site), tombstones grow O(deletions) forever (never expired — would resurrect). Delta sends only pages/deltas/tombstones the peer lacks (per-page versioned diff), not whole site. Single-writer so no G-counter needed; concurrent edits via merge + version LWW.

## Trust

- Single-owner: all writes require `VerifyingKey == owner` + valid `Signature`. Client forgery without owner's `SigningKey` is rejected in `verify`. Contract key prefix pins owner identity — forging prefix requires owning the exact VK that hashes to that 10-char prefix (brute-force vanity-ID via `TDiffff/freenet-vanity-id` exists but only grinds prefix, not full key).
- WASM rebuild → new `ContractKey` (same as website) — would orphan existing sites.

## Mapping to freenet-contract-design

- §0 pure reducer, §2 idempotent (per-page `max(version)`), §3 structural summary + non-empty delta only when behind; empty delta when converged (teaches #5072 `self_delta_empty` backstop).
- §7 tombstone safety: expiry of deletion marker is unsafe (Delta gets it right — tombstone persists).
- Contrast with River: Delta is single-writer LWW-per-page, River is multi-writer signed-set per member/message.

## References

- `contracts/site-contract/src/lib.rs:1-356`, `common/src/state.rs:1-~500` (state, merge, delta, summarize)
- `common/src/lib.rs`, `common/Cargo.toml`
- This reference pinned to HEAD `f0257f2c` — not a tag; Delta has no published tags/releasing cadence (see `RELEASING.md` when added)
