---
description: Review all loaded skills for quality, generality, and command-abstraction issues
agent: plan
---

Scan every skill in the `<available_skills>` catalog.

**Skip built-in skills** — those whose `<location>` contains `<built-in>` (e.g., `customize-opencode`). They are not owned by the project and should not be reviewed.

For each remaining skill:

1. Load it via the `skill` tool.
2. **Webfetch cross-reference**: If the skill describes a tool, library, or external service, `webfetch` its official docs or repo to verify the information is accurate and current.
3. **URL freshness**: Extract every URL from the skill body, `webfetch` each one, and flag any that return 404 or are unreachable.
4. Check each rule below and flag violations.

## Checks

### Naming & Tiering
- Name matches the naming convention: `opencode-*` (general), `*-py`/`*-rs`/`*-ts` (language-specific), or bare name (tool).
- Directory name matches `name` frontmatter field.
- Description doesn't mention a specific project.
- **Disambiguation rule:** A bare-name tool is a violation ONLY when another variant of the same tool with a `-{{language_fullname}}` suffix already exists in `<available_skills>`. The `<available_skills>` list is the sole authority — external implementations in other languages are irrelevant. If a tool has exactly one skill in `<available_skills>`, bare name is mandatory and MUST NOT be flagged.

### Command Abstraction (three-signal rule)
For every `bash` block or shell command in the skill:

| If the instruction... | It must use | Flag |
|---|---|---|
| Teaches the skill's own subject (e.g., pixi showing `pixi run pytest`) | Concrete tool command | 🟡 if it uses `[[AGENTS.md::KEY]]` instead |
| Is an incidental project action (e.g., "run tests before PR" in a git skill) | `[[AGENTS.md::KEY]]` | 🔴 if it hardcodes a tool command |
| References code, file paths, or module structure | `{{template_vars}}` | 🔴 if it uses concrete paths |

Decision question: *Would a reader need to see the actual command to learn the tool?* Yes → concrete. No → KEY.

### Template Variables
- General skills should use: `{{project_name}}`, `{{module_name}}`, `{{project_root}}`.
- Language-specific `*-py` skills may use: `{{package}}`, `{{Module}}`.
- Language-specific `*-rs` skills may use: `{{crate}}`, `{{module}}`.
- Bare-name tool skills that are inherently language-specific (e.g., `pixi` → Python) MAY use that language's template vars — ✅ no flag.
- Flag if template variables don't match the language suffix.

### Generality
- Zero project-specific identifiers (no package names, no hardcoded paths). Convention/rule skills (`lele-syntax-*` etc.) are exempt — they document project standards.
- Description triggers correctly for the intended audience.
- Single responsibility — one skill = one domain.

## Output Format

```
## Skill: <name>

| Check | Result |
|-------|--------|
| Name valid | ✅ / ❌ |
| Name follows tier | ✅ / ❌ |
| Command abstraction | ✅ / 🟡 / 🔴 (list each violation) |
| Template vars match language | ✅ / 🔴 |
| Generality | ✅ / 🟡 / 🔴 |

Issues:
- ...
```

End with:
- **Summary**: X skills reviewed, Y issues found (Z critical, W minor).
