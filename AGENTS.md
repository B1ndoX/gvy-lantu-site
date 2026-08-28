# GVY Blueprint Site Agent Rules

These rules apply to the entire `gvy-lantu-site` repository.

## Required Context

Before changing code, data, workflows, deployment behavior, or documentation, read:

1. `/Users/bindox/Documents/项目交接文档/蓝图网相关.md`
2. `README.md`

The handoff document is written for a person or AI with no prior context. Do not rely on chat history as the only record of project behavior or decisions.

## Project Boundary

- Work only in `/Users/bindox/Documents/Codex/Projects/starcitizen-crawler/gvy-lantu-site` unless the user explicitly asks to update the handoff document above.
- Do not modify `gvy-official-site`, `blueprint-site`, the Wikelo project, bots, NAS content, or unrelated work directories.
- The formal repository is `B1ndoX/gvy-lantu-site`, branch `main`.
- The formal domain is `https://lantu.gvyvoyagers.vip` and deployment is Tencent Cloud EdgeOne Pages / Makers.
- Never configure GitHub Pages or point DNS to `b1ndox.github.io`.
- Publish only the newest verified stable `LIVE` data. Never publish PTU, EPTU, Tech Preview, Evocati, or another test channel.

## Data And Cache Safety

- Data refresh scripts may update only validated data and calibration files. They must not write cache timestamps or versions into `assets/app.js` or `index.html`.
- `assets/app.js` must retain exactly one `__BUILD_DATA_VERSION__` placeholder.
- `npm run build` must derive the production data revision from the exact bytes of both public JSON snapshots and fingerprint the transformed application.
- Production health checks must verify the exact versioned URLs used by browsers for CSS, JavaScript, compressed JSON, and uncompressed JSON. Do not substitute a random health-check query parameter for the real client cache key.
- Preserve stable-LIVE selection, coverage thresholds, atomic replacement, 14-day backups, heartbeat commits, changed and unchanged production checks, and automatic rollback of only the workflow's own unhealthy refresh commit.
- Mineral radar signals are manual-only. The scheduled GitHub Actions workflow must not run `scripts/refresh_mineral_signals.py`; run it only after the user explicitly requests a signal refresh, then validate, back up, commit, and deploy the resulting snapshot normally.

## Verification And Release

- Keep edits scoped and preserve unrelated user changes.
- Run the complete unit test suite, syntax checks, `git diff --check`, and `npm run build` before release.
- For rendered changes, test meaningful interactions and responsive layouts, including mobile, 16:9 desktop, 2K, and ultrawide when the affected surface can change across those sizes.
- Commit and push every formal project change from this repository. Do not leave deployment-affecting work uncommitted.
- After push, wait for EdgeOne and run `scripts/check_production_health.py` against the formal domain. Git push success alone is not deployment proof.
- Finish with a clean worktree and confirm local `HEAD` equals `origin/main`.

## Mandatory Handoff Update

Every task that changes any of the following must update `/Users/bindox/Documents/项目交接文档/蓝图网相关.md` in the same task:

- user-visible features or responsive behavior;
- blueprint, localization, mineral, signal, quality, or dismantling data behavior;
- refresh, cache, backup, validation, rollback, CI, or EdgeOne deployment logic;
- production versions, record counts, fingerprints, timestamps, or verified status;
- a discovered failure, root cause, workaround, or permanent prevention rule.

Update the current-state snapshot, the relevant operating rule, and the historical mistake/prevention section where applicable. Do not update only `README.md`. Do not put blueprint-site rules into `舰队官网相关.md`, and do not copy fleet-site internals into the blueprint handoff.

A task covered by this section is not complete until the handoff document is accurate for a completely context-free successor.
