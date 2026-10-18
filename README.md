# GVY Lantu Site

Static site for the GVY blueprint search website. This is a separate production project from the GVY official site.

The formal production entry should be deployed through Tencent Cloud EdgeOne Pages / Makers at `https://lantu.gvyvoyagers.vip`.

Do not configure GitHub Pages for this repository, and do not point DNS back to `b1ndox.github.io`.

Official fleet website content belongs in the separate `gvy-official-site` project.

Official localization version labels may start with a numeric series or the
official `Alpha ` prefix (for example, `Alpha 4.10：奥里森之围`). The reader
preserves the original INI and manifest label, verifies their complete bytes,
and still requires the same major/minor series as the selected stable LIVE.
Production localization accepts only the current NAS official enhanced Chinese
pack or fully Chinese pack. The former official English-first bilingual pack
is no longer a permitted production source or historical fallback. Its archived
bytes remain in Git/backups for diagnosis, not production calibration.
An English-first bilingual majority across verified name keys fails closed;
ordinary English item names, model codes and Chinese-first enhanced annotations
are not banned. Detection uses contents, not known hashes or version labels.
Chinese name lines take priority after specification annotations are excluded.
Only exact English label wrappers or suffixes are removed; official model and
brand tokens are retained. Untranslated English/English duplicates do not claim
a Chinese match, and INI keys (including flags) remain unchanged.
Detection uses each value's structure, not a pack name or known hash. Switching
between permitted Chinese packs rebuilds whenever it differs from the currently
applied content; touching an identical source does not advance data timestamps.
For item names, standalone bracketed size/class/grade or percentage-modifier
annotations are not name lines. English model names such as VK-00 and FR-66
remain the name when the pack adds only a Chinese specification on another line.
Repeated English tails may use the verified full name, its quoted nickname, a
size-prefix-free model, or its exact Mining Laser/Module name. Only case and
space/hyphen differences are accepted; unmatched tails and legitimate model
tokens remain intact. Snapshot validation rejects annotation-only item names.
Do not remove an English tail if it is the only place that carries the model or
variant identifier, even when the tail otherwise matches a verified alias.

## Project Boundaries

- This repository contains only the GVY blueprint query site.
- The production domain is `https://lantu.gvyvoyagers.vip`.
- The formal fleet name and logo lockup use `星远`; the public-facing "星远舰队" link must point to `https://www.gvyvoyagers.vip`.
- The adjacent "维科洛查询" link must point to `https://wikelo.gvyvoyagers.vip`.
- Do not modify or publish the fleet official site from this repository.
- Do not use `blueprint-site` as a production directory.
- Do not enable GitHub Pages or point DNS to `b1ndox.github.io`.

## Blueprint Filter Rules

The filter order is fixed:

1. 类型
2. 组件类型
3. 等级
4. 组件类别
5. 材料
6. 任务类型
7. 制造商
8. 任务奖励来源
9. 重置筛选

`组件类型` is enabled only when `类型` is `舰船组件`. Its options are generated from the current blueprint data and include available component types such as 冷却器、电源、护盾、量子驱动、雷达、采矿激光、牵引光束、加油模块 and 打捞模块. `组件类别` is also enabled only for ship components and represents 军用、民用、隐形、竞赛、工业等类别.

The closed filter controls must remain compact. 等级、材料和制造商使用相同的短框宽度；任务奖励来源按文字内容收紧，不能保留无意义的横向空白。宽屏时整组控件铺满筛选栏，并让最后的重置按钮与右侧内边距对齐。

Dropdown menus are independent from their closed control width. Every menu must start at the left edge of its trigger and expand to the right. The trigger text and the first menu option must share the same vertical text alignment. Do not right-align a menu so that it expands backward over earlier filters. Long menus may grow up to the configured maximum width and then use their internal scrollbar.

Responsive behavior:

- Wide desktop: one row, distributed across the full filter width.
- Up to 1320 px: compact wrapping with fixed short controls.
- 621-720 px: three-column grid so long menus still open to the right without leaving the viewport.
- Up to 620 px: compact two-column mobile grid with no horizontal page overflow.

## Detail Text Layout

The seven dismantling information fields remain separate compact boxes with centered labels and values. Grid children must stretch to the cell width, not retain an overflowing intrinsic width. Values wrap completely inside their boxes, including uninterrupted English identifiers; do not shorten official manufacturer names or hide them behind an ellipsis. Box height follows the content.

Desktop keeps seven columns. Up to 620 px, use four columns with the fifth field (manufacturer) spanning two: four fields in the first row, then manufacturer, size and grade in the second row. Keep that field order when maintaining the markup.

Manufacturing specification values, detail titles and recovered-material names also allow long tokens to wrap. Quality-result rows and their value groups wrap when space is insufficient, preserving the displayed numbers and units. Compact result-list summaries and closed filter controls retain their intentional ellipsis behavior.

When names or layout rules change, inspect actual text bounds inside each box, not only the page's total scroll width: an overflowing centered value may leave the page width unchanged. Include long manufacturers, English specification identifiers and large quality values at 320/390 px, responsive breakpoints, 16:9 desktop, 2K and ultrawide.

## Mission Rewards

Each acquisition task shows its reported star system(s). Missing systems are
explicitly marked; template locations are not replaced with guessed places.
Clicking a task opens its blueprint reward pools and any recorded physical item
rewards, including quantities and owner-only/delivery conditions. Blueprint rows
open the corresponding blueprint without changing saved favorites.

Acquisition tasks share one compact list across source pools, deduplicated by
contract ID without merging distinct same-title tasks. Show twelve rows initially;
if only one to three would remain hidden, show them too (up to fifteen total).
The current 678 task-linked blueprints average 11.03 unique contracts; twelve is
a stable display limit, not a live average that changes the layout on each refresh.
Use the native disclosure only when at least four rows remain hidden.
Clickable task names are white without underlines, with an arrow and visible
hover/focus feedback; non-clickable legacy rows retain neutral text. A task's
reward dialog still keeps its independent pools separate.

Reward lookup uses the exact contract ID and its explicit pool IDs, not a task
name, faction or a transitive shared-blueprint association. Same-title tasks in
different systems remain separate. Following SCMDB's mission reward display,
each pool lists compact candidate rows with an `N 选 1` draw count, trigger and
pool trigger probability. Multiple pools draw independently; a completed pool
stops awarding blueprints. Pool membership is not a single-completion award
quantity, and a 100% pool trigger is not a 100% drop rate for each member. Do not
calculate individual odds from entry count or weights alone.
An `N 选 1` pool is not a promise of an unowned blueprint or completion in N runs.
Duplicate/pity behavior is not fully verified. Physical rewards are separate from
blueprints: a weighted group is one bundle whose items are awarded together when
selected, not a choice between its individual rows. Display group-selection
probabilities as such, with recorded quantities, owner and delivery restrictions.

Task dialogs add a collapsed conditions/location disclosure without changing the
compact source list. Requirements retain rank thresholds and their sharing flags,
crime ranges, legality, sharing, repeat restrictions, cooldowns (minutes), required
intros and optional faction entry points separately. Required completion tags and
excluded completion tags must never be interchanged. XP is a rank's starting
threshold, not an invented upper XP limit. Candidate task sites are not guaranteed
acceptance locations; region membership and unresolved/additional constraints are
explicit. Locations and requirements use the same exact-LIVE contract IDs, with
official contextual/keyed Chinese first. Unresolved game label keys do not become
user-facing place names. The mineral dialog is unchanged.

The dialog follows its content height up to the viewport cap, with a scrollable
body and a non-overlapping footer. Its width follows content within responsive
limits: candidate lists use two columns above 620 px and one column on phones.
Chinese/English star systems and displayed task titles participate in the
existing full-text search; this is not a dedicated star-system filter and does
not describe a manufacturing site or mineral location. Opening a reward from
`我的蓝图` exits the favorites-only view without changing any saved favorites.

`missionRewards` is generated and validated with the same exact-LIVE snapshot.
A missing/outdated reward schema triggers a full rebuild through the existing
refresh entry point, with its validation, 14-day backup and atomic replacement.
After that migration, new LIVE/localization changes and maintenance/forced
rebuilds update rewards normally. An unchanged six-hour check does not independently
refetch the same-build mission table. No extra runtime API or schedule is added.
Missing/empty referenced pools and malformed system arrays fail validation.
Before replacement, task, referenced-pool, task-linked-blueprint and physical-item
coverage are compared with the previous cache; a drop exceeding 20% aborts the
candidate and keeps the previous data for investigation.
The same guard now covers conditions, location references, matched base-stat
records and previously available absolute-quality panels. Reward schema 3 and
item-stat schema 1 migrate through that same refresh entry point, not a new job.

Task titles preserve the raw contract's localization key and token substitutions.
The official template is accepted only when its fully expanded English matches
the actual task title; keyed ranks/cargo scales then expand from the verified
Chinese snapshot. This also applies to prerequisite titles. Runtime placeholders
remain placeholders, with known labels translated, never invented locations.
Faction names use their own validated key/English identity, not an unrelated
contractor or manufacturer. Conflicting templates retain a traceable translation
fallback. Missing title metadata, unresolved templates and the known partial-cache
regressions fail candidate validation. Original English titles remain searchable.
The migration reuses the full rebuild and coverage/backup guards above.

Localization QA must inspect rendered manufacturing, dismantling, task rewards
and conditions, including armor/clothing attachment labels, mode labels and
mineral names. Do not strip ordinary model codes, acronyms, units or deliberate
bilingual places. Base-attribute labels wrap within their existing specification
boxes, including multi-mode labels at 320 px; no font reduction or ellipsis.

## Base Attributes And Quality

`scripts/scmdb_item_stats.py` extracts base attributes from the selected exact-LIVE
SCMDB item export. Join blueprint `productEntityClass` to the exact entity, never
authorize gameplay metrics through a name-only fallback. Resolve weapon fire-mode,
ammo and magazine pool indexes structurally (including index zero); mismatched
builds, duplicate entities and invalid references fail closed. Basic values use
a collapsed `基础属性` disclosure with existing specification boxes; quality-aware
values continue using the existing `成品品质效果` rows and sliders.

For simple single/automatic modes, distinguish per-projectile damage from a whole
shot and include pellet count and damage multiplier in theoretical DPS. Simplify
only a verified one-entry looping sequence with matching RPM. Do not invent a
single-shot/DPS result for burst, charge, beam, complex sequences or explosive
ammo; retain the reliable metrics and relative-quality fallback instead. Baseline
panels are Q500; theory excludes armor, distance falloff, reload and charging cycles.
Do not assign an unverified SCU/10-GM unit to a raw quantum-fuel coefficient.

Exact-version community enrichment remains optional. It may fill missing metrics,
but must never erase/override primary SCMDB values or mix firing-mode calculations.
An unavailable or cross-build fallback leaves verified primary values intact.
Coverage metadata and payloads must agree; source/log messages must not claim that
all absolute attributes are absent merely because the optional fallback is late.

## Local Preview

```bash
npm run build
python3 -m http.server 8002 --directory dist
```

Open `http://127.0.0.1:8002/`.

When the user requests local-only review, keep the preview available and do not
push, open a release PR, trigger Actions or deploy. Keep preview data separate
from release code commits; later publish the code first and rebuild data through
the original cloud pipeline so its backup and production checks are not bypassed.

## Build

`npm run build` creates a production-only `dist/` directory. `edgeone.json` configures Makers to publish that directory so refresh scripts, localization sources, caches, and repository documentation are not exposed as site files.

## Production Deployment

Commit and push production changes only from this repository. Tencent Cloud EdgeOne Pages / Makers builds the connected `B1ndoX/gvy-lantu-site` repository with `npm run build` and publishes `dist/` to `https://lantu.gvyvoyagers.vip`.

The project deliberately has no runtime npm dependencies. EdgeOne uses its supported Node.js `24.5.0` image, skips package installation with `node --version`, and runs the repository-owned static build script. The generated HTML is revalidated on every request, while fingerprinted assets and version-keyed JSON remain long-cacheable.

After every automated data deployment, `scripts/check_production_health.py` polls the formal domain for up to 15 minutes. Runs with no repository change still perform an immediate production snapshot check, so an EdgeOne outage, stale deployment, or corrupted public payload cannot remain silently green between data releases. Updated and unchanged deployments are verified through the exact versioned CSS, JavaScript, compressed JSON, and uncompressed JSON URLs used by browsers. The checker requires the deployed asset fingerprints and embedded data revision to match the final repository checkout, verifies that the public blueprint payload is stable `LIVE`, compares its complete semantic hash with the committed payload, and performs the same complete comparison plus coverage checks for mineral locations and signals. If an automated refresh commit does not become healthy, the workflow reverts that exact machine commit, pushes the previous verified snapshot, and waits for production recovery. It never automatically reverts an unrelated manual commit. A successful Git push alone is not proof that production deployment has completed.

Production checks distinguish transient transport failures from snapshot failures.
`--network-timeout 300` (also the default) permits five minutes of recovery for
timeouts, DNS/connection failures, interrupted transfers and allowlisted temporary
HTTP responses (408, 429, selected 5xx). Probes back off by 5, 10, 20, then at most
30 seconds; socket timeouts are capped at 15 seconds and the remaining request
budget. Every retry restarts the complete production check. Success is reported
only after both JSON forms and all required assets match, never merely because
the homepage responds again. A recovered transient failure stays in the logs
but does not fail the job or trigger its failure-email notification.

The recovery deadlines are fixed when checking starts and never reset after
partial progress. An unchanged run uses `--timeout 0`: network-only failures
receive the five-minute grace, but content/hash errors, invalid JSON, certificate
failures and non-retryable HTTP responses do not. Changed deployments and rollback
verification retain `--timeout 900`; the network grace is inside, not appended to,
that 15-minute window. `--network-timeout 0 --timeout 0` explicitly disables
recovery retries. Persistent connectivity failures and real deployment mismatches
still exit nonzero, preserve the existing rollback rules, and reach the final
failure-reporting step. Notifications are not muted or reconfigured. The final
report identifies source and production outcomes separately. This does not alter
NAS/source validation, data timestamps, refresh schedules, or manual-only signals.

For manual releases, also verify filter interactions, desktop/mobile overflow, console errors, and both the `星远舰队` and `维科洛查询` destinations.

## Data Refresh

Blueprint data refreshes are handled by `.github/workflows/refresh-blueprint-data.yml`.
The normal schedule (`17 */6 * * *`, UTC) checks SCMDB every six hours and only accepts the newest stable `LIVE` release. `PTU`, `EPTU`, Tech Preview, and other test channels are never published by this site, even when SCMDB lists them first or gives them a higher version number.

The maintenance schedule (`43 17 1,15 * *`, UTC) runs twice monthly with `--force`. It rebuilds the current stable LIVE release even when the version string is unchanged, so upstream corrections, localization calibration changes, and same-version crafting changes are not missed. It also updates `.github/refresh-heartbeat.json`; do not delete this tracked file or remove it from the commit allowlist.

The header shows the active LIVE version. Hovering or keyboard-focusing the version badge reveals `dataUpdatedAt` as `更新 YYYY/MM/DD HH:mm` in Asia/Shanghai; tapping the badge provides the same information on touch devices. This timestamp changes only after a newer release or a scheduled/manual forced calibration has been fetched, localized, validated, backed up, and atomically published. Routine six-hour checks with no newer LIVE release do not change it.

If SCMDB has no newer `LIVE` version and the verified NAS localization source has not changed, a normal six-hour run keeps the existing data cache and makes no commit (except a newly available exact-version quality enrichment). A localization hash/adapter change rebuilds the same LIVE release through this same command. The twice-monthly maintenance run intentionally creates a verified calibration snapshot and heartbeat commit. A stale manifest is prevented from rolling an existing `LIVE` release backward.
If a newer `LIVE` version exists, `scripts/refresh_blueprint_data.py` locks the build to that exact release, regenerates the blueprint index, applies localization in this priority order:

1. NAS official Star Citizen localization, matched through verified game localization keys
2. Legacy localization snapshot and FlowCLD Chinese calibration for unresolved names
3. Google Translate fallback cache

### Official Localization Input

The authoritative file is `/volume1/docker/starcitizen-shared-input/localization/data/localization/chinese_(simplified)/global.ini` on NAS. The former `Documents/data` source is no longer authoritative. The existing `python3 scripts/refresh_blueprint_data.py` command is the only blueprint refresh entry point; no additional localization schedule or standalone sync CLI is introduced here.

An independently maintained NAS publisher uploads `global.ini.gz` and `source.json` to this repository's input-only `nas-localization` branch. GitHub Actions resolves the branch once to an immutable commit, reads both files from that commit, and verifies manifest schema, original byte length, original INI SHA256, source path and version label before use. A normal local run reads NAS over the existing `ssh nas` connection and verifies the source hash. Neither path writes to NAS. Source failure aborts the candidate and reports failure; it never presents a stale snapshot as a successful sync.

The helper `scripts/official_localization.py` produces the build input `data/official-localization/localization/starcitizen/nas-keyed-names.json`. The derived snapshot is backed up and committed with the existing workflow data allowlist, but is not included in `dist/`. Raw INI files remain on the input branch, never in the production output. Publisher deployment keys and scheduling belong to the separate NAS publisher, not this site.

The Chinese file currently declares only the `4.10` series. English key labels are read from an immutable `StarCitizenWiki/scunpacked-data` commit declaring the same series, not used as gameplay stats. `exactBuildVerified` remains false: this is not proof of an exact LIVE build match. A source series mismatch, invalid hash, or low coverage fails closed. On a new NAS hash or adapter revision the existing refresh rebuilds and applies official names last. Identical inputs preserve the snapshot timestamp. Exact names bridge upstream records to game keys; manufacturer codes and property keys take precedence. Item/vehicle, planet/company and crafting-slot contexts are distinct; full item names take precedence over short-name keys. Conflicting or missing matches retain marked legacy fallbacks and are listed in the refresh log, never guessed or claimed as NAS-verified.

The frontend uses verified material `nameZh` before its hardcoded fallback table. The mineral refresh similarly applies the verified snapshot to mineral and location names without refreshing signal values. Mineral footer copy stays `数据更新`, with no last-check timestamp.

The same staged build also attempts to attach compact base attributes from the community-maintained `StarCitizenWiki/scunpacked-data` item export. The source commit must declare the exact same `X.Y.Z-LIVE.build` version as the SCMDB blueprint index, and matching/base-stat coverage must pass minimum thresholds before those values are accepted. A temporary source outage or a lagging community release never blocks a newer verified LIVE blueprint release: the site publishes the SCMDB quality coefficients and relative effects first, then retries the version-matched base-stat enrichment on later six-hour runs. It never combines base attributes from one game build with quality coefficients from another.

Before replacing data files, the script saves a local backup under `.data-backups/`.
Local backups are retained for 14 days and are ignored by Git.
In GitHub Actions, the backup folder is also uploaded as a workflow artifact with 14-day retention.
The upload must enable `include-hidden-files: true` for `.data-backups/`; validate
an actual artifact after a changed-data run, not just the workflow's conclusion.
All staged public files are validated before same-filesystem atomic replacement. Transient SCMDB network failures are retried up to three times; if refresh still fails, the existing LIVE cache and its displayed update time remain unchanged.

The same six-hour workflow then runs `scripts/refresh_mineral_locations.py`. It fetches the current commodity/location relationships from UEX API 2.0, rebuilds all five supported location groups, applies the verified NAS location localization, and preserves the calibrated Chinese fallbacks that are absent from that package. The candidate must retain at least 30 materials, 25 materials with reliable locations, 100 total locations, and 100 location-specific signal mappings. It is also compared with the last verified cache, and large coverage drops are rejected. If the source data is unchanged, `retrievedAt` is not advanced and no commit is created.

Mineral radar signals are deliberately excluded from both schedules. `scripts/refresh_mineral_signals.py` runs only after the user explicitly requests a manual signal refresh. It verifies the embedded `RADAR_DATA` published by the Shadow Guardians Mining Resource Finder, maps source aliases such as Quantanium/Quantainium, and updates only the radar base, maximum cluster, and derived values already attached to local mineral locations. Location distribution is not inferred by this signal-only step. A visible source version label is optional: when the upstream page omits it, the refresh stores a deterministic `content-<sha256>` revision derived from the fully parsed and validated signal definitions. Coverage, required-material, range, backup, and atomic-replacement checks remain mandatory.

Mineral location updates and manually requested signal updates both use strict coverage checks, a 14-day backup under `.data-backups/`, and same-filesystem atomic replacement. The production build derives one frontend data revision from the exact bytes of both verified JSON files, so either a blueprint change or a mineral change automatically creates a new browser cache URL without editing application source. If an automated blueprint or location source is unavailable, incomplete, or invalid, that step keeps the last deployed verified cache and the workflow reports failure after checking production. A signal-source outage cannot fail scheduled runs because signals are not fetched automatically. If verified values are unchanged, no mineral-data commit is created. The mineral dialog displays the newest valid timestamp among the location snapshot and the last manually verified signal calibration.

## Long-Term Unattended Operation

The site is designed to remain available for at least a year and to continue beyond that without routine application maintenance. It is a static site: browsing, filtering, favorites, quality controls, dismantling, and mineral dialogs do not depend on an application server, database, login provider, secret, or expiring API token at request time.

The persistence chain is:

1. GitHub Actions checks stable-LIVE blueprint data and mineral locations four times per day; mineral radar signals remain on the last manually verified snapshot.
2. New data is built in a temporary directory and must pass unit, coverage, channel, localization, count, uniqueness, and source consistency checks.
3. The previous verified files are backed up before same-filesystem atomic replacement.
4. Only approved generated files are staged and committed; unrelated or untracked files are never swept into an automated commit.
5. The workflow rebases onto the current `main` branch before pushing, reducing races with a manual repository update.
6. EdgeOne builds the pushed commit, and the workflow then rebuilds the final checkout and compares the formal production domain with that exact snapshot.
7. If no file changes, the workflow still compares the existing formal production snapshot with the verified repository state.
8. If a source fails, the workflow reports failure while the existing static production deployment and verified cached data remain usable. If an automated refresh deployment fails production verification, that exact machine commit is automatically reverted and the restored production snapshot is verified. The next six-hour run retries automatically.

GitHub documents that scheduled workflows in public repositories can be disabled after 60 days without repository activity. The twice-monthly heartbeat provides continuing repository activity even when Star Citizen stays on one LIVE version for months. Its minute `43` schedule also avoids the high-load start-of-hour window where GitHub says scheduled runs may be delayed or dropped.

Long-term recovery layers:

- `main` Git history retains every deployed data revision beyond the 14-day artifact window.
- `.data-backups/` is uploaded as a 14-day GitHub Actions artifact whenever present.
- A failure before push leaves the previous EdgeOne deployment untouched; an unhealthy automated refresh after push is reverted and redeployed from Git history.
- Content hashes prevent stale JavaScript/CSS reuse. `npm run build` derives `DATA_VERSION` from the exact blueprint and mineral JSON bytes, embeds it into the built application, and therefore gives every changed data snapshot a new URL. HTML uses revalidation instead of immutable caching.
- Production verification extracts that embedded revision, recomputes it from the committed files, then validates both compressed and uncompressed JSON through the same versioned URLs used by browsers. It cannot pass by adding a separate health-check cache bypass.

The workflow uses the Node 24 releases of the official GitHub actions (`checkout@v7`, `setup-python@v7`, `setup-node@v7`, and `upload-artifact@v7`). Keep those major versions current when GitHub announces a runner-runtime deprecation.

Do not weaken the system by removing the two schedules, `continue-on-error` plus final failure reporting, the heartbeat, atomic replacement, validation thresholds, content fingerprints, production health polling for both changed and unchanged runs, or stable-LIVE selection. Do not make test-channel data a fallback for a missing LIVE source.

This design removes routine maintenance but cannot make third-party ownership disappear. The GitHub repository must remain enabled, the EdgeOne project and connected repository must remain authorized, and the `gvyvoyagers.vip` domain/DNS/TLS account must remain valid. Upstream format changes cannot corrupt production, but a permanently changed upstream format will keep the last verified cache and produce failed Action runs until its adapter is updated.

Useful manual audit commands:

```bash
python3 -m unittest discover -s tests -v
node --check assets/app.js
npm run build
python3 scripts/check_production_health.py --timeout 0
gh run list --workflow refresh-blueprint-data.yml --limit 12
```

## Blueprint Tools: Favorites, Quality, and Dismantling

The `我的蓝图` filter is deliberately browser-local. A user can save or remove a blueprint with the detail-panel button; the saved IDs live in `localStorage` under `gvy-lantu-favorite-blueprints-v1`. There is no account, cloud profile, or cross-device synchronization, so the interface must never imply that a login is available or required.

Each material card reads its slot's `modifiers` from the selected LIVE SCMDB crafting dataset and contains a compact quality slider plus the active linearly interpolated property coefficient or additive adjustment. Multi-segment quality curves are grouped by property and only the segment containing the selected quality is evaluated. Values from separate material slots that affect the same multiplicative property are multiplied; additive properties are summed relative to Q500.

The manufacturing detail panel contains a compact `成品品质效果` summary above the material cards. When the exact-version community item export provides a reliable base attribute, the summary shows `Q500 base -> selected-quality result` and the percentage change. Metrics without a trustworthy base attribute show only the SCMDB-derived relative change. Blueprints whose crafting slots expose no modifier formula do not show a slider or a quality-result panel; the interface must not fabricate effects for them.

Current 4.9.0 LIVE coverage is 1,540 blueprints with SCMDB quality modifiers, 1,530 exact item matches, and 1,508 blueprints with at least one compact base attribute. The remaining modifier-bearing records retain exact relative effects only. Known limitations are deliberate: recoil, damage mitigation, maximum tractor volume, and some newly introduced or unnamed items do not have a complete compact base panel; the preview models data values and cannot guarantee that the current in-game inventory UI displays every crafted adjustment correctly.

Manufacturing and dismantling are separate query modes selected from the prominent centered mode switch in the summary strip, between the result count and sorting controls. The manufacturing mode keeps material quality controls inside their corresponding material cards. The dismantling mode only lists records with verified recoverable outputs, changes the material filter to recovered output, hides mission-only controls, and renders a dedicated dismantling detail view.

Production builds fingerprint `assets/styles.css` and the transformed `assets/app.js` in the generated `dist/index.html`. During that build, `DATA_VERSION` is generated from the combined content hash of `data/blueprint-index.json` and `data/mineral-locations.json`; the generated revision also changes the application fingerprint. This is required because EdgeOne serves assets with a long immutable cache lifetime. Blueprint and mineral JSON requests use that content-derived query key and retain the previous verified cache when refresh validation fails. Refresh scripts must only update validated data files; they must never write a timestamp or version string into `assets/app.js` or `index.html`.

Dismantling is derived from the same LIVE dataset: it takes the first blueprint tier's resource and item inputs, applies the separate SCMDB resource/entity-class blacklists, and then applies the published dismantle efficiency and time. Resource quantities are displayed in SCU; recoverable item quantities are displayed as item counts. Do not silently substitute UEX, PTU, or manually estimated values for these outputs; if a future verified source adds exact per-item dismantling recipes, introduce it as an explicit versioned data adapter with validation and a visible source label.
