---
name: jiff-rs
description: Use when handling dates/times with Jiff. Docs links, upstream examples, and a few gotchas.
---

# jiff-rs — Date-Time Library

Temporal-inspired date-time with DST-aware arithmetic, lossless zone-aware formatting, and
automatic Time Zone Database integration.

## Docs & examples

| Topic | URL |
|-------|-----|
| API docs | `https://docs.rs/jiff` |
| Book / usage | `https://docs.rs/jiff/latest/jiff/` |
| Repository / changelog | `https://github.com/BurntSushi/jiff` |
| Compare / design / platform | `https://github.com/BurntSushi/jiff/blob/master/COMPARE.md` / `DESIGN.md` / `PLATFORM.md` |

## Minimal example

```rust
use jiff::{civil, Timestamp, Span};

let ts: Timestamp = "2024-08-10T23:14:00Z".parse()?;
let zoned = ts.to_zoned(jiff::tz::TimeZone::get("America/New_York")?);
let later = zoned.checked_add(2.hours())?;
assert_eq!(later.to_string(), "2024-08-10T23:14:00-04:00[America/New_York]");
```

Key types: `Zoned` (zone-aware instant), `Timestamp` (zone-free), `civil::Date/Time/DateTime`
(local intent), `Span` (calendar + clock units), `SignedDuration` (precise signed delta).

## Gotchas

- Default to `Span` for durations; `SignedDuration` only for precise clock deltas.
- Prefer `checked_add` over raw arithmetic — DST-aware `SpanArithmetic`.
- Serde support is opt-in (`features = ["serde"]`).
- Still on the `0.2` line — check `CHANGELOG.md` before upgrading.
