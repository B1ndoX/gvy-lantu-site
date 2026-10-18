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

- Official Chinese localization now comes from the NAS `starcitizen-shared-input/localization/data/localization/chinese_(simplified)/global.ini`, not Documents/data. GitHub consumes the NAS publisher's input-only `nas-localization` branch at one immutable commit; validate gzip length, SHA256, manifest and version series. Keep this inside the existing refresh command and schedules, with no separate weekly audit or sync flow. Do not deploy or change NAS credentials/services from this project.
- Accept only the current NAS official enhanced Chinese or fully Chinese pack for production localization. The former official English-first bilingual pack is no longer a production source or fallback. Keep historical Git/backups for traceability, never silently restore that pack. Content-based policy checks must preserve ordinary English names/model codes and Chinese-first enhanced annotations, without pinning a known source hash or version.
- Match official names by verified game keys and explicit context. Do not fuzzy-match same-name ships/components or planets/companies. Unresolved entries retain labeled fallbacks. The package's major/minor version is not exact LIVE-build verification, and English name bridges must never authorize cross-build gameplay stats.
- Preserve mission title keys, token substitutions and faction keys from the raw contract. Dynamic titles must expand the verified official template and every keyed token only after the English expansion matches the raw title; never reuse a partially translated completed-title cache. Use that same resolver for task sources and prerequisite titles. A faction key must match the actual faction, not a different sender. Retain traceable fallbacks when templates disagree; do not guess missing locations or treat a keyed lookup alone as proof of a matching title.
- Localization QA must render all manufacturing, dismantling and task detail records, not only the reported samples or JSON fingerprints. Check task grammar, known attachment enums, firing-mode labels and mineral names while preserving model codes, units, intended bilingual places and original-English search. Long base-attribute labels must wrap inside their boxes on narrow screens, never disappear behind ellipses.

- Data refresh scripts may update only validated data and calibration files. They must not write cache timestamps or versions into `assets/app.js` or `index.html`.
- `assets/app.js` must retain exactly one `__BUILD_DATA_VERSION__` placeholder.
- `npm run build` must derive the production data revision from the exact bytes of both public JSON snapshots and fingerprint the transformed application.
- Production health checks must verify the exact versioned URLs used by browsers for CSS, JavaScript, compressed JSON, and uncompressed JSON. Do not substitute a random health-check query parameter for the real client cache key.
- Preserve stable-LIVE selection, coverage thresholds, atomic replacement, 14-day backups, heartbeat commits, changed and unchanged production checks, and automatic rollback of only the workflow's own unhealthy refresh commit.
- Production health checks give transient transport errors a bounded recovery window (300 seconds without a deployment; inside the existing 900-second deployment window otherwise). Recovery must rerun the full exact-client-URL check. Never treat a snapshot mismatch as a network success, reset deadlines indefinitely, mute failure notifications, or skip persistent failures/rollback reporting.
- Mineral radar signals are manual-only. The scheduled GitHub Actions workflow must not run `scripts/refresh_mineral_signals.py`; run it only after the user explicitly requests a signal refresh, then validate, back up, commit, and deploy the resulting snapshot normally.
- Mission rewards must join the exact contract ID to its explicit `blueprintRewards` pool IDs, then to that pool's blueprint members. Never merge same-title missions or infer additional pools through a shared item. Show all reported systems and mark missing systems explicitly. Each pool draws one blueprint independently subject to its trigger/chance; its member count is not the number awarded at once and its trigger chance is not a per-blueprint drop rate. Verify the matching SCMDB LIVE mission page before changing these semantics; do not relabel a verified pool as unconfirmed merely to avoid a misleading count.
- Base attributes prioritize the same exact-LIVE SCMDB item export, joined by product entity ID with validated shared-table indexes. Community data may fill gaps only at the exact build and must never erase primary metrics. Distinguish single projectiles from whole shots; never fabricate DPS for unsupported burst/charge/sequence/explosive modes or infer units from a raw coefficient. Missing absolute metrics retain their relative-quality effects.
- Mission requirements keep optional faction entry points separate from mandatory intros, completed tags separate from excluded tags, and task candidate sites separate from acceptance constraints. Preserve sharing flags, missing values, official keyed translations and coverage guards. Do not claim N pool members means N runs to finish collection. A selected physical-item bundle awards its contained rows together; its selection probability is not a blueprint drop rate.
- Source lists start with twelve unique tasks. Show all when the remaining tail is at most three; otherwise use the existing expand/collapse control. Do not restore the former eight-row limit or merge task identities to shorten the list.

## Verification And Release

- Keep edits scoped and preserve unrelated user changes.
- Run the complete unit test suite, syntax checks, `git diff --check`, and `npm run build` before release.
- For rendered changes, test meaningful interactions and responsive layouts, including mobile, 16:9 desktop, 2K, and ultrawide when the affected surface can change across those sizes.
- Commit and push every formal project change from this repository. Do not leave deployment-affecting work uncommitted.
- After push, wait for EdgeOne and run `scripts/check_production_health.py` against the formal domain. Git push success alone is not deployment proof.
- Finish with a clean worktree and confirm local `HEAD` equals `origin/main`.
- An explicit local-preview-only request overrides publishing steps: do not push, create a release PR, dispatch workflows or deploy. Save local code and preview-data checkpoints separately, retain the preview server, and document the unpublished branch/commits rather than claiming it matches production.

## Mandatory Handoff Update

Every task that changes any of the following must update `/Users/bindox/Documents/项目交接文档/蓝图网相关.md` in the same task:

- user-visible features or responsive behavior;
- blueprint, localization, mineral, signal, quality, or dismantling data behavior;
- refresh, cache, backup, validation, rollback, CI, or EdgeOne deployment logic;
- production versions, record counts, fingerprints, timestamps, or verified status;
- a discovered failure, root cause, workaround, or permanent prevention rule.

Update the current-state snapshot, the relevant operating rule, and the historical mistake/prevention section where applicable. Do not update only `README.md`. Do not put blueprint-site rules into `舰队官网相关.md`, and do not copy fleet-site internals into the blueprint handoff.

A task covered by this section is not complete until the handoff document is accurate for a completely context-free successor.
