---
name: opencode-mcp
description: Use when creating, configuring, or wiring a global MCP server in opencode. Covers opencode.json mcp block, local vs remote types, command/args, env var interpolation {env:VAR}, enabled flag, and verification.
---

# opencode-mcp — Global MCP Server Setup (General, Global Only)

This skill is **global/general only**. MCP servers are declared in the global config. No project-local `.opencode/opencode.json` variant.

## 1. Where MCP Lives

* Global config file: `~/.config/opencode/opencode.json` (JSON, not JSONC). If it does not exist, create it.
* Key: top-level `mcp: { "<server_name>": { ... } }`.
* Opencode reads this file on startup — restart after changes.

## 2. Minimal Shape

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "test-orchestrator": {
      "type": "local",
      "command": ["{env:FBX_MCP_EXE}"],
      "enabled": true
    }
  }
}
```

### Fields

| Field | Required | Values | Notes |
|---|---|---|---|
| `type` | yes | `local` \| `remote` | `local` spawns a command; `remote` connects to URL |
| `command` | for `local` | `string[]` | Executable + args. Use `"{env:VAR}"` for env interpolation — do not hardcode secrets |
| `url` | for `remote` | `string` | Remote MCP endpoint |
| `enabled` | no | `boolean` | Default `true`. Set `false` to keep config but disable |

## 3. Template — New MCP Server

Replace `{{mcp_name}}`, `{{command}}`, `{{env_var}}`:

```json
{
  "mcp": {
    "{{mcp_name}}": {
      "type": "local",
      "command": ["{env:{{env_var}}}"],
      "enabled": true
    }
  }
}
```

With args:

```json
{
  "mcp": {
    "{{mcp_name}}": {
      "type": "local",
      "command": ["{env:{{env_var}}}", "--port", "3000"],
      "enabled": true
    }
  }
}
```

Remote variant:

```json
{
  "mcp": {
    "{{mcp_name}}": {
      "type": "remote",
      "url": "https://example.com/mcp",
      "enabled": true
    }
  }
}
```

## 4. Steps to Add a Server

1. Ensure `~/.config/opencode/opencode.json` exists (create with `$schema` if missing).
2. Merge the new entry under `mcp` — do not overwrite existing servers.
3. Export the env var referenced in `command` (e.g., `export FBX_MCP_EXE=/path/to/bin`).
4. Restart opencode and verify: `opencode mcp list` or check startup logs for `mcp:<server_name>`.

## 5. Common Mistakes

* Using a bare string for `command` instead of an array — must be `["bin", "arg1"]`.
* Hardcoding a secret path instead of `"{env:VAR}"` — breaks portability.
* Forgetting `enabled: true` and wondering why the server is inert (defaults to enabled, but explicit is clearer).
* Editing a project-local `.opencode/opencode.json` expecting global effect — MCP is global only.
* Not restarting opencode after editing the JSON.

## 6. Example — Restoring `test-orchestrator`

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "test-orchestrator": {
      "type": "local",
      "command": ["{env:FBX_MCP_EXE}"],
      "enabled": true
    }
  }
}
```

If `permission.skill` is also needed (e.g., `definition-*`, `opencode-*`), keep it alongside `mcp` in the same file — do not split into `opencode.jsonc`.

## 7. When NOT to Use

* Project-specific tool wiring — use `devenv-rs` or crate-level config instead.
* Skill definitions (`definition-*`) — those are permissions, not MCP.
