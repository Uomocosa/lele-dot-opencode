---
name: ui-sketch-rs
description: Use when the user says "ui-sketch-rs option 1 2 4" (or similar) after an agent proposed numbered ideas for a Bevy UI element. Renders exactly the chosen options as one lele-bevy-preview scene, so one test run sends one numbered Telegram album to compare. Production code is untouched until the user picks a winner; then only the winner is ported in and the sketch file is deleted.
---

# ui-sketch-rs: render the chosen UI options and let the user pick on Telegram

## How it's used

1. The user asks any agent for ideas or a plan for some UI. The agent answers with
   **numbered options**: 1, 2, 3, ... Each has a short name and one or two lines describing
   what changes. Code previews are welcome, but no ASCII art is needed.
2. The user replies `ui-sketch-rs option 1 2 4`. That is the trigger for this skill.
3. The agent sketches ONLY those options, renders them once, and the user gets one album.
4. The user picks one (`lock 2`), asks for a mix (`2 with 4's colors`), or asks for tweaks.

Keep the option numbers stable for the whole conversation. A mix or tweak gets the next
free number (5, 6, ...) and is never renumbered. That way the Telegram captions always match
the chat.

Load `bevy-rs` and `lele-rs` first. This skill assumes the crate already uses
`lele-bevy-preview` (`*_ui_png_preview` tests, output in a gitignored `ui_preview/`).

## How delivery works (lele-bevy-preview v0.0.18, checked against the pinned source)

- `Scene::run(&Config)` renders every `State` to a PNG, plus one MP4 if `timeline` is `Some`.
- It sends the whole scene as ONE album (chunks of 10). The caption is numbered:
  `N. 🖼 <state label> · new|changed` (`▶` for the MP4). The item numbers are album positions,
  NOT option numbers, so put the option number/letter in every state AND timeline label.
- Every scene needs at least one `State` (empty `states` is a hard error), so an animated scene
  sends a PNG + an MP4 (2 items).
- **`LELE_PREVIEW_DRY_RUN=1`** renders everything, logs the decisions and stashes the files in
  `ui_preview/<dir>/_unsent/` WITHOUT sending. Use it for every look-only iteration; send once at
  the end. A dry run does not write the baseline, so the next real run still reports `new`.
- Raw frames of every clip stay in `ui_preview/<dir>/<scene>_frames/frame-NNNN.png` after any run
  (dry or real): review motion from those (crop/scale them) instead of re-rendering.
- A clip whose frames are all identical fails with `StaticClip` — that means your motion never ran.
- Only `New`/`Changed` captures are sent, compared against the manifest in `out_dir`. An
  unchanged re-run is silent, so force a resend with `LELE_PREVIEW_RESEND_ALL=1`.
- With no Telegram creds it logs a warning and leaves the files on disk. Tell the user.
- Only one timeline (video) per scene. For animated options, use one scene per option.

## Steps

1. **Sketch.** Create `<crate>/src/ui/<area>/__ui_sketch__/<topic>.rs`, wired in through
   `#[cfg(test)] mod __ui_sketch__;` (with a `mod.rs`). Everything goes inside `#[cfg(test)]`.
   - One fn per chosen option, `fn option_2_<slug>(parent: &mut ChildSpawnerCommands)`.
     Start from a COPY of the real spawner and change only what that option needs. Never
     edit the real spawner or its constants. Put new values as local `const`s in this file.
   - Every option renders the same fixture, so the comparison is fair. Include the edge
     cases side by side (e.g. with/without friends, full room, long name).
   ```rust
   #[test]
   fn friend_badge_sketch_ui_png_preview() {
       let out = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("ui_preview/sketch");
       lele_bevy_preview::scene::Scene {
           name: String::from("sketch · friend badge"),
           kind: lele_bevy_preview::scene::Kind::System,
           build: preview_build,          // spawns fixture once per option, each root marked + hidden
           states: vec![
               lele_bevy_preview::scene::State { label: "1 · split pill".into(), apply: show_option::<1> },
               lele_bevy_preview::scene::State { label: "2 · side chip".into(),  apply: show_option::<2> },
               lele_bevy_preview::scene::State { label: "4 · ring".into(),       apply: show_option::<4> },
           ],
           timeline: None,                // Some(..) to show hover/press motion
       }
       .run(&Config { out_dir: out, ..Default::default() })
       .expect("preview");
   }
   ```
   `show_option::<N>`: see Gotchas below. For motion, see **Animated options** below.
2. **Render once:**
   `just t friend_badge_sketch_ui_png_preview --no-capture 2>&1` (with the PATH prefix from the global
   CLAUDE.md). If the `PREVIEW_ARTIFACT=` lines say `status=same`, re-run with
   `LELE_PREVIEW_RESEND_ALL=1`. Reply "album sent: 1, 2, 4" and stop.
3. **Iterate.** For a mix or tweak, add the next number as a new state and re-render.
   Don't touch production code.
4. **Lock in** only after an explicit pick:
   - Port the chosen fn into the real spawner. Move its constants to
     `__basic__/constants.rs` and delete anything that is now unused.
   - Delete `__ui_sketch__/`, its `mod` line, and `ui_preview/sketch/`.
   - Extend the real `*_ui_png_preview` test with the new edge cases and run it.
   - Run `just clippy 2>&1` and the area's tests. Commit per the memory rules.

## Animated options (trials E and E3, 2026-11-18)

- **One scene per option, one test per scene.** Only one timeline per scene, and a run cap is per
  test: one `just t <pattern>` run executes every test the pattern matches, so pick patterns that
  match exactly one sketch test. With a 3-run cap, plan "dry runs + 1 send", not 3 sends.
  No `SketchOption`/`show_option` machinery is needed when each scene holds one option.
- **`Timeline::apply` runs ONCE**, on frame `lead_in_frames + 1` (default 6), not every frame. Use it
  to kick the change (insert `Hovered(true)`, swap a resource); the motion itself must come from a
  test-local system that reads `Time`.
- **Each captured frame = one manual `1/fps` tick + 5 zero-delta `app.update()`s.** Per-`Update`
  counters tick 6x per frame; drive motion from `Time::elapsed_secs()` only.
- **No slow-motion knob.** For a 250-400 ms animation, stretch it in the sketch (e.g.
  `Time<Virtual>::set_relative_speed(0.25)`) and say "at 0.25x" in the label; ~36 frames per change
  at 30 fps is judgeable, 9 is not.
- **The state PNG must show the finished animation:** `render_state_in_fresh_app` warms up at zero
  delta, calls `apply` once, then updates once — so the state's `apply` must jump the animation to its
  end (e.g. backdate the start time).
- **A correct end-state PNG is not evidence the animation is right.** Always look at mid-motion frames.
- **Bevy layout gotcha for rolling/sliding columns:** a clipped window of height `h` holding a column
  of two rows gets the column shrunk/stretched by the parent, so row 2 renders in row 1's slot (the new
  value pops instead of sliding). Give the column `height: 2h` + `flex_shrink: 0.0` and each row
  `height`/`min_height: h` + `flex_shrink: 0.0`.
- **Clippy is the crate's full pedantic/nursery `-D warnings` set** even for scratch: expect
  `into_inner()` on `Res`, `const fn` on tiny selectors, and integer compares instead of float `==`.
  Run clippy with the justfile's `CARGO_TARGET_DIR`, not a bare `cargo clippy`.

## Gotchas found in the first trial (2026-11-17)

- **The lint gate is red while a sketch exists.** lele-lint flags `LELECORE002` (the dir
  `__ui_sketch__` is not snake_case) and `LELE023` (`#[cfg(test)] mod` inside `mod.rs`). So
  while sketching, gate only on clippy plus the sketch test, not on `just check-crate` or
  `just lint`. **No commits** in the repo until lock-in removes the sketch, because the prek
  hooks would fail. `__ui_sketch__/` is gitignored; the `mod` line in `mod.rs` is not.
  If other work must be committed while a sketch exists, move `__ui_sketch__/` out of the tree and
  stash the `mod` line for the commit, then restore both byte-identically. Lock in or delete the
  sketch as soon as the user picks, so this workaround is short-lived.
- **When a production API the sketch reuses is refactored,** the sketch stops compiling and breaks
  every test build: delete the sketch file once its question is answered.
- **Showing one option per state:** mark every option root `SketchOption<const N: usize>`
  and spawn it with `display: Display::None`. Each state's `apply` runs `show_option::<N>`,
  which sets every root to `Display::None` and root N to `Display::Flex`. Use `Display`, not
  `Visibility`: `center_roots` puts all parentless nodes into one column, so a hidden root
  still takes up space.
  ```rust
  fn show_option<const N: usize>(world: &mut World) {
      let mut q = world.query::<(&mut Node, Has<SketchOption<N>>)>();
      for (mut node, on) in q.iter_mut(world) {
          if node.position_type == PositionType::Absolute { continue; } // badges etc.
          node.display = if on { Display::Flex } else { Display::None };
      }
  }
  ```
  (Filter `q` to `With<SketchRoot>` in real code.)
- **Write state types in full:** `lele_bevy_preview::scene::State`, never bare `State`,
  which clashes with `bevy::prelude::State`.
- **Share the frame, write each option's body:** put the common row frame and name clip in
  helpers, and write only the part that changes in each option fn.
- **See what was sent:** run `just t <test> --no-capture 2>&1`, because nextest hides stdout
  on a passing test. `ui_preview/sketch/_log/deliveries.log` should show
  `event=send … result=ok(N)`.

## Rules

- The sketch file is scratch. Never commit it and don't make it pass lele-lint, but keep it
  compiling, because nextest builds the whole test target.
- One topic per sketch file, at most 10 options per album.
- Options are spawn-time visuals plus test-driven state only. If one needs a new system,
  make it a test-local system added in `preview_build`.
- If the user rejects everything, delete the sketch file and go back to proposing ideas.
