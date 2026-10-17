---
name: grill-me
description: Use when the user types "grill me" or explicitly asks to be interviewed relentlessly about a plan or design. User-invoked only; delegates to the `grilling` skill.
disable-model-invocation: true
---

Call the `skill` tool with id `grilling` (Claude Code: the `Skill` tool with "grilling"), then follow that skill exactly.

This skill is a thin trigger only. All interview behavior lives in `grilling`.

---

Source: <https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md>
