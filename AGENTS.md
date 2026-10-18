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
- SCMDB is the primary gameplay source for recipes, item stats/class, mission types/rewards, dismantling rules and mining. Keep one normalized writer per data domain. Supplemental sources may fill only explicit missing values at a verified identity and exact LIVE build, never overwrite a primary value or treat zero/explicit absence as missing. The existing FlowCLD cache is an exact-blueprint-ID language fallback only; do not reintroduce its duplicate online gameplay fetch. NAS official Chinese remains the authoritative localization source.
- Mineral distributions and signals update together through `scripts/refresh_mineral_locations.py` in the existing schedules. This supersedes the former manual-only rule. Lock `mining_data` to the exact blueprint LIVE; validate tables, references, finite values, modes, cluster counts and coverage before one backup/atomic replacement. Do not fetch UEX distributions or parse Shadow Guardians HTML in parallel. On source failure retain the last verified snapshot and report failure. Before committing/pushing validate the blueprint/mining version pair; never deploy a newer blueprint snapshot with incompatible cached mining data. The old signals script is a thin compatibility alias, not a second writer or schedule.
- Mining locations are evidenced spawn regions, not guaranteed exact points. Never turn generic Lagrange templates into named stations or invent coordinates. Mixed deposits retain the primary mineral's signature even when viewing a secondary material. FPS/ROC shared per-rock signatures are not unique gemstone IDs and must not be multiplied by cluster size. Preserve actual possible cluster counts rather than inventing every count up to a global maximum. Routine identical inputs keep the data timestamp unchanged.
- Mission rewards must join the exact contract ID to its explicit `blueprintRewards` pool IDs, then to that pool's blueprint members. Never merge same-title missions or infer additional pools through a shared item. Show all reported systems and mark missing systems explicitly. Each pool draws one blueprint independently subject to its trigger/chance; its member count is not the number awarded at once and its trigger chance is not a per-blueprint drop rate. Verify the matching SCMDB LIVE mission page before changing these semantics; do not relabel a verified pool as unconfirmed merely to avoid a misleading count.
- Base attributes prioritize the same exact-LIVE SCMDB item export, joined by product entity ID with validated shared-table indexes. Community data may fill gaps only at the exact build and must never erase primary metrics. Distinguish single projectiles from whole shots; never fabricate DPS for unsupported burst/charge/sequence/explosive modes or infer units from a raw coefficient. Missing absolute metrics retain their relative-quality effects.
- Mission requirements keep optional faction entry points separate from mandatory intros, completed tags separate from excluded tags, and task candidate sites separate from acceptance constraints. Preserve sharing flags, missing values, official keyed translations and coverage guards. Do not claim N pool members means N runs to finish collection. A selected physical-item bundle awards its contained rows together; its selection probability is not a blueprint drop rate.
- Source lists start with twelve unique tasks. Show all when the remaining tail is at most three; otherwise use the existing expand/collapse control. Do not restore the former eight-row limit or merge task identities to shorten the list.
- The literal `[蓝图]` marker is light blue `#b8c9f1` in task source rows, reward-dialog headings and prerequisite/completed/excluded task titles, distinct from cyan systems. It comes from the Chinese title, not a generated reward flag; its absence never means no blueprint rewards. Escape all text before wrapping that exact marker; do not recolor ordinary 蓝图 text, other bracketed placeholders, full titles or search data. Keep the existing font, wrapping and click targets.
- Reward/result metadata uses verified compact class/grade labels (军A/隐A/工C/民B/竞D); never invent a missing class or grade. Summary order is category, component/weapon type, compact class/grade, size, then optional manufacturer. Keep full fields in details and class/grade visible before trailing main-list text. Ship-weapon full types must combine the primary subtype with a verified family, not treat all lasers as cannons or use conflicting legacy subcategories. Summary labels fall back to their existing subtype only when actual width/line measurements require it, and restore on widening. Preserve existing styles, fonts and columns; test all reward pools and main results on narrow screens, including the compact label's own visible text bounds.
- Quality keeps a stable 72px by 23px capsule and slider. Center label and number together, size the tabular-digit field to the actual digits and use matching 14px line boxes; do not reserve a wide four-digit field that optically shifts 1-3 digit values. The default value is 500 (or the recipe's higher minimum), shown as a semi-transparent gray placeholder, not prefilled text; focusing clears the draft for fresh typing, and leaving it empty preserves the effective quality. Editing or moving the slider confirms it in cyan. Hover/focus shows a smaller input/range hint centered above the capsule, within viewport bounds. Do not add Enter/Tab acceptance rules, separate quick-value buttons, or restore the removed update-summary feature. Accept integer qualities only, cap at 1000, reject minus/decimal/exponent input, and enforce each recipe minimum when editing ends without applying invalid drafts to results.
- Craft plans persist separately from favorites in browser-local storage, with bounded integer counts and validated recipe choices. Totals use one option per slot, distinguish SCU from item counts and different quality minima, and scale sequential craft time without promising elapsed completion time. Missing/version-removed items remain visible for removal and are excluded with a warning, never silently substituted. Shared blueprint links contain only exact ID/mode; denied clipboard access provides a selectable link, and missing IDs are reported without selecting a same-name item.
- Capsule pointer activation must stay within its visible 72px by 23px box. Do not rely on implicit enclosing-label activation or allow tooltip/nearby empty clicks to focus the input. Keep the explicit input's accessible name and ordinary Tab/Shift+Tab behavior.

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
