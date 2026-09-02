# Atlas — Contract Structure Reference

Source: `freenet/atlas` @ `HEAD 25582555` (2026-08-30) — **no tag; main branch head**, WIP
Path: `contracts/index-contract/src/lib.rs`, `common/src/*`, `contracts/web-container/`
Crate: `atlas-index-contract` + `atlas-common`
Serialization: CBOR (`ciborium`); `Parameters = IndexParams` (root key + limits)
Parameters: `IndexParams { root_verifying_key: VerifyingKey, limits, epoch }` — root key authorizes which online signing keys may write; determines contract key via `Blake3(code_hash || params_bytes)`
Build: `cargo build -p atlas-index-contract --target wasm32-unknown-unknown --features freenet-main-contract`

> **Status WIP** — Atlas is under active development / design proposal stage (`PROPOSAL.md`). No published tags; expect API churn. This reference is best-effort at HEAD.

## State shape

`IndexState` (`common/src/: IndexState`):

```rust
pub struct IndexState {
    pub root_auth: RootAuthorization,              // root-signed delegation of online signing keys
    pub records: BTreeMap<SubjectId, Record>,      // one current record per subject (e.g. site/app id)
}
pub struct Record {
    pub subject: SubjectId,
    pub version: u64,                             // monotonic, per-subject
    pub payload: Vec<u8>,                          // indexed content (URL, metadata, ranking hints)
    pub signature: Signature,                      // by authorized online key
}
pub struct RootAuthorization {
    pub root_signature: Signature,                 // root_key signs authorized online VKs
    pub online_keys: Vec<VerifyingKey>,
}
```

Ranking/search is client-side; contract enforces only **signatures, authorization, structure, bounds, versioned merge**.

## Four functions

### validate_state (`contracts/index-contract/src/lib.rs:validate_state`)
- Empty → `Valid` (not-yet-initialized). Otherwise `from_reader::<IndexState>` + `parse_params` → `st.verify(&params)` (checks `root_auth.root_signature` over `online_keys` by `root VK`, each `Record.signature` by an `online_keys` entry, `version` monotonic, bounds on `payload` size / `records` count).

### update_state (`src/lib.rs:update_state`)
- Empty → `IndexState::default()`. Folds each `UpdateData`:
  - `State(bytes)` → `IndexState` + `incoming.verify(&params)?` (untrusted — verify before merge) + `st.merge(&incoming)` (per-subject LWW by `version`)
  - `Delta(bytes)` → skip if empty else `IndexDelta` + `st.apply_delta(&delta, &params)` (verifies delta signatures)
  - `StateAndDelta{state, delta}` → both paths
- CBOR serialize → `UpdateModification::valid`.

### summarize_state
- `st.summarize()` → CBOR `IndexSummary` — structural map of `SubjectId → version` (per-subject version vector), not scalar count.

### get_state_delta
- `st.compute_delta(&peer_summary)` → `Option<IndexDelta>` = records where `our_version > peer_version` per `SubjectId`. `None` → empty `StateDelta`, else CBOR `IndexDelta`. Per-key diff, not whole index.

## Merge laws

Per-subject LWW by `version` (monotonic `u64`). `root_auth` is LWW by root signature freshness (higher authorized set version). Commutative/associative/idempotent. `records` map union; concurrent writes to different subjects both survive; same subject — higher `version` wins (tie-break by serialized bytes). No clock read.

## Scaling

State = O(subjects) — one record per subject (e.g. site), not per click. High-churn ranking is client-side, contract stores only current record per subject (durable discovery). Durable + low-churn complements Raven's high-churn feed. Delta sends only lagging subjects (peer missing `version 5` for `SubjectId X` but holds `4` → that one record). Sharding not yet applied — single index contract; future may shard by subject prefix if `records` grows.

## Trust

- Root key (`IndexParams.root`) is trust anchor — only holders of root `SigningKey` can authorize online keys (`RootAuthorization`). Readers verify offline (contract enforces `verify`). Forking contract → new key (isolated index). Client without root key cannot forge valid `Record`.
- Anti-Sybil not in contract — Atlas is durable index, Sybil resistance is via `Ghost Keys`/donation minting at higher layer (same as Raven).
- WASM bytes pin merge/bounds logic.

## Mapping to freenet-contract-design

- §0 pure reducer, §2 idempotent (`max(version)`), §3 structural summary (per-subject versions) avoids scalar-total masking (compensating divergence: two peers could hold 100 subjects at different versions but same count).
- §5 O(subjects) not O(clicks) — durable discovery vs Raven's live feed tradeoff is exactly §7 "which contract do you need?" decision.
- §6 root-signed authorization is the external evidence that closes client-forgery gap (trusted signer pattern).

## References

- `contracts/index-contract/src/lib.rs`, `common/src/index_state.rs` (verify/merge/delta), `PROPOSAL.md`, `FREENET.md`
- `contracts/web-container/` (site hosting alongside index)
- Pinned to HEAD `25582555` (2026-08-30) — no tag
