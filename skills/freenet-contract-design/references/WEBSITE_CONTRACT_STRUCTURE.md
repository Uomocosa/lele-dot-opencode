# Website — Contract Structure Reference

Source: `freenet/freenet-core` @ `v0.2.132` (`0ca7e02b`)
Path: `crates/website-contract/src/lib.rs` (also published as committed `crates/fdev/resources/website_contract.wasm`)
Crate: `freenet-website-contract` — used by `fdev website publish/list` (`cargo install --path crates/fdev`)
Serialization: CBOR (`ciborium`) for metadata; state is length-prefixed binary (`u64 BE`) not CBOR map
Parameters: `Parameters = [u8; 32]` raw Ed25519 verifying key bytes (not CBOR)
Build: `cargo build -p freenet-website-contract --target wasm32-unknown-unknown --release --no-default-features --features freenet-main-contract,contract && cp target/.../freenet_website_contract.wasm crates/fdev/resources/website_contract.wasm` — committed WASM embedded via `include_bytes!` in `fdev`

## State shape

Wire format (`src/lib.rs:83-84`, doc at `crates/website-contract/README.md`):

```
[u64 BE metadata_len][CBOR WebContainerMetadata][u64 BE web_len][web: tar.xz bytes]
```

```rust
pub struct WebContainerMetadata { pub version: u32, pub signature: Signature } // CBOR
const MAX_METADATA_SIZE: u64 = 1024;
const MAX_WEB_SIZE: u64 = 100 * 1024 * 1024; // sanity ceiling; binding limits are 50 MiB MAX_STATE_SIZE + 64 MiB transport cap
```

`version` is the monotonic LWW key; `signature = Ed25519_sign(SigningKey, version.to_be_bytes() || web_bytes)` (message = BE version bytes + raw archive).

## Four functions

### validate_state (`src/lib.rs:58`)
- Checks `Parameters.len()==32` → `VerifyingKey::from_bytes`. Reads `metadata_len` (BigEndian, `>MAX_METADATA_SIZE` → error), CBOR `WebContainerMetadata`, rejects `version==0 → InvalidState`, reads `web_len` (`>MAX_WEB_SIZE` → error), reads `web_bytes`, verifies `verifying_key.verify_strict(version_be || web_bytes, signature)` → `Valid` else `Other("Signature verification failed")`.

### update_state (`src/lib.rs:169`)
- Parses `current_version = parse_version(state)` (0 if empty). Takes `data.into_iter().next()` only (single update; empty vec → `InvalidUpdate`). Parses `new_version` from `State(new_state)`. Checks `new_version > current_version` else `InvalidUpdateWithInfo { reason: "must be higher" }`. Delta input → `InvalidUpdate`. Returns `valid(new_state)` (replaces, no merge — LWW). **Idempotent** only because version is monotonic and checked: replay of same version is rejected, higher version already held means incoming is not newer.

### summarize_state (`src/lib.rs:213`)
- Empty → `StateSummary(vec![])`. Otherwise `parse_version` → CBOR `u32` → `StateSummary`. **Scalar summary** (single `u32`).

### get_state_delta (`src/lib.rs:228`)
- Empty state → empty delta. Otherwise `current_version = parse_version(state)`, `summary_version = ciborium::from_reader::<u32>(summary)`; if `current_version > summary_version` → `StateDelta(state.to_vec())` (whole state), else empty delta. No per-key diff — whole-state-or-nothing.

## Merge laws

Not a CRDT set/union — single-writer LWW register keyed by `version`. Commutative/idempotent only under single-writer assumption: concurrent writers at same `version` — higher version wins deterministically if one is larger; equal versions are rejected, so second writer's state with same version never replaces. Multi-writer concurrent `version+1` from two different contents — last writer to be merged wins (by `UpdateData::State` iteration order, first `data[0]` only). This is last-writer-wins, not convergent multi-writer.

## Scaling

State = O(web archive size) (tar.xz). No per-user/per-click state — single versioned blob. Delta is whole state when behind (cost = full site on every lagging peer), empty when converged. Efficient because sites update infrequently; not suitable for high-frequency multi-writer.

## Trust & key management

- `ContractKey = Blake3(code_hash || verifying_key_bytes)`. `fdev website init <name>` generates `~/.config/freenet/website-keys/<name>.toml` with Ed25519 keypair; `published-contract` is not needed — key is derived locally.
- Only holder of `SigningKey` can produce valid `signature` over `version || web`; any peer can verify via `Parameters` (VerifyingKey). Signature binds version+content — tampering fails `validate_state`.
- **WASM pinning**: changing `MAX_METADATA_SIZE`/`MAX_WEB_SIZE` or any code rehashes `website_contract.wasm` → new `ContractKey` for every site. Must rebuild committed `crates/fdev/resources/website_contract.wasm` and ship `fdev` update; existing sites keep old key unless user passes `--contract-wasm` legacy WASM. Warning at `src/lib.rs:19-23`.

## Mapping to freenet-contract-design

- §0 pure reducer: validates signature, version monotonic — no hidden state.
- §1 reconcile wall: would be LWW scalar if used for multi-writer; as single-writer LWW it is correct but teaches the cost of scalar+whole-state-delta (no incremental sync). Contrast with River's per-field delta.
- §3 wiring: scalar summary (`u32`) suffices because LWW version fully orders states; `get_state_delta` whole-state is intentional, not a degenerate scalar total.
- §6 key splits: contract key pins code (verification rule), parameters pin owner identity (who may sign). Client forgery without signing key is rejected; re-publishing requires owner key.

## References

- `crates/website-contract/src/lib.rs:1-459`, `crates/website-contract/README.md`
- `crates/website-contract/Cargo.toml`, `crates/fdev/resources/website_contract.wasm` (committed)
- `freenet.org/build/manual/publish-a-website` (format doc)
