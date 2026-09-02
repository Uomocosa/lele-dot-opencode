# Freenet Contract References

Pinned contract analyses next to `SKILL.md`. Each file documents one official Freenet app's contract(s) against `freenet-contract-design` §0-9 and the four-function wiring.

## Files (specific tag pin)

| File | Source | Tag / Head | Status |
|------|--------|------------|--------|
| `RIVER_CONTRACT_STRUCTURE.md` | `freenet/river` `contracts/room-contract` | `v0.1.51` (`5e84434d`) | stable |
| `PING_CONTRACT_STRUCTURE.md` | `freenet/freenet-core` `apps/freenet-ping` | `v0.2.132` (`0ca7e02b`) | stable — reference CRDT |
| `WEBSITE_CONTRACT_STRUCTURE.md` | `freenet/freenet-core` `crates/website-contract` | `v0.2.132` | stable |
| `DELTA_CONTRACT_STRUCTURE.md` | `freenet/delta` `contracts/site-contract` | `HEAD f0257f2c` (2026-08-30) — no tag | WIP — no published tags |
| `RAVEN_CONTRACT_STRUCTURE.md` | `freenet/raven` (4 shards) | `v0.1.4` (`fa9acdbc`) | WIP — shards `0.0.0`, ADR-0001 |
| `ATLAS_CONTRACT_STRUCTURE.md` | `freenet/atlas` `contracts/index-contract` | `HEAD 25582555` (2026-08-30) — no tag | WIP — proposal stage |

Ghost Keys (`freenet/ghostkeys`) is a delegate/vault (no on-chain contract), documented inline in `RAVEN`/`ATLAS` trust sections.

## Updating

Re-pin by updating the Source line and re-reading `contracts/*/src/lib.rs` + `common/src/*` at the new commit. Delta/Atlas have no tags — repin to new HEAD and update the date.
