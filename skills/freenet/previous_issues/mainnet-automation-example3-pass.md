# Mainnet Automation — Example 3 Pass (peers=0 → peers=2 fix)

**Date:** 2026-08-24  
**Status:** PASS — root cause identified and confirmed (Ack-fix), verified by a controlled run + a full end-to-end harness pass. Earlier "peers=0" theory was wrong (see Root cause).  
**Target:** example_3 (`freenet_libp2p_bevy_example_3`)  
**Crate:** `mainnet-automation-3`

## Symptom

Previous mainnet-automation-3 runs failed intermittently with **peers=0 / peers=1** — instances launched on the public Freenet mainnet but converged only partially or not at all. The convergence gate (`received peer input ... player_id=`) saw fewer than n−1 peers, so the test timed out or asserted failure.

## Root cause

**Not a Freenet discovery problem.** Clean log analysis proved Freenet roster discovery was fine — the roster contract reached **3/3 on failed runs too**. The intermittent failure was a **libp2p `request_response` misuse in our own netcode layer**:

- `src/p2p/run.rs` handled every inbound netcode request as fire-and-forget but **never sent a reply** — `let latest_netcode: Option<NetcodeMsg> = None;` was immutable and never set, and the reply path only ran `if let Some(reply) = latest_netcode`.
- `netcode_tick.rs` broadcasts every `Commit`/`Reveal` as a `send_request` to every roster peer, every tick.
- `request_response` keeps a request pending until it is answered (sender-side ~10s timeout). Broadcasting thousands of **unanswered** requests per tick over one yamux connection degraded the connection until the **receive leg died**.

**Observed signature:** failing runs sent ~12k outbound snapshots but received **0** inbound netcode (`received netcode commit` / `received peer input`), even with a full 3/3 roster.

### Why our initial diagnosis (documented elsewhere) was wrong
- `/src/.../p2p_protoc.rs:2649`: `subscriber_peer_ids` is **always empty by design** in freenet 0.2.128 — not a failure signal.
- Naive `grep -c` on the logs under-counted because logs contain ANSI escape codes. Strip first: `sed 's/\x1b\[[0-9;]*m//g' FILE | grep -c '...'`.

## What we changed

1. **`src/p2p/netcode_msg.rs`** — added a no-op `NetcodeMsg::Ack` variant.
2. **`src/p2p/run.rs`** — now replies `NetcodeMsg::Ack` to **every** inbound netcode request (this is the fix), and added request-response `OutboundFailure`/`InboundFailure` logging plus dial/connect lifecycle logging.
3. **`src/boxes/bevy_systems/netcode_tick.rs`** — handles `Ack` as a no-op; logs inbound from a peer not in the roster.
4. **`src/roster/*`** — added Phase-1 diagnostic instrumentation: contract identity (`contract_id`/`code_hash`/`params_hex`), per-entry delivery latency (`roster::change` with `seq`/`arrival`/`latency_secs`), and periodic `NodeDiagnostics` sampling (`freenet::diag`).
5. **`src/p2p/run.rs` test** — `two_swarm_netcode_exchange` updated to skip `Ack` no-ops (it previously encoded the broken no-response behavior).

Secondary issue found (not the root cause, tracked separately): the automation generates a **fresh contract key every run** (`local-mainnet-{unix}-{nanos}`), so a run can race the first `Put` of a cold contract and stall in `setup_contract` (`Get`→`NotFound` through the 60s grace window → `timeout after 30s` → retries), never starting the roster loop. See `docs/CONVERGENCE_INVESTIGATION.md` in the repo.

## Verification

Ran the full automation:

```bash
cd freenet_libp2p_bevy_example_3
CARGO_TARGET_DIR=/tmp/frt-build cargo run -p mainnet-automation-3
```

### Results

| Field | Value |
|-------|-------|
| Contract | `local-mainnet-1787597208-9160` |
| Instances | 3 launched, all mutually converged |
| Moved | All 3: `moved=true` |
| Peers | All 3: `peers=2, ready=true` |
| Error signatures | None |
| Roster | Clean seed (1 Put), max cumulative offline 0.0s |
| Video | `session.mp4` produced |
| Cleanup | Killed, pgrep clean |

### Key indicator

**peers=2 on all 3 instances** — each sees the other two. Previously this was 0/1 on failed runs.

### Confirmation of the root-cause fix (controlled run, before this E2E)

Fresh 3-instance mainnet run with the Ack fix in place:

| metric | FAILING run (before fix) | after Ack fix |
|---|---|---|
| roster reached `len=3` | 3/3 (even on failures) | 3/3 — 86–96× on each |
| `received peer input` (inbound) | **0** | **8099 / 8151 / 7793** |
| `received netcode commit` | **0** | 8153 / 8202 / 7799 |
| request-response failure logs | — | **0 / 0** |

## Cleanup verification

After the run, confirmed no leftover game processes with `pgrep -af freenet-libp2p-bevy-example-3`. The automation's drop guard killed all instances; `pgrep clean` confirmed.

## Learnings

- **"peers=0/1" on mainnet runs is NOT proof of a Freenet discovery problem.** Freenet got the roster to 3/3 even on failures. Verify with clean, ANSI-stripped log counts before blaming the mesh.
- **libp2p `request_response` must be answered.** If you broadcast game messages as `send_request` and never call `send_response`, unanswered requests accumulate and the connection's inbound leg silently dies (outbound keeps working). Always reply (an `Ack` no-op is enough).
- **`subscriber_peer_ids` is always empty by design** in freenet 0.2.128 — do not use it as a health signal.
- **Strip ANSI before counting log lines**, or every `grep -c` is unreliable.
- **peers=2 on 3 instances = full mesh**; this is the convergence target.
- **Roster "clean seed (1 Put)"** is the expected flow for a shared `--contract-params`. A `⚠ RACE: 2-Put` is a known fresh-key edge, not this failure.
- **Documented upstream:** freenet-core #3465, #4064, #3362, #4626 (propagation is unreliable) and flaky propagation tests #4910/#5175/#4691 — but none were the discriminator for this bug.
- **Full writeup:** `freenet_libp2p_bevy_example_3/docs/CONVERGENCE_INVESTIGATION.md`.
- **More runs still recommended** to confirm stability across mainnet conditions (the harness is otherwise subject to the fresh-key deploy flake described above).
