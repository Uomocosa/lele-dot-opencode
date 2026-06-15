---
description: Scan all skills on disk, read current opencode.json permissions, and propose glob pattern changes to cover newly added skills.
subtask: true
---

You are auditing skill coverage in this project's `opencode.json`.

## Step 1: Find all skills on disk

Use `glob` to find every `SKILL.md` in these locations:

- Global: `~/.config/opencode/skills/*/SKILL.md`
- Local/project: `.opencode/skills/*/SKILL.md`

Collect every result.

## Step 2: Read each SKILL.md to get the name

For each skill found, use `read` to get the `name` field from its YAML frontmatter (between the first `---` delimiters). Extract the `name:` value.

Collect all names into a full list.

## Step 3: Read current opencode.json permissions

Read the project's `opencode.json` (or `opencode.jsonc`) from any of these locations:

- `./opencode.json`
- `./opencode.jsonc`
- `.opencode/opencode.json`

Extract the current `permission.skill` object. If no `permission` or `permission.skill` exists, record that as empty.

## Step 4: Classify each skill by name pattern

For each skill name, classify it into one of these categories:

| Pattern | Category | Matched by |
|---|---|---|
| `opencode-*` | General | `"opencode-*": "allow"` glob |
| `*-py` | Python-specific | `"*-py": "allow"` glob |
| `*-rs` | Rust-specific | `"*-rs": "allow"` glob |
| `*-ts` | TypeScript-specific | `"*-ts": "allow"` glob |
| Bare name (e.g. `pixi`, `libp2p`, `bevy`) | Tool — must be exact | `"pixi": "allow"` (exact) |
| `*-{{language_fullname}}` (e.g. `grpc-rust`) | Multi-language tool — must be exact | `"grpc-rust": "allow"` (exact) |

## Step 5: Compare current permissions vs what's needed

For each category:

- **General (`opencode-*`):** If any skill matches this pattern, the glob `"opencode-*": "allow"` should be present.
- **Language-specific (`*-py`, `*-rs`, `*-ts`):** If any skill matches, the corresponding glob should be present.
- **Bare-name tools:** Each must be listed by its exact name.
- **Multi-language tools (`*-{{language_fullname}}`):** Each must be listed by its exact name.

Report:
- Which globs/exact names are **missing** (skills exist on disk but not covered by current permissions)
- Which rules are **redundant** (permissions for tools/skills that no longer exist on disk)
- Which rules are **correct** (match)

## Step 6: Propose changes

Present a clear proposal showing:

1. The current `permission.skill` block (or note it's missing).
2. The recommended `permission.skill` block that covers all skills on disk.
3. A diff-like summary of what changed.

End with: "Would you like me to apply this change to opencode.json?"

## Notes

- **Read skills from disk using `read`** — do NOT use the `skill` tool to load them. The whole point is to discover skills that may not be loaded yet.
- Skip any skill whose directory has been deleted but the cache still references it.
- Built-in skills (like `customize-opencode`) are not in the global folder — they are hardcoded in opencode core. Do not propose adding them to permissions.
