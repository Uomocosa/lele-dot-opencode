# Reconciliation, Scaling & Trust in Freenet Contracts — Deep Dive

The working out behind the `freenet-contract-design` SKILL.md. Abstract and pattern-only; not
tied to a specific project or version.

## 1. The contract is a pure reducer

A Freenet contract exposes a fixed set of stateless functions the host runs:

- `validate_state(state)` — should I host this state?
- `update_state(state, data) -> new_state` — apply a batch of updates.
- `summarize_state(state) -> summary` — a compact digest a peer can compare.
- `get_state_delta(state, their_summary) -> delta` — what to send a peer that's behind.

`update_state` has no side tables and no memory of prior invocations. Its only inputs are the
current state and this batch of `UpdateData` (`State` or `Delta`). It runs on every node that
hosts the contract, so:

- It must be **deterministic** (all nodes reach the same state from the same inputs).
- It must be **idempotent and commutative** — the host does not guarantee exactly-once,
  in-order delivery. Re-delivery and reordering are normal, so "apply this twice" must equal
  "apply it once," and order must not matter.

This is the definition of a **join-semilattice / CRDT merge**: merge is a `max`/`union`/per-key
combine, not an "apply N times" operation.

## 2. Why a scalar last-writer-wins counter reconciles badly

Consider a state that is a single `u64` "count", where each update *replaces* the whole value
(last writer wins), the summary is the count itself, and `get_state_delta` returns nothing.

| Function | Behavior | Effect on reconciliation |
|---|---|---|
| `update_state` | replace count with incoming value | last-writer-wins; no merge |
| `summarize_state` | count (equals the whole state) | summary ~= state; nothing to diff |
| `get_state_delta` | empty | no delta to send |

Because two replicas apply their *own* writes to the *same* scalar, and each replaces the other's,
their increments never combine. The node's delta path is additionally gated by an efficiency
check (roughly: the summary must be small relative to the state size, so a delta is worth
sending). An empty delta (or a summary that is the state itself) never triggers a useful merge.

Two such replicas that later read the "same" value have done so coincidentally — each reached a
similar number on a disjoint copy. That is not convergence.

**So:** any "aggregate" contract meant to converge must be a mergeable structure with a compact
summary and a real (non-empty) delta. Verified 0.2.101 nuance: the anti-entropy summary comparison
is byte equality with full-state heal (`node.rs:2698-2701`, no size gate found on that path), so a
**per-tag map summary** is preferred over a scalar total — equal totals can mask compensating
divergence (`{a:8}` vs `{a:4,b:4}`) that a byte-compare of per-tag maps catches.

## 3. Idempotent merge: the value must travel with the update

The correct transition folds the incoming value under a commutative, idempotent operator:

- `map[tag] = max(map[tag], Value(from_data))`
- `set.extend(Values(from_data))`

Replaying the same `{tag: V}` is a no-op. A "trigger" that the contract turns into `+1` is not
idempotent:

```
state {A:5}; deliver "A clicked"   -> {A:6}
state {A:6}; re-deliver "A clicked" -> {A:7}   // double-counted; contract can't tell it's a repeat
```

Because the contract has no memory, the only way to survive re-delivery is for the update to
carry a **monotonic value** that `max`-merge treats as "already seen" on replay. That requirement
is unavoidable: **you cannot dedup without carrying a monotonic token, and the moment you carry
one you've reintroduced a client-chosen value.**

## 4. The delta/interest flow and the efficiency gate

Peers track each other's interest and summary for a contract. To bring a stale peer up to date,
the holder computes a delta for the peer's summary and sends it. The delta path is only followed
when a delta is *efficient* — i.e. small relative to the full state — and when
`get_state_delta` actually returns bytes.

- A **scalar summary** (count, length) over a collection state is small, so the efficiency check
  passes once the state is non-trivial.
- A **non-empty delta** (whole remaining state, or a true per-key diff) is what the remote
  `update_state` merges in.

Keep `summarize_state` compact and `get_state_delta` returning actual bytes (the whole state is a
simple, correct default; per-key diffs are an optimization). Prefer a **per-tag map summary** when
the state is a keyed collection: the 0.2.101 anti-entropy compare is byte equality, so structural
summaries detect divergences that equal-total scalar summaries mask.

## 5. The G-counter: a mergeable, additive, offline-retaining counter

State: `map<participant_key, count>`. Merge: element-wise `max`. Total: Σ values.

Properties:
- **Commutative + associative + idempotent** → reconciles regardless of delivery order.
- **Concurrent writers on different slots both survive**: two participants merge to N+M (the
  counter actually adds), not N-overwrites-M (last-writer-wins).
- **Never evict**: a participant's slot persists whether or not they are online. Offline
  retention is automatic — a returning participant finds their old count. There is no eviction
  job and no "offline" concept needed in the state.
- **Count is a value, not a log**: state grows with the number of *participants*, not with the
  number of *clicks*. A slot going 1 → 1,000,000 is the same 8 bytes.

Worked merge (two writers, distinct slots):

```
w1 writes {A:3}          -> state {A:3}, total 3
w2 writes {B:7}          -> state {A:3, B:7}, total 10   (max-merge keeps both)
replay {B:7}             -> state uncharged (B already 7) — idempotent
```

## 6. Scaling physics: users vs clicks

The decisive question is whether state grows with **participants** or with **actions**.

| | Map<key,count> (G-counter / aggregate) | Per-action log / set |
|---|---|---|
| State growth | O(participants) | O(total actions) — unbounded |
| Many clicks by one participant | value grows in place (no new entry) | one new entry per action |
| Delta size | O(whole state) = O(participants) when whole-state | O(actions) |

Implications:
- A **value** can grow to any magnitude at fixed width — "clicking a lot" never adds a slot.
- An **entry-per-action** structure is unbounded; it is the right tool only when you genuinely
  need every action retained (audit log), and it does not scale to "many users clicking a lot."
- **Replication multiplier:** freenet copies a contract to each interested peer, so both state
  and every delta are multiplied by the peer count. Whole-state deltas over a huge state are
  expensive per peer.
- **Information bound:** retaining a distinct per-participant figure for N participants is
  inherently Ω(N). No data structure escapes it. For extreme N, move per-participant history
  out-of-band and keep only aggregates (e.g. N shard accumulators) in the replicated state —
  but then you only know per-shard totals, not per-participant.

## 7. Trust: the contract key separates two different attacks

`ContractKey` is derived from the contract code bytes + parameters. This gives a clean split:

**Attack 1 — modify the contract.** Change `update_state` → different wasm → different key → a
different, isolated contract that honest peers (running the canonical code+params) never touch.
This is true content-addressing: to join your game a peer must run your exact published
code+params, which runs your enforced transition. Open-sourcing the contract does not weaken this
gate — it makes the rules auditable while the key still pins the exact code.

**Attack 2 — modify the client.** The client is a separate layer; it calls the contract with
`UpdateData`. A user can keep your *identical* contract (same key) and run their own caller that
submits a valid-but-dishonest value (e.g. an inflated slot). The key does not vouch for input
truth — it only guarantees *which transition function* ran. Anyone can write their own client
against your honest contract.

Because idempotent merge forces an update to carry a client-chosen monotonic value (§3), Attack 2
is always possible in a pure CRDT. Preventing it needs an unforgeable evidence source:

| Option | Stops self-inflation? | Cost |
|---|---|---|
| Trusted signer (server receipts) | Strong | Centralization (a party the user can't impersonate must sign each action) |
| Hardware attestation (TEE) | Strong | Trust moves to the CPU vendor; platform-dependent |
| Proof-of-work per action | Bounded (each fake action costs real compute) | Replay-safe PoW needs O(actions) proof-state, or a monotonic-seq design that breaks CRDT ordering/reliability |
| Timestamps / triggers | No | Client-minted monotonic values; forgeable, just like a bare value |

### The choose-2-of-3 tradeoff

You generally get two of: **scale** (compact, reliable state), **anti-cheat** (bounded
self-inflation), **decentralization** (no trusted party). A fully-decentralized, low-state
contract cannot also verify input truth; a scale-focused contract is deterministic and reliable
but trusts the client's reports; an anti-cheat contract pays in centralization or storage.

## 8. Practical checklist

1. Define the *state shape for a mergeable CRDT* before writing `update_state`.
2. `update_state` merges `data` under `max`/`union`; it never counts its own invocations.
3. `summarize_state` returns a compact scalar; `get_state_delta` returns non-empty bytes.
4. For a shared total that converges + offline retention → G-counter (`map<key,count>`, never
   evict).
5. Decide the trust stance up front: pure CRDT (client-reported), trusted signer, or PoW — and
   accept the chosen tradeoff.
