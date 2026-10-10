---
name: definition-state-machine
description: Use when designing, reviewing, or refactoring a state machine / reducer — one State record, a single update entrypoint, Input and Output types, and transition functions that RETURN outputs instead of taking an output sink. Works with any project, any language. Provides language-agnostic definitions and pseudocode.
---

# State Machine — Definitions

This skill is **definitions + pseudocode only**. No language-specific code, no toolchain.
The concrete Rust module path, names and file layout live in `lele-syntax-rs`
(`references/RATIONALE.md` → *State machines*); this skill defines the shape only.

## 1. At a glance

| Term | Meaning |
|------|---------|
| **State** | The machine's entire memory. Data only: no queued outputs, no sockets, no clock, no handles. |
| **Input** | Sum type of every event that can arrive (a command, a network event, a timer tick, an external change). |
| **Output** | Sum type of every effect the machine requests (notify the UI, send a network command). Values, not actions. |
| **update** | The one entrypoint: `update(state, input) -> outputs`. The only function the outside world calls. |
| **transition** | Any internal function that reads/changes state and returns outputs (`handle_*`, `dial_*`, `send_*`). |
| **shell** | The imperative driver that owns `State`, feeds `Input`, executes `Output`. |

## 2. Canonical shape (pseudocode)

```
domain/
  state_machine/
    State                                          # data only
    Input                                          # every event in
    Output                                         # every effect out
    update(state, input, now) -> list<Output>      # one entrypoint
    handle_command(state, command, now) -> list<Output>
    handle_net_event(state, event, now) -> list<Output>
    dial_candidates(state, now) -> list<Output>
    send_hello(state, peer) -> list<Output>        # single-effect helper too
    snapshot(state) -> Snapshot                    # pure reader: no outputs
```

```
function update(state, input):
    match input:
        Command(c)      -> handle_command(state, c)
        NetEvent(e)     -> handle_net_event(state, e)
        LobbyUpdated(l) -> handle_lobby(state, l)
        Tick            -> tick(state)
```

## 3. Rules

1. **One entrypoint.** The world calls `update(state, input) -> outputs` and nothing else.
   Everything reachable from it is a transition.
2. **`State` is data.** No `outputs` field, no I/O handles, no clock. Time and dependencies
   arrive as parameters (`now`); outputs leave as the return value.
3. **Effects are values.** `Output` is a sum type the shell matches on and performs; the core
   never performs I/O.
4. **Transitions return their outputs; they never take an output sink.** No `out: &mut list<Output>`
   parameter. Returning puts the effect in the signature, so a call site shows what a step can emit:

```
// BAD — the sink hides the effect; every caller must pre-create a buffer
function handle_command(state, outputs, command):
    ...
    outputs.push(Output.Notify(Joined(room)))

// GOOD — the effect is the return value
function handle_command(state, command) -> list<Output>:
    ...
    return [Output.Notify(Joined(room))]
```

   Cost is ~zero with a lazy vector: an empty list allocates nothing, only non-empty emissions
   allocate.
5. **Both channels, one direction each.** State goes *in* (state parameter); outputs come *out*
   (return value). A transition that mutates state *and* emits still returns its outputs.
6. **Pure readers are separate.** Deriving a view (`snapshot`, `hello`, `publish_target`) is a
   plain function of the state returning a value — not a transition, no outputs.
7. **Compose, don't accumulate.** When a step fans out to several transitions, concatenate their
   returned lists in call order.

## 4. Why this shape

- **Functional core, imperative shell.** All decisions live in the honest core; sockets, clock
  and the framework live in the thin shell that drives it.
- **Honest by construction.** Returning outputs makes the effect channel explicit — the caller
  controls inputs *and* observes outputs from the signature. A shared sink is still honest, but
  the return value reads better and composes.
- **Deterministic & replayable.** Feed a recorded `Input` sequence into a fresh `State`; the
  `Output` sequence and final state reproduce — good for tests, snapshots, time-travel.
- **Testable.** A test is `update(state, input)` then assert on `(state, outputs)`; no buffer to
  pre-create.

## 5. Checklist (reviews)

1. Exactly one `update` entrypoint?
2. Does `State` contain any output queue, socket, or clock? (should be none)
3. Does any transition take a mutable output sink instead of returning outputs?
4. Are pure readers (snapshot/derive) separate from transitions?
5. Does a test assert on both the new state *and* the returned outputs?

Refs: Gary Bernhardt, *Boundaries*; Firezone, *sans-IO*; Redux reducer; Mealy machine.
