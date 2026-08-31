---
name: bevy
description: Use when working on projects that depend on the Bevy game engine. Covers Plugin struct+delegate separation, Component/Resource/Message types, system conventions (Res/ResMut/Query/Commands/MessageWriter), testing with App, plugin composition, internal module layout, and derive macros for bevy 0.19.
---

# BEVY-SPECIFIC SYNTAX & PATTERNS

Bevy engine patterns for Rust projects that depend on `bevy`. This skill may override general conventions where Bevy idioms differ.

**Targets bevy 0.19.** For older versions, adjust `Message`/`MessageWriter`/`MessageReader` to `Event`/`EventWriter`/`EventReader` accordingly. See [bevy releases](https://github.com/bevyengine/bevy/releases) for version history.

## Sources

| Topic | URL |
|-------|-----|
| API docs (App, Component, Resource, Messages) | `https://docs.rs/bevy` |
| Book / getting started | `https://bevy.org/learn/` |
| Examples (per-subcrate) | `https://github.com/bevyengine/bevy/tree/main/examples` |
| Migration guides / releases | `https://github.com/bevyengine/bevy/releases` |
| Feature flags | `https://github.com/bevyengine/bevy/blob/main/Cargo.toml` |

## 1. Bevy Module & File Patterns

### Plugin Struct + Delegate Separation

Separate the Plugin struct definition from its `impl Plugin for ...` trait implementation. Both files live in the domain folder. The thin delegate calls a private sibling method file:

```
{{module}}/
  plugin.rs                    # struct Plugin + Default + thin delegates
  plugin_build.rs              # fn build(plugin, app) + test_usage  (PRIVATE module)
```

```rust
// {{module}}/plugin.rs
use super::plugin_build;
use bevy::prelude::*;

pub struct Plugin;

#[rustfmt::skip]
impl bevy::prelude::Plugin for Plugin {
    fn build(&self, app: &mut App) { plugin_build::build(self, app) }
}
```

- The method file is `{{module}}/plugin_build.rs` — `<struct>_<method>.rs` naming.
- The thin delegate `impl Plugin for ...` block MUST be annotated with `#[rustfmt::skip]`.
- `plugin_build` is a PRIVATE module (`mod` in mod.rs) — only callable through the thin delegate.

### Component, Resource, and Event Types

All Bevy type-defining structs and enums live as files in the domain folder — no `component/` or `resource/` subdirectories. The `#[derive(...)]` macro is sufficient to convey the type's role.

```rust
// {{module}}/click_counter.rs
use bevy::prelude::Component;

#[derive(Component)]
pub struct ClickCounter { pub count: u32 }
```

```rust
// {{module}}/network_state.rs
use bevy::prelude::Resource;

#[derive(Resource)]
pub struct NetworkState {
    pub connected_peers: Vec<PeerId>,
}
```

```rust
// {{module}}/event.rs
use bevy::prelude::Message;

#[derive(Message, Debug, Clone)]
pub enum Event {
    DiscoveredPlayer(PeerId),
    JoinRequest(PeerId),
    PlayerJoined(PeerId),
    PlayerLeft(PeerId),
}
```

**Bevy 0.19 constraint — Resources are Components:** `Resource` is now a subtrait of `Component`; `#[derive(Resource)]` implements both. A type can no longer derive both `#[derive(Component)]` and `#[derive(Resource)]` — split shared data into distinct resource and component types.

Events are consumed via `MessageWriter<T>` / `MessageReader<T>` (the newer Bevy API replacing `EventWriter`/`EventReader`).

## 2. Bevy System Conventions

Systems are plain functions living in the `{{module}}/bevy_systems/` folder. File naming follows the function name (snake_case).

### System Parameters

Use `Res<T>` / `ResMut<T>` for resources, `Query<&T, &mut T>` for components, `Commands` for spawning, `MessageWriter<T>` / `MessageReader<T>` for events:

```rust
// {{module}}/bevy_systems/poll_network.rs
use bevy::prelude::*;
use crate::{{module}};

pub fn poll_network(
    mut session: ResMut<{{module}}::Session>,
    mut input_buffer: ResMut<{{module}}::RemoteInputBuffer>,
    mut network_state: ResMut<{{module}}::NetworkState>,
    mut peer_state: ResMut<{{module}}::PeerState>,
    mut events: MessageWriter<{{module}}::Event>,
) { ... }
```

### System Registration

Register systems with `app.add_systems()` inside the Plugin's `build` method:

```rust
// {{module}}/plugin_build.rs
use bevy::prelude::*;
use crate::{{module}};

pub fn build(_plugin: &{{module}}::Plugin, app: &mut App) {
    app.init_resource::<{{module}}::Tick>()
       .init_resource::<{{module}}::NetworkState>()
       .insert_resource({{module}}::Session::new(...))
       .add_systems(FixedUpdate, (
           {{module}}::bevy_systems::poll_network,
           {{module}}::bevy_systems::log_peer_count,
           {{module}}::bevy_systems::broadcast,
           {{module}}::bevy_systems::apply_remote_inputs,
       ));
}
```

Use `FixedUpdate` for fixed-timestep game logic, `Update` for per-frame UI/input logic.

## 3. Bevy Testing Patterns

When a system requires a Bevy `App` context, construct a minimal working `App` inside the test:

```rust
// {{module}}/bevy_systems/detect_click.rs
use bevy::prelude::*;
use crate::{{module}};

pub fn detect_click(
    mut query: Query<(&{{module}}::Owner, &mut {{module}}::ClickCounter, &GlobalTransform)>,
    mouse_button_input: Res<ButtonInput<MouseButton>>,
    windows: Query<&Window>,
) {
    if !mouse_button_input.just_pressed(MouseButton::Left) { return; }
    for (_owner, mut counter, _transform) in &mut query {
        counter.count += 1;
    }
}

#[cfg(test)]
mod tests {
    use bevy::prelude::*;
    use crate::{{module}};

    #[test]
    fn test_usage() {
        let mut app = App::new();
        app.world_mut().spawn((
            {{module}}::Owner(PeerId::random()),
            {{module}}::ClickCounter { count: 0 },
            GlobalTransform::default(),
        ));

        let mut mouse_input = ButtonInput::<MouseButton>::default();
        mouse_input.press(MouseButton::Left);
        app.insert_resource(mouse_input);

        app.add_systems(Update, detect_click);
        app.update();

        let mut query = app.world_mut().query::<&{{module}}::ClickCounter>();
        let counter = query.single(app.world());
        assert_eq!(counter.count, 1);
    }
}
```

**Key patterns:**
- `App::new()` — fresh app instance
- `app.world_mut().spawn(...)` — spawn entities with component tuples
- `app.insert_resource(...)` — inject resources
- `app.add_systems(ScheduleName, system_fn)` — register the system under test
- `app.update()` — run one frame
- `app.world_mut().query::<&T>()` — read back component data for assertions

### Testing Resource Initialization

```rust
let mut app = App::new();
app.insert_resource(MyResource { ... });
app.add_systems(Update, my_system);
app.update();
```

### Testing Events (Message)

```rust
let mut app = App::new();
app.add_message::<MyEvent>();
app.add_systems(Update, handle_event);
app.world_mut()
    .resource_mut::<Messages<MyEvent>>()
    .write(MyEvent::Variant(value));
app.update();
```

## 4. Bevy Plugin Composition

When composing multiple plugins, add them as a tuple:

```rust
// main.rs or plugin builder
use crate::p2p;
use crate::sync;

app.add_plugins((
    p2p::Plugin::new(config),
    sync::Plugin,
));
```

## 5. Common Bevy Derive Macros

| Derive | Used On | Purpose |
|--------|---------|---------|
| `#[derive(Component)]` | struct | Marks struct as an ECS component |
| `#[derive(Resource)]` | struct | Marks struct as a global singleton resource |
| `#[derive(Message)]` | struct/enum | Marks type as a Bevy event message |
| `#[derive(Bundle)]` | struct (optional) | Groups multiple components (use raw tuples instead by convention) |

## 6. Internal Domain Layout

Every domain lives in a single folder under `src/`. Structs, methods, systems, and types are all co-located. **System functions live in a `bevy_systems/` subfolder** to avoid filename collisions with Component types. No `structs/`/`methods/`/`system/` split.

```
src/
  lib.rs                         # pub mod {{module}}; + crate-level re-exports
  {{module}}/                    # domain folder
    mod.rs
    plugin.rs                    # struct Plugin + Default + thin delegates
    plugin_build.rs              # fn build + test_usage  (PRIVATE)
    config.rs                    # struct Config + Default + thin delegates
    config_new.rs                # fn new + test_usage  (PRIVATE)
    config_coop.rs               # fn coop + test_usage  (PRIVATE)
    peer_state.rs                # #[derive(Resource)] struct PeerState + thin delegates
    peer_state_accept_peer.rs    # method  (PRIVATE)
    click_counter.rs             # #[derive(Component)] struct ClickCounter
    event.rs                     # #[derive(Message)] enum Event
    bevy_systems/
      mod.rs
      poll_network.rs            # system function  (PUBLIC)
      broadcast.rs               # system function  (PUBLIC)
      detect_click.rs            # system function  (PUBLIC)
```

**Visibility rules:**
- Struct types → `pub mod <name>;` + `pub use <name>::<Type>;` in mod.rs (public)
- Method files → `mod <struct>_<method>;` in mod.rs (PRIVATE)
- System functions → `pub mod bevy_systems;` in mod.rs — NOT re-exported at domain root. `bevy_systems/mod.rs` flattens via `pub use` (see lele-syntax-rs Rule 3)
- Pure enums → `pub mod <name>;` + `pub use <name>::<Type>;` in mod.rs (public)

**mod.rs example:**
```rust
mod plugin;
mod plugin_build;
mod config;
mod config_new;
mod config_coop;
mod peer_state;
mod peer_state_accept_peer;
mod click_counter;
mod event;
pub mod bevy_systems;

pub use click_counter::ClickCounter;
pub use config::Config;
pub use event::Event;
pub use peer_state::PeerState;
pub use plugin::Plugin;
```

**Consumer imports:**
```rust
use crate::{{module}};
// {{module}}::plugin::Plugin
// {{module}}::bevy_systems::poll_network(...)
```

Method files are never imported directly — they are called exclusively through the struct's thin delegates.

## 7. System Placement

### Definition
A **system function** is any function registered with `app.add_systems()` inside a `{{module}}/plugin_build.rs` file.

### Placement Rules

| Function type | Location | Example |
|---|---|---|
| Registered in `add_systems()` | `{{module}}/bevy_systems/` | `bevy_systems/poll_network.rs` |
| Plain helper (no SystemParams) | Inline in the calling system file, or as a level file in `{{module}}/` | `handle_incoming_message.rs` |
| Internal builder/spawn helper used only by one system | Same file as the calling system (private helper) | `spawn_remote_player` inside `handle_player_join.rs` |

A function that takes a Bevy type as a plain reference (e.g., `&ButtonInput<KeyCode>`) is NOT a system — it is a helper.

### Consumer Imports

Systems registered in `{{module}}/bevy_systems/` are accessed via domain prefix:

```rust
// {{module}}/plugin_build.rs
use crate::{{module}};

app.add_systems(FixedUpdate, {{module}}::bevy_systems::poll_network);
```

Plain helpers in `{{module}}/` are accessible through the domain module:

```rust
use crate::{{module}};
{{module}}::handle_incoming_message(...);
```

## 8. Command Pattern: Core Logic + Wrapper Systems

Separate **core logic** (pure functions) from **input handling** (Bevy systems) when an action can be triggered from multiple sources.

```
{{module}}/
  increment.rs              # Core logic (pure function)
  increment_button.rs       # GUI wrapper (calls increment)
  increment_cli.rs          # CLI wrapper (calls increment)
```

### Core Logic Function

Pure function with no Bevy system parameters. Named after the action:

```rust
// {{module}}/increment.rs
use crate::{{module}};

pub fn increment(state: &mut {{module}}::ClickerState, amount: u64) {
    state.count = state.count.wrapping_add(amount);
    let _ = state.cmd_tx.send({{module}}::ClickerCommand::Increment { count: state.count });
}
```

**Key rules:**
- No `Query`, `Res`, `Commands`, or other Bevy system parameters
- Takes plain Rust types (`&mut T`, `u64`, etc.)
- Named after the action (e.g., `increment`, `spawn_enemy`, `apply_damage`)
- Easily testable without Bevy `App`

### Wrapper Systems

Thin Bevy systems that extract input and call the core logic. Named with a suffix indicating the trigger source:

```rust
// {{module}}/increment_button.rs
use bevy::prelude::*;
use crate::{{module}};
use super::increment;

pub fn increment_button(
    interaction: Query<&Interaction, (Changed<Interaction>, With<{{module}}::IncrementButton>)>,
    mut state: ResMut<{{module}}::ClickerState>,
) {
    for interaction in &interaction {
        if *interaction == Interaction::Pressed {
            increment(&mut state, 1);
        }
    }
}
```

### Naming Convention

| Function | Location | Naming |
|----------|----------|--------|
| Core logic | `{module}/{action}.rs` | `{action}` (e.g., `increment`) |
| GUI wrapper | `{module}/{action}_button.rs` | `{action}_button` |
| CLI wrapper | `{module}/{action}_cli.rs` | `{action}_cli` |
| Keyboard wrapper | `{module}/{action}_key.rs` | `{action}_key` |
| Network wrapper | `{module}/{action}_network.rs` | `{action}_network` |

### When to Use

Use when:
- An action can be triggered from multiple sources
- You want to test the logic without Bevy
- The logic is complex enough to warrant isolation

Skip when:
- The action is trivial (e.g., just incrementing a counter by 1)
- There's only one input source
- The logic is tightly coupled to Bevy types (e.g., spawning entities)
