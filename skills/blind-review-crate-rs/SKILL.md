---
name: blind-review-crate-rs
description: Use when the user wants a blind legibility review of a Rust crate — samples N files (default 5) from src/ and methods/ (skipping __basic__/, mod.rs, lib.rs, main.rs, build.rs, constants.rs, tests, generated and recently reviewed files), runs blind-review-file-rs on each with parallel tool-less subagents, then reports one combined table and refactor-workflow-rs-format edit previews. No edits.
---

# Blind Review — crate sample (Rust)

A spot check of naming and abstraction trends, not a crate-wide audit.

## Invocation

- `/blind-review-crate-rs <crate> [count=5] [--weight random|churn|size] [--seed N]`
- For one file, use `blind-review-file-rs` directly.

## 1. Setup

Load `blind-review-file-rs` and follow its Setup. Its steps 2–4 are the per-file procedure.

## 2. Sample

```bash
python3 ~/.config/opencode/skills/blind-review-crate-rs/scripts/sample.py <crate> --count <n> [--weight churn] [--seed N] 2>&1
```

Echo the seed and the picked files. `--weight churn` favours often-changed files; `size` favours
large ones. Files listed in `<crate>/.review-history` are skipped (`--no-history` to ignore).

## 3. Review each file

Run `blind-review-file-rs` steps 2–4 for every picked file. Spawn all round-1 `blind-reader`
subagents **in parallel** (one per file), then all round-2 continuations in parallel, then grade.

## 4. Report

1. One combined table (`blind-review-file-rs/references/REPORT.md`), one row per file, plus the
   evidence lines.
2. **Trends** — up to 3 lines: names or patterns that confused readers across files.
3. **Proposed edits** in `refactor-workflow-rs` format (`batch | lens | change | why` + literal
   before/after previews), at most 5 batches.
4. **"Feed these into `/refactor-workflow-rs`?"**

## 5. Record

```bash
python3 ~/.config/opencode/skills/blind-review-crate-rs/scripts/sample.py <crate> --record <file>... 2>&1
```

## Hard rules

- Every rule of `blind-review-file-rs` applies.
- No edits, no commit.
