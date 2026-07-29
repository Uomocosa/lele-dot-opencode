# Atomic File Structure Examples

These examples demonstrate the atomic file decomposition pattern for a `Config` struct with methods.

## Directory Layout

```
structs/p2p/
  config.rs             # struct + Default + thin delegate impl blocks
methods/p2p/
  config/
    mod.rs              # pub mod declarations + pub use flattening
    new.rs              # pub fn new() -> Config + tests
    coop.rs             # pub fn coop() -> Config + tests
    with_timeout.rs     # pub fn with_timeout(cfg: Config, ms: u64) -> Config + tests
```

> Replace `{{module}}` with the actual module name (e.g., `p2p`, `boxes`).

## Struct File (`structs/{{module}}/config.rs`)

```rust
// structs/{{module}}/config.rs
use crate::methods::{{module}}::config as config_method;

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
    pub fn new() -> Self { config_method::new() }
    pub fn coop() -> Self { config_method::coop() }
    pub fn with_timeout(self, ms: u64) -> Self { config_method::with_timeout(self, ms) }
}

#[rustfmt::skip]
impl fmt::Display for Config {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { config_method::fmt(self, f) }
}
```

> Replace `{{module}}` with the actual module name.

## Method File (`methods/{{module}}/config/new.rs`)

```rust
// methods/{{module}}/config/new.rs
use crate::structs::{{module}}::Config;

pub fn new() -> Config { Config::default() }

#[cfg(test)]
mod tests {
    use crate::structs::{{module}}::Config;
    use super::new;

    #[test]
    fn test_usage() {
        let config = new();
        assert!(config.enable_mdns);
    }
}
```

> Replace `{{module}}` with the actual module name.

## Method File (`methods/{{module}}/config/with_timeout.rs`)

```rust
// methods/{{module}}/config/with_timeout.rs
use crate::structs::{{module}}::Config;

pub fn with_timeout(cfg: Config, ms: u64) -> Config {
    Config { timeout_secs: ms, ..cfg }
}

#[cfg(test)]
mod tests {
    use crate::structs::{{module}}::Config;
    use super::with_timeout;

    #[test]
    fn test_usage() {
        let config = with_timeout(Config::default(), 5000);
        assert_eq!(config.timeout_secs, 5000);
    }
}
```

> Replace `{{module}}` with the actual module name.

## Trait Method File (`methods/{{module}}/config/fmt.rs`)

```rust
// methods/{{module}}/config/fmt.rs
use crate::structs::{{module}}::Config;
use std::fmt;

pub fn fmt(cfg: &Config, f: &mut fmt::Formatter<'_>) -> fmt::Result {
    write!(f, "Config(timeout: {})", cfg.timeout_secs)
}

#[cfg(test)]
mod tests {
    use crate::structs::{{module}}::Config;

    #[test]
    fn test_usage() {
        let config = Config::default();
        let s = format!("{}", config);
        assert!(s.starts_with("Config"));
    }
}
```

> Replace `{{module}}` with the actual module name.

## Module Flattening (`methods/{{module}}/config/mod.rs`)

```rust
// methods/{{module}}/config/mod.rs
pub mod new;
pub mod coop;
pub mod with_timeout;
pub mod fmt;

pub use new::new;
pub use coop::coop;
pub use with_timeout::with_timeout;
pub use fmt::fmt;
```
