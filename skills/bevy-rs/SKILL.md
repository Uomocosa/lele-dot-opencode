---
name: bevy-rs
description: Use when working in a crate that depends on the Bevy game engine (bevy 0.19, Rust). Docs links plus the patterns we use here — plugin struct+delegate separation, bevy_systems placement, App-based testing, and the core-logic + wrapper-system command pattern.
---

# bevy-rs — Bevy (Bevy-specific conventions)

Bevy patterns for Rust crates that depend on `bevy`. Where Bevy idioms differ, these override
the general `lele-syntax-rs` rules.

**Targets bevy 0.19.** Older versions use `Event`/`EventWriter`/`EventReader`; 0.19 uses
`Message`/`MessageWriter`/`MessageReader`.

## Docs & examples

| Topic | URL |
|-------|-----|
| Book / getting started | `https://bevy.org/learn/` |
| API docs | `https://docs.rs/bevy` |
| Examples (per-subcrate) | `https://github.com/bevyengine/bevy/tree/main/examples` |
| Releases / migration guides | `https://github.com/bevyengine/bevy/releases` |
| Feature flags | `https://github.com/bevyengine/bevy/blob/main/Cargo.toml` |

## How we use Bevy here

### Plugin struct + delegate separation

The `Plugin` struct file holds data only; the `impl Plugin` body is an atomic delegate to a
private sibling `<struct>_<method>.rs` method file (never `super::`).

```
{{module}}/
  plugin.rs         # struct Plugin + Default + atomic delegates
  plugin_build.rs   # fn build(plugin, app) + test_usage   (PRIVATE)
```

```rust
// {{module}}/plugin.rs
use crate::{{module}};
use bevy::prelude::*;

pub struct Plugin;

#[rustfmt::skip]
impl bevy::prelude::Plugin for Plugin {
    fn build(&self, app: &mut App) { {{module}}::plugin_build::build(self, app) }
}
```

### Component / Resource / Message types

Type-defining structs/enums are atomic files in the domain folder — no `component/`/`resource/`
subdirectories; the derive conveys the role.

```rust
#[derive(Component)] pub struct ClickCounter { pub count: u32 }
#[derive(Resource)]  pub struct NetworkState { pub connected_peers: Vec<PeerId> }
#[derive(Message, Debug, Clone)] pub enum Event { DiscoveredPlayer(PeerId), PlayerLeft(PeerId) }
```

**0.19 constraint:** `Resource` is now a subtrait of `Component`, so a type can no longer derive
both `#[derive(Component)]` and `#[derive(Resource)]` — split shared data into distinct types.

### Systems live in `bevy_systems/`

Registered systems are plain functions in `{{module}}/bevy_systems/`, file named after the
function. `mod.rs` declares `pub mod bevy_systems;` and does **not** re-export systems at the
domain root; `bevy_systems/mod.rs` flattens via `pub use`.

```rust
// {{module}}/plugin_build.rs
use crate::{{module}};
use bevy::prelude::*;

pub fn build(_plugin: &{{module}}::Plugin, app: &mut App) {
    app.init_resource::<{{module}}::NetworkState>()
       .add_systems(FixedUpdate, (
           {{module}}::bevy_systems::poll_network,
           {{module}}::bevy_systems::broadcast,
       ));
}
```

`FixedUpdate` for fixed-timestep game logic, `Update` for per-frame UI/input.

### Testing with `App`

```rust
let mut app = App::new();
app.world_mut().spawn((Owner(PeerId::random()), ClickCounter { count: 0 }));
app.insert_resource(mouse_input);
app.add_systems(Update, detect_click);
app.update();
let counter = app.world_mut().query::<&ClickCounter>().single(app.world());
assert_eq!(counter.count, 1);
```

### Command pattern: core logic + wrapper systems

When an action has multiple triggers, split pure core logic from the Bevy input wrappers.
Test the core without a Bevy `App`.

```
{{module}}/increment.rs          # pure fn increment(state, amount)
{{module}}/increment_button.rs   # fn increment_button(Query, ResMut) -> calls increment
{{module}}/increment_cli.rs      # fn increment_cli(...)            -> calls increment
```

```rust
// {{module}}/increment.rs — no Query/Res/Commands
pub fn increment(state: &mut {{module}}::ClickerState, amount: u64) {
    state.count = state.count.wrapping_add(amount);
}
```

## Notes

- Compose plugins as a tuple: `app.add_plugins((p2p::Plugin::new(cfg), sync::Plugin));`.
- `lele_bevy_lint` is authoritative for the Bevy-specific rules: run
  `devenv tasks run lele:bevy-lint 2>&1` (codes E005/E008/E029/E037/E038/E039) or
  `cargo run --manifest-path ../lele_bevy_lint/Cargo.toml -- --explain E0xx`. See the
  `bevy-ui-preview` skill for the UI preview rules (E029/E037/E038/E039), the
  `lele_bevy_preview` scene DSL and the test template.
