---
name: jiff-rs
description: Use when handling dates/times with Jiff. Covers Zoned/Timestamp/civil types, Span durations, time zones, parsing/formatting (Temporal/RFC3339), and serde integration. Works with any Rust project.
---

# jiff-rs — Date-Time Library (Jiff)

Date-time library that encourages the pit of success. Inspired by Temporal (TC39). High-level primitives with DST-aware arithmetic, lossless zone-aware formatting, and automatic Time Zone Database integration. Docs-only skill; no config file template is needed.

## Sources

| Topic | URL |
|-------|-----|
| Crate page (v0.2.35) | `https://crates.io/crates/jiff` |
| API docs (Zoned, Timestamp, Span, civil, tz, fmt) | `https://docs.rs/jiff` |
| Book (usage, examples, features) | `https://docs.rs/jiff/latest/jiff/` |
| Comparison / design rationale / platform support | `https://github.com/BurntSushi/jiff/blob/master/COMPARE.md` / `DESIGN.md` / `PLATFORM.md` |
| Repository / changelog | `https://github.com/BurntSushi/jiff` |

## 1. Installation

```toml
# Cargo.toml
[dependencies]
jiff = "0.2"
```

```bash
cargo add jiff
```

MSRV 1.70. Crate features: `serde` (opt-in `Serialize`/`Deserialize` via Temporal RFC3339/9557/ISO8601 hybrid), `tz-system`/`tzdb-bundle`/`tzdb-zoneinfo` (time zone database), `std`/`alloc` variants. No `devenv.nix` package needed.

## 2. Core Types

| Type | Meaning |
|------|---------|
| `Zoned` | Primary type — time-zone-aware instant (timestamp + civil time + `tz::TimeZone` triple) |
| `Timestamp` | Instant as 96-bit nanoseconds since Unix epoch (precise, zone-free) |
| `civil::Date`, `civil::Time`, `civil::DateTime` | Inexact calendar/clock time ("civil"/"local"/"plain"/"naive") |
| `tz::TimeZone` | IANA zone rules (offset from UTC for a region) |
| `Span` | Duration mixing calendar + clock units (years, months, days, hours…); prefer over `SignedDuration` |
| `SignedDuration` | Signed 96-bit nanoseconds (like `std::time::Duration` but signed) |

`Zoned` = `Timestamp` + `civil::DateTime` + `TimeZone`; choose `Timestamp` for storage/comparison, `Zoned` for wall-time, `civil` for local intent.

## 3. Example

```rust
use jiff::{civil, Timestamp, Span};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let ts: Timestamp = "2024-08-10T23:14:00Z".parse()?;
    let zoned = ts.to_zoned(jiff::tz::TimeZone::get("America/New_York")?);
    let later = zoned.checked_add(2.hours())?;
    assert_eq!(later.to_string(), "2024-08-10T23:14:00-04:00[America/New_York]");
    assert_eq!(later.timestamp().to_string(), "2024-08-11T03:14:00Z");

    let span: Span = "2 years, 3 months".parse()?;
    let dt = civil::date(2024, 6, 15).at(12, 0, 0, 0);
    let zoned2 = dt.to_zoned(jiff::tz::TimeZone::UTC)?;
    let _ = zoned2.checked_add(span)?;
    Ok(())
}
```

Time Zone Database: Unix reads `/usr/share/zoneinfo` / `TZDIR` / `/etc/localtime`; Windows embeds or maps `GetDynamicTimeZoneInformation` via CLDR. No manual setup in most cases.

## 4. Parsing & Formatting

Temporal-specified hybrid format (best of RFC 3339 + RFC 9557 + ISO 8601) enables lossless round-tripping of `Zoned` and `Span`. `strptime`/`strftime` also available on all types (`Zoned::strptime`, `Zoned::strftime`). With `serde` feature, all types serialize as Temporal strings (see `fmt::temporal`).

## 5. Pitfalls

- Default to `Span` for durations; `SignedDuration` only for precise clock deltas.
- No `1.0` yet (0.2 line) — API may evolve; check `CHANGELOG.md` when upgrading.
- Serde support is opt-in (`features = ["serde"]`); without it, `Serialize`/`Deserialize` not implemented. Integer-timestamp serde requires `serde` + `jiff::fmt::serde` helpers.
- Prefer `checked_add` / DST-aware `SpanArithmetic` over raw arithmetic on wall time.
