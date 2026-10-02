---
name: reqwest-rs
description: Use when making HTTP requests with reqwest in Rust. Docs links, upstream examples, and a few gotchas.
---

# reqwest-rs — HTTP Client

Async `Client` (tokio) by default, opt-in `blocking` API. JSON, forms, multipart, redirects,
proxies, cookies, TLS, WASM.

## Docs & examples

| Topic | URL |
|-------|-----|
| API docs | `https://docs.rs/reqwest` |
| Repository | `https://github.com/seanmonstar/reqwest` |
| Upstream examples | `https://github.com/seanmonstar/reqwest/tree/master/examples` |
| Feature flags | `https://docs.rs/crate/reqwest/latest/features` |
| Rust cookbook (web clients) | `https://rust-lang-nursery.github.io/rust-cookbook/web/clients.html` |

## Minimal example

```rust
let client = reqwest::Client::builder()
    .timeout(std::time::Duration::from_secs(10))
    .build()?;

let body = client.get("https://httpbin.org/get")
    .query(&[("foo", "bar")])
    .send().await?
    .error_for_status()?
    .text().await?;
```

`Cargo.toml`: `reqwest = { version = "0.12", features = ["json"] }` + a tokio runtime.

## Gotchas

- Reuse one `Client` (connection pooling); `reqwest::get` in a loop exhausts sockets.
- Pick one runtime: async `Client` or `reqwest::blocking::Client`. Never block inside `#[tokio::main]`/`#[tokio::test]`.
- `json()` / `.json()` need `features = ["json"]`; `form()` needs `form`; `multipart` needs `multipart`.
- `rustls` vs `native-tls`: enable only one `default-tls` provider.
- WASM ignores `timeout`, `cookie_store`, and TLS config — the browser owns them.
