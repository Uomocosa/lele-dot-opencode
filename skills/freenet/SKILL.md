---
name: freenet
description: Use when developing Freenet contracts, delegates, or WebSocket clients, or when launching/wiring Freenet nodes. Docs links, the lele contract harness, and the non-obvious gotchas — idempotent merge, local-vs-network notifications, canonical wasm, replica-split bridging, node roles/ring.
---

# freenet — Contracts, Clients, and Nodes

Freenet apps have three parts: a **Contract** (WASM shared state on untrusted peers), a
**Delegate** (WASM private state on the user's node), and a **UI/client** (WebSocket to the local
node at `127.0.0.1:7509`; nodes talk P2P and the deterministic `ContractKey` routes requests).

## Docs, references & examples

| Topic | URL / file |
|-------|-----|
| Official manual | `https://freenet.org/build/manual/` |
| `freenet-stdlib` API | `https://docs.rs/freenet-stdlib` |
| `freenet-core` (node) | `https://github.com/freenet/freenet-core` |
| Minimal Rust example (`freenet-ping`) | `https://github.com/freenet/freenet-core/tree/main/apps/freenet-ping` |
| Reference apps | `https://github.com/freenet/river`, `https://github.com/freenet/freenet-scaffold` |
| Whitepaper | `https://freenet.org/pdf/freenet-whitepaper.pdf` |
| Gateway index | `https://freenet.org/keys/gateways.toml` |

Local references in this skill directory (load on demand — do **not** paste inline):

- `references/reconciliation-and-scaling.md` — full derivation of the CRDT merge, delta flow,
  the G-counter, scaling proof, trust split, and the **universal contract test suite**.
- `references/*_CONTRACT_STRUCTURE.md` — worked contract shapes (delta, ping, website, river, atlas, raven).
- `references/ring-and-discovery.md` — ring topology, node roles, `--gateway` flags, hermetic meshes.
- `glossary/` — per-term nomenclature (`idempotent`, `crdt-g-counter`, `structural-summary`,
  `delta-empty-delta`, `lww`, `tombstone`, `ttl`, `window-cap`, `sharding-facade`, `allow-list-root-auth`, `logical-vs-wall-clock`).

## The lele contract harness

`freenet_contract_harness` is the crate that makes a contract *good*: it exercises the universal
suite (CRDT laws, four-function wiring, rejection safety, Broken-flag liveness) against your
state/merge so a bad contract fails fast instead of silently splitting on mainnet.

```bash
# harness is its own repo: github.com/Uomocosa/freenet-contract-harness
cargo nextest run --manifest-path ../freenet-contract-harness/Cargo.toml -- --nocapture
# consuming crate: add it as a dev-dependency (git + tag) and call `run_suite`
```

Freenet crates also wire local/cross-OS end-to-end recipes (`just harness`, `just contract`); there
is no floor-task checker (`lele_enforce_config` is retired). See
`references/reconciliation-and-scaling.md` §test-suite for the generator-based suite to parameterize
(`gen_state()` / `gen_update()`).

## Gotchas (the non-obvious parts)

**`update_state` must be an idempotent, commutative merge.** Read the new value from the update
`data`, never `state + 1` — a non-idempotent contract is flagged **BROKEN** and the flag persists
across restarts (`rm -rf ~/.local/share/freenet/db` to clear).

```rust
// ✅ merge from data (idempotent)          // ❌ state+1 (double-counts on replay)
let v = deserialize(data)?;                 let v = deserialize(state)? + 1;
Ok(UpdateModification::valid(serialize(&v)?))  Ok(UpdateModification::valid(serialize(&v)?))
```

- **Local mode skips `UpdateNotification`.** `freenet local` / `run_local_node` returns
  `UpdateResponse` directly and never calls `commit_state_update`; use network mode
  (`serve_client_api_with_listener` + `NodeConfig` + `run_network_node`) whenever pub/sub matters.
- **Absorbing a notification must MERGE** (max/union per key) for slot-map state — replacing the
  local map wipes foreign slots on every single-key tick (real production bug).
- **Contract key = `Blake3(wasm_bytes)` + params.** A rebuild changes the key even for identical
  source, so ship one canonical committed `.wasm` (embedded via `include_bytes!`); never rebuild
  per deployment.
- **Fresh-key concurrent `Put`s can split into disjoint replica groups** (anti-entropy is
  neighbor-pair-only, ~5-min heartbeat). Bridge from the client with a routed
  `ContractRequest::Subscribe { key, summary: Some(per_tag_summary) }` every ~30s; heals in
  ~10-60s. A local re-`Get` never bridges (answered locally); re-`Put` times out.
- **No request-response correlation.** After `Get { subscribe: true }` you may get
  `SubscribeResponse` then an `UpdateNotification` before `GetResponse` — loop on recv and skip
  unexpected variants.
- **WebSocket connect can hang** — wrap `connect_async` in `tokio::time::timeout(5s, …)`.
- **`tikv-jemalloc-sys` fails on a path with spaces** — keep the full `freenet` crate in
  `[dev-dependencies]` by default, and set `[build] target-dir = "/tmp/frt-build"` (with `jobs = 6`)
  in `.cargo/config.toml` so the build happens off the space-containing path.
- **Node roles / "they discover each other via Freenet":** peers share routing only when they join
  the *same ring*. Isolated gateways each seed a disjoint ring and can never see each other. Load
  `references/ring-and-discovery.md` before spawning/wiring nodes.
