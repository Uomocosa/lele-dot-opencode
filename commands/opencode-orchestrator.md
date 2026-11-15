---
name: opencode-orchestrator
description: Orchestrate opencode workers (SmartWorker = opencode-go/deepseek-v4.1-flash#low, EfficientWorker = opencode-go/muse-spark-1.3-contributor#low). Follows orchestrator-core; this skill only says how to launch, resume and read opencode sessions. User-invoked only (/opencode-orchestrator <task> [--worker smart|efficient] [--model provider/model#variant]).
disable-model-invocation: true
---

# opencode orchestrator

**First load the `orchestrator-core` skill and follow it** (role, SmartWorker/EfficientWorker
choice, prepare, brief, verify, decide, cost, report). This file only adds the opencode
specifics.

Request: $ARGUMENTS

## Workers

**Workers are ONLY opencode sessions started with `opencode run`.** Never use Claude's
`Agent`/`Task` tool or any Claude subagent as a worker, not even "to go faster" or for one
small step. If `opencode` is missing or fails to start, STOP and tell the user.

- **SmartWorker**: `-m opencode-go/deepseek-v4.1-flash#low`
- **EfficientWorker**: `-m opencode-go/muse-spark-1.3-contributor#low`
- Effort is the `#variant` suffix of the model. An unknown variant fails at once with
  "Variant unavailable for <model>: <variant>" (checked 2026-11-15).
- Read-only SmartWorker plans: add `--agent plan`.

Check the model exists before anything else:
`opencode models 2>&1 | grep -Fx "<model without #variant>"`.
`opencode models` can return a short list while the background service is busy, so on no match
wait a few seconds and check once more. Some working models (e.g. Muse Spark Contributor) are
never listed, so still no match → probe it with a one-shot run in the scratchpad:
`timeout 90 opencode run -m <model#variant> "reply OK" < /dev/null 2>&1`.
It answers → use it. Probe fails → **STOP**. Tell the user the model was not found and show the
closest names from `opencode models`. Never fall back to another model on your own.

**Quota.** opencode-go has a weekly usage limit. A run that fails with "OpenCode Go usage limit
reached (weekly, resets in …)" → stop and tell the user the reset time; never switch to Claude
workers on your own.

Shell calls need `export PATH="/home/uomocosa/Syncthing/[R] Rust/bin:$HOME/.cargo/bin:$HOME/.local/bin:$HOME/.opencode/bin:$PATH" &&`.

## opencode-specific preparation

- A killed `opencode run` (e.g. the Bash 2 h background limit) does **not** stop its session: it
  keeps working inside opencode's background service. Before starting or resuming any worker in
  the same directory, export the old session and wait until its last message has
  `"type": "idle"` (re-export every ~15 s; no new messages for 2 min also counts as stopped).
  Long tasks: split them into turns well under 2 h, or resume the same session with `--session`.
- If the task has a slash command (e.g. `/lint-fix`), the worker prompt is that command plus its
  argument. Otherwise write the brief (orchestrator-core §2).
- Plan runs (`--agent plan`) may go in parallel; editing runs stay one per directory.

## Launch

From the target directory, in the background, with a session title you can find again:

```bash
cd "<dir>" && opencode run -m <model#variant> --auto --format json --title "<short title>" "<prompt>" \
  < /dev/null > <scratch>/<title>.jsonl 2>&1
```

Run that command with the Bash tool's `run_in_background: true` (max `timeout`), **not** with
`nohup … &` or a `( … & )` subshell. `opencode run` exits when the worker's turn ends, so the
harness notifies you the moment the worker stops — no polling, no "wait for idle" loop.

Always close stdin (`< /dev/null`): started in the background with stdin open, `opencode run`
waits for input and never starts the session. Confirm it started: the `.jsonl` gets a
`step_start` line within a minute, or the session export gains messages.

If the run was started detached anyway, poll the export **written to a file first** (piping
`opencode session export` straight into a JSON parser truncates large sessions) until its last
message has `"type": "idle"`. Never wait on `pgrep -f "<title>"`: it matches the watcher's own
command line and never ends.

Then find the session id: `opencode session list` (run in `<dir>`), newest first.

## Read what the worker really did

- The `.jsonl` stream can stop early while the session goes on in opencode's background
  service. **The source of truth is the session export:**
  `cd "<dir>" && opencode session export <session-id> > <scratch>/<title>-export.json`
- The session is finished when its last message has `"type": "idle"`; `info.outcome` says how it
  ended. The worker's final report is the text of the last assistant message.
- Summarise with a short script: per assistant message, tool name + input path/command, and
  every text block. Look at the last ~5 messages first.
- Do not touch the target directory while the worker is running: check the export first.

## Resume (answer the worker)

```bash
cd "<dir>" && opencode run --session <session-id> -m <model#variant> --auto --format json "<answer + next step>" \
  < /dev/null > <scratch>/<title>-2.jsonl 2>&1
```

## Cost

Record the session cost from the export (per-message cost/tokens) in the plan file for each step.
