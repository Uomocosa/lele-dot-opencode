---
name: opencode-create-skill
description: Create reusable opencode agent skills. Use when the user asks to create a new skill, make a skill for X, or set up agent instructions. ALWAYS evaluates existing alternatives before creating anything new. Enforces maximal generality so skills work across ANY project using this opencode setup.
---

# Create Skill

You are a skill architect. Your job is to create skills that are **maximally general across projects, maximally reusable**, and never project-specific.

## Phase 1: Community Discovery (MANDATORY)

**Do NOT create a skill until you have searched the community ecosystem.**

1. Search GitHub for relevant opencode skills: `anthropics/skills`, `vercel-labs/skills`, `mattpocock/skills`, `obra/superpowers`.

2. **Verify each source via `webfetch`.** Do not just list names — fetch the repo page or its README to confirm the skill exists, is still maintained, and actually does what the name suggests.

For every match found, report to the user:
   - Skill name, source repo
   - What it does (summary)
   - Your evaluation: does it fully cover the need? Partially? Not at all?

**If an adequate existing skill exists:** Recommend it and stop. Do not create a duplicate.

**Only proceed to Phase 2 if** no existing skill adequately covers the need.

## Phase 2: Generality-first Design

Before writing any file, design the skill to be **project-agnostic**:

### Generality Rules (enforced)
1. **Zero project-specific identifiers.** No package name, no module path from this project. Use template variables: `{{project_name}}`, `{{module_name}}`, `{{project_root}}`.
   - **Exception:** Convention/rule skills (whose purpose is to document a specific project's code standards, e.g., `lele-syntax-py`) are allowed to reference project-specific package names and architecture. They should still use template variables where possible.
   - **Exception:** Tool-name skills (e.g., `pixi`, `cargo`, `npm`) keep their bare name — the tool's interface IS the subject.
2. **Description-first.** The `description` field must make sense in ANY project. Test: read the description aloud — if it mentions a specific project, rewrite.
3. **Single responsibility.** One skill = one domain. If the skill does two unrelated things, split it.
4. **Progressive disclosure.** The `name` + `description` must be enough for an agent to decide whether to load the skill. Put the most critical instructions first.
5. **Flagging table** (enforced by `/review-skills` command):

| Scenario | Flag |
|---|---|---|
| Tool skill uses `[[AGENTS.md::KEY]]` for its own core action (e.g., pixi skill: `[[AGENTS.md::RUN_ALL_TESTS]]` instead of `pixi run pytest`) | 🟡 Flag — obscures the tool's interface |
| Workflow skill hardcodes a tool command (e.g., git skill: `pixi run pytest` instead of `[[AGENTS.md::RUN_ALL_TESTS]]`) | 🔴 Flag — breaks portability |
| Convention/pattern skill hardcodes a tool command | 🟡 Flag — same reason, lower severity |
| Convention/pattern skill hardcodes a language-native toolchain command (e.g., `cargo` for `*-rs`, `pip`/`pytest` for `*-py`, `npm`/`tsc` for `*-ts`) | ✅ No flag — teaching the language's native tooling |
| Tool skill uses `[[AGENTS.md::KEY]]` for an incidental action (e.g., in a PR checklist) | ✅ No flag |
| Language-specific skill (`*-py`, `*-rs`, `*-ts`) uses wrong template variables for that language | 🔴 Flag — breaks in target language |
| Bare-name tool skill that is inherently language-specific (e.g., `pixi` → Python) uses that language's template vars | ✅ No flag — expected for a language-tied tool |

### Structure template

```
skill-name/
  SKILL.md            # YAML frontmatter + instructions
  references/         # Detailed docs, test prompts, edge cases
  scripts/            # Executable utilities (bash, python, etc.)
  assets/             # Templates, static files
```

## Phase 3: Naming & Tiering

Every skill must follow the naming convention so per-project filtering works.

### Naming — tier decides suffix

* **General — opencode (`opencode-*`):** General opencode workflow/tooling (e.g., `opencode-git-workflow`, `opencode-mcp`). Always general, never language-specific.
* **General — definitions (`definition-*`):** General language-agnostic definitions and pseudocode (e.g., `definition-function-taxonomy`). Always general, never language-specific.
* **Language-specific (`*-rs`, `*-py`, `*-ts`):** Any skill tied to a single language MUST carry the suffix — including language-specific tools/crates (e.g., `bevy-rs`, `avian-rs`) and convention skills (e.g., `lele-syntax-rs`). A language-specific skill without a suffix is a violation.
* **Language-agnostic tool (bare `{{tool_name}}`):** A cross-language protocol/platform MUST be bare with no suffix (e.g., `libp2p`, `freenet`). Adding `-rs`/`-py`/`-ts` to a language-agnostic tool is a violation. Main example: `libp2p` stays `libp2p`.

No `*-(language_fullname)` multi-variant pattern — reuse `*-rs`/`*-py`/`*-ts` for per-language variants; the bare name is the agnostic protocol.

| Pattern | Category | When to use | Example | Permissions filter |
|---|---|---|---|---|
| `opencode-*` | General workflow | Opencode workflow/tooling | `opencode-git-workflow` | `"opencode-*": "allow"` (glob) |
| `definition-*` | General definitions | Language-agnostic definitions/pseudocode | `definition-function-taxonomy` | `"definition-*": "allow"` (glob) |
| `{{tool_name}}` (bare) | Language-agnostic tool | Cross-language platform/protocol | `libp2p`, `freenet`, `pixi` | `"name": "allow"` (exact) |
| `*-rs` / `*-py` / `*-ts` | Language-specific | Any single-language content (tool crate + conventions) | `bevy-rs`, `lele-syntax-rs` | `"*-rs": "allow"` (glob) |

### Three tiers of skills

| Tier | Location | Scope | Example |
|---|---|---|---|
| **General — opencode** (`opencode-*`) | `~/.config/opencode/skills/` | Any project, any language | `opencode-git-workflow` |
| **General — definitions** (`definition-*`) | `~/.config/opencode/skills/` | Any project, any language | `definition-function-taxonomy` |
| **Language-specific** (`*-rs`/`*-py`/`*-ts`) | `~/.config/opencode/skills/` | Filtered per-project via permissions | `bevy-rs`, `lele-syntax-rs` |
| **Language-agnostic tool** (bare) | `~/.config/opencode/skills/` | Always listed, never auto-loaded | `libp2p`, `freenet` |
| **Project-specific** | `.opencode/skills/` in each repo | That project only | Internal conventions |

### Per-project filtering

Each project's `opencode.json` uses `permission.skill` to select which global skills are visible:

```json
{
  "permission": {
    "skill": {
      "*": "deny",
      "opencode-*": "allow",
      "definition-*": "allow",
      "*-py": "allow",
      "pixi": "allow"
    }
  }
}
```

Last matching rule wins. Project-specific skills in `.opencode/skills/` are always listed regardless of global permissions.

## Phase 4: Drafting

Create the `SKILL.md` with:

```yaml
---
name: skill-name            # lowercase, hyphens, 1-64 chars
description: |              # 1-1024 chars, must trigger correctly
  Use when... [trigger conditions]. Works with any project.
---
```

Then the body. Structure it for how agents actually read:
- Most important instructions FIRST
- Step-by-step workflow
- Examples with concrete inputs/outputs
- Common mistakes and edge cases

### Template variable convention

Use language-agnostic template variables. When the skill IS language-specific (`*-py`, `*-rs`, etc.), use that language's idiom:

| Context | Variable |
|---------|----------|
| Unspecified/general | `{{project_name}}`, `{{module_name}}`, `{{project_root}}` |
| Python (`*-py`) | `{{package}}`, `{{Module}}` |
| Rust (`*-rs`) | `{{crate}}`, `{{module}}` |

## Phase 5: Validation

### Principle of Least Flag

**Only flag clear, mechanical violations.** If you find yourself debating internally whether something is a violation, it passes. False negatives (missing a borderline issue) are acceptable; false positives (flagging correct code) erode trust in the command and create back-and-forth loops. When a check is ambiguous, the answer is "no flag."

### Deterministic checks

Every check below must resolve to a binary yes/no from data on disk. No "would a hypothetical agent..." reasoning.

| Check | Pass condition |
|-------|----------------|
| Name valid? | Lowercase, hyphens, 1-64 chars. `name` frontmatter == directory basename. |
| Name follows tier? | `opencode-*` → general. `*-py`/`*-rs`/`*-ts` → language-specific. Bare name → tool. Check against **this project's `<available_skills>` and AGENTS.md manifest**, not external reality. A bare-name tool is a violation ONLY when another variant of the same tool with a `-{{language_fullname}}` suffix already exists in `<available_skills>`. The `<available_skills>` list is the sole authority — external implementations in other languages are irrelevant. |
| Zero project references? | No literal package name or project identifier in code blocks or description. Convention/rule skills (`lele-syntax-*` etc.) are exempt — they document project standards. |
| Commands follow three-signal rule? | For each `bash` block: teaching the skill's own tool → concrete. Incidental project action → `[[AGENTS.md::KEY]]`. Language-native toolchain (`cargo` for `*-rs`, `pytest` for `*-py`, `npm` for `*-ts`) → concrete (explicit exception). |
| Template vars match language? | General: `{{project_name}}`/`{{project_root}}`/`{{module_name}}`. `*-py`: add `{{package}}`/`{{Module}}`. `*-rs`: add `{{crate}}`/`{{module}}`. Using a general var in a language-specific skill is NOT a violation. |
| URL freshness? | For every external URL in the skill body, `webfetch` it. Only 4xx/5xx/unreachable is a violation. Redirects and slow responses are fine. |
| Version targeting? | Not a check — tool skills may pin a version. Being behind latest is never a violation. |

## Phase 6: Post-Creation — Permission Check

After creating the skill, check whether the project's `opencode.json` permissions cover it:

1. Read the project's `opencode.json` (or `opencode.jsonc`) and locate `permission.skill`.
2. Based on the skill's name pattern:
   - If it's a **general** skill (`opencode-*`), check that `"opencode-*": "allow"` exists.
   - If it's **language-specific** (`*-py`/`*-rs`/`*-ts`), check the corresponding glob exists.
   - If it's a **bare-name tool** (e.g. `pixi`, `libp2p`), check it's listed by exact name.
   - If it's a **multi-language tool** (`*-{{language_fullname}}`), check it's listed by exact name.
3. If the permission is missing, propose updating `opencode.json` with the needed rule.
4. After saving, tell the user to quit and restart opencode for changes to take effect.

Refer to `/update_opencode_json_permissions` for a full scan of all skills vs permissions.
