# Connection timing: what freenet does and what we measured

Measured on mainnet in `freenet-libp2p-bevy-plugin`, freenet 0.2.155, 2026-11-06. Source facts are from
that version; recheck them after a bump. App comparison: River at commit `b78f81f`.

## What the node does

- **`ring_peers` and `transport_peers` differ.** `transport_peers=2` with `ring_peers=0` means the node
  is connected to the gateways but has not joined the ring.
- **Client requests work before the ring join.** `peer_ready` is set when the gateway handshake
  completes. With an empty ring a `Get` is routed through the gateway. Before the handshake, a
  subscribing `Get` fails at once with `PeerNotJoined`.
- **Shipped apps do not wait for the ring.** River, mail, delta and freenet-ping's app gate on the
  socket at most; only freenet-ping's tests poll diagnostics.
- **Every operation has a hardcoded 60s TTL** (`OPERATION_TTL`). A `Get` goes to one peer; if that
  peer never answers, nothing else happens until the TTL ends.
- **`NotFound` can fail to arrive**, even on a key nobody holds. Never make "heard `NotFound`" the only
  way to publish.
- **Client `Get`s are not deduplicated** in 0.2.155: each gets a fresh transaction, so a resend is a
  real new attempt.
- **`return_contract_code: false` only changes what the client receives.** The node still fetches
  the wasm over the network.
- **64 KB is a streaming threshold, not a limit.** Published contracts we measured are 110-988 KB.
  Size was not a visible slow factor: a 193 KB `Put` took 1.1s at p50.
- **The ring location comes from the public IP** (/24), so all nodes on one machine or LAN share one
  location.
- **The peer cache saves only after 30s of uptime**, never on shutdown, and expires after 300s. Runs
  shorter than 30s leave nothing to reconnect from.
- **One connection per key.** A relaunch with the same identity from a new port waits while a gateway
  still treats the old session as alive. A new handshake from the same address tears the old session
  down at once.
- **The `freenet` binary keeps its port** through `config.toml`. Passing `network_port: Some(..)`
  overrides that; pass `None` for a saved node folder.

## Timings to start from

| Purpose | Value | Source |
|---|---|---|
| Connect to the node | 5s | River `CONNECTION_TIMEOUT_MS` |
| Reconnect to the node | 3s doubling to 60s, +-20% jitter | River `RECONNECT_*_MS` |
| Silence before seeding a `Put` | 20s | River `REPUT_DELAY_MS` |
| `Put` response | 60s | River CLI `PUT_RESPONSE_TIMEOUT` |
| Waits on a `Get` with no fallback | above 60s | River: must exceed `OPERATION_TTL` |
| `blocking_subscribe` | `false` | River, everywhere |

20s and 40s of silence tied in an interleaved A/B, 8 runs each. `blocking_subscribe: false` was not
measurably faster; with it, `recv` code must skip a late `SubscribeResponse`.

## Measured behaviour

- Saved node folder: the relaunch finds its contract locally in under 1s and never deploys.
- Relaunch ring join after a 10s gap: about 60s on a random port; 14s at worst with the same port
  (those last runs also had a 90s pause between pairs). After 6 minutes: 3-5s.
- With 2+ deployers on a fresh key, a room took 35-126s to reach the slowest peer. A random delay
  before deploying lost its A/B: it added about 11s and did not reduce deployers.
- The slowest peer tends to see a room when it joins the ring.
- Ring joins of 60-100s remain, with no complete explanation. They happen more with several nodes
  on one machine, and also with a single node, more rarely.

## Testing on one machine

- **Sibling nodes distort joins.** Same public IP means same ring location, so a CONNECT can route to
  a sibling, which accepts and then fails to hole-punch to its own public IP. Treat N>=2 on one
  machine as pessimistic, and keep an N=1 check.
- **Back-to-back runs distort joins.** Paused 90s: 5 of 24 peers over 30s. No pause: 11 of 24 slow or
  never joined. Peers from the previous run have just exited. Keep a pause in loops.
- **Mainnet drifts between sessions.** One day's baseline had 0 of 15 stalls, the day before 4 of 12.
  Interleave A/B runs; do not compare against old numbers.
- **Pass/fail does not measure speed.** Record timings, and judge a change on those. "Lobby ready" can
  look fast while other peers cannot yet see a room, so also measure when everyone sees it.
- **Nested cargo inside a test** inherits `CARGO_MANIFEST_DIR`, which `ring`'s build script tracks, so
  it rebuilds about 27 crates on each run. Strip `CARGO_*` and `NEXTEST_*` from the inner command.
