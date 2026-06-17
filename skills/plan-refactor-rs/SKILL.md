---
name: plan-refactor-rs
description: Use when auditing Rust source files against all loaded convention/pattern/rule skills. Loads every convention skill, then scans every .rs file in src/ for violations against those rules.
---

## Instructions

1. Scan the `<available_skills>` catalog in your system prompt. Load every skill whose name or description matches conventions, patterns, syntax, architecture rules, or project standards.
2. For every `.rs` file in `src/`, check compliance with each loaded rule set.
3. Report every violation with:
   - File path and line number
   - The rule being violated
   - Explanation of the violation
   - Suggested fix
