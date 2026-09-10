# Sharding / facade

**Where from:** `references/RAVEN_CONTRACT_STRUCTURE.md:14` ADR-0001 `user-shard/thread-shard/global-index-shard` + `facade`; skill `§5`.

**Description:** Partition one big contract into many shard contracts (`Raven 4 shards`: `user-shard`/`inbox-shard`/`global-index-shard`/`thread-shard` + `facade` loader). Each shard `O(cap)`; global total = sum shards. Single-contract variant: `shard = hash(key) % S` and state = `BTreeMap<ShardId, Aggregate>` `O(S)` constant.

**Memory cost:** `O(S × cap)` fixed (e.g., `S=64` shards × `cap=200` → bounded, vs `O(users)` linear). Replication per shard.

**Speed:** Parallel sync per shard; delta per shard only lagging shard.

**Pros:** Scales to large `N` with bounded single-contract size; the concrete answer to `Ω(N)` per-key bound.

**Cons:** Single `O(S)` aggregate loses exact per-key breakdown (sum only) unless each shard keeps its own `map<key,value>` (`O(users)` across shards). Cross-shard atomicity none.

**When to use:** `N` too large for single map, or global total / per-thread feed only needed (Raven global index, thread shards).

**Vulnerability:** Shard collision Sybil — attacker grinds keys to same shard. Mitigate `shard = hash(pubkey)` not attacker-chosen, plus per-shard allow-list.

**Example:**
```rust
// pseudocode — generic sharding
const S: u16 = 64;
let shard = hash(&key) % S;
shards.entry(shard).and_modify(|v| *v = (*v).max(new_value)).or_insert(new_value);
```

**Mapping:** Skill `§5` information bound.

---
