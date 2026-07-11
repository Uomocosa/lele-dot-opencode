---
name: opencode-git-workflow
description: Use when the user asks about git commands, commit messages, branch management, rebasing, merging, resolving merge conflicts, stashing, reverting, or any git workflow. Provides commit message conventions, atomic commit rules, branching strategy, rebase workflow, conflict resolution protocol, stashing patterns, and dangerous-command safeguards.
---

# Git Workflow

## 0. Authorization Gate

**Never stage, commit, push, merge, rebase, or amend without an explicit command from the user.**
An "explicit command" is a direct statement such as "commit", "stage that file",
"push to origin", or "merge the PR". Vague acknowledgments like "yes", "ok",
"go ahead", or mere silence do NOT count. If the user's intent is ambiguous,
ask: "I need an explicit command to proceed. What would you like me to do?"

This rule overrides all other instructions in this skill.

## 1. Commit Message Convention

Use **Conventional Commits** format:

```
<type>(<scope>): <imperative description>

[optional body]

[optional footer]
```

### Types

| Type | When to use |
|------|-------------|
| `feat:` | A new feature |
| `fix:` | A bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code change that neither fixes a bug nor adds a feature |
| `test:` | Adding or fixing tests |
| `chore:` | Build process, CI, tooling, dependencies |
| `perf:` | Performance improvement |
| `style:` | Formatting (not code logic) |

### Rules

- **Imperative present tense:** "Add feature" not "Added feature"
- **Lowercase after type:** `feat: add pagination` not `feat: Add pagination`
- **No period at end of subject line**
- **Scope optional** but encouraged when module-specific: `fix(mlp): handle NaN in loss`
- **Breaking changes:** append `!` after type/scope: `feat!: change API signature`
- **Body** wraps at 72 characters, explains *why* not *what*

### Examples

```
feat: add session persistence across restarts

Persist session state to disk on every tick so reconnecting peers
can resume without full re-sync.
```

```
refactor(api): extract normalization from handler
```

```
fix(auth): return error on invalid token instead of panic
```

## 2. Branch Naming

```
<type>/<short-description>
```

### Patterns

| Pattern | Example |
|---------|---------|
| `feat/<desc>` | `feat/session-persistence` |
| `fix/<desc>` | `fix/nan-loss` |
| `refactor/<desc>` | `refactor/extract-normalization` |
| `chore/<desc>` | `chore/update-deps` |
| `docs/<desc>` | `docs/api-readme` |

### Rules

- Lowercase, hyphens between words
- Keep under 50 characters
- Delete branch after merge

## 3. Atomic Commits

One commit = one logical change. A commit must:

- **Pass tests** (run via `[[AGENTS.md::RUN_ALL_TESTS]]` — see `## Project Commands` in AGENTS.md)
- Be a single concern (don't mix formatting changes with logic changes)

### When to split

Split into multiple commits when a change touches:
- Two unrelated modules (e.g., ML + Dataset)
- A refactor + a feature in the same file
- Mechanical changes (renames, re-exports) + logic changes

### When to combine

Combine into one commit when:
- Fixing a bug introduced in the same branch's earlier commit (rebase + squash)
- Changes are interdependent and don't pass tests individually

## 4. Rebase Workflow

Prefer rebase over merge to maintain a linear history.

### Before pushing (clean up local history)

```bash
git rebase -i HEAD~N
```

Common operations:
- `pick` — keep as-is
- `fixup` / `f` — keep changes but discard the commit message
- `squash` / `s` — combine with previous, edit message
- `reword` / `r` — edit commit message only
- `edit` / `e` — stop to amend

### Before pulling upstream

```bash
git fetch origin
git rebase origin/main
```

### After rebasing

```bash
git push --force-with-lease
```

### Golden rule

**Never rebase commits that exist on a shared branch** (main, release, or another person's branch).

## 5. Conflict Resolution Protocol

1. **List conflicted files:**
   ```bash
   git status
   ```
2. **Open each file and find conflict markers:**
   ```
   <<<<<<< HEAD
   (your/current change)
   =======
   (incoming change)
   >>>>>>> branch-name
   ```
3. **For each conflict:**
   - Understand both sides
   - Choose one side, or write a combined version
   - **Remove the conflict markers**
   - Verify the result works: `[[AGENTS.md::RUN_ALL_TESTS]]` for affected modules
4. **Stage and continue:**
   ```bash
   git add <resolved-files>
   git rebase --continue
   ```
5. **If stuck:** `git rebase --abort` or `git merge --abort`

## 6. Stashing

```bash
# Save current work (including untracked files)
git stash -u

# Save with a descriptive message
git stash push -m "wip: half-done refactor of MLP training"

# List stashes
git stash list

# Apply and keep on the stack
git stash apply

# Apply and drop
git stash pop
```

### When to stash
- Need to switch branches temporarily
- Need to pull/rebase but have dirty working tree

### When NOT to stash
- Work spanning more than a few hours — commit it (even as `wip:`) on a feature branch

## 7. Revert vs. Reset

| Situation | Command | Effect |
|-----------|---------|--------|
| Undo a **published** commit | `git revert <commit>` | Creates a new commit that undoes changes |
| Undo a **local** commit | `git reset --soft HEAD~1` | Keeps changes staged |
| Discard a local commit and its changes | `git reset --hard HEAD~1` | Destroys changes. Use with extreme caution |
| Unstage a file | `git reset HEAD <file>` | Keeps file changes but unstages them |

## 8. PR / Review Flow

1. **Before opening a PR:**
   - Run tests: `[[AGENTS.md::RUN_ALL_TESTS]]`
   - Rebase onto latest `main`
   - Squash fixup commits into logical units
2. **During review:**
   - Address feedback in new commits (don't amend yet)
3. **Before merge:**
   - Squash fixup/response commits
   - Rebase onto latest `main` again
4. **Merge strategy:** Prefer **squash merge** or **rebase merge**.

## 9. Dangerous Command Safeguards

| Don't | Instead |
|-------|---------|
| `git push --force` | `git push --force-with-lease` |
| `git reset --hard HEAD~N` without checking | `git log --oneline -N` first |
| `git commit -m "..."` without body | Write multi-line commit messages explaining *why* |
| `git rebase main` without fetching first | `git fetch origin && git rebase origin/main` |

## 10. Quick Reference

```bash
# Inspect
git log --oneline --graph -20
git diff
git diff --cached
git status

# Branch
git checkout -b feat/foo
git branch -d feat/foo

# Remote
git fetch origin
git pull --rebase
git push --force-with-lease

# Cleanup
git clean -fd
```
