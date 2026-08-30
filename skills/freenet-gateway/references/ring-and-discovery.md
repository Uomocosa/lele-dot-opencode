# Ring & discovery deep-dive (freenet 0.2.101+)

Supplementary detail for `freenet-gateway`. All file:line references are to the pinned
`freenet-0.2.101` crate source (`~/.cargo/registry/src/index.crates.io-*/freenet-0.2.101/`).

## Chord / small-world ring

- Key-space is `[0.0, 1.0)`. Each node holds a `Location`; each contract key maps to a `location`.
- A node belongs to the ring by forming `min_connections..max_connections` (default `10..20`)
  **neighbor** links to the nearest ring positions around its own location
  (`src/ring/connection_manager.rs`, `src/ring/location.rs`).
- Ops `Get`/`Put`/`Update` are routed hop by hop toward the peer(s) responsible for the key's
  location; the acceptor executes the contract's WASM and replies, and the response is routed back.
- **InterestSync** is the periodic anti-entropy heartbeat: a 5-min (`INTEREST_HEARTBEAT_INTERVAL`,
  `ring/interest.rs`) **neighbor-pair** exchange of interest hashes + hosting-state advertisements.
  On summary mismatch (byte-equality compare, `node.rs:2698-2701`) it heals via targeted
  `SyncStateToPeer`. It is **not** a ring-wide reconciler: it only reaches directly-connected
  neighbors with matching registered interests, skips `None`-summary peers (`update.rs:310-315`),
  and there is no multi-hop or location-scoped re-sync in 0.2.101. This is why a cold fresh-key
  `Put` race heals slowly (~300s after ring join, if the split nodes ever become connected
  neighbors) and why client-driven bridging (`ContractRequest::Subscribe { key, summary }`) is the
  fast recovery path.

## Peer identity (gateway vs client)

- `PeerId` is `transport_keypair.public() + (address, port)`; for a gateway that address/port come
  from `public-network-address` + `public-network-port`, both **required** by
  `NetworkApiConfig::validate()` (config.rs:1617).
- `peer_id` is derived by `public_address.zip(public_port)` (config.rs:590); `None` for a plain
  client peer.
- Each node's own ring `location` is `config.location` when pinned, else hashed from its address
  (`Location::from(...)`, `node.rs:491-493`, `ring/location.rs`).
- Seed peers become `InitPeerNode { peer_key_location, location }` (node.rs:415-494); a client peer
  **must** have at least one, else `get_gateways()` bails (node.rs:737-751).

## Bootstrap resolution (config.rs `Config::build`)

1. `OperationMode::Local` → empty gateways, no external peers.
2. Network and `!skip_load_from_network` → fetch `FREENET_GATEWAYS_INDEX`
   (`= "https://freenet.org/keys/gateways.toml"`, config.rs:79) and **replace** the on-disk cache,
   warning on dropped pinned peers (#4275).
3. `skip_load_from_network && is_gateway` → fully isolated (empty seeds) unless inline `--gateways`
   were provided.
4. `skip_load_from_network && !has_cli_gateways` → use on-disk `gateways.toml`; with
   `--gateway`(s), CLI entries **replace** the cache (#3980).
5. Otherwise fall back to `gateways.toml`; a non-gateway with no public identity and no seeds is
   rejected ("Cannot initialize node without gateways").
6. `--gateway "ip:port,hex-pubkey"` entries are parsed by `parse_gateway` and **prepended** (they win
   on address collision).