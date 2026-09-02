# Raven — Contract Structure Reference

Source: `freenet/raven` @ `v0.1.4` (`fa9acdbc`) — pinned tag
Paths: `contracts/{user-shard,inbox-shard,global-index-shard,thread-shard,facade}/src/lib.rs` + `common/` + `contracts/facade-types/`
Crates: `freenet-microblogging-user-shard`, `-inbox-shard`, `-global-index-shard`, `-thread-shard`, `-facade` (+ `facade-types` shared types, `facade-loader`)
Serialization: CBOR (`ciborium`) for states/summaries/deltas; ML-DSA-65 (`ml-dsa =0.1.0-rc.8`) signatures (not ed25519) — **post-quantum**
Parameters: per-contract raw ML-DSA-65 VK bytes (owner or shard epoch)
Build: `cargo build -p freenet-microblogging-user-shard --target wasm32-unknown-unknown --features freenet-main-contract` (repeat per shard)

> **Status WIP** — Raven is under active development (see `DESIGN.md`, `RELEASING.md`). Shard design follows ADR-0001; some shards have `version = 0.0.0` indicating pre-release. This reference reflects `v0.1.4` and may lag `main`.

## Architecture — sharded microblog (ADR-0001)

Raven shards mutable state to bound single-contract size and allow parallel sync:

| Shard | Crate | Contract | State | Write authority | Scaling |
|-------|-------|----------|-------|-----------------|---------|
| User | `user-shard` | `UserShard` | `posts: Vec<Post>` (newest `MAX_POSTS=200`), `profile: Profile` (LWW `seq`), `follows: BTreeMap<key, FollowState{seq,following}>` | **Owner-writes only** — `Post::verify` + `author == owner`; profile/follows via `SignedOp` (ML-DSA over domain-tagged payload) | O(posts_window + follows) — posts windowed, follows capped 5000 |
| Inbox | `inbox-shard` | `InboxShard` | per-user inbox of mentions/notifs | Owner-writes (recipient) | O(inbox entries) |
| Global Index | `global-index-shard` | `GlobalIndexShard` | global feed index (post refs) | Multi-writer (open index) | O(indexed post refs) — high churn |
| Thread | `thread-shard` | `ThreadShard` | replies per thread | Multi-writer (repliers) | O(replies) per thread |
| Facade | `facade` + `facade-types` + `facade-loader` | aggregator | resolves shards via `facade-types` | delegates to shards | — |
| Test | `test-contract` | — | test harness | — | — |

## Four functions — per shard (pattern shared)

Illustrated with `user-shard` (`contracts/user-shard/src/lib.rs` — doc comments are extensive):

- **validate_state**: deserializes `UserShard` + params VK, checks `Post::verify` per post, `SignedOp::verify` for profile/follows, bounds (`MAX_CONTENT_LEN`, `MAX_FOLLOWS=5000`, `MAX_FOLLOW_TARGETS_PER_OP=1000`, `MAX_TARGET_KEY_LEN=3904`).
- **update_state**: iterates **every** `UpdateData` (not just `data[0]`) — dispatches per `ShardDelta` enum variant (posts vs profile vs follows) so full-state `Sd::State` deserializes `UserShard` and folds all three surfaces. This fixes a prior bug where only one surface reconciled.
- **summarize_state**: structural per-surface summary (e.g. post IDs, profile `seq`, per-key follow `seq`) — not scalar.
- **get_state_delta**: per-surface diff vs peer summary; `None` → empty `StateDelta`, `Some(delta)` → CBOR `ShardDelta`. Must be empty when peer is converged.

Other shards follow same skeleton with shard-specific types (`InboxDelta`, `GlobalIndexDelta`, etc.). `facade` stitches them at UI/dm level.

## Merge laws

- **posts**: grow-set deduped by content-address `id`, truncated to newest `MAX_POSTS=200` by `(timestamp, id)` desc (total order; no clock in contract). Order-independent. Over-window eviction is post-merge `truncate_posts` as function of `(timestamp,id)` set — not arrival order.
- **profile**: LWW by monotonic `seq` (tie-break by serialized bytes for determinism). `seq` higher wins.
- **follows**: per-key `FollowState { seq, following }`. Merge keeps higher `seq` per key; on equal `seq`, `Unfollow` wins. This is a join semilattice (convergent), unlike bare add/remove set. `MAX_FOLLOWS` cap enforced post-merge by `truncate_follows` (tombstones evicted first, then largest key — never arrival order). Over-cap eviction is best-effort lossy.

All merges are commutative/associative/idempotent. `facade` contracts treat each shard as independent.

## Scaling

- User shard: `posts` window 200 caps click-growth; `follows` cap 5000 caps per-user social graph. Both are functions of key sets, not arrival order (deterministic truncation).
- Global index / thread shards: unbounded multi-writer — rely on sharding (per-epoch, per-thread) to partition. High churn handled by delta-per-shard sync (only lagging thread's shard fetched).
- Delta size per sync is O(lagging entries), not whole social graph.

## Trust

- Post-quantum: ML-DSA-65 (NIST PQC) not ed25519 — Raven is first Freenet app to rotate suite.
- Owner-writes surfaces (user shard) — only owner's VK accepted (`VK == params`). Multi-writer surfaces (global index, thread) — any signed post accepted, abuse resistance via `Ghost Keys`/`facade` Sybil gating (separate subsystem).
- WASM bytes pin contract logic; ML-DSA params pin owner. Forking contract → new key (isolated shard epoch).

## Mapping to freenet-contract-design

- §0 pure reducer: merges are pure (no clock), `seq` monotonic replaces wall time.
- §2 idempotent: per-post `id` dedup, per-key `seq` max — replay no-op.
- §3 wiring: structural summary per field (posts/profile/follows each contribute) + non-empty delta only for lagging keys — avoids scalar-total masking.
- §5 scaling: sharding is the concrete answer to "O(users) vs O(clicks)" — window 200 + cap 5000 + shard partition keep single-contract state bounded; cross-tag forgery not applicable (per-owner shards).
- §6 anti-cheat: self-inflation of `seq` possible (client forges `SignedOp.seq+1`) — owner-writes surface trusts owner's client; multi-writer surfaces accept open writes, rely on higher-level Sybil layer.

## References

- `contracts/user-shard/src/lib.rs`, `contracts/thread-shard/src/lib.rs`, `contracts/global-index-shard/src/lib.rs`, `contracts/inbox-shard/src/lib.rs`
- `contracts/facade/src/lib.rs`, `contracts/facade-types/src/lib.rs`
- `common/src/post.rs`, `common/src/signed_op.rs` (`SignedOp`, `USER_SHARD_CONTEXT`)
- `DESIGN.md`, `CLAUDE.md`, `published-contract/` (pinned WASM)
