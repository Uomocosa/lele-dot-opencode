# Allow-list / root auth

**Where from:** Atlas `IndexParams { root_verifying_key, limits, epoch }` + `RootAuthorization`; Website `Parameters = [u8; 32]` verifying key; Raven owner `VerifyingKey` in `Parameters`.

**Description:** `Parameters` pinned in `ContractKey = Blake3(WASM || params)` declares who may write. Every `update_state` verifies `incoming` signature against a key in the allow-list / `RootAuthorization` / owner key before `max`/`union`. Changing the set forks the key (flag day).

**Memory cost:** `O(allow-list)` in `Parameters` (replicated via key), `O(1)` per verify (ed25519).

**Speed:** `O(1)` sig verify per entry (`ed25519 64B`).

**Pros:** Client forgery on same key becomes detectable — honest peers drop unsigned inflated values. Forked WASM already isolated via key.

**Cons:** Key rotation forks `ContractKey`; WASM size `+30-100K` for `ed25519-dalek`; loss of key = loss of right to increment.

**When to use:** Same-key client forgery must be blocked and you can manage keys. Otherwise accept **Choose-2** tradeoff.

**Vulnerability:** Private key leak → full impersonation; allow-list public — privacy leaks participants. Mitigate per-shard keys.

**Example:**
```rust
// pseudocode — Atlas-style root delegation
let allow: BTreeSet<VerifyingKey> = deserialize(params);
if !allow.is_empty() && !allow.contains(&signer) { continue; }
if !verify(&signer, &payload, sig) { continue; } // Atlas RootAuthorization, Website version+payload
```

**Mapping:** Skill `§6`.

---
