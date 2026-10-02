---
description: Symlink every global opencode skill into ~/.claude/skills so Claude Code can use them
agent: primary
---

Run the idempotent sync script:

```bash
bash ~/.config/opencode/scripts/sync-claude-skills.sh
```

It links every `~/.config/opencode/skills/<name>/` (with valid `name`+`description` frontmatter)
into `~/.claude/skills/<name>`, and removes stale/broken symlinks that point into the opencode
skills directory (e.g. retired skills or renamed dirs). The Claude-managed `synced/` directory is
left untouched. Re-run after adding, retiring, or renaming a global skill.
