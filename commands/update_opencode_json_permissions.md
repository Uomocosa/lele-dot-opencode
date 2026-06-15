---
description: Audit every skill on disk against the project's purpose and current permissions. For each skill, evaluate whether to add, keep, or remove it.
subtask: true
---

You are auditing which skills should be permitted in this project.

## Step 1: Find all skills on disk

Use `glob` to find every `SKILL.md` in:
- Global: `~/.config/opencode/skills/*/SKILL.md`
- Local/project: `.opencode/skills/*/SKILL.md`

Collect all results. For each, read the `name` field from YAML frontmatter.

## Step 2: Read the project to understand its purpose

Explore the project root to understand:
- **Language stack** — look for build/config files: `Cargo.toml`, `package.json`, `pyproject.toml`, `CMakeLists.txt`, `go.mod`, `pixi.toml`, etc.
- **Purpose and domain** — read `README.md`, `OBJECTIVE.md`, or any project-description files.
- **Project-specific agent instructions** — read `AGENTS.md` if it exists.
- **Current permissions** — read `opencode.json` (or `opencode.jsonc`) for the `permission.skill` block.

Identify what the project does and what tools/languages it uses.

## Step 3: For each skill on disk, report status and evaluate

Prefix every skill with its current permission status emoji:

| Emoji | Meaning |
|-------|---------|
| ✅ | Allowed in `permission.skill` with `"allow"` |
| ❌ | Not allowed (explicitly denied or absent from permissions) |
| 🗑️ | Stale — permission rule exists but skill file not on disk |

### For each non-stale skill, provide:
- **Add it?** Yes / No / Keep / Remove
- **Reason to add:** <why it helps the project>
- **Reason not to add:** <why it doesn't belong>
- **Reason to remove (if currently allowed):** <why it shouldn't be>

### For stale skills:
Just flag them for removal.

## Evaluation guidelines

- **General skills** (`opencode-*`): generally beneficial — keep unless they conflict with project rules.
- **Language-specific** (`*-rs`, `*-py`, `*-ts`): only keep/add if the project uses that language.
- **Bare-name tools** (`bevy`, `libp2p`, `pixi`): only keep/add if the project uses or is likely to use that tool/framework.
- **Stale rules**: always recommend removal.

## Output format

```
Legend:
✅ = Allowed | ❌ = Not allowed | 🗑️ = Stale (skill not on disk)

✅ opencode-git-workflow
  → Keep. General skill, always useful.

❌ lele-syntax-py
  → Skip. Project is Rust-only, Python skills irrelevant.

🗑️ libp2p-rust
  → Remove from permissions. No skill named "libp2p-rust" exists on disk.

❌ libp2p
  → Add. Project uses libp2p networking; skill provides guidance.
```

## Legend

Include this at the bottom:

```
✅ = Currently allowed in permissions | ❌ = Not allowed (denied or absent) | 🗑️ = In permissions but skill not on disk
```

## Notes

- **Read skills from disk using `read`** — do NOT use the `skill` tool to load them. The whole point is to discover skills that may not be loaded yet.
- Skip any skill whose directory has been deleted but the cache still references it.
- Built-in skills (like `customize-opencode`) are not in the global folder — they are hardcoded in opencode core. Do not propose adding them to permissions.
