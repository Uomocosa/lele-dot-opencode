---
name: blind-review-file-rs
description: Use when the user wants a blind review of ONE Rust file — a tool-less `blind-reader` subagent sees only that file and explains what it is responsible for (round 1), then also sees the definitions of the types it uses and its atomic-delegate bodies (round 2); the main agent grades both answers against the real crate and proposes refactor previews in refactor-workflow-rs format. No edits.
---

# Blind Review — one file (Rust)

Measures **legibility**: can a reader with no crate context tell what this file is for from its
names alone (round 1), and with the types and delegate bodies (round 2)? The gap between the
reader's answer and the truth is the finding.

## Invocation

- `/blind-review-file-rs <path/to/file.rs>`. Also run per file by `blind-review-crate-rs`.
- Read-only: this skill never edits code.

## 1. Setup

Load `lele-rs` and `definition-abstraction` (main agent only — the reader gets the primer in
`references/PROMPTS.md`, never the crate).

## 2. Round 1 — the file only

Spawn the **`blind-reader`** subagent (it has no file tools). Send the round-1 prompt from
`references/PROMPTS.md` with the file's text pasted in. Never paste anything else.

## 3. Round 2 — plus context

```bash
export PATH="$HOME/.cargo/bin:$PATH" && python3 ~/.config/opencode/skills/blind-review-file-rs/scripts/context.py <file> 2>&1
```

Send its output with the round-2 prompt to the **same** subagent (Claude Code: `SendMessage` to
its id; opencode: `task` with the previous `session_id`), so it revises its own answer.

## 4. Grade

Now read the file's real users in the crate (grep for its items) and grade each round with
`references/REPORT.md`: ✅ correct · 🟡 partial · ❌ wrong, one line of evidence each.
Round-1 miss = naming problem; round-2 miss = abstraction problem. An agent is a kinder reader
than a human: treat confusion as strong signal, understanding as weak signal.

## 5. Report

Emit the row (and, standalone, the table header) from `references/REPORT.md`, then the
**proposed edits** in `refactor-workflow-rs` format — `batch | lens | change | why` plus literal
`// before` / `// after` previews, driven by the confused names and the misses. End with:
**"Feed these into `/refactor-workflow-rs`?"**

## Hard rules

- The reader sees only what the scripts and prompts give it; never let it read files.
- Report the reader's answers verbatim (trim, don't rewrite).
- No edits, no commit.
