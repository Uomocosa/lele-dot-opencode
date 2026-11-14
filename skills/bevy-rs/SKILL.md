---
name: bevy-rs
description: Use when working in a crate that depends on the Bevy game engine (bevy 0.20, Rust). Docs links plus the patterns we use here — plugin struct+delegate separation, __bevy_systems__ placement, App-based testing, and the core-logic + wrapper-system command pattern.
---

# bevy-rs — Bevy (Bevy-specific conventions)

Bevy patterns for Rust crates that depend on `bevy`. Where Bevy idioms differ, these override
the general `lele-syntax-rs` rules.

**Targets bevy 0.20.** Older versions use `Event`/`EventWriter`/`EventReader`; 0.19 uses
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

### Plugin lifecycle methods stay inline (`LELE043`)

Trait impl methods follow the same `atomic_delegates` placement as inherent ones (`LELE017`),
except the methods listed in `[[lele.lint.inline_trait_methods]]`. Every Bevy repo lists the
`Plugin` lifecycle methods there, so `build` / `ready` / `finish` / `cleanup` are written in
the trait impl, next to the plugin struct: the impl is the plugin's wiring manifest. Never
delegate them, never forward them to an inherent `build_plugin` shell (`LELE043` rejects both).
The trait impl co-locates with the type (`LELE042`).

```toml
# lele.toml
[[lele.lint.inline_trait_methods]]
trait   = "bevy::app::Plugin"
methods = ["build", "ready", "finish", "cleanup"]
reason  = "plugin lifecycle methods are the plugin's wiring; read them next to the plugin struct"
```

```rust
// {{module}}/plugin.rs
use bevy::prelude::*;
use crate::{{module}};

pub struct Plugin;

impl bevy::prelude::Plugin for Plugin {
    fn build(&self, app: &mut App) {
        app.init_resource::<{{module}}::NetworkState>()
            .add_systems(FixedUpdate, (
                {{module}}::bevy_systems::poll_network,
                {{module}}::bevy_systems::broadcast,
            ));
    }
}
```

Other trait methods with long bodies are delegated like inherent ones; their body file is
trait-prefixed: `__methods__/<type>/<trait>_<method>.rs` (e.g. `display_fmt.rs`), unless the
method already starts with the trait name (`from_celsius.rs`, `visit_item_mod.rs`).

`lib.rs` mounts the crate-root bodies folder with
`#[path = "../__methods__/mod.rs"] mod methods;` (private, never re-exported — bodies are
reached through their type's methods, never `methods::…`).

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

### Systems live in `__bevy_systems__/`

Registered systems are plain functions in `{{module}}/__bevy_systems__/`, one item per file
named after the function (`LELEBEVY002`). `mod.rs` mounts the dunder folder with
`#[path = "__bevy_systems__/mod.rs"] pub mod bevy_systems;` (or `pub(crate)`) — Rust paths
stay `{{module}}::bevy_systems::…` — and never re-exports a system at the domain root
(`LELEBEVY001`); `__bevy_systems__/mod.rs` flattens via `pub use`.

```rust
// {{module}}/mod.rs
#[path = "__bevy_systems__/mod.rs"]
pub mod bevy_systems;
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
{{module}}/increment.rs                     # pure fn increment(state, amount)
{{module}}/__bevy_systems__/increment_button.rs  # fn increment_button(Query, ResMut) -> calls increment
{{module}}/increment_cli.rs                 # fn increment_cli(...)            -> calls increment
```

```rust
// {{module}}/increment.rs — no Query/Res/Commands
pub fn increment(state: &mut {{module}}::ClickerState, amount: u64) {
    state.count = state.count.wrapping_add(amount);
}
```

## Notes

- Compose plugins as a tuple: `app.add_plugins((p2p::Plugin::new(cfg), sync::Plugin));`.
- Each crate adds only what it owns (`lele-syntax-rs` RATIONALE §16): a shared plugin offers a
  `.with(..)` seam; each crate contributes its own systems or methods; only the app (or test binary)
  composes them.
- `lele-bevy-lint` is authoritative for the Bevy-specific rules: run `just bevy-lint`, or
  `lele-bevy-lint --rule-list` / `--explain <name>` (installed from
  `github.com/Uomocosa/lele-rust-linter`). See the `bevy-ui-preview` skill for the UI preview
  rules, the `lele_bevy_preview` scene DSL and the test template.

**0.20 buttons:** `Interaction` and `bevy::ui::widget::Button` are deprecated. Use `bevy::ui_widgets::Button` with `Hovered::default()`, and detect presses with `Added<Pressed>`. To disable a button insert `InteractionDisabled`: removing `Hovered` is not enough, because `Button` observers still add `Pressed`.
