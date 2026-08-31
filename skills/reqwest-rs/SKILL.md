---
name: reqwest-rs
description: Use when making HTTP requests with reqwest in Rust. Covers async Client/ClientBuilder, blocking client, RequestBuilder/Response, JSON/form/multipart, TLS features, redirect/proxy/cookie/timeout config, and error handling. Works with any Rust project.
---

# reqwest-rs — HTTP Client (reqwest)

Ergonomic, batteries-included HTTP client. Async `Client` (tokio) by default plus opt-in `blocking` API. Handles JSON, urlencoded forms, multipart, redirects, proxies, cookies, TLS, and WASM. Docs-only skill; no config file template is needed.

## Sources

| Topic | URL |
|-------|-----|
| Crate page (v0.12, MSRV 1.75, edition 2021) | `https://crates.io/crates/reqwest` |
| API docs (Client, RequestBuilder, Response, blocking, tls, redirect, cookie, multipart, proxy) | `https://docs.rs/reqwest` |
| Feature flags (24 flags, 4 defaults) | `https://docs.rs/crate/reqwest/latest/features` |
| Repository / examples / changelog | `https://github.com/seanmonstar/reqwest` |
| Cargo manifest (features, optional deps, MSRV) | `https://github.com/seanmonstar/reqwest/blob/master/Cargo.toml` |
| Cookbook (web clients) | `https://rust-lang-nursery.github.io/rust-cookbook/web/clients.html` |

## 1. Installation

```toml
# Cargo.toml
[dependencies]
reqwest = { version = "0.12", features = ["json"] }
tokio = { version = "1", features = ["full"] } # required for async Client
```

```bash
cargo add reqwest --features json
cargo add tokio --features full
```

MSRV 1.75. Pure Rust crate with TLS via `rustls-tls` (aws-lc-rs) by default — no `devenv.nix` package needed. For `native-tls` on Linux, add `pkgs.openssl` + `pkgs.pkg-config` to `devenv.nix: packages` unless `native-tls-vendored` is used.

### Feature flags (from `Cargo.toml: [features]`)

| Feature | Enables | Notes |
|---------|---------|-------|
| `default` | `default-tls` + `charset` + `http2` + `system-proxy` | Default set |
| `default-tls` | `rustls-tls` (via `__rustls-aws-lc-rs` + `rustls-platform-verifier`) | Default TLS; swap for `native-tls` |
| `rustls-tls` | `hyper-rustls` + `tokio-rustls` + `rustls` + platform verifier (`aws-lc-rs`) | Primary rustls feature in 0.12 (alias `rustls` also exists) |
| `rustls-tls-webpki-roots` / `rustls-tls-manual-roots` | `rustls-tls` + root store choice | WebPKI roots (default) vs manual roots |
| `rustls-no-provider` | rustls without crypto provider (bring your own) | Advanced |
| `native-tls` / `native-tls-vendored` | `hyper-tls` + `native-tls-crate` + `tokio-native-tls` | OS TLS; `-vendored` builds OpenSSL |
| `json` | `serde` + `serde_json` | `RequestBuilder::json` / `Response::json` |
| `form` / `query` | `serde` + `serde_urlencoded` | `form()` / `query()` serialization |
| `multipart` | `mime_guess` + `futures-util` | `multipart::Form` (`blocking::multipart::Form` has no `.file().await` — use `Part::bytes`) |
| `blocking` | `futures-channel` + `futures-util` + `tokio/sync` | `reqwest::blocking::Client` |
| `cookies` | `cookie` + `cookie_store` | `ClientBuilder::cookie_store(true)` |
| `charset` (default) | `encoding_rs` + `mime` | `Response::text()` charset decoding |
| `http2` (default) | `h2` + hyper http2 | HTTP/2 |
| `system-proxy` (default) | `hyper-util/client-proxy-system` | System proxy auto-detect (disabled when `default-features = false`) |
| `gzip` / `brotli` / `zstd` / `deflate` | `tower-http` decompression | Response decompression |
| `stream` | `tokio-util` + `futures-util` + `wasm-streams` + `tokio/fs` | `Response::bytes_stream()` |
| `socks` | — | SOCKS5 proxy (`socks5://`) |
| `hickory-dns` | `hickory-resolver` + `once_cell` | Async DNS resolver over `getaddrinfo` |
| `http3` (unstable) | `h3` + `h3-quinn` + `quinn` + `rustls` | Requires `RUSTFLAGS="--cfg reqwest_unstable"` |

Disable defaults to slim: `reqwest = { version = "0.12", default-features = false, features = ["rustls-tls"] }`.

## 2. Quick Start

### Single GET (shortcut)

```rust
let body = reqwest::get("https://www.rust-lang.org")
    .await?
    .text()
    .await?;
println!("body = {body:?}");
```

Reuse `Client` for multiple requests (connection pooling via keep-alive):

```rust
use std::collections::HashMap;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let resp = reqwest::get("https://httpbin.org/ip")
        .await?
        .json::<HashMap<String, String>>()
        .await?;
    println!("{resp:#?}");
    Ok(())
}
```

## 3. Client & ClientBuilder

```rust
use std::time::Duration;
use reqwest::{Client, redirect};

let client = Client::builder()
    .user_agent("my-app/1.0")
    .timeout(Duration::from_secs(10))
    .connect_timeout(Duration::from_secs(5))
    .redirect(redirect::Policy::limited(5))
    .cookie_store(true) // requires `cookies` feature
    .build()?;
```

Key `ClientBuilder` methods (`https://docs.rs/reqwest/latest/reqwest/struct.ClientBuilder.html`):

| Method | Purpose |
|--------|---------|
| `timeout(Duration)` | Total request timeout (incl. body) |
| `connect_timeout(Duration)` | TCP connect timeout |
| `pool_idle_timeout(Duration)` / `pool_max_idle_per_host(usize)` | Connection pool tuning |
| `redirect(Policy)` | `Policy::none()` / `limited(n)` / `custom(fn)` |
| `cookie_store(bool)` | Enable session cookies |
| `default_headers(HeaderMap)` | Headers on every request |
| `user_agent(String)` | Default User-Agent |
| `proxy(Proxy)` / `no_proxy()` | Proxy override / disable system proxies |
| `danger_accept_invalid_certs(bool)` / `add_root_certificate(Certificate)` | TLS overrides |
| `identity(Identity)` | Client certificate (mTLS) |
| `https_only(bool)` | Reject http URLs |
| `http2_prior_knowledge()` / `http1_title_case_headers()` | Protocol tweaks |
| `connector_layer(tower::Layer)` | Custom connector (tower) |

`Client::new()` == `ClientBuilder::default().build()`. Clone is cheap (Arc internally).

WASM: `timeout()`, `connector_layer()` and several builder methods are unavailable; TLS/cookies/proxy provided by browser.

## 4. Requests (RequestBuilder)

```rust
let client = reqwest::Client::new();

// GET with query + headers + bearer auth
let res = client.get("https://httpbin.org/get")
    .query(&[("foo", "bar"), ("baz", "quux")]) // requires `query` feature or manual
    .header("X-Custom", "value")
    .bearer_auth("token123")
    .send()
    .await?;

// POST raw body
let res = client.post("http://httpbin.org/post")
    .body("the exact body that is sent")
    .send()
    .await?;

// POST JSON (requires `json` feature + Serialize)
let mut map = std::collections::HashMap::new();
map.insert("lang", "rust");
let res = client.post("http://httpbin.org/post")
    .json(&map)
    .send()
    .await?;

// POST form (requires `form` feature + Serialize)
let params = [("foo", "bar"), ("baz", "quux")];
let res = client.post("http://httpbin.org/post")
    .form(&params)
    .send()
    .await?;

// Multipart (requires `multipart` feature)
let form = reqwest::multipart::Form::new()
    .text("key", "value")
    .file("file", "/tmp/foo.txt").await?;
let res = client.post("http://httpbin.org/post")
    .multipart(form)
    .send()
    .await?;
```

`RequestBuilder` is consumed by `send().await`. For manual control: `client.get(url).build()?` → `Request`, then `client.execute(request).await?`. Implements `IntoUrl` for `String`, `&str`, `Url`.

Optional `retry` module (`https://docs.rs/reqwest/latest/reqwest/retry/index.html`, not WASM): tower retry policy for idempotent requests.

## 5. Responses

```rust
let resp = client.get("https://httpbin.org/get").send().await?;

// Status & headers
let status = resp.status(); // reqwest::StatusCode (re-export of http::StatusCode)
let headers = resp.headers();
resp.error_for_status_ref()?; // Err if 4xx/5xx (borrowed)
let resp = resp.error_for_status()?; // consuming variant

// Bodies
let text: String = resp.text().await?; // charset-aware via `charset` feature
// let bytes: bytes::Bytes = resp.bytes().await?;
// let json: MyType = resp.json::<MyType>().await?; // requires `json`
// let stream = resp.bytes_stream(); // requires `stream` feature

// Streaming to file (stream feature)
use futures_util::StreamExt;
use tokio::io::AsyncWriteExt;
let mut stream = resp.bytes_stream();
while let Some(chunk) = stream.next().await {
    // write chunk?
}
```

`Response` fields: `url()`, `remote_addr()`, `content_length()`, `cookies()` (with `cookies`), `version()`. `StatusCode::is_success()` / `is_client_error()` helpers.

## 6. Blocking Client

> **Rule**: pick one runtime mode. `reqwest::Client` (async, needs `tokio`) **or** `reqwest::blocking::Client` (sync, needs `features = ["blocking"]`). Do not mix — `blocking` inside `#[tokio::main]` / `#[tokio::test]` blocks the executor. If you are already in `tokio`, stay async or use `tokio::task::spawn_blocking(|| blocking_client.get(...).send())`.

```rust
// Cargo.toml: reqwest = { version = "0.12", features = ["blocking", "json"] }
let resp = reqwest::blocking::get("https://httpbin.org/ip")?
    .json::<std::collections::HashMap<String, String>>()?;

let client = reqwest::blocking::Client::new();
let text = client.get("https://www.rust-lang.org").send()?.text()?;
```

Same builder API under `reqwest::blocking::ClientBuilder`. Reuse one blocking client (connection pooling) and keep it out of `tokio` contexts.

## 7. Advanced Topics

### Redirects

```rust
use reqwest::redirect;
let client = reqwest::Client::builder()
    .redirect(redirect::Policy::custom(|attempt| {
        if attempt.previous().len() > 3 { attempt.stop() } else { attempt.follow() }
    }))
    .build()?;
```

Default: 10 hops. `Policy::none()` to disable.

### Proxies

System proxies (`HTTP_PROXY`/`http_proxy`, `HTTPS_PROXY`/`https_proxy`, `ALL_PROXY`/`all_proxy`, `NO_PROXY`) enabled by default via `system-proxy`. Override:

```rust
let proxy = reqwest::Proxy::http("https://secure.example")?;
let client = reqwest::Client::builder().proxy(proxy).build()?;
let client = reqwest::Client::builder().no_proxy().build()?; // disable
// SOCKS: export https_proxy=socks5://127.0.0.1:1086  (requires `socks` feature)
```

See `examples/tor_socks.rs`.

### TLS

Default is `rustls` (aws-lc-rs). Alternatives:

```toml
reqwest = { version = "0.12", default-features = false, features = ["native-tls", "json"] }
# or vendored OpenSSL:
reqwest = { version = "0.12", default-features = false, features = ["native-tls-vendored"] }
```

```rust
use reqwest::tls;
let cert = tls::Certificate::from_pem(&std::fs::read("ca.pem")?)?;
let identity = tls::Identity::from_pkcs12_der(&std::fs::read("client.p12")?, "password")?;
let client = reqwest::Client::builder()
    .add_root_certificate(cert)
    .identity(identity)
    .danger_accept_invalid_certs(false)
    .build()?;
```

Module `reqwest::tls` (`https://docs.rs/reqwest/latest/reqwest/tls/index.html`) holds `Certificate`/`Identity`.

### Cookies

```rust
let client = reqwest::Client::builder().cookie_store(true).build()?;
```

`resp.cookies()` iterates `Cookie` (`https://docs.rs/reqwest/latest/reqwest/cookie/index.html`).

### WASM

When `target_arch = "wasm32"` + `target_os = "unknown"`, `Client` wraps `window.fetch` / ServiceWorker. Same async API but no `blocking`, `cookie`, `tls` config, `timeout`, `connector_layer`. See `https://docs.rs/reqwest/latest/reqwest/#wasm`.

### HTTP/3 (unstable)

```toml
reqwest = { version = "0.12", features = ["http3"] }
```
```bash
RUSTFLAGS="--cfg reqwest_unstable" cargo build
```
See `examples/h3_simple.rs`.

## 8. Error Handling

```rust
let res = client.get("https://httpbin.org/status/404").send().await;
match res {
    Ok(resp) => match resp.error_for_status() {
        Ok(ok) => println!("ok: {}", ok.status()),
        Err(e) => eprintln!("http error: {e} status={:?}", e.status()),
    },
    Err(e) if e.is_timeout() => eprintln!("timeout: {e}"),
    Err(e) if e.is_connect() => eprintln!("connect: {e}"),
    Err(e) if e.is_redirect() => eprintln!("redirect loop: {e}"),
    Err(e) => eprintln!("other: {e} url={:?}", e.url()),
}
```

`reqwest::Error` helpers: `is_timeout`, `is_connect`, `is_redirect`, `is_request`, `is_body`, `is_decode`, `status()`, `url()`, `source()`. Body decode errors surface on `text()`/`json()`.

## 9. Pitfalls

- Missing `tokio` runtime → `Client` panics at `send().await` without `#[tokio::main]` or `Runtime`. Always run async reqwest inside tokio.
- Forgetting `features = ["json"]` → `RequestBuilder::json` / `Response::json` not found.
- Using `reqwest::get` in a loop without reusing `Client` → no connection pooling, socket exhaustion. Reuse one `Client`.
- `rustls` vs `native-tls` feature conflict — pick one `default-tls` provider; enabling both pulls both stacks.
- `blocking::Client` inside `#[tokio::main]` / `#[tokio::test]` → blocks executor thread; use `tokio::task::spawn_blocking` or stay async (see §6 rule).
- `danger_accept_invalid_certs(true)` in production — disables verification.
- `redirect::Policy::none()` without handling `3xx` — manual follow required.
- WASM target silently ignores `timeout`, `cookie_store`, TLS config — configure via browser instead.
- `.text().await` without `charset` feature → incorrect decoding for non-UTF8 bodies.
- HTTP/3 requires `--cfg reqwest_unstable` — without it the `http3` feature is a no-op.
- `httpbin.org` examples fail offline — mock with `wiremock`/`mockito` in tests.
