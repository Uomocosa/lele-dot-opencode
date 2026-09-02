---
description: Save current conversation as repo-wide summary in .opencode/summaries/
agent: primary
---

Create a repo-wide conversation summary in `.opencode/summaries/` (projects/.opencode/summaries/).

**Input:** `$ARGUMENTS` as slug (e.g., `global-counter-candidate-1-strict`). If empty, use current branch name sanitized (`git branch --show-current`).

**Steps:**

1. Ensure dir exists: `mkdir -p projects/.opencode/summaries`
2. Compute filename: `date +%Y_%m_%d_%H_%M`-`<slug>.md` (sanitize slug: `tr -cs 'a-zA-Z0-9-' '-'` lowercased, trim `-`)
3. Gather context (read-only):
   - `git log --oneline -10`
   - `git status --short`
   - `git diff --stat` (staged + unstaged)
   - `git worktree list` (if any `candidate/*` worktrees)
   - `ls freenet_example/.local-run/` (recent mainnet logs)
4. Write `projects/.opencode/summaries/<filename>.md` with **only bullets, no prose**, in this exact structure:

```markdown
# <slug> — YYYY-MM-DD HH:MM

- goal: <one bullet, why this conversation exists>
- why: <one bullet, why this approach vs alternatives>

- created: <bullets, each `path` — what new files/dirs/branches/worktrees were created>
- edited: <bullets, each `path:line` — what was modified and why (one line per file)>
- verified: <bullets, `devenv tasks run <task> 2>&1` results, `cargo test` counts, `freenet:run-local-mainnet` PASS/FAIL with log path>
- decisions: <bullets, candidate choice, `+1` vs `N=5+sig`, `O(users)` vs `O(gap)` tradeoff>
- next: <bullets, what remains for candidate/2-signed etc.>
```

Keep bullets only. No introduction, no conclusion, no emojis. Reference paths with `file:line` where applicable.

5. Print created path: `echo "saved: projects/.opencode/summaries/<filename>"`

Do not `git add`/`commit`/`push` — just write files. Repo-wide, not per-crate.

Example: `/save-conversation global-counter-candidate-1-strict` → `projects/.opencode/summaries/2026_09_02_15_40-global-counter-candidate-1-strict.md`
