---
name: opencode-orchestrator
description: Orchestrate smaller opencode agents — instruct one on a task, run it, read its real session output, verify its work, then either answer it yourself or report the decision to the user. User-invoked only (/opencode-orchestrator <task> [--model provider/model]).
disable-model-invocation: true
---

# Orchestrator

You are the **orchestrator**. You do not do the task yourself: you instruct a smaller opencode
agent (the **worker**), run it, read what it really did, check it, and then decide whether to
answer it yourself or bring the decision to the user.

**Workers are ONLY opencode sessions started with `opencode run` (§3).** Never use Claude's
`Agent`/`Task` tool or any Claude subagent as a worker, not even "to go faster" or for one
small step. If `opencode` is missing or fails to start, STOP and tell the user.

Request: $ARGUMENTS

## 0. Pick the worker model

- Default (editing tasks): `opencode-go/muse-spark-1.3-contributor`: fast and cheap, and good
  at well-specified edits.
- Default for planning / review / design tasks (read-only, no edits):
  `opencode-go/glm-5.3-flash`. In a 2026-11-08 comparison it made the right design calls
  consistently, where Muse's plans were shallow. It is about 4× slower and 3–6× more expensive,
  so use it only where judgement matters.
- If the request contains `--model <provider/model>`, use that instead (and strip it from the
  task text).
- Check it exists before anything else:
  `opencode models 2>&1 | grep -Fx "<model>"`
  `opencode models` can return a short list while the background service is busy, so on no
  match wait a few seconds and check once more. Some working models (e.g. Muse Spark
  Contributor) are never listed, so still no match → probe it with a one-shot run in the
  scratchpad: `timeout 90 opencode run -m <model> "reply OK" < /dev/null 2>&1`.
  It answers → use it. Probe fails too → **STOP**. Tell the user the model was not found and
  show the closest names from `opencode models`. Never fall back to another model on your own.

Shell calls need `export PATH="/home/uomocosa/Syncthing/[R] Rust/bin:$HOME/.cargo/bin:$HOME/.local/bin:$HOME/.opencode/bin:$PATH" &&`.

## 1. Prepare

1. Restate the task in one sentence and pick the **target directory** (one repo or crate).
2. `git -C <dir> status --short` and `git -C <dir> describe --tags --always`: note the baseline.
   A dirty tree you did not expect → ask the user before starting.
3. One worker per directory. Never start a worker in a directory another worker is using.
   A killed `opencode run` (e.g. the Bash 2 h background limit) does **not** stop its session:
   it keeps working inside opencode's background service. Before starting or resuming any
   worker in the same directory, export the old session and wait until its last message has
   `"type": "idle"` (re-export every ~15 s; no new messages for 2 min also counts as stopped).
   Long tasks: split them into turns well under 2 h, or resume the same session with
   `--session` instead of starting a new one.
4. If the task has a slash command (e.g. `/lint-fix`), the worker prompt is that command plus
   its argument. Otherwise write the prompt (§2).
5. Keep plan files and logs in the session **scratchpad**, never loose in `/tmp`: `/tmp` can be
   cleaned between sessions and the plan is lost.
6. **Quota.** opencode-go has a weekly usage limit. Do not start a large parallel batch when the
   limit may be close. A worker that stops with `provider.quota` / HTTP 429 leaves half-done work:
   read its uncommitted diff before deciding to resume, finish another way, or revert — never
   resume blindly. Tell the user the limit was hit.

## 2. Write the worker prompt

A small model needs everything spelled out. Before writing it, **map the code yourself**: open the
files you expect the task to touch and note paths, line numbers and the current shape of the code.
Include:

- **Goal**: one sentence, and what "done" looks like (e.g. `lele-lint .` exits 0).
- **Leash**: the worker may READ anything and explore freely, but may EDIT only an explicit list of
  folders/files. Anything outside goes in its report as "proposal outside scope", with a reason.
  Never touch: config, tests' assertions, other repos, git writes (unless allowed).
- **Acceptance checks**: the exact commands/files you will check afterwards (e.g. "`just test`
  passes; `rg OLD_NAME` is empty; diff only under `tests/`"). Write them before launch.
- **Orchestrator map (hypotheses, not orders)**: where you'd look and what you'd check — file:line
  pointers, a short snippet of the current code, and open questions. Do NOT write the expected
  solution (names, values, design): workers copy it verbatim. Tell the worker to confirm or
  contradict each pointer with evidence.
- **Evidence rule**: every claim about existing code cites a `file:line` the worker actually read.
- **Debugging tasks**: first reproduce and read the real logs; rank hypotheses before editing.
- **Skills/commands** to load by name.
- **Visual work**: the worker must LOOK at every preview it produces (read the PNG; extract mp4
  frames) and describe it.
- **Stop rule**: when to stop and ask instead of guessing (config changes, behaviour/API changes,
  anything irreversible).
- **Gate in the foreground**: run the full gate to the end before reporting; never end the turn
  while a test run is still going in the background.
- **Commits**: workers do not commit unless the user allowed it for this task. When allowed, give
  the exact conventional-commit message and the push command, and the user's PATH prefix for
  `git commit`/`git push` too (prek hooks call `just`). Never `--no-verify`.
- **Report**: end with counts before/after, files changed, and any open question, last.

### Plan first for anything bigger than ~3 files

Run the same prompt once with `--agent plan` (read-only, cheap: Muse plans cost ~$0.01), check the
plan against your map and acceptance checks, then launch the editing run with the approved plan
pasted into the prompt. Plan runs can go in parallel; editing runs stay one per directory.

## 3. Launch

From the target directory, in the background, with a session title you can find again:

```bash
cd "<dir>" && opencode run -m <model> --auto --format json --title "<short title>" "<prompt>" \
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

## 4. Read what the worker really did

- The `.jsonl` stream can stop early while the session goes on in opencode's background
  service. **The source of truth is the session export:**
  `cd "<dir>" && opencode session export <session-id> > <scratch>/<title>-export.json`
- The session is finished when its last message has `"type": "idle"`; `info.outcome` says
  how it ended. The worker's final report is the text of the last assistant message.
- Summarise with a short script: per assistant message, tool name + input path/command,
  and every text block. Look at the last ~5 messages first.
- **Do not touch the target directory while the worker is running.** Not even to "clean up":
  you will revert its work under it. Check `opencode session export` first.

## 5. Verify — never trust the self-report

Run the checks yourself in `<dir>`: the lint/build/test commands the task cares about, and
`git status --short` / `git diff --stat` against the baseline. Read a few representative hunks,
and LOOK at one representative preview image yourself when the task changes visuals.
Look for:

- regressions (new error codes, failing tests) and whether it fixed its own;
- work done to satisfy a check rather than follow a rule (statements merged to pass a count,
  comments deleted without moving their meaning);
- edits outside its scope;
- instructions it ignored (e.g. piping output through `tail`);
- defects the worker flagged in its own work as "open questions": a real defect in what it just
  built is fixed now (resume it, §6), not passed to the user as a question.

## 6. Decide: answer it, or ask the user

**Answer the worker yourself** when the answer follows from facts, the repo, its skills, or a
rule the user already stated:

```bash
cd "<dir>" && opencode run --session <session-id> -m <model> --auto --format json "<answer + next step>" \
  < /dev/null > <scratch>/<title>-2.jsonl 2>&1
```

**Report to the user and stop** when the choice is theirs: config or rule changes,
behaviour/API changes, scope beyond the request, deleting or reverting work, or anything you
are not sure of. Present it as: what the worker did, what you verified, the open question, and
2–3 concrete options with your recommendation.

When the cause of a failure is a tool or skill (a linter false positive, a skill that misled the
worker), say so and propose the fix to the tool or skill — that fixes every future run.

## 7. Final report to the user

- Outcome: done / partial / stopped, with before → after numbers you measured yourself.
- What went well and what went wrong, citing the transcript.
- Commits the workers made (if allowed), and uncommitted changes left in `<dir>`.
- Proposed fixes to skills/tools, and the next step.
