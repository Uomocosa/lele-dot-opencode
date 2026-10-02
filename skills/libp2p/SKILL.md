---
name: libp2p
description: Use when establishing direct p2p connections with rust-libp2p (SwarmBuilder, transports, stream protocols). Docs links plus the patterns we use here — identity bridge from our ed25519 keys and polling the Swarm from Bevy.
---

# libp2p — P2P Networking Patterns

**Target: libp2p 0.56.** Check [releases](https://github.com/libp2p/rust-libp2p/releases) for
version history.

## Docs & examples

| Topic | URL |
|-------|-----|
| API docs (Swarm, SwarmBuilder, behaviours) | `https://docs.rs/libp2p` |
| Upstream examples (ping, request-response, …) | `https://github.com/libp2p/rust-libp2p/tree/master/examples` |
| Repository / releases | `https://github.com/libp2p/rust-libp2p` |
| Specification (protocols, transports) | `https://github.com/libp2p/specs` |
| Feature flags | `https://docs.rs/crate/libp2p/latest/features` |

## Minimal swarm

```rust
use libp2p::{noise, tcp, yamux};

let mut swarm = libp2p::SwarmBuilder::with_new_identity()
    .with_tokio()
    .with_tcp(tcp::Config::default(), noise::Config::new, yamux::Config::default)?
    .with_dns()?
    .with_behaviour(|_| ping::Behaviour::default())
    .map_err(|e| std::io::Error::other(e.to_string()))?
    .with_swarm_config(|cfg| {
        cfg.with_idle_connection_timeout(std::time::Duration::from_secs(u64::MAX))
    })
    .build();
```

`Cargo.toml`: `libp2p = { version = "0.56", features = ["tcp", "noise", "yamux", "tokio", "dns"] }`.

## How we use libp2p here

### Identity bridge (our ed25519 keys ↔ libp2p)

Both our identity layer and libp2p use ed25519; the same seed derives both, binding our node
identity and `PeerId` cryptographically.

```rust
use libp2p::identity::Keypair;

fn bridge_identity(secret_bytes: &[u8; 32]) -> Option<Keypair> {
    Keypair::ed25519_from_bytes(secret_bytes).ok()
}

let mut swarm = libp2p::SwarmBuilder::with_existing_identity(libp2p_kp)
    .with_tokio()
    // ... rest of builder
    .build();
```

### Stream framing (real-time data)

A `Stream` implements `AsyncRead` + `AsyncWrite`; use a length-prefixed `bincode` frame.

```rust
let bytes = bincode::serialize(pos)?;
stream.write_all(&(bytes.len() as u32).to_be_bytes()).await?;
stream.write_all(&bytes).await?;
```

### Bevy integration — poll the Swarm on one thread

`Swarm` is `!Sync`. Spawn the tokio runtime on a background thread; the swarm loop sends events
over an `mpsc` channel that a Bevy system drains.

```rust
let (tx, rx) = tokio::sync::mpsc::unbounded_channel();
std::thread::spawn(move || {
    let rt = tokio::runtime::Runtime::new()?;
    rt.block_on(async move {
        let mut swarm = build_swarm().await;
        loop {
            let event = swarm.select_next_some().await;
            tx.send(event).ok();
        }
    });
});
```

```rust
fn poll_swarm_events(events: Res<EventChannel<SwarmEvent>>) {
    while let Ok(event) = events.rx.try_recv() {
        // translate to Bevy Messages
    }
}
```

Prefer the built-in `request_response` behaviour over a hand-written `ConnectionHandler` for
simple req/res protocols.
