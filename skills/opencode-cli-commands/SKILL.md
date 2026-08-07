---
name: opencode-cli-commands
description: |
  CRITICAL — Load this skill IMMEDIATELY any time the word "opencode" appears in a user
  message. Covers: version check, upgrade, session management, server/headless mode,
  models, providers, and all CLI subcommands. This is THE reference for how to operate
  the opencode CLI tool itself. Works with any project.
---

# OpenCode CLI Commands

**IF A USER MENTIONS "opencode" — STOP AND LOAD THIS SKILL.** Do not guess CLI
flags, version numbers, or upgrade procedures. Everything you need is here.

## Version Check

```bash
opencode --version
```

Compare against latest GitHub release:

```bash
curl -s https://api.github.com/repos/anomalyco/opencode/releases/latest | grep '"tag_name"'
```

## Upgrade

**Always prefer the built-in upgrade command.** It handles platform detection,
download, and binary replacement correctly.

```bash
opencode upgrade                    # upgrade to latest
opencode upgrade v1.18.14           # upgrade to a specific version
opencode upgrade --method curl      # force curl method (most reliable)
```

Available methods: `curl`, `npm`, `pnpm`, `bun`, `brew`, `choco`, `scoop`.

### Install location

The curl method installs to `~/.opencode/bin/opencode` (standalone ELF binary).
If opencode was originally installed via `npm i -g opencode-ai`, the PATH symlink
may still point to the old npm location. After upgrading via curl, fix it:

```bash
ln -sf ~/.opencode/bin/opencode $(which opencode)
```

### Known pitfalls

- **"Text file busy"** — the running opencode cannot overwrite itself. The upgrade
  handles this by installing the new binary alongside the old one.
- **npm method may fail** — the npm package name is `opencode-ai` (not `opencode`).
  Prefer curl.

## Session Flags (used with `opencode [project]`)

| Flag | Purpose |
|------|---------|
| `-c, --continue` | Resume the last session in the directory |
| `-s, --session <id>` | Resume a specific session by ID |
| `--fork` | Fork a session when continuing (new branch, old intact) |
| `-m, --model <provider/model>` | Override the default model |
| `--agent <name>` | Use a specific agent |
| `--prompt <text>` | Send a prompt directly (non-interactive) |
| `--auto` | Auto-approve permissions (dangerous) |
| `--mini` | Start minimal interactive interface |

## Session Management

```bash
opencode session list                        # list all sessions
opencode session delete <sessionID>          # delete a session
opencode export [sessionID]                  # export session as JSON
opencode export --sanitize [sessionID]       # export with sensitive data redacted
opencode import <file>                       # import session from JSON or URL
```

## Headless / Server Mode

```bash
opencode serve                               # start headless server (--port, --hostname)
opencode web                                 # start server + open web UI
opencode serve --port 4090 --hostname 0.0.0.0 --mdns
```

## Models & Stats

```bash
opencode models [provider]                   # list available models
opencode stats                               # show token usage and cost
```

## Providers / Auth

```bash
opencode providers                           # manage AI providers and credentials
# alias: opencode auth
```

## MCP Management

```bash
opencode mcp add [name]                      # add an MCP server
opencode mcp list                            # list MCP servers
opencode mcp auth [name]                     # authenticate OAuth MCP server
opencode mcp debug <name>                    # debug OAuth connection
```

## Agents

```bash
opencode agent create                        # create a new agent
opencode agent list                          # list all agents
```

## GitHub / PR

```bash
opencode github                              # manage GitHub agent
opencode pr <number>                         # fetch and checkout a GitHub PR branch
```

## Plugins

```bash
opencode plugin <module>                     # install plugin and update config
# alias: opencode plug
```

## Other Commands

```bash
opencode completion                          # generate shell completion script
opencode acp                                 # start ACP (Agent Client Protocol) server
opencode debug                               # debugging tools
opencode uninstall                           # uninstall and remove all related files
opencode db                                  # database tools
```

## Post-Upgrade Verification

After any upgrade, verify:

```bash
opencode --version
which opencode
```

The binary should report the expected version, and `which opencode` should point to
`~/.opencode/bin/opencode` (curl install) or the npm/nvm bin directory (npm install).
