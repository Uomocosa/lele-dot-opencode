---
description: Clear all lele-lint / lele-bevy-lint errors in one crate, one rule code at a time, no git writes (user commits)
agent: build
---

Load the `lele-lint-fix-rs` skill and follow it exactly.

Crate: $ARGUMENTS

If no crate is given above, ask which crate to fix before doing anything.

Never run git reset/checkout/restore/stash/clean/add/commit, and never edit the repo root or lele-lint-test-crates/ — those hold other uncommitted work. In tests/ only follow renames (use lines/paths), never change what a test checks.
