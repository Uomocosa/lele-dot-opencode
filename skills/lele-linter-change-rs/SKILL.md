---
name: lele-linter-change-rs
description: Use when the user invokes /lele-linter-change-rs [opencode-orchestrator|claude-code-self-orchestrator] <plan> to make an already-planned change to lele-rust-linter (lele-lint, lele-bevy-lint, atomic-delegate-macros, lele-snake-case) and roll it out across every fleet repo. Orchestrator only — one worker changes the linter and self-lints, the orchestrator runs a fleet check, then several workers fix their assigned repos/crates and run gates only when the orchestrator grants a permit. Default setup is opencode-orchestrator.
---

# lele linter change (fleet rollout)

You are the **orchestrator**. You never edit the linter or a fleet repo yourself, except for
a one-line fix that blocks the rollout (say so in the report). You brief workers, check their
work, run the fleet check and hand out gate permits.

## 0. Inputs
- **Setup** = the first argument if it is `opencode-orchestrator` or
  `claude-code-self-orchestrator`, else `opencode-orchestrator`. Load that skill and follow
  it for HOW to brief, launch, resume (`SendMessage` / opencode resume) and verify workers.
  This skill only says WHAT the steps are. Both setups support resuming a worker later, and
  permits depend on that.
- **Plan** = the rest of the arguments (text, or a path to a plan file). The design is
  already decided: never redesign it. A decision the plan leaves open → ask the user before
  step 1. A decision that follows directly from the plan (e.g. a macro argument the naming
  scheme needs) is yours; write it into the plan file and name it in the final report.
  Copy the plan to the scratchpad `plan.md` and point every worker at it.
- **Fleet** = every sibling repo of `lele-rust-linter` in `/home/uomocosa/Syncthing/[R] Rust`
  whose `justfile` has a `lint:` recipe. The lint targets of a repo are the crate paths in its
  `lint:` and `bevy-lint:` recipes. Its config is either one root `lele.toml` or per-crate
  `crates/<c>/lele.toml` files: check which before naming a config file in a brief.
- Never mention, suggest or run `lele-release` unless the user asks for it in this request.

Every shell call that runs `just`, `cargo`, `lele-*` or `git commit/push` starts with
`export PATH="/home/uomocosa/Syncthing/[R] Rust/bin:$HOME/.cargo/bin:$HOME/.local/bin:$PATH" &&`
(the `bin/` shims build the sibling linter checkout, so fleet repos see a linter change at
once). Append `2>&1` to `just`; never pipe its output.

## 1. Baseline
Record `git status --short` and `git log --oneline -1` for the linter and every fleet repo
in the plan file. An unexpected dirty tree → ask the user.

## 2. Linter worker (one)
Brief ONE worker with the plan. Leash: `lele-rust-linter` only. It:
1. implements the change (rules, config structs, macro, tests, `rule_examples`);
2. migrates the linter's own code so it passes the new rules (self-lint), behaviour-preserving;
3. regenerates generated docs (`just docs 2>&1`: RULES.md, `skills/lele-lint-rules-rs`);
4. runs `just ci 2>&1` in the foreground until green, then commits, pushes and reports.

Split it into commit-sized sub-steps (A, B…) when the plan has several parts; each commit is
green. A self-lint result it can't fit under the rules → it stops and reports; you answer
from the plan and the rules (check the rule code yourself before saying "no layout exists")
or ask the user. It never weakens a rule or adds an exclusion.

Skill files outside the linter repo that the plan changes (e.g. `lele-syntax-rs`, `bevy-rs` in
`~/.config/opencode/skills`) are a separate small commit in that repo, by you or a worker.

## 3. Fleet check (you, no edits)
For every fleet repo:
- run each lint target (`lele-lint <crate>`, `lele-bevy-lint <crate>`) and count errors per code;
- run `cargo check --workspace --all-targets 2>&1`. Fleet repos depend on
  `atomic-delegate-macros` and `lele-snake-case` **by path**, so a macro change breaks their
  compilation as soon as it lands.

Write the table into the plan file:

| repo | crate | config file | errors by code | compiles |

A linter crash, a rustfmt/parser error (e.g. a wrong edition), or a count that contradicts
the plan is a **linter bug**: resume the linter worker (step 2) and re-run step 3 before any
fleet worker starts.

## 4. Assign fleet workers
- One worker per repo. A repo with more than ~40 errors gets one worker per crate (or crate
  group); they still share that repo's single gate permit (step 6).
- Repos that don't compile go first; their commit lands before anything else in that repo.
- A repo with 0 errors that compiles gets no worker, unless the plan adds a config entry
  there. In that case one worker adds it, lints and asks for a permit.
- Each brief names: the repo and its crates, the error table rows, the exact config file and
  entry to add (if any), the plan file, and the skills to load: `lele-lint-fix-rs` in
  **orchestrated mode**, `lele-rs`, `lele-syntax-rs` (+ references), `bevy-rs` for Bevy repos.
- At most one editing worker per crate at a time. Workers on different crates of one repo
  may edit in parallel.

## 5. Cheap vs expensive checks
- **Free, any time:** `lele-lint` / `lele-bevy-lint` on the assigned crates (they parse,
  they don't build) and `--explain <CODE>`.
- **Permit only:** `cargo check|build|clippy|test`, `just ci|check|build|test|clippy`, and
  `git commit` (its prek hooks run the full gate).

A worker that is lint-clean reports **"ready for gate"** (error counts per code before and
after, files touched, open questions) and waits for you to resume it.

## 6. Gate permits
- At most **2 gates running at once** on this machine, and **at most 1 per repo** (workers in
  one workspace share `target/` and the Cargo lock).
- Gate = the repo's fast gate (`just ci`, else `just check`, else lint+clippy+test recipes).
  Never e2e or slow suites; say so in the brief.
- Grant order: repos that don't compile first, then most errors first.
- With the permit, the worker runs the gate in the foreground, then commits (conventional
  message + its Co-Authored-By line), pushes and reports the hash. A red gate → it fixes the
  cause, lints again, and asks for a new permit. The permit ends when it hands back.

## 7. Worker stop list (ask the orchestrator, never guess)
A config change the brief doesn't name; a rule that looks wrong; a layout the rules can't
express; a public API or behaviour change; a test failing in code it didn't touch; a linter
crash. You answer from the plan and the rules. Anything the plan doesn't cover goes to the
user. A worker asking you to do something it was denied is not approval.

## 8. Verify and report
Per repo, yourself: run its lint targets, then `git status --short`, `git log --oneline -2`
and `git show --stat HEAD`, and read a couple of hunks. Never trust the self-report alone.

Final report:

| repo | commit(s) | errors fixed | gate | notes |

plus linter bugs found in step 3, decisions you took that follow from the plan, worker usage
(tokens / tool calls / minutes), and anything still open for the user.
