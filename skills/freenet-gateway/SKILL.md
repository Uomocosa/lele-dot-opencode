---
name: freenet-gateway
description: Use when working with Freenet node network roles, ring topology, or any task that spawns or wires up multiple freenet nodes — gateways vs client peers, bootstrap seed gateways, the --is-gateway/--public-network-address/--public-network-port/--skip-load-from-network/--gateway flags, joining the public mainnet ring, deterministic hermetic test meshes, why peers discover each other yes/no ("they need to discover each other via Freenet"), the fresh-key Put race and its verified root cause (divergent replica groups, neighbor-pair-only anti-entropy), and client-side split bridging. Works with any project that embeds or launches Freenet nodes.
---

# Freenet Node Roles, the Ring, and Peer Discovery

Freenet is a **small-world / chord-style DHT ring** over key-space `[0.0, 1.0)`. Every node has a
`location`, forms a small set of ring **neighbors** (default `10..20` connections), and routes a
`Get`/`Put`/`Update` **toward the node(s) responsible for the contract key's location**. State is
propagated by push-on-update within a connected replica group and reconciled between
**directly-connected neighbors** by the InterestSync anti-entropy heartbeat (~5-min cadence) — it
is *not* a ring-wide reconciler (see the fresh-key Put race section below). None of this requires a
central registry: peers come to share routing only when they are members of the *same* ring.

This skill is the reference for the two node roles, the bootstrap flags, and how to reason about
whether two nodes can see each other. Readers should also load the `freenet` skill for contract and
client development. Terminology here maps to `freenet` v0.2.101+ (`NetworkArgs` in `config.rs`,
`node.rs`, `ring.rs`). A short companion reference lives in `references/ring-and-discovery.md`.

## The two node roles — decide before you spawn

| | **Gateway node** (`--is-gateway`) | **Client peer** (`--is-gateway` absent / false) |
|---|---|---|
| Public identity | Has a **fixed** `PeerId(transport_pubkey, (public_address, public_port))`. Both `--public-network-address` **and** `--public-network-port` are **mandatory** (validation errors if missing). | **None** by default (`peer_id == None`). Learns its external socket from the network. |
| Inbound P2P | **Accepts inbound connections**; others dial it. Skips the peer-cache ("peers connect to them"). | Does **not** accept/serve inbound as an anchor. |
| Bootstraps a ring? | Yes — can seed a **brand-new ring** (with `--skip-load-from-network` it runs **fully isolated**, never meshing with production). | **No** — must dial one or more seed gateways to join an existing ring. |
| To join a network | Optional (it *is* an anchor) | **Required:** `get_gateways()` errors "At least one remote gateway is required to join an existing network" unless it has a public identity or is a gateway. |

Rule of thumb:
- **Joining the public mainnet / an existing ring** → run the node as a **client peer**
  (`is_gateway:false`, no public address, `skip_load_from_network:false`). This is the "normal peer"
  posture that reproduces how real users connect.
- **Hosting an anchor / starting a private deterministic mesh** → run a small number as **gateways**
  on loopback with a pinned `--location`, and let the rest be client peers that `--gateway` them.

## Bootstrap seed gateways — where they come from

A node that is joining (non-gateway, or a gateway that wants to mesh) needs a list of `GatewayConfig
{ address, public_key_path, location }` seed peers. Resolution order in `Config::build()`:

1. `OperationMode::Local` (`freenet local`, single-node testing) → **no seeds**, no external peers
   (`UpdateNotification` is not dispatched to subscribers).
2. Network mode, not `--skip-load-from-network` → fetch the **remote gateway index**
   (default `https://freenet.org/keys/gateways.toml`) over HTTPS and **replace** the on-disk cache
   (warns about dropped pinned peers, #4275). This is how a fresh peer genuinely joins mainnet.
3. `--skip-load-from-network` (isolated) → do **not** fetch the index: use the on-disk
   `gateways.toml` cache, **unless** an explicit `--gateway`/`--gateways` is given, in which case the
   CLI entries **replace** the cache (strictly additive, #3980).

Explicit `--gateway "ip:port,hex-pubkey"` dials a **specific** seed peer — the format is
`socket + ',' + 64-hex X25519 public key` (the key is written to a secrets file and parsed by
`parse_gateway`). It is the primary tool for a same-machine / hermetic test mesh.

## The flags (from `NetworkArgs`)

| Flag | Meaning |
|---|---|
| `--network-address` | IP to **bind** the UDP network listener (default dual-stack). |
| `--network-port` | UDP **bind** port for the listener (default 31337). |
| `--public-network-address` | Advertised address → feeds `PeerId`. Required for gateways. |
| `--public-network-port` | Advertised port → feeds `PeerId`. Required for gateways. |
| `--is-gateway` | Accept/serve inbound P2P; hold a public identity; may seed a ring. |
| `--skip-load-from-network` | Don't fetch the remote gateway index (isolated/hermetic). |
| `--gateway ip:port,hex-pubkey` | Dial a specific seed gateway (repeatable). |
| `--gateways <json>` | Hidden `InlineGwConfig` JSON mesh injection (deterministic tests). |
| `--location` | Pin a node/gateway's ring location (deterministic tests). |
| `--min/--max-number-of-connections` | Ring degree targets (defaults 10/20). |
| `--min-active-connections` | Bootstrapping readiness target (e.g. `wait_ready`). |

## Why peers "discover each other via Freenet" — the mental model

There is **no central registry and no address exchange**. Two nodes "see" each other (share a
contract) if and only if:

1. They are members of the **same ring** (they bootstrapped from the same seed gateways / the same
   index → they share routing toward key locations), and
2. Their operations on the same key **route to the same responsible replica**(s).

So "all three connect" for a contract **requires all three nodes to have joined the same ring.**
Three nodes launched as **isolated gateways** (`--is-gateway` + `--skip-load-from-network`, no
`--gateway`) each **seed their own disjoint ring** — three separate universes that can never find
each other. That is not a network race; it is a trivial non-connection. If your harness "isn't
converging," check this first: are the nodes even in the same ring?

## The fresh-key Put race (cold-start seed) — verified root cause

Even inside a shared ring, the **first `Put` of a brand-new key** is a race. Verified against
freenet 0.2.101 source (`operations/put/op_ctx_task.rs`, `operations/update.rs`, `node.rs`):

- Each node's `Put` **stores locally first**, then relays `PutMsg::Request` along **its own greedy
  route** (`ring.closest_potentially_hosting`), which depends on that node's learned routing state.
  Three nodes started independently → three different routing states → the Put chains can
  terminate at different nodes. The code itself documents this failure mode ("the network splits
  into divergent state groups", `op_ctx_task.rs:2521-2527`).
- There is **no node-side state versioning, no LWW, no ring-wide conflict resolution**. Merging
  only happens when relay chains physically intersect (the contract's `update_state` then decides).
- **Anti-entropy is not a global reconciler.** It is the `Ring::interest_heartbeat`
  (`ring/interest.rs`, `INTEREST_HEARTBEAT_INTERVAL = 300s`): a **5-minute exchange between
  directly-connected neighbors with matching registered interests**. On summary mismatch
  (byte-equality compare, `node.rs:2698-2701`) it heals via targeted `SyncStateToPeer`.
  Nodes not connected to each other, or holding the contract without a matching registered
  interest summary, **never converge through it**. Peers with a `None` summary are explicitly
  skipped (`update.rs:310-315`). There is no multi-hop, location-scoped, or periodic ring-wide
  re-sync anywhere in 0.2.101.
- Symptom timeline (observed repeatedly on mainnet): the split singleton heals at **~280-360s**
  after its node joins the ring — the heartbeat discovering a hosting neighbor — no matter how
  many client-level retries fire in between.

### Client-side bridge recovery (the mitigation that works on mainnet)

Two "obvious" client retries are **ineffective**, measured repeatedly:

- **Get-with-subscribe re-issued from a hosting node answers locally** (the node serves its own
  replica without hitting the network) — zero bridging effect.
- **Re-`Put` of the current state** relays via the gateway and typically ends in
  `put: attempt timed out (90s)` without reaching the other replica group. (It is harmless —
  idempotent merge — but it does not heal.)

What **does** bridge, verified on mainnet (heal in ~10-60s vs ~300s):

- Send a routed **`ContractRequest::Subscribe { key, summary: Some(per_tag_summary) }`** from the
  client. The node's subscribe path (`operations/subscribe.rs`) routes toward the key and seeds the
  subscriber's baseline state via a **remote subscribe-GET**, plugging the node into the other
  replica group's broadcast tree. With a per-tag summary (matching `summarize_state`) the delta
  reconciliation is exact.
- Arm the bridge on two conditions: (a) **no foreign slot ever seen**, and (b) **foreign values
  stopped advancing** — merged nodes can have a *frozen notification stream* (`BROADCAST_NO_TARGETS`,
  no co-host advertisement) while the network has already merged. Track the sum of foreign slot
  values and refresh the "last foreign activity" timestamp only when it changes.
- Cadence ~30s works; the subscribe leg must have a timeout (the response can lag) so the client
  tick loop is not starved.

Still true from before: a stable/persistent contract key sidesteps the race entirely, but a
fresh-key + bridge design is the honest deployment posture — the bridge recovers the race within
seconds-to-a-minute, which is what "friends cold-starting the same app" actually needs.

## Reproducing mainnet vs hermetic in a harness

- **Real mainnet (how different peers actually connect):** spawn each node as a **client peer**
  (`is_gateway:false`, `skip_load_from_network:false`, no public address) so all bootstrap from the
  public index and join the production ring. Add a per-run unique contract param so each run targets
  a **fresh key** (a fixed empty-params key already exists on mainnet → everyone `Get`-succeeds and
  the fresh-key race can't manifest — but that also stops exercising the cold-start path real users
  hit; keep fresh keys if that's the scenario under test, and bridge splits via
  `ContractRequest::Subscribe` as described above).
- **Hermetic deterministic mesh (fast, same-machine):** one node = isolated gateway
  (`--is-gateway --skip-load-from-network --public-network-address 127.0.0.1 --public-network-port P
  --network-port P`); the others = client peers with `--gateway 127.0.0.1:P,<gw-pubkey-hex>`.
  Deterministic, no internet flakiness, still reproduces the Put race.

## Troubleshooting

| Symptom | Causes / fix |
|---|---|
| "Gateway nodes must specify a public network port" | `--is-gateway` without `--public-network-port` (and address). Both are mandatory (validation). |
| "Cannot initialize node without gateways" | Non-gateway, no public identity, index unreachable + empty cache + no `--gateway`. Provide seeds or make it a gateway. |
| "At least one remote gateway is required to join an existing network" | Client peer booted with no seed gateways. Add `--gateway` or drop `--skip-load-from-network` so it fetches the index. |
| "Gateway running in isolated mode" | `--is-gateway + --skip-load-from-network` with no seeds → intentionally disjoint ring. Add `--gateway`(s) to mesh it. |
| `wait_ready` times out bootstrapping mainnet | Mainnet can refuse gateway dials for minutes. Retry with capped backoff (see the freenet examples' embedded-node loop). |
| Fresh-key replicas split; each seeder sees only its own writes | Concurrent `Put`s of the same new key seeded disjoint replica groups. Client-driven bridge: routed `ContractRequest::Subscribe { key, summary }` every ~30s from each seeder heals in ~10-60s; a local `Get` re-check never bridges (answered locally), and re-`Put`s time out. See the fresh-key Put race section. |
| Replica merged but client counts frozen; node logs `BROADCAST_NO_TARGETS` | Node's subscription is stale — no co-host advertisement in its broadcast targets. The client's foreign slots stop advancing while peers tick. Re-issue `ContractRequest::Subscribe` (the routed subscribe re-plugs the node into the replica tree) and only refresh foreign-activity timestamps when foreign *values* change. |
| Node converges to "everyone Get-succeeds, no race" | The contract key already exists (deterministic empty params). Use unique per-run params to exercise a fresh-key seed. |
| Self-connections / wrong own address | Gateway advertises from `public_address`+`public_port`; ensure these are the reachable address (loopback for hermetic). |
| Node never joins ring behind a VPN/datacenter NAT; node logs `RING_TRANSPORT_DESYNC: transport has connections but ring topology is empty`, `ring_connections=0` for minutes, dials to regular peers fail `OutboundFailed: max connection attempts reached` while gateway links stay `is_transient=true` | Symmetric/datacenter NAT breaks hole-punching to regular peers, so the node keeps only transient gateway links that are never promoted. Verified with a ProtonVPN (M247) exit: send-path works (state propagates via gateway relays) but the node can't receive — subscriptions/updates never route back. Not fixable app-side; needs a NAT that permits hole-punching or a VPN with port forwarding. |

## References
- Official manual, P2P network & architecture:
  <https://freenet.org/build/manual/architecture/p2p-network/>
- Gateway index: <https://freenet.org/keys/gateways.toml>
- `freenet` crate source: `NetworkArgs`/`Config::build` in `config.rs`, node roles in `node.rs`,
  ring/ConnectionManager in `ring/` (the exact semantics current for freenet 0.2.101+).
- Companion deep-dive: `references/ring-and-discovery.md` (this skill directory).