---
name: freenet-rs
description: Freenet contract development — WASM contracts, WebSocket client protocol, node modes (local vs network), commutative monoid contract design, pub/sub, fdev/freenet-scaffold tooling, Makefile automation, integration testing, and common pitfalls.
---

# Freenet Development Guide

## Architecture

Freenet apps have three components:
- **Contract**: WASM module defining shared state + validation rules. Runs on untrusted peers.
- **Delegate**: WASM module with private state (keys, secrets). Runs on the user's own node only.
- **UI**: Web UI connecting to the local node via WebSocket. Can be TypeScript/Vite or Rust (Dioxus).

The client (CLI or UI) connects to the **local** freenet node via WebSocket at `127.0.0.1:7509`. Nodes communicate via P2P. The deterministic `ContractKey` routes requests globally — no IP sharing needed.

## Project Structure

```
my-app/
├── Cargo.toml              # Workspace definition
├── Makefile.toml           # Build tasks
├── contract/               # Contract implementation
│   ├── Cargo.toml
│   └── src/lib.rs
├── delegate/               # Delegate (optional)
│   ├── Cargo.toml
│   └── src/lib.rs
├── ui/                     # Web frontend (optional)
└── src/                    # Native client binary
```

## Node Modes

| Mode | Command | UpdateNotification | Use Case |
|------|---------|-------------------|----------|
| Local | `freenet local` | ❌ Skipped (`perform_contract_update` shortcut, no `commit_state_update` → no `send_update_notification`) | Single-client testing |
| Network | `freenet network --is-gateway --skip-load-from-network --public-network-address 127.0.0.1 --public-network-port 31337` | ✅ Full pipeline | Multi-client / cross-machine |

**Critical:** `freenet local` returns `UpdateResponse` immediately without calling `send_update_notification()`. Subscribers never receive `UpdateNotification`. Always use network mode for multi-client demos.

In network mode, the update goes through: `request_router → start_client_update → commit_state_update → send_update_notification`. The `BroadcastStateChange` to network peers (via `BROADCAST_NO_TARGETS`) is separate from local WebSocket notifications and requires peer connections.

## Contract Development

### Cargo.toml

```toml
[package]
name = "my-contract"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
freenet-stdlib = { version = "0.8", features = ["contract", "freenet-main-contract"] }
serde = { version = "1", features = ["derive"] }
bincode = "1"
```

The `freenet-main-contract` feature is **required** for the `#[contract]` macro to emit the WASM exports (`validate_state`, `update_state`, `summarize_state`, `get_state_delta`).

### Contract Implementation

```rust
use freenet_stdlib::prelude::*;

struct MyContract;

#[contract]
impl ContractInterface for MyContract {
    fn validate_state(
        parameters: Parameters<'static>,
        state: State<'static>,
        related: RelatedContracts<'static>,
    ) -> Result<ValidateResult, ContractError> { ... }

    fn update_state(
        parameters: Parameters<'static>,
        state: State<'static>,
        data: Vec<UpdateData<'static>>,
    ) -> Result<UpdateModification<'static>, ContractError> { ... }

    fn summarize_state(
        parameters: Parameters<'static>,
        state: State<'static>,
    ) -> Result<StateSummary<'static>, ContractError> { ... }

    fn get_state_delta(
        parameters: Parameters<'static>,
        state: State<'static>,
        summary: StateSummary<'static>,
    ) -> Result<StateDelta<'static>, ContractError> { ... }
}
```

### Commutative Monoid Requirement

Contract state must be mergeable regardless of order (join-semilattice):
- **Commutative**: merge order doesn't matter
- **Associative**: grouping doesn't matter  
- **Idempotent**: same update data → same result every time

`update_state` **must** use the update `data` to compute the new state, NOT increment from current `state`:

```rust
// ✅ CORRECT — reads new value from update data (idempotent)
fn update_state(data: Vec<UpdateData>) -> Result<UpdateModification> {
    let UpdateData::State(s) = data.into_iter().next() else { return Err(...) };
    let val = deserialize(s.as_ref())?;
    Ok(UpdateModification::valid(State::from(serialize(&val)?)))
}

// ❌ WRONG — increments from current state (non-idempotent)
fn update_state(data: Vec<UpdateData>) -> Result<UpdateModification> {
    let val = deserialize(state.as_ref())? + 1;  // IGNORES data!
    Ok(UpdateModification::valid(serialize(&val)?))
}
```

**Non-idempotent contracts are flagged as BROKEN** by the node. The broken flag persists across restarts in the DB. Clear with `rm -rf ~/.local/share/freenet/db`. Future versions may add TTL-based auto-recovery (PR #4306) or retire the probe entirely (issue #4320).

### freenet-scaffold (Complex State)

For complex state types, `freenet-scaffold` auto-generates `summarize`, `delta`, `apply_delta`, `merge`, and `verify`:

```rust
use freenet_scaffold_macro::composable;
use serde::{Deserialize, Serialize};

#[composable]
#[derive(Serialize, Deserialize, Clone, Default, PartialEq, Debug)]
pub struct AppState {
    pub field1: Type1,
    pub field2: Type2,
}
```

### Contract Unit Tests

Tests live in the same file after the implementation. No separate test directory.

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_usage() {
        let params = Parameters::from(Vec::new());
        let state = State::from(bincode::serialize(&0u64).unwrap());
        let update = vec![UpdateData::State(State::from(bincode::serialize(&42u64).unwrap()))];
        let result = MyContract::update_state(params, state, update);
        assert!(result.is_ok());
    }
}
```

### Build Contract

```bash
cargo build --release --target wasm32-unknown-unknown
```

## Client Development

### Cargo.toml

```toml
[package]
name = "my-client"
version = "0.1.0"
edition = "2021"

[dependencies]
freenet-stdlib = { version = "0.8", features = ["net"] }
tokio = { version = "1", features = ["rt", "sync", "macros", "rt-multi-thread", "time"] }
tokio-tungstenite = "0.27"
http = "1"
futures-util = "0.3"
tracing = "0.1"
tracing-subscriber = "0.3"
serde = { version = "1", features = ["derive"] }
bincode = "1"

[dev-dependencies]
freenet = "0.2"    # Only needed for integration tests
tempfile = "3"
```

**Important:** Put the full `freenet` crate in `[dev-dependencies]`, not `[dependencies]`. It pulls in `wasmtime` → `tikv-jemalloc-sys` which fails to build if the project path contains spaces (configure's `--prefix` rejects them).

### WebSocket Connection Protocol

**URL:** `ws://127.0.0.1:7509/v1/contract/command?encodingProtocol=native`

**Header:** `encoding-protocol: native`

**Serialization:** bincode (not flatbuffers). Both `ClientRequest` and `HostResponse` implement `Serialize`/`Deserialize`.

```rust
// Send
let bytes = bincode::serialize(&request)?;
ws_sink.send(Message::Binary(bytes.into())).await?;

// Receive
let bytes = match msg { Message::Binary(d) => d, _ => continue };
let response: HostResponse = bincode::deserialize(&bytes)?;
```

**5s timeout on connect:** `connect_async` can hang indefinitely. Wrap with `tokio::time::timeout(5s, ...)`.

### Client Operations

```rust
use freenet_stdlib::client_api::*;
use freenet_stdlib::prelude::*;

// Connect
let url = format!("ws://{host}:{port}/v1/contract/command?encodingProtocol=native");
let mut request = url.into_client_request()?;
request.headers_mut().insert("encoding-protocol", HeaderValue::from_static("native"));
let (ws_stream, _) = tokio::time::timeout(5s, connect_async(request)).await??;

// Put (deploy)
client.send(ContractRequest::Put {
    contract: ContractContainer::from(ContractWasmAPIVersion::V1(wrapped)),
    state: WrappedState::new(serialize(&0)?),
    related_contracts: RelatedContracts::default(),
    subscribe: true,
    blocking_subscribe: false,
}).await?;

// Get + Subscribe
client.send(ContractRequest::Get {
    key: *contract_key.id(),
    return_contract_code: false,
    subscribe: true,
    blocking_subscribe: true,
}).await?;

// Update
client.send(ContractRequest::Update {
    key: contract_key,
    data: UpdateData::State(State::from(serialize(&count)?)),
}).await?;
```

### No Request-Response Correlation

Messages arrive FIFO on a single channel. There is no request-response ID matching. When you send `Get { subscribe: true }`, you might receive:
1. An `UpdateNotification` from another client (before `GetResponse`)
2. Then the `GetResponse`

Always loop on recv and skip unexpected message types:

```rust
loop {
    match recv_with_timeout(client).await? {
        GetResponse { key, state } => break (key, state),
        UpdateNotification { .. } => continue,  // stray notification
        NotFound { .. } => { sleep(1s); continue; }  // retry or deploy
    }
}
```

### Counter Sync Pattern

```rust
loop {
    // Drain notifications, syncing local count with node state
    while let Some(msg) = recv_timeout(10ms) {
        match msg {
            UpdateNotification { update } => count = deserialize(update),
            UpdateResponse { .. } => {}  // just a confirmation
        }
    }
    count += 1;
    send(Update { data: State(serialize(count)) });
    sleep(1s);
}
```

## fdev Tool (Publishing)

`fdev` is the freenet developer tool, installed from the same repo as the node:

```bash
cargo install --path crates/fdev
```

Publish a contract to a local node:

```bash
fdev -p 7509 publish \
    --code target/wasm32-unknown-unknown/release/my_contract.wasm \
    contract \
    --state initial_state.cbor
```

Publish a web UI (served as a Freenet web container):

```bash
fdev website publish
```

## Makefile.toml Pattern

```toml
[tasks.build-contract]
command = "cargo"
args = ["build", "--release", "--target", "wasm32-unknown-unknown"]
cwd = "./contract"

[tasks.start-node]
command = "bash"
args = ["-c", "freenet network --is-gateway --skip-load-from-network --public-network-address 127.0.0.1 --public-network-port 31337 &"]

[tasks.wait-for-node]
command = "bash"
args = ["-c", "for i in $(seq 1 30); do curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:7509/ 2>/dev/null | grep -q '200\\|400\\|404' && break; sleep 1; done"]

[tasks.run]
dependencies = ["build-contract", "start-node", "wait-for-node", "run-client"]
```

## Integration Testing

Use `freenet::run_local_node()` to spin an in-process node. Requires `#[tokio::test(flavor = "multi_thread")]` for wasmtime's `spawn_blocking`.

```rust
#[tokio::test(flavor = "multi_thread")]
async fn test_e2e() {
    let temp_dir = tempfile::tempdir().unwrap();
    let config = ConfigArgs {
        mode: Some(OperationMode::Local),
        config_paths: ConfigPathsArgs {
            config_dir: Some(temp_dir.path().to_path_buf()),
            data_dir: Some(temp_dir.path().to_path_buf()),
            log_dir: Some(temp_dir.path().to_path_buf()),
        },
        ..Default::default()
    };
    let config = Arc::new(config.build().await.unwrap());
    let executor = Executor::from_config_local(config).await.unwrap();
    let ws_config = WebsocketApiConfig {
        address: IpAddr::V4(Ipv4Addr::LOCALHOST),
        port: 17510,  // Use non-default port to avoid conflicts
        ..Default::default()
    };
    tokio::spawn(async move { run_local_node(executor, ws_config).await });
    tokio::time::sleep(Duration::from_secs(2)).await;

    let mut client = FreenetClient::connect("127.0.0.1", 17510).await.unwrap();
    // ... test logic
}
```

## Delegate Pattern (Private State)

Delegates run on the user's node only. They store secrets and perform crypto.

```rust
struct MyDelegate;

#[delegate]
impl DelegateInterface for MyDelegate {
    fn process(
        parameters: Parameters<'static>,
        attested: Option<&'static [u8]>,
        message: InboundDelegateMsg,
    ) -> Result<Vec<OutboundDelegateMsg>, DelegateError> {
        match message {
            InboundDelegateMsg::ApplicationMessage(msg) => { ... }
            InboundDelegateMsg::GetSecretResponse(response) => { ... }
            _ => Ok(vec![]),
        }
    }
}
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Contract violates update_state idempotency" + "Marking contract as broken" | `update_state` ignores `data` and increments from `state` | Read new state from `data`, not `state` |
| No `UpdateNotification` received | Using `freenet local` | Switch to `freenet network --is-gateway ...` |
| Counter resets to 0 on restart | `Put { state: 0 }` overwrites existing state | Try `Get + subscribe` first; `Put` only on `NotFound` |
| "unexpected response to get: UpdateNotification { .. }" | Stray notification from other client arrives before GetResponse | Loop on recv, `continue` on `UpdateNotification` |
| `tikv-jemalloc-sys` configure fails (space in path) | Project path contains spaces | Move `freenet` crate to `[dev-dependencies]` |
| WebSocket connection hangs | `connect_async` blocks indefinitely | Add `tokio::time::timeout(5s, ...)` |
| "Module cache miss — compiling" on every run | WASM compilation cache cleared | Normal for first run; cached thereafter |
| `#[contract]` macro produces no WASM exports | Missing `freenet-main-contract` feature | Add `features = ["contract", "freenet-main-contract"]` |
| Contract state changes not persisted | Contract marked broken | `rm -rf ~/.local/share/freenet/db` |
| Multi-thread runtime required | wasmtime uses `spawn_blocking` | Use `#[tokio::test(flavor = "multi_thread")]` |

## Reference

- [Freenet Documentation](https://freenet.org/build/manual/)
- [freenet-stdlib docs.rs](https://docs.rs/freenet-stdlib)
- [freenet-scaffold](https://github.com/freenet/freenet-scaffold)
- [freenet-core](https://github.com/freenet/freenet-core)
- [River (reference app)](https://github.com/freenet/river)
- [freenet-ping (minimal Rust example)](https://github.com/freenet/freenet-core/tree/main/apps/freenet-ping)
- [Whitepaper (PDF)](https://freenet.org/pdf/freenet-whitepaper.pdf)
