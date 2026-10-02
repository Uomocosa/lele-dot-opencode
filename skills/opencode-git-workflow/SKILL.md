---
name: opencode-git-workflow
description: Use for git commands, commit messages, branch management, rebasing, merging, conflict resolution, stashing, and reverting. Commit conventions, atomic commits, rebase workflow, and dangerous-command safeguards.
---

# Git Workflow

## 0. Authorization Gate

**Never stage, commit, push, merge, rebase, or amend without an explicit command from the user.**
An explicit command is a direct statement ("commit", "stage that file", "push to origin",
"merge the PR"). "Yes"/"ok"/"go ahead"/silence do **not** count — ask. This overrides everything
below.

## 1. Commit Messages — Conventional Commits

```
<type>(<scope>): <imperative description>

[optional body — why, wrapped at 72]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `style`.
Lowercase after the type, no trailing period, imperative mood ("add", not "added"); breaking
changes get `!` (`feat!: change API`). Scope is optional but encouraged (`fix(mlp): …`).

## 2. Branches

`<type>/<short-description>` — e.g. `feat/session-persistence`, `fix/nan-loss`. Lowercase,
hyphenated, <50 chars, delete after merge.

## 3. Atomic Commits

One logical change per commit; it must pass tests (`[[AGENTS.md::RUN_ALL_TESTS]]`). Split when a
change spans two modules, mixes refactor + feature, or mixes mechanical renames with logic.
Combine only when changes are interdependent.

## 4. Rebase

Prefer rebase over merge for linear history.

```bash
git fetch origin && git rebase origin/main   # before pulling upstream
git rebase -i HEAD~N                          # cleanup before pushing: pick/fixup/squash/reword/edit
git push --force-with-lease                   # never bare --force
```

**Never rebase commits that exist on a shared branch.**

## 5. Conflicts

1. `git status` to list conflicts.
2. Resolve each file (choose a side or combine), remove the `<<<<<<<`/`=======`/`>>>>>>>`
   markers.
3. Verify: `[[AGENTS.md::RUN_ALL_TESTS]]`.
4. `git add <files>` then `git rebase --continue` (or `git rebase --abort` if stuck).

## 6. Stashing

```bash
git stash -u                              # include untracked
git stash push -m "wip: half-done refactor"
git stash list / git stash apply / git stash pop
```

Use to switch branches or rebase with a dirty tree. If the work spans hours, commit it on a
feature branch instead.

## 7. Undo

| Situation | Command |
|---|---|
| Undo a published commit | `git revert <commit>` (new commit) |
| Undo a local commit, keep changes staged | `git reset --soft HEAD~1` |
| Discard local commit + changes (careful) | `git reset --hard HEAD~1` |
| Unstage a file | `git reset HEAD <file>` |

## 8. Safeguards & Quick Reference

| Don't | Instead |
|---|---|
| `git push --force` | `git push --force-with-lease` |
| `git reset --hard HEAD~N` blindly | `git log --oneline -N` first |
| `git rebase main` without fetching | `git fetch origin && git rebase origin/main` |

```bash
git log --oneline --graph -20   # inspect
git diff / git diff --cached    # working / staged
git status
git checkout -b feat/foo ; git branch -d feat/foo
git clean -fd
```
