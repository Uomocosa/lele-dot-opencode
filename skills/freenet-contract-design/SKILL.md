---
name: freenet-contract-design
description: Use when designing a Freenet contract's state, update, summary and delta so it reconciles reliably between peers, scales to many users x clicks, and reasons about trust/anti-cheat. Covers the delta-merge wall, idempotent commutative (CRDT) merge, per-tag vs scalar summaries (0.2.101 byte-equality compare), the G-counter pattern, O(users) vs O(clicks) scaling, contract-key isolation vs client forgery, fresh-key concurrent-Put splits, and the scale/anti-cheat/reliability tradeoff. Works with any project that writes Freenet contracts.
---

# Freenet Contract Design

How to shape a Freenet contract so it actually reconciles, scales, and has a defensible
trust model. Focuses on the *design of the contract state and transition logic*, not on
building tooling (see the `freenet` skill for that) or node/ring wiring (see `freenet-gateway`).

## 0. The rule that all else follows from

A contract's `update_state(state, data)` is a **pure, stateless reducer**: it sees only the
current state and this batch of incoming updates, has no memory of its own history, and runs
deterministically on *every* node that hosts the contract. The node does **not** guarantee
exactly-once delivery of an update. So:

> **Your state transition must be idempotent and commutative (a CRDT merge).** Applying the
> same update twice must equal applying it once; reordering must not change the result.

Everything else in this skill is a consequence of that single fact.

## 1. The reconcile wall (symptom: "it never merges")

A state that is a single scalar and is **replaced** by each incoming update (last-writer-wins),
with an **empty delta** and a summary equal to the whole state, will not delta-merge between
peers: there is no per-key diff to send, and the small-state efficiency gate rejects the delta
path. Two replicas each accumulate their own writes and never see each other. When two such
replicas happen to read "equal," it is coincidental, not converged.

> **Design rule:** if your contract answers "how many / what is the aggregate" and you want peers
> to converge, you need a mergeable state and a real delta — not a single replaced scalar.

## 2. Idempotent merge

`update_state` must **merge `data` in**, reading the new value from the update payload — never
increment from the current `state`:

- Correct (idempotent): `new_value = max(current, Value(from data))`.
- Broken (non-idempotent): `new_value = current + 1`, ignoring `data`.

A bare `+1` trigger **double-counts** under duplicate re-delivery, because the contract cannot
tell a repeat from a fresh action. To be replay-safe, an update must **carry its monotonic value**
so that `max`-style merge is a no-op on a replay. This is the defining constraint: **idempotent
merge forces every update to carry a monotonic value**, and that same value is what a dishonest
client can inflate (see §5).

## 3. Wire the four functions for reconciliation

All four must agree on one state shape and one merge:

| Function | Role in reconciliation | Good shape |
|---|---|---|
| `validate_state` | Accept/reject a state you'll host | Deserialize the shape; reject garbage |
| `update_state` | Apply updates — **the merge** | Fold each `State`/`Delta` payload into current by max/union |
| `summarize_state` | Compact digest a peer compares | A small scalar (e.g. count, length) — keeps the delta-efficiency check true |
| `get_state_delta` | What you send a peer that's behind | **Non-empty**: whole state, or a real per-key diff |

A scalar summary over a map/collection state keeps `summary_size * 2 < state_size` true, so the
delta path is actually taken. An empty `get_state_delta` disables the path entirely.

> **Verified 0.2.101 nuance — prefer a per-tag (structural) summary.** The anti-entropy path
> compares summaries by **byte equality** (`node.rs:2698-2701`) and heals mismatches by pushing
> full state (`SyncStateToPeer`); we found **no size-efficiency gate** on that path. Two
> consequences:
> 1. A **per-tag map summary is strictly better** than a total: equal totals can mask compensating
>    divergence (e.g. `{a:8}` vs `{a:4,b:4}` — both total 8 but different states), which the
>    byte-compare would miss with a scalar summary but catches with a structural one.
> 2. `get_state_delta` should compare the peer's summary per-key and return **only the lagging
>    keys** (with a whole-state fallback when the summary doesn't deserialize). With scalar
>    summaries this is impossible — the delta degenerates to the whole state anyway.
> Keep the summary small regardless; the efficient-delta guidance above still matters for
> `update_state`-driven propagation.

## 4. The G-counter pattern (a mergeable, additive counter)

For "count how many total" that must reconcile **and** remember each participant offline:

- State = `map<participant_key, count>`, merge = element-wise `max`, total = Σ values.
- This is commutative/associative/idempotent → reconciles on any order.
- **Never evict a slot.** A participant going offline keeps their slot (and count) untouched;
  offline retention is free. Returned participants see their old count intact.
- Concurrent writers to *different* slots both survive the merge (N + M, not N-overwrites-M).

## 5. Scaling physics: users vs clicks

| What grows | Map<key,count> G-counter | Per-action log / set |
|---|---|---|
| More **participants** | O(participants) | O(participants) |
| More **actions per participant** | O(1) — the value widens internally, slot count unchanged | O(actions) — one element per action, unbounded |

- Store counts (a value can grow forever at fixed width); do not store an entry per action unless
  you genuinely need a log.
- Replication multiplies: state and every delta are copied to each interested peer, so per-action
  state and whole-state deltas both scale with the peer count.
- Per-participant retention is an information bound: retaining a distinct figure for N
  participants is inherently Ω(N); no data structure avoids it. At extreme scale you must move to
  aggregates (shards) and keep per-participant history out-of-band.

## 6. Trust & anti-cheat: the contract key splits two different attacks

The `ContractKey` is derived from the **contract code (wasm) + parameters**.

- **Forking the contract** (changing `update_state`) → different code → **different key** → a
  different, isolated game. Honest users sharing the canonical code+params are protected from
  modified-code peers; open-sourcing the contract does not weaken this (the key pins the exact
  code, and makes the enforced rules auditable).
- **Forking the client** (changing the caller, not the contract) → **same key, same honest
  contract**. A modified client can submit a valid-but-dishonest update (e.g. an inflated slot
  value) that the merge accepts. The key protects the game from *code* forks, not from *input*
  forgeries. The client is a separate layer and anyone can write their own against your contract.

Because merge must be idempotent and carry a monotonic value (§2), that value is always
client-reportable. Preventing self-inflation requires external evidence the client can't forge:
a trusted signer (centralization cost), hardware attestation, or proof-of-work (storage or
reliability cost). Timestamps/triggers don't help — they're client-minted monotonic values too.

### The choose-2-of-3 tradeoff

| Goal | Naive shape | Cost |
|---|---|---|
| **Scale** (many users × clicks, small state) | provenance-free G-counter | gives up anti-cheat (count is client-reported) |
| **Anti-cheat** (bounded self-inflation) | PoW or trusted signer | PoW: O(clicks) proof-state or fragile non-CRDT; signer: centralization |
| **Reliable CRDT merge** | idempotent, provenance-free merge | gives up anti-cheat |

You can generally hold two of these. Pick per requirement; don't try to build all three into a
fully-decentralized, low-state contract.

## 7. Which contract do you actually need?

- Need a **shared total** that converges → G-counter (map<key,count>, max-merge).
- Need a **deduped / union** of actions (bounded) → set/union contract.
- Need **per-action history** (audit log) → a per-key log/set; accept O(actions) state.
- Need **anti-cheat** → bring an unforgeable evidence source; know which of scale/reliability you
  give up.

## 8. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| "Never merges"; replicas show coincidentally-equal values | Scalars replaced last-writer-wins with empty/whole-state summary and empty delta. Move to a mergeable map + scalar summary + non-empty `get_state_delta`. |
| "Contract violates update_state idempotency / marked broken" | `update_state` increments from `state` instead of merging `data`. Read the new value from the update payload. |
| Count resets / clobbered | `Put` overwrote existing state. `Get`+subscribe first; `Put` only on `NotFound`. |
| Fresh-key concurrent `Put`s → 3-way split, each replica counts ~1×rate | Not a merge bug: the node-side relay chains terminated in different places (verified in 0.2.101 — "divergent state groups", `op_ctx_task.rs:2521-2527`). Fix at the app level: each client runs a routed `ContractRequest::Subscribe { key, summary }` every ~30s while it sees no foreign slots; heals in ~10-60s. A local Get re-check never bridges (answered locally). |
| Two writable replicas diverge | Update isn't mergeable, or deltas are empty/inefficient. Ensure commutative+idempotent merge and an efficient non-empty delta. |
| Merged replicas but totals differ by a few ticks | Sample skew: each client's last tick lands within (#instances−1) ticks. Use an absolute tolerance (`#instances + 3`), never a percentage. |
| Count inflated by client | That's the input-forgery gap (§6). Only an unforgeable source closes it if anti-cheat is required. |

## 9. Universal test suite — every contract must pass

Copy this suite into `contract/src/lib.rs:#[cfg(test)]` (pure unit, no node) plus one
network-mode integration. Parameterize with two generators the contract must supply:

* `gen_state() -> State` — any valid state (include `empty_state()` / default).
* `gen_update(&State) -> UpdateData` — a valid delta/state for that base.
* `decode(&State) -> YourState` for assertions; `params()` / `related()` helpers.

### A — Four-function wiring (reconcile wall: §1, §3)

```rust
#[test] fn validate_accepts_gen() {
    assert!(MyContract::validate_state(params(), gen_state(), related()).is_ok());
}
#[test] fn validate_rejects_garbage() {
    for bad in [b"" as &[u8], b"not-bincode", &[0xFF; 32]] {
        assert!(MyContract::validate_state(
            params(), State::from(bad.to_vec()), related()
        ).is_err());
    }
}
#[test] fn summarize_deterministic() {
    let s = gen_state();
    let a = MyContract::summarize_state(params(), s.clone()).unwrap();
    let b = MyContract::summarize_state(params(), s).unwrap();
    assert_eq!(a.as_ref(), b.as_ref());
}
#[test] fn summarize_detects_structural_divergence() {
    // G-counter nuance (§3): byte-equality anti-entropy. Equal totals with
    // different shape must have different summaries, else delta never fires.
    if let Some((a, b)) = gen_divergent_equal_total() {
        assert_ne!(
            MyContract::summarize_state(params(), a).unwrap().as_ref(),
            MyContract::summarize_state(params(), b).unwrap().as_ref()
        );
    }
}
#[test] fn delta_nonempty_and_roundtrips() {
    let base = gen_state();
    let ahead = apply(base.clone(), vec![gen_update(&base)]);
    let summary = MyContract::summarize_state(params(), base.clone()).unwrap();
    let delta = MyContract::get_state_delta(params(), ahead.clone(), summary).unwrap();
    assert!(!delta.as_ref().is_empty() || ahead.as_ref() == base.as_ref(),
        "empty delta disables anti-entropy (§1)");
    let merged = MyContract::update_state(
        params(), base, vec![UpdateData::Delta(delta)]
    ).unwrap().unwrap_valid();
    assert_eq!(merged.as_ref(), ahead.as_ref(), "delta must converge peer");
}
#[test] fn delta_handles_bad_summary() {
    let s = gen_state();
    let bad = StateSummary::from(b"garbage".to_vec());
    let delta = MyContract::get_state_delta(params(), s.clone(), bad).unwrap();
    let merged = MyContract::update_state(
        params(), empty_state(), vec![UpdateData::Delta(delta)]
    ).unwrap();
    assert!(merged.is_ok(), "must fallback to whole-state, not panic");
}
```

### B — CRDT laws (pure reducer: §0, §2; Broken flag)

```rust
fn apply(state: State<'static>, datas: Vec<UpdateData<'static>>) -> State<'static> {
    MyContract::update_state(params(), state, datas).unwrap().unwrap_valid()
}

#[test] fn update_idempotent() {
    let s = gen_state(); let d = gen_update(&s);
    assert_eq!(apply(s.clone(), vec![d.clone()]).as_ref(),
               apply(s.clone(), vec![d.clone(), d.clone()]).as_ref());
    assert_eq!(apply(s.clone(), vec![d.clone()]).as_ref(),
               apply(apply(s.clone(), vec![d.clone()]), vec![d]).as_ref());
}
#[test] fn update_commutative() {
    let s = gen_state(); let a = gen_update(&s); let b = gen_update(&s);
    assert_eq!(apply(s.clone(), vec![a.clone(), b.clone()]).as_ref(),
               apply(s.clone(), vec![b, a]).as_ref());
}
#[test] fn update_associative() {
    let s = gen_state(); let a = gen_update(&s); let b = gen_update(&s); let c = gen_update(&s);
    let ab_c = apply(apply(s.clone(), vec![a.clone(), b.clone()]), vec![c.clone()]);
    let a_bc = apply(s.clone(), vec![a, b, c]);
    assert_eq!(ab_c.as_ref(), a_bc.as_ref());
}
#[test] fn update_reads_data_not_state_plus1() {
    // Canonical freenet bug — `state+1` double-counts on replay.
    let s = gen_state();
    let d = gen_update(&s);
    let once = apply(s.clone(), vec![d.clone()]);
    let twice = apply(s.clone(), vec![d.clone(), d.clone()]);
    assert_eq!(once.as_ref(), twice.as_ref(),
        "must be max/union from data (§2), not +1 from state");
}
#[test] fn update_empty_and_unknown_noop() {
    let s = gen_state();
    assert_eq!(apply(s.clone(), vec![]).as_ref(), s.as_ref());
    let unk = UpdateData::Related;
    assert_eq!(apply(s.clone(), vec![unk]).as_ref(), s.as_ref());
}
#[test] fn update_rejects_garbage_data_without_panic() {
    let s = gen_state();
    let bad = State::from(b"not-state".to_vec());
    let res = MyContract::update_state(params(), s, vec![UpdateData::State(bad)]);
    assert!(res.is_ok() || res.is_err(), "must not trap in wasmtime");
    if let Ok(m) = res { let _ = m.unwrap_valid(); }
}
#[test] fn property_crdt_random() {
    // proptest/quickcheck: contract supplies Arbitrary for State/UpdateData
    // proptest! { |(s in gen_states(), a in gen_updates(), b in gen_updates())| {
    //     prop_assert_eq!(apply(s.clone(), vec![a.clone(), b.clone()]),
    //                    apply(s.clone(), vec![b, a]));
    // }}
}
```

### C — Node liveness (network-mode only; local mode hides Broken)

```rust
#[tokio::test(flavor = "multi_thread")] async fn not_marked_broken() {
    // Use freenet skill Pattern B: serve_client_api_with_listener + NodeConfig + run_network_node
    let node = TestNode::start_network().await;
    let key = deploy(&node, wasm()).await;
    for _ in 0..20 { update_count(&node, key, gen_update(&get_state(&node, key).await)).await.unwrap(); }
    assert!(get_count(&node, key).await.is_ok(), "Broken flag persists in DB (§8)");
}
```

Opt-in (not universal): scale/O(participants), cross-tag forgery, `+1` rate limit,
signature/PoW anti-cheat — these trade scale vs anti-cheat per §6 choose-2-of-3 and
belong in a contract-specific `adversarial.rs` (see `freenet_example` hardening).

## References
- `references/reconciliation-and-scaling.md` — the full derivation: pure-reducer model,
  delta/interest flow and the efficiency gate, worked G-counter merges, the scaling proof, the
  trust split, and the trigger/timestamp/PoW/signed-receipt review.
