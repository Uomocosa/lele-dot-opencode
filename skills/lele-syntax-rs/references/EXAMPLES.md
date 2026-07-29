# Atomic File Structure Examples

These examples demonstrate the co-located domain pattern for a `Config` struct in a `p2p` domain module.

## Directory Layout

```
src/
  lib.rs                    # pub mod p2p; + re-exports
  p2p/
    mod.rs                  # module tree + public re-exports
    config.rs               # struct Config + Default + thin delegates
    config_new.rs           # fn new() -> Config + test_usage  (PRIVATE)
    config_coop.rs          # fn coop() -> Config + test_usage  (PRIVATE)
    config_with_timeout.rs  # fn with_timeout(cfg, ms) -> Config + test_usage  (PRIVATE)
    config_fmt.rs           # fn fmt(cfg, f) -> fmt::Result + test_usage  (PRIVATE)
```

## Module Declaration (`p2p/mod.rs`)

```rust
mod config;
mod config_new;
mod config_coop;
mod config_with_timeout;
mod config_fmt;

pub use config::Config;
```

Method modules are `mod` (private). Only the `Config` type is re-exported publicly.

## Struct File (`p2p/config.rs`)

```rust
use std::fmt;
use super::config_new;
use super::config_coop;
use super::config_with_timeout;
use super::config_fmt;

pub struct Config {
    pub timeout_secs: u64,
    pub enable_mdns: bool,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            timeout_secs: 30,
            enable_mdns: true,
        }
    }
}

#[rustfmt::skip]
impl Config {
    pub fn new() -> Self { config_new::new() }
    pub fn coop() -> Self { config_coop::coop() }
    pub fn with_timeout(self, ms: u64) -> Self { config_with_timeout::with_timeout(self, ms) }
}

#[rustfmt::skip]
impl fmt::Display for Config {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { config_fmt::fmt(self, f) }
}
```

## Method File — Constructor (`p2p/config_new.rs`)

```rust
use super::config::Config;

pub fn new() -> Config { Config::default() }

#[cfg(test)]
mod tests {
    use super::new;

    #[test]
    fn test_usage() {
        let config = new();
        assert!(config.enable_mdns);
        assert_eq!(config.timeout_secs, 30);
    }
}
```

## Method File — Named Default (`p2p/config_coop.rs`)

```rust
use super::config::Config;

pub fn coop() -> Config {
    Config {
        timeout_secs: 10,
        enable_mdns: false,
    }
}

#[cfg(test)]
mod tests {
    use super::coop;

    #[test]
    fn test_usage() {
        let config = coop();
        assert_eq!(config.timeout_secs, 10);
        assert!(!config.enable_mdns);
    }
}
```

## Method File — Builder (`p2p/config_with_timeout.rs`)

```rust
use super::config::Config;

pub fn with_timeout(cfg: Config, ms: u64) -> Config {
    Config {
        timeout_secs: ms,
        ..cfg
    }
}

#[cfg(test)]
mod tests {
    use super::with_timeout;
    use crate::p2p::Config;

    #[test]
    fn test_usage() {
        let config = with_timeout(Config::default(), 5000);
        assert_eq!(config.timeout_secs, 5000);
        assert!(config.enable_mdns);
    }
}
```

## Method File — Trait Method (`p2p/config_fmt.rs`)

```rust
use super::config::Config;
use std::fmt;

pub fn fmt(cfg: &Config, f: &mut fmt::Formatter<'_>) -> fmt::Result {
    write!(f, "Config(timeout: {})", cfg.timeout_secs)
}

#[cfg(test)]
mod tests {
    use crate::p2p::Config;

    #[test]
    fn test_usage() {
        let config = Config::default();
        let s = format!("{}", config);
        assert!(s.starts_with("Config"));
    }
}
```

## Grouped Example (user-chosen subfolder)

When the user decides to group `Config` files into a subfolder:

```
p2p/
  mod.rs
  config/
    mod.rs
    config.rs
    config_new.rs
    config_coop.rs
    config_with_timeout.rs
    config_fmt.rs
```

`p2p/mod.rs`:
```rust
pub mod config;     // subfolder — items NOT re-exported at p2p root
```

`p2p/config/mod.rs`:
```rust
mod config;
mod config_new;
mod config_coop;
mod config_with_timeout;
mod config_fmt;

pub use config::Config;
```

Consumer path: `use crate::p2p::config::Config;`

The struct file's thin delegates use the same `use super::*;` pattern relative to the `config/` folder. Method filenames keep the `<struct>_<method>.rs` convention inside the subfolder.
