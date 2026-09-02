# Ping — Contract Structure Reference

Source: `freenet/freenet-core` @ `v0.2.132` (`0ca7e02b`)
Paths: `apps/freenet-ping/contracts/ping/src/lib.rs`, `apps/freenet-ping/types/src/lib.rs`
Crate: `freenet-ping` (contract) + `freenet-ping-types` (pure Rust, no WASM)
Serialization: `serde_json` (state is JSON, not CBOR) — `Parameters = PingContractOptions { ttl: Duration, frequency: Duration, tag: String, code_key: String }`
Build: `cargo build -p freenet-ping --target wasm32-unknown-unknown --features freenet-main-contract`

## State shape

`Ping` (`types/src/lib.rs:42`) — **the reference CRDT for convergence correctness** (see extensive doc comments):

```rust
pub struct Ping {
    from: BTreeMap<String, Vec<DateTime<Utc>>>, // BTreeMap for canonical CBOR/JSON encoding (byte-equal compare)
    pub padding: Option<Vec<u8>>,                // inflated size for streaming tests
}
impl Deref for Ping { type Target = BTreeMap<String, Vec<DateTime<Utc>>>; }
```

- `BTreeMap<String, Vec<DateTime<Utc>>>`: per-peer observations. `BTreeMap` (not `HashMap`) because summaries are compared **byte-for-byte** — `HashMap` iteration order would make identical logical states encode differently (core #5320).
- `MAX_HISTORY_PER_PEER = 10` (`types/src/lib.rs:40`): newest 10 kept regardless of age, plus any older still within `ttl` (measured back from the state's own newest timestamp — see below).

## Four functions

### validate_state (`contracts/ping/src/lib.rs:8`)
- Allows empty bytes. Otherwise deserializes `Ping` via `serde_json::from_slice`; returns `Valid` with no plausibility check (any state that deserializes is accepted — future-timestamp/unauthenticated, see merge doc).

### update_state (`contracts/ping/src/lib.rs:39`)
- Deserializes `PingContractOptions` params (`ttl`) + current `Ping` (default if empty). Folds each `UpdateData`:
  - `State(s)` / `Delta(s)` / `StateAndDelta{state,delta}` → each non-empty `serde_json::from_slice::<Ping>` → `ping.merge(update, opts.ttl)` (same path for State and Delta — both are full `Ping` fragments merged by union).
  - Skips empty; `InvalidUpdate` on unknown variant.
- Returns `State(serde_json::to_vec(&ping))`. **Idempotent**: `merge` re-unions; replay is no-op. No `state + 1`.

### summarize_state (`contracts/ping/src/lib.rs:201`)
- Empty → `StateSummary(vec![])`. Otherwise returns **whole state bytes verbatim** (`StateSummary(state.to_vec())`). Commentary at `:187-200` explains: Ping's state IS the set of observations — no smaller summary still answers "which timestamps do you not have". Compressible contracts should summarize; Ping deliberately does not. `self_delta_empty` diagnostic does not apply (large summary cost is one round-trip bandwidth, not per-update).

### get_state_delta (`contracts/ping/src/lib.rs:239`)
- Deserializes `Ping` state + `Ping` summary (both JSON). Calls `ping.delta_against(&ping_summary)` (`types/src/lib.rs:442`) which returns `Option<Ping>` = `S \ R` (missing entries only) + padding iff ours would win the merge tie-break.
- `None` → `StateDelta(vec![])` (empty delta = honest "up to date", makes `self_delta_empty` hold). `Some(delta)` → `serde_json::to_vec(delta)` → `StateDelta`. Skips TTL pruning on sender — pruning is receiver's merge job.

## Merge laws — why this contract is the textbook

`Ping::merge(&mut self, other: Self, ttl: Duration)` (`types/src/lib.rs:197`) — pure function of inputs (no `Utc::now()`):

1. **Padding**: longer wins; equal length → `existing < incoming` (total order) — commutativity by tie-break, not `self`-bias (fixed latent defect).
2. **Union first**: `self.from.extend(other.from)` — nothing judged before union (symmetric).
3. **Logical clock**: `reference = max(self.from.values().flatten())` (newest timestamp in union, computed AFTER union so both orders see same `max`). TTL measured as `reference <= t + ttl` (`retain_history`), not wall clock — wall clock would violate `merge(A,B)==merge(B,A)` across TTL boundaries (#5320, `fdev verify-merge`).
4. **`retain_history`**: newest-first sort + dedup, keep newest 10 plus any older still within TTL (only when `len > 10`). `retain(|_,v| !v.is_empty())` removes phantom empty entries (hand-built payload `name: []`).

Properties pinned by tests:
- `merge_is_idempotent` (A+A==A), `merge_is_commutative_across_the_expiry_boundary`, `merging_the_same_pair_at_two_moments_gives_the_same_answer` (determinism — logical clock), `updates_reports_a_new_timestamp_that_displaces_one_at_capacity` (reporting via `contains`, not `len`), `a_delta_against_our_own_state_is_nothing` (`self_delta_empty`), `applying_the_delta_reaches_the_same_state_as_applying_the_whole_state` (delta equivalence).

## Delta equivalence

`delta_against` builds a per-peer `BTreeSet` (not `HashSet` — WASM deterministic, no hasher divergence) of recipient timestamps, collects `S \ R` per name. `Some(delta)` iff `missing.is_empty()==false || padding_wins`. Proof in doc comment: merging delta gives `R ∪ (S\R) == R ∪ S` with same `reference`, so prune identically. Complexity `O((n+m) log m)` not `O(n*m)` — bounded only by 50 MiB `MAX_STATE_SIZE`, not by type.

## Scaling

Per-peer history capped at newest 10 + in-window tail. Live state settles at ~`ttl × write_rate` per peer; frozen state retains whatever it settled at (no further ageing — "a state nobody is writing to stops ageing"). **Not an absolute cap**: TTL branch only reached when `len > 10`, so a peer that accumulated 500 timestamps inside one TTL window retains all 500 once writes stop. Peer names never swept. Absolute cap must be added in `validate_state` if needed.

## Trust trade-off

- **Convergence vs. forgery**: logical clock makes merge deterministic but lets a future-dated timestamp (unauthenticated — `validate_state` checks nothing) pin `reference` a year ahead, truncating every peer's history to 10 and never recovering (newest-ten pin). Doc at `types/src/lib.rs:146-191` calls this a genuine regression vs wall clock; fix is `validate_state` rejecting implausible timestamps (fine to read clock there — rejecting input is not merging).
- Takeaway quoted in docs: "Reading the clock at the WRITE (`insert`) is what makes it data; reading it at the MERGE is what makes the merge non-deterministic."

## Mapping to freenet-contract-design

- §0 pure reducer: merge is pure — TTL anchored on `max(union)` not `Utc::now()`.
- §2 idempotent: `merge` unions, not `+1`.
- §3 wiring: whole-state summary (intentional), non-empty per-key delta when behind; empty delta when converged (teaches `self_delta_empty`/`whole_state_self_delta` diagnostics #5072).
- §5 scaling: demonstrates `MAX_HISTORY_PER_PEER` floor vs TTL window, `O(peers × window)` with frozen-state retention disclosure.

## References

- `apps/freenet-ping/contracts/ping/src/lib.rs:1-315`
- `apps/freenet-ping/types/src/lib.rs:40-1105` (read entire doc comments)
- `freenet-core` conformance verifier (`fdev verify-merge`, #5320/#5352)
