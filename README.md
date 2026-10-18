# GVY Lantu Site

Static site for the GVY blueprint search website. This is a separate production project from the GVY official site.

The formal production entry should be deployed through Tencent Cloud EdgeOne Pages / Makers at `https://lantu.gvyvoyagers.vip`.

Do not configure GitHub Pages for this repository, and do not point DNS back to `b1ndox.github.io`.

Official fleet website content belongs in the separate `gvy-official-site` project.

## Reviewed Releases

The original refresh workflow accepts an optional manual `prepare_only` input
(default false). With `force=true`, this rebuilds exact-LIVE data in GitHub,
validates the paired snapshots, builds the site, and uploads both the original
14-day backup and a separate `gvy-lantu-prepared-release` artifact. Preparation
never commits/pushes `main`, checks uninstalled candidate assets against the
production domain, or reports that a deployment passed. Both source steps must
succeed before the candidate artifact can be produced. Scheduled runs and normal
manual refreshes keep their existing publish, health-check and rollback behavior.

For a reviewed code release, start from production `main`, pick code changes only,
prepare cloud data on the release branch, inspect its immutable run/head and
artifact, then commit only the generated-data allowlist to that same branch.
Rerun tests, coverage/version validation, build and browser QA before merging the
reviewed code and data together. Do not publish local preview-data checkpoints.
After merge, verify the actual EdgeOne client URLs against that final revision;
keep the previous production commit and cloud backup available for rollback.

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
Hide the redundant literal `[蓝图]` hint from all displayed task titles, including
source rows, reward-dialog headings and prerequisite/completed/excluded tasks.
Preserve original localization and reward data. Bracketed runtime placeholders
such as `[目标]`, `[地点]`, `[飞船]`, `[编号]` and `[位置]` use light blue `#b8c9f1`,
distinct from cyan star systems. Escape text before adding their inline spans;
keep ordinary 蓝图 text, fonts, wrapping and click targets unchanged. A title's
old suffix never determines reward eligibility or probability.

Reward candidates and result-list summaries show verified compact class/grade
labels: Military/Stealth/Industrial/Civilian/Competition become 军/隐/工/民/竞,
combined with A-D only when the data provides a valid grade. Without a recognized
class, omit the compact class/grade field entirely, including a bare A-D. Do not
invent a class or show a lone grade in plan metadata, reward pools, list summaries
or their summary tooltips. Original grade fields, search and filtering remain intact. Summary
order is category, component/weapon type, compact class/grade, size, and optional
manufacturer (for example, 舰船组件 · 冷却器 · 隐C · S1 · 制造商).
Keep class/grade before trailing size/manufacturer text and verify actual visible
bounds on narrow screens; detail boxes retain full class and grade fields.
At 360px and below, reduce only the result-card column gaps and horizontal
padding so this order remains readable without shrinking text or moving grade first.

Ship weapons use their primary SCMDB subtype plus an explicit family from an
exact tag or canonical English type suffix: cannon, repeater, gatling, scattergun
or mass driver. Never relabel every laser weapon as a cannon or override the
primary subtype with a conflicting legacy calibration/tag. Unknown families keep
their existing subtype. Full types also appear in detailed manufacturing and
dismantling information and participate in search, as do compact class/grades.
Summary rows try the full type, measure actual width and line height, and fall
back to the original subtype if it would overflow or wrap. Recheck after result
rendering, dialog opening and a frame-debounced window resize. Wider layouts
restore full names. Keep fonts, colors, row styling and responsive columns intact;
do not shrink text or hide names to force a full type to fit. Main-list trailing
manufacturer text retains its existing intentional ellipsis and full tooltip.

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
user-facing place names. Preserve the mineral dialog's existing content-driven layout.

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
but must join a unique entity UUID, never a name, and must never erase/override primary SCMDB values or mix firing-mode calculations.
An unavailable or cross-build fallback leaves verified primary values intact.
Coverage metadata and payloads must agree; source/log messages must not claim that
all absolute attributes are absent merely because the optional fallback is late.
The scheduled refresh no longer fetches this duplicate gameplay export. SCMDB's
exact-LIVE item table supplies the primary panel; unsupported absolute metrics
retain their relative effects. Component class and mission type also come from
the same primary tables, not the secondary blueprint site's metadata.

Quality inputs retain a stable 72px by 23px pill beside each slider. The label
and numeric field are centered together; the field uses tabular-digit width
for its current value/placeholder and the same 14px line box as the label.
Only a pointer click within the capsule activates its numeric input; the tooltip
and surrounding empty area must not activate it. Keyboard Tab focus still works.
The initial
500 (or higher recipe minimum) is a semi-transparent gray placeholder, not
prefilled input text; focusing starts an empty draft. Leaving it empty preserves
the effective quality. Editing or moving the slider changes it to cyan.
Hover/focus reveals a smaller input/range hint
centered above the capsule without shifting the surrounding layout.
Enter/Tab retain their ordinary browser behavior, with no special acceptance
rule. Only integers are allowed, with maximum 1000 and the recipe minimum.
Negative/decimal/exponent input is rejected; high values clamp immediately,
and unfinished below-minimum drafts never affect calculations and clamp on blur.
The separate quick-value row and update-summary feature are not part of this UI.

## Craft Plan And Sharing

`制作清单` stores bounded counts and recipe choices in browser-local storage
under `gvy-lantu-craft-plan-v1`, independently of favorites. Adding a blueprint
opens its list; counts scale material amounts and sequential craft time. Resource
amounts use SCU, item inputs use counts, and different minimum qualities remain
separate. One alternative is selected per recipe slot; alternatives are never
all added together. Unknown/removed IDs remain removable and are excluded from
totals with a warning. Storage failure leaves the current session usable and
explicitly reports that it was not saved. No login, cloud permanence or device
synchronization is implied.

The plan dialog stays content-height driven and at most 640px wide. Planned item
names come first at 16px in the existing soft gold, ahead of material requirements.
Their following parentheses show `category · size · compact class/grade` at 12px
in muted regular text, wrapping naturally without shrinking the name. Omit missing
fields; without a recognized class omit the grade too, rather than showing a bare A-D.
Each row places its single-item craft duration to the left of the quantity
controls, separated by 16px. This is secondary 12px muted text, not multiplied
by the row count; narrow screens let its label/value wrap within that left area.
Use the same first-tier recipe duration as the total calculation, showing unknown
when unavailable and preserving a real zero. Do not invent missing durations.
Planned-piece and `清单总耗时` totals follow the materials at a secondary 14px in
white, with smaller muted labels. One short note explicitly states that material
and time totals include every item and its quantity in the whole plan; time is
estimated for sequential crafting, excluding queueing, not a single-item duration
or promised parallel completion time. Materials use aligned `material / quality
requirement / total amount` columns rather than two-column cards or a dot-separated sentence.
Resource totals retain SCU, item totals retain pieces, and missing quality stays
explicit instead of being invented. Saved-state and clear controls are secondary.
Within the material table, only quality digits use pale periwinkle `#b8c9f1`
(13px) and total-amount digits use soft mint `#9de2bf` (14px). Prefixes, units and
column labels stay muted; keep both below the gold item name's visual priority.
Each quantity has separate 32px desktop increment/decrement targets and direct input,
bounded to 1-9999. Recalculation preserves editable row/action nodes so input
blur cannot swallow the next click or disrupt keyboard Tab. Mobile places the
quantity controls below the item name with 40px touch targets. Quantity-control
borders and symbols stay muted, rather than visually dominating the item name.
Check actual reading order, relative typography and color, not only overflow.

Share links encode only the exact blueprint ID and craft/dismantle mode in the
URL fragment. They do not export favorites, filters or the craft plan. Clipboard
failure opens a selectable link. Opening an unavailable ID reports the missing
blueprint rather than substituting a same-name result.

## Local Preview

```bash
npm run build
python3 -m http.server 8002 --directory dist
```

Open `http://127.0.0.1:8002/`.

When the user requests local-only review, keep the preview available and do not
push, open a release PR, trigger Actions or deploy. Keep preview data separate
from release code commits. For later publication, use the original workflow's
non-publishing preparation mode, review its cloud candidate, and merge code and
data together so backup and production checks are not bypassed.

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
NAS/source validation, data timestamps, or existing refresh schedules. Mining
signals follow the unified automatic refresh described below.

For manual releases, also verify filter interactions, desktop/mobile overflow, console errors, and both the `星远舰队` and `维科洛查询` destinations.

## Data Refresh

Blueprint data refreshes are handled by `.github/workflows/refresh-blueprint-data.yml`.
The normal schedule (`17 */6 * * *`, UTC) checks SCMDB every six hours and only accepts the newest stable `LIVE` release. `PTU`, `EPTU`, Tech Preview, and other test channels are never published by this site, even when SCMDB lists them first or gives them a higher version number.

The maintenance schedule (`43 17 1,15 * *`, UTC) runs twice monthly with `--force`. It rebuilds the current stable LIVE release even when the version string is unchanged, so upstream corrections, localization calibration changes, and same-version crafting changes are not missed. It also updates `.github/refresh-heartbeat.json`; do not delete this tracked file or remove it from the commit allowlist.

The header shows the active LIVE version. Hovering or keyboard-focusing the version badge reveals `dataUpdatedAt` as `更新 YYYY/MM/DD HH:mm` in Asia/Shanghai; tapping the badge provides the same information on touch devices. This timestamp changes only after a newer release or a scheduled/manual forced calibration has been fetched, localized, validated, backed up, and atomically published. Routine six-hour checks with no newer LIVE release do not change it.

If SCMDB has no newer `LIVE` version and the verified NAS localization source has not changed, a normal six-hour run keeps the existing blueprint cache and makes no blueprint commit. A localization hash/adapter or source-policy schema change rebuilds the same LIVE through this command. The twice-monthly maintenance run intentionally creates a verified calibration snapshot and heartbeat commit. A stale manifest cannot roll an existing `LIVE` release backward. Mining still checks the exact selected build on every existing run, including same-build corrections.
If a newer `LIVE` version exists, `scripts/refresh_blueprint_data.py` locks the build to that exact release, regenerates the blueprint index, applies localization in this priority order:

1. NAS official Star Citizen localization, matched through verified game localization keys
2. Legacy localization snapshot and FlowCLD Chinese calibration for unresolved names
3. Google Translate fallback cache

### Official Localization Input

The authoritative file is `/volume1/docker/starcitizen-shared-input/localization/data/localization/chinese_(simplified)/global.ini` on NAS. The former `Documents/data` source is no longer authoritative. The existing `python3 scripts/refresh_blueprint_data.py` command is the only blueprint refresh entry point; no additional localization schedule or standalone sync CLI is introduced here.

An independently maintained NAS publisher uploads `global.ini.gz` and `source.json` to this repository's input-only `nas-localization` branch. GitHub Actions resolves the branch once to an immutable commit, reads both files from that commit, and verifies manifest schema, original byte length, original INI SHA256, source path and version label before use. A normal local run reads NAS over the existing `ssh nas` connection and verifies the source hash. Neither path writes to NAS. Source failure aborts the candidate and reports failure; it never presents a stale snapshot as a successful sync.

The helper `scripts/official_localization.py` produces the build input `data/official-localization/localization/starcitizen/nas-keyed-names.json`. The derived snapshot is backed up and committed with the existing workflow data allowlist, but is not included in `dist/`. Raw INI files remain on the input branch, never in the production output. Publisher deployment keys and scheduling belong to the separate NAS publisher, not this site.

The Chinese file currently declares only the `4.10` series. English key labels are read from an immutable `StarCitizenWiki/scunpacked-data` commit declaring the same series, not used as gameplay stats. `exactBuildVerified` remains false: this is not proof of an exact LIVE build match. A source series mismatch, invalid hash, or low coverage fails closed. On a new NAS hash or adapter revision the existing refresh rebuilds and applies official names last. Identical inputs preserve the snapshot timestamp. Exact names bridge upstream records to game keys; manufacturer codes and property keys take precedence. Item/vehicle, planet/company and crafting-slot contexts are distinct; full item names take precedence over short-name keys. Conflicting or missing matches retain marked legacy fallbacks and are listed in the refresh log, never guessed or claimed as NAS-verified.

The frontend uses verified material `nameZh` before its hardcoded fallback table. The mineral refresh applies that same snapshot to mineral and location names. Mineral footer copy stays `数据更新`, with no last-check timestamp or public source attribution.

The staged build uses SCMDB's exact-version item export for base stats and class, and the exact contracts for mission types. It no longer refetches another site's copy of those gameplay fields. FlowCLD is a committed, exact-blueprint-ID Chinese-name fallback only; it is no longer fetched in the scheduled pipeline and cannot supply gameplay metadata. Google/local language caches fill unresolved text before verified NAS keys are applied last. The community enrichment utility requires an immutable same-build source and a unique entity UUID but is not called automatically. Missing trustworthy absolute metrics retain relative-quality effects instead of values from another game build.

Before replacing data files, the script saves a local backup under `.data-backups/`.
Local backups are retained for 14 days and are ignored by Git.
In GitHub Actions, the backup folder is also uploaded as a workflow artifact with 14-day retention.
The upload must enable `include-hidden-files: true` for `.data-backups/`; validate
an actual artifact after a changed-data run, not just the workflow's conclusion.
All staged public files are validated before same-filesystem atomic replacement. Transient SCMDB network failures are retried up to three times; if refresh still fails, the existing LIVE cache and its displayed update time remain unchanged.

The same six-hour workflow runs `scripts/refresh_mineral_locations.py` once for both distributions and signals. Its structured input is SCMDB `mining_data-<exact blueprint LIVE>.json`. Schema, manifest counts, element/composition/cluster references, finite values, modes and coverage must validate. It retains at least 30 materials, 25 with locations, 100 location entries and 100 signal locations, with relative drop guards against the previous primary snapshot. The one-time schema-2 migration removes unverifiable legacy station mappings rather than relabeling them as current-LIVE evidence. NAS location names remain authoritative. Identical normalized contents retain the previous `retrievedAt` and exact file bytes.

This automatic policy supersedes the former manual-only signal rule. The old `refresh_mineral_signals.py` is only a compatibility alias to the same writer; no separate step or schedule is added. UEX distribution fetching and Shadow Guardians HTML signal parsing have been removed. A valid source with an unmapped material is not permission to fabricate a mine or copy an older build. Source failure preserves the last verified snapshot and remains a real failed refresh, not a successful timestamp-only update.

Mixed deposits show their primary mineral's signal, not the searched secondary material's global signature. Actual possible cluster counts are preserved. FPS/ROC signatures are shared per-rock readings and are not multiplied into invented cluster totals. Named areas retain system/parent context; generic Lagrange or asteroid templates are explicitly regions, never expanded into named stations. The export does not provide validated surface coordinates, so none are invented.

The mineral dialog retains its existing styling and content-driven height, capped
by the viewport. Location lists use two columns above 620 px and one column on
phones. Compact star-system controls filter exact reported systems without merging
location identities; known system/parent paths remain visible. Named distribution
areas are separate from generic region templates. Templates start collapsed when
named areas exist, or expanded when they are the only available locations.

Signals use one compact, gold-bordered popover anchored to the signal button,
without expanding or rearranging location rows. Desktop hover opens it; leaving
both the button and popover closes it after a short pointer-transition grace
period, even when the button still has mouse focus. Touch taps toggle it; tapping
outside or its close control dismisses it. The rest of the location is not a
signal trigger. Enter/Space opens it for keyboard users, Escape dismisses the
signal layer before the mineral dialog, and Tab remains within the dialog.
Filtering, scrolling the location list, resizing and closing the dialog remove
the old popover. The portal is outside the scrolling card, clamped to the dialog
and viewport, with internal scrolling for unusually long signal content.
Both dimensions follow the contents; 360px width and 400px height are upper
limits, not fixed sizes. Signal-button occlusion was explicitly deferred by the
user, so this compacting change leaves the original positioning helper intact.

Prioritize the searched primary mineral and explicitly label secondary matches.
Signal readings use the original gold capsules in a wrapping flex row, never
columns generated from cluster counts. Visible cluster-configuration lines are
omitted; the underlying actual count/value pairs remain in the data and each
capsule's accessible label. More readings wrap naturally without widening the popover.
Shared FPS/ROC values stay per-rock readings in their own labeled groups.
Explanatory signal notes appear once in smaller text at the bottom of the layer,
not repeatedly between each group heading and its readings.
Single-mode headings omit the mode already shown outside; only genuinely mixed
signal modes retain their compact labels, without the redundant mineral-body suffix.
Generic templates are marked as
non-exact locations. The dialog restores focus and the prior body scroll setting;
closed template contents must not enter the focus loop. This locally approved
popover design supersedes the earlier inline-only presentation, not its data rules.

Distributions and signals share a 14-day backup and atomic file replacement. `--validate-only` performs offline coverage/schema and blueprint/mining version-pair checks before building and again after workflow rebase, before push. A changed blueprint build with incompatible cached mining cannot be published. Production checks enforce the same pair and full hashes. The combined data fingerprint and existing failure/rollback behavior are retained. No new runtime API, schedule or credential is needed.

## Long-Term Unattended Operation

The site is designed to remain available for at least a year and to continue beyond that without routine application maintenance. It is a static site: browsing, filtering, favorites, quality controls, dismantling, and mineral dialogs do not depend on an application server, database, login provider, secret, or expiring API token at request time.

The persistence chain is:

1. GitHub Actions checks stable-LIVE blueprint data plus exact-version mineral distributions/signals four times per day, through the existing schedules.
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

The manufacturing detail panel contains a compact `成品品质效果` summary above the material cards. When the exact-version primary item export provides a reliable base attribute, the summary shows `Q500 base -> selected-quality result` and the percentage change. Metrics without a trustworthy base attribute show only the SCMDB-derived relative change. Blueprints whose crafting slots expose no modifier formula do not show a slider or a quality-result panel; the interface must not fabricate effects for them.

The validated 4.10.2 LIVE snapshot has 1,618 blueprints, 1,617 exact item matches, 1,549 with quality modifiers, and 1,440 with a trustworthy absolute quality metric. These are coverage observations, not hardcoded limits or proof of a complete weapon panel for every item. Unsupported metrics retain relative effects only; these calculations cannot guarantee that the in-game UI displays every crafted adjustment identically.

Manufacturing and dismantling are separate query modes selected from the prominent centered mode switch in the summary strip, between the result count and sorting controls. The manufacturing mode keeps material quality controls inside their corresponding material cards. The dismantling mode only lists records with verified recoverable outputs, changes the material filter to recovered output, hides mission-only controls, and renders a dedicated dismantling detail view.

Production builds fingerprint `assets/styles.css` and the transformed `assets/app.js` in the generated `dist/index.html`. During that build, `DATA_VERSION` is generated from the combined content hash of `data/blueprint-index.json` and `data/mineral-locations.json`; the generated revision also changes the application fingerprint. This is required because EdgeOne serves assets with a long immutable cache lifetime. Blueprint and mineral JSON requests use that content-derived query key and retain the previous verified cache when refresh validation fails. Refresh scripts must only update validated data files; they must never write a timestamp or version string into `assets/app.js` or `index.html`.

Dismantling is derived from the same LIVE dataset: it takes the first blueprint tier's resource and item inputs, applies the separate SCMDB resource/entity-class blacklists, and then applies the published dismantle efficiency and time. Resource quantities are displayed in SCU; recoverable item quantities are displayed as item counts. Do not silently substitute UEX, PTU, or manually estimated values for these outputs; if a future verified source adds exact per-item dismantling recipes, introduce it as an explicit versioned data adapter with validation and a visible source label.
