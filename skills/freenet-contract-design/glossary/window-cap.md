# Window / cap

**Where from:** `references/RIVER_CONTRACT_STRUCTURE.md:59` `MessagesV1 max_recent_messages=100`; `RAVEN_CONTRACT_STRUCTURE.md:15` `MAX_POSTS=200`; Ping `MAX_HISTORY_PER_PEER=10`.

**Description:** Hard limit on how many entries kept per key/collection (`River MessagesV1 max_recent_messages=100`, `Raven MAX_POSTS=200`, `Ping MAX_HISTORY_PER_PEER=10 + TTL tail`, Delta `next_page_id` monotonic). Only newest survive, truncation deterministic by `(timestamp, id)` or lexicographic key, not arrival order, so concurrent merges agree.

**Memory cost:** `O(cap)` bounded per key, `O(keys×cap)` total. Independent of clicks.

**Speed:** Truncate `O(n log n)` sort after merge.

**Pros:** Absolute bound; prevents `O(clicks)` blow-up.

**Cons:** Over-cap eviction discards data (Raven `truncate_follows` drops largest key). Frozen state retains window contents forever — not self-pruning.

**When to use:** Message feed, recent history, active-window counter. Pair with TTL for time + count bound.

**Vulnerability:** Eviction chosen by key order can be gamed (attacker forces eviction of victim’s entry by flooding cap). Mitigate per-owner caps.

**Example:**
```rust
fn truncate(msgs: &mut Vec<Msg>) { msgs.sort_by_key(|m| m.id); msgs.truncate(100); }
```

**Mapping:** Skill `§5` O(clicks) vs O(users).

---
