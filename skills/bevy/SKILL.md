---
name: bevy
description: Use when working on projects that depend on the Bevy game engine. Covers Plugin struct+delegate separation, Component/Resource/Message types, system conventions (Res/ResMut/Query/Commands/MessageWriter), testing with App, plugin composition, internal module layout, and derive macros for bevy 0.19.
---

# BEVY-SPECIFIC SYNTAX & PATTERNS

Bevy engine patterns for Rust projects that depend on `bevy`. This skill may override general conventions where Bevy idioms differ.

**Targets bevy 0.19.** For older versions, adjust `Message`/`MessageWriter`/`MessageReader` to `Event`/`EventWriter`/`EventReader` accordingly. See [bevy releases](https://github.com/bevyengine/bevy/releases) for version history.

## 1. Bevy Module & File Patterns

### Plugin Struct + Delegate Separation

Separate the Plugin struct definition from its `impl Plugin for ...` trait implementation. The trait impl in `structs/{{module}}/plugin.rs` is a thin delegate calling a free function in `methods/{{module}}/plugin/` per the atomic file structure rule:

```
structs/{{module}}/
  plugin.rs                    # struct Plugin { ... }
                               # + #[rustfmt::skip] impl Plugin for Plugin { fn build(...) {
                               #     crate::methods::{{module}}::plugin::build(self, app) } }
methods/{{module}}/
  plugin/
    mod.rs                     # pub mod declarations + pub use flattening
    build.rs                   # pub fn build(plugin: &Plugin, app: &mut App)
```

- The function file inside `methods/{{module}}/plugin/` follows snake_case naming — e.g., `build.rs` for `fn build()`.
- The thin delegate `impl Plugin for ...` block in `plugin.rs` MUST be annotated with `#[rustfmt::skip]`.

### Component, Resource, and Event Types

All Bevy type-defining structs and enums live as peers in `structs/{{module}}/` — no `component/` or `resource/` subdirectories. The `#[derive(...)]` macro is sufficient to convey the type's role.

```rust
// structs/{{module}}/click_counter.rs
use bevy::prelude::Component;

#[derive(Component)]
pub struct ClickCounter { pub count: u32 }
```

```rust
// structs/{{module}}/network_state.rs
use bevy::prelude::Resource;

#[derive(Resource)]
pub struct NetworkState {
    pub connected_peers: Vec<PeerId>,
}
```

```rust
// structs/{{module}}/event.rs
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

Systems are plain functions living in `system/{{module}}/`. File naming follows the function name (snake_case).

### System Parameters

Use `Res<T>` / `ResMut<T>` for resources, `Query<&T, &mut T>` for components, `Commands` for spawning, `MessageWriter<T>` / `MessageReader<T>` for events:

```rust
// system/{{module}}/poll_network.rs
use bevy::prelude::*;
use crate::structs::{{module}}::{Session, RemoteInputBuffer, NetworkState, PeerState, Event};

pub fn poll_network(
    mut session: ResMut<Session>,
    mut input_buffer: ResMut<RemoteInputBuffer>,
    mut network_state: ResMut<NetworkState>,
    mut peer_state: ResMut<PeerState>,
    mut events: MessageWriter<Event>,
) { ... }
```

### System Registration

Register systems with `app.add_systems()` inside the Plugin's `build` method:

```rust
// methods/{{module}}/plugin/build.rs
use bevy::prelude::*;
use crate::structs::{{module}}::{Plugin, Tick, NetworkState, Session};
use crate::system::{{module}};

pub fn build(_plugin: &Plugin, app: &mut App) {
    app.init_resource::<Tick>()
       .init_resource::<NetworkState>()
       .insert_resource(Session::new(...))
       .add_systems(FixedUpdate, (
           {{module}}::poll_network,
           {{module}}::log_peer_count,
           {{module}}::broadcast,
           {{module}}::apply_remote_inputs,
       ));
}
```

Use `FixedUpdate` for fixed-timestep game logic, `Update` for per-frame UI/input logic.

## 3. Bevy Testing Patterns

When a system requires a Bevy `App` context, construct a minimal working `App` inside the test:

```rust
// system/{{module}}/detect_click.rs
use bevy::prelude::*;
use crate::structs::{{module}}::{Owner, ClickCounter};

pub fn detect_click(
    mut query: Query<(&Owner, &mut ClickCounter, &GlobalTransform)>,
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

    #[test]
    fn test_usage() {
        let mut app = App::new();
        app.world_mut().spawn((
            Owner(PeerId::random()),
            ClickCounter { count: 0 },
            GlobalTransform::default(),
        ));

        let mut mouse_input = ButtonInput::<MouseButton>::default();
        mouse_input.press(MouseButton::Left);
        app.insert_resource(mouse_input);

        app.add_systems(Update, detect_click);
        app.update();

        let mut query = app.world_mut().query::<&ClickCounter>();
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
use crate::structs::p2p::Plugin as P2pPlugin;
use crate::structs::sync::Plugin as SyncPlugin;

app.add_plugins((
    P2pPlugin::new(config),
    SyncPlugin,
));
```

## 5. Common Bevy Derive Macros

| Derive | Used On | Purpose |
|--------|---------|---------|
| `#[derive(Component)]` | struct | Marks struct as an ECS component |
| `#[derive(Resource)]` | struct | Marks struct as a global singleton resource |
| `#[derive(Message)]` | struct/enum | Marks type as a Bevy event message |
| `#[derive(Bundle)]` | struct (optional) | Groups multiple components (use raw tuples instead by convention) |

## 6. Internal Subfolder Convention

Every crate MUST follow the three-tree layout. Types live in `structs/`, method implementations in `methods/`, and systems in `system/`. Each tree mirrors the domain module hierarchy — create a module entry only when it has content (sparse trees).

```
src/
  lib.rs                         # pub mod structs; pub mod methods; pub mod system;
  structs/                       # all type definitions
    {{module}}/
      mod.rs
      plugin.rs                  # struct Plugin + thin delegates
      config.rs                  # struct Config + Default + thin delegates
      event.rs                   # #[derive(Message)] enum Event
      peer_state.rs              # #[derive(Resource)] struct PeerState + thin delegates
      click_counter.rs           # #[derive(Component)] struct ClickCounter
      ...
  methods/                       # method free functions (per-struct directories)
    {{module}}/
      mod.rs
      plugin/
        mod.rs
        build.rs                 # pub fn build(plugin: &Plugin, app: &mut App)
      config/
        mod.rs
        new.rs
        coop.rs
      peer_state/
        mod.rs
        accept_peer.rs
        add_connected_peer.rs
      ...
  system/                        # Bevy systems and module-level free functions
    {{module}}/
      mod.rs
      poll_network.rs
      broadcast.rs
      detect_click.rs
      ...
```

Items in `system/{{module}}/` are NOT re-exported at the module root. Consumers import them through the `system` submodule:
```rust
use crate::system::{{module}};
{{module}}::poll_network(...);
```

Methods in `methods/{{module}}/{{type}}/` are never imported directly — they are called exclusively through the struct's thin delegates in `structs/{{module}}/{{type}}.rs`.

## 7. System Placement

### Definition
A **system function** is any function registered with `app.add_systems()` inside a `methods/{{module}}/plugin/build.rs` file.

### Placement Rules

| Function type | Location | Example |
|---|---|---|
| Registered in `add_systems()` | `system/{{module}}/` | `poll_network.rs` |
| Plain helper (no SystemParams) | Inline in the calling system file, or as a level file in `system/{{module}}/` | `handle_incoming_message.rs` |
| Internal builder/spawn helper used only by one system | Same file as the calling system (private helper) | `spawn_remote_player` inside `handle_player_join.rs` |

A function that takes a Bevy type as a plain reference (e.g., `&ButtonInput<KeyCode>`) is NOT a system — it is a helper.

### Consumer Imports

Systems registered in `system/{{module}}/` must be imported through the `system` submodule:
```rust
// methods/{{module}}/plugin/build.rs
use crate::system::{{module}};

{{module}}::poll_network
```

Plain helpers in `system/{{module}}/` are imported directly:
```rust
use crate::system::{{module}}::handle_incoming_message;
```

## 8. Command Pattern: Core Logic + Wrapper Systems

Separate **core logic** (pure functions) from **input handling** (Bevy systems) when an action can be triggered from multiple sources.

```
system/{{module}}/
  increment.rs              # Core logic (pure function)
  increment_button.rs       # GUI wrapper (calls increment)
  increment_cli.rs          # CLI wrapper (calls increment)
```

### Core Logic Function

Pure function with no Bevy system parameters. Named after the action:

```rust
// system/{{module}}/increment.rs
use crate::structs::{{module}}::ClickerState;

pub fn increment(state: &mut ClickerState, amount: u64) {
    state.count = state.count.wrapping_add(amount);
    let _ = state.cmd_tx.send(ClickerCommand::Increment { count: state.count });
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
// system/{{module}}/increment_button.rs
use bevy::prelude::*;
use crate::structs::{{module}}::IncrementButton;
use crate::structs::{{module}}::ClickerState;
use super::increment;

pub fn increment_button(
    interaction: Query<&Interaction, (Changed<Interaction>, With<IncrementButton>)>,
    mut state: ResMut<ClickerState>,
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
| Core logic | `system/{module}/{action}.rs` | `{action}` (e.g., `increment`) |
| GUI wrapper | `system/{module}/{action}_button.rs` | `{action}_button` |
| CLI wrapper | `system/{module}/{action}_cli.rs` | `{action}_cli` |
| Keyboard wrapper | `system/{module}/{action}_key.rs` | `{action}_key` |
| Network wrapper | `system/{module}/{action}_network.rs` | `{action}_network` |

### When to Use

Use when:
- An action can be triggered from multiple sources
- You want to test the logic without Bevy
- The logic is complex enough to warrant isolation

Skip when:
- The action is trivial (e.g., just incrementing a counter by 1)
- There's only one input source
- The logic is tightly coupled to Bevy types (e.g., spawning entities)
