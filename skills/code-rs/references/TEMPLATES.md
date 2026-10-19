# code-rs templates

## Plan

````markdown
> **PLAN ONLY — no edits until you say proceed.**

**Setup:** <proof block from WORKFLOW_SETUP.md>

## Understanding
Goal: <one sentence>

Assumptions (correct me if wrong):
- A1. ...

Open questions (plan assumes the [default]):
- Q1. ... [default]

## Blocks

### Block 1 — `fn compute_peer_score` (new) · `crates/net/src/peer/compute_peer_score.rs`
Kind:      function (pure | atomic delegate | bevy system | type | trait impl | test | mod)
Role:      <one sentence: what it does, not how>
Signature: `pub fn compute_peer_score(info: &PeerInfo) -> PeerScore`
Used by:   Block 3, existing `dial_best_peer` (crates/net/src/dial.rs:42)
Names:
  1. `compute_peer_score` ✅ — <why chosen>
  2. `score_peer` — <tradeoff>
  3. `peer_score` — <tradeoff>

## Previews
<one preview per block, format below>

## Code-size review
- Duplication: ...
- Near-duplicates: ...
- Functional reshapes: `[FP1 higher-order] Block 2 + Block 4 → one fn taking impl Fn(&Peer) -> bool`
  + preview   (or "nothing to reduce")

**Proceed, or what should change?**
````

## Preview marker format (mandatory)

Every line starts with a 2-char marker column, then the code:

| marker | meaning                          | appears in       |
|--------|----------------------------------|------------------|
| `- `   | line deleted                     | BEFORE only      |
| `! `   | line changed (old / new version) | BEFORE and AFTER |
| `+ `   | line added                       | AFTER only       |
| `  `   | unchanged context                | both             |

`!` lines pair up in order: the n-th `!` in BEFORE becomes the n-th `!` in AFTER.
Keep a few unchanged context lines; elide long unchanged runs with `  // ...`.

Edit of an existing file:

````markdown
**Block 2 — `dial_best_peer`** · `crates/net/src/dial.rs`
```rust
// BEFORE
  pub fn dial_best_peer(peers: &[PeerInfo]) -> Option<PeerId> {
!     let best = peers.first()?;
-     tracing::debug!("dialing first peer");
      Some(best.id)
  }
```
```rust
// AFTER
  pub fn dial_best_peer(peers: &[PeerInfo]) -> Option<PeerId> {
!     let best = peers.iter().max_by_key(|p| compute_peer_score(p))?;
+     tracing::debug!(peer = %best.id, "dialing best-scored peer");
      Some(best.id)
  }
```
````

New file: no BEFORE; write `// BEFORE: (new file)` then an AFTER where every line is `+ `.
Deleted file: BEFORE where every line is `- `, then `// AFTER: (file deleted)`.
