---
name: plan-remove-dead-code-py
description: Use when searching for Python files whose primary pub item has zero internal consumers in the package. Searches for import references, then presents candidates for user evaluation.
---

## Goal
Find and report files whose primary `pub` item has zero internal consumers in the codebase.

## Phase −1 — CRITICAL setup (blocking)
Before searching:
1. Load `lele-syntax-py` and read it in full — its `*Method/` subpackages, PascalCase
   subpackages, `__HELPER_DIR__` and new-import-system re-exports change what a "consumer" is.
2. Load `pixi` when the project has `pixi.toml` / `[tool.pixi]`; verification runs through it.
3. Run the **baseline** test suite once and record pre-existing failures.
4. Open the first reply with a **Setup:** block (skills loaded, files read, baseline result).
   No candidate list may appear before it.

## Detection Method
For each `.py` file that defines a class or top-level function:

1. Identify the item name.
2. Search the package for all of these patterns:
   - `from {{package}}.` or `import {{package}}.` references (direct import).
   - Re-exports in any `__init__.py` (e.g., `from .Module import Item`).
   - Imports guarded by `TYPE_CHECKING` blocks.
   - Dynamic imports (`importlib.import_module`, `__import__`).
3. Exclude the file's own imports and its module's `__init__.py` re-export.
4. If zero external references remain, the file is a removal candidate.
5. Before finalizing, check for string-based references (e.g., `"Module.Item"` in config or registry patterns) — flag these for user review rather than skipping automatically.

## Exemptions
- Items explicitly intended as public API for external consumers. Determine this by checking:
  - Is the name listed in the package's `__all__` variable (in any `__init__.py`)?
  - Is the name re-exported from a top-level `__init__.py` without a leading underscore?
  - Does the name appear in public docs or a `README` usage example?
  - When uncertain, ask the user rather than assuming.
- Do not remove public API surface without explicit confirmation.

## Dry-Run Mode
Before any deletion, list all candidates and present them for confirmation:
- Show file path, primary item name, and zero-consumer count
- Present all candidates together as a group and require explicit user approval before proceeding
- Skipping user approval is a violation

## Verification
After removal, run tests:
```
[[AGENTS.md::RUN_ALL_TESTS]]
```
(Resolved from `## Project Commands` in AGENTS.md.)
