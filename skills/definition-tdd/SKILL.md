---
name: definition-tdd
description: Use when fixing bugs or adding behavior with the fast-red to slow-gate TDD loop — one fast failing test per iteration, logging before fixing, full fast suite green before any slow end-to-end run, stop on first slow red. Works with any project, any language. Provides language-agnostic definitions and pseudocode.
---

# TDD Loop — Fast Red to Slow Gate (Definitions)

This skill is **definitions + pseudocode only**. No language-specific code, no toolchain.
Concrete runner commands come from the project's `AGENTS.md`
(e.g. `[[AGENTS.md::RUN_ALL_TESTS]]`); this skill only defines the loop order.

## 1. Definitions

| Term | Meaning |
|------|---------|
| **Fast test** | Deterministic, no network/GUI/clock dependence (inject or simulate time). Finishes in seconds. First oracle, runs every iteration. |
| **Slow test** | End-to-end: real I/O, network, GUI, wall-clock waits. Minutes to hours. Last oracle, runs only when all fast tests are green. |
| **RED** | Exactly one fast test fails and the failure names one defect. |
| **GREEN** | That one test passes with the minimal fix, plus the full fast suite passes. |
| **Gate** | One slow test run. First red stops the run; analysis returns to fast tests. |

## 2. The Loop (pseudocode)

```
loop:
    1. FAST RED  = write (or pick) ONE fast test exposing ONE defect; run ONLY it
    2. LOG FIRST = add observable logging at the suspect functions BEFORE the fix
                   (inputs, decision, reason — so red output names the origin)
    3. GREEN     = minimal fix for that ONE test; no drive-by changes
    4. FAST FULL = run the whole fast suite ([[AGENTS.md::RUN_ALL_TESTS]] or equivalent);
                   any red -> back to 3, never forward
    5. SLOW GATE = run ONE slow test; on FIRST red stop immediately -> back to 1
                   with the slow log as evidence for the next fast test
    6. DONE      = slow suite green -> optional full matrix / release checks
```

## 3. Rules

1. **Never run a slow test twice** without an intervening fast-red test.
2. **Never fix from slow logs alone** — first reproduce the defect in a fast test.
3. **One defect per iteration** — one fast test, one fix, one gate.
4. **Never refactor while RED** — get to GREEN first.
5. **Logging before fixing** — if the red test cannot name the origin, add logging until it can.
6. **Stop on first slow red** — do not collect more slow failures; one is enough to restart the loop.

## 4. Failure Criteria Are Tests Too

Qualitative complaints ("joining feels slow", "sometimes empty") must be
converted into a failing assertion before any fix:

```
// bad: "entering a room should be fast"
// good: join room X -> occupants visible within K ticks, both directions,
//       else RED
function joiner_sees_occupants_fast_and_vice_versa()
    join(room_X)
    advance(K_ticks)
    assert visible(joiner, occupants) and visible(occupants, joiner)
```

## 5. Common Mistakes

* Editing code, running the slow suite, editing again — the spin this loop exists to prevent.
* Writing all fast tests first, then all fixes (horizontal slicing). Work in vertical slices: one test, one fix, repeat.
* Fixing the slow-test symptom (timeouts, retries, sleeps) instead of reproducing the defect fast.
* Adding logging after the fix — logging is diagnosis, it belongs before.
* Letting a passing slow run excuse a skipped fast-full suite.
