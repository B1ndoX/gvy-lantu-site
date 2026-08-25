# GVY Lantu Site

Static site for the GVY blueprint search website. This is a separate production project from the GVY official site.

The formal production entry should be deployed through Tencent Cloud EdgeOne Pages / Makers at `https://lantu.gvyvoyagers.vip`.

Do not configure GitHub Pages for this repository, and do not point DNS back to `b1ndox.github.io`.

Official fleet website content belongs in the separate `gvy-official-site` project.

## Project Boundaries

- This repository contains only the GVY blueprint query site.
- The production domain is `https://lantu.gvyvoyagers.vip`.
- The "GVY 主页" link must point to `https://www.gvyvoyagers.vip`.
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

## Local Preview

```bash
npm run build
python3 -m http.server 8002 --directory dist
```

Open `http://127.0.0.1:8002/`.

## Build

`npm run build` creates a production-only `dist/` directory. `edgeone.json` configures Makers to publish that directory so refresh scripts, localization sources, caches, and repository documentation are not exposed as site files.

## Production Deployment

Commit and push production changes only from this repository. Tencent Cloud EdgeOne Pages / Makers builds the connected `B1ndoX/gvy-lantu-site` repository with `npm run build` and publishes `dist/` to `https://lantu.gvyvoyagers.vip`.

The project deliberately has no runtime npm dependencies. EdgeOne uses its supported Node.js `24.5.0` image, skips package installation with `node --version`, and runs the repository-owned static build script. The generated HTML is revalidated on every request, while fingerprinted assets and version-keyed JSON remain long-cacheable.

After every automated data deployment, `scripts/check_production_health.py` polls the formal domain for up to 15 minutes. Runs with no repository change still perform an immediate production snapshot check, so an EdgeOne outage, stale deployment, or corrupted public payload cannot remain silently green between data releases. Updated and unchanged deployments are verified through the exact versioned CSS, JavaScript, compressed JSON, and uncompressed JSON URLs used by browsers. The checker requires the deployed asset fingerprints and embedded data revision to match the final repository checkout, verifies that the public blueprint payload is stable `LIVE`, compares its complete semantic hash with the committed payload, and performs the same complete comparison plus coverage checks for mineral locations and signals. If an automated refresh commit does not become healthy, the workflow reverts that exact machine commit, pushes the previous verified snapshot, and waits for production recovery. It never automatically reverts an unrelated manual commit. A successful Git push alone is not proof that production deployment has completed.

For manual releases, also verify filter interactions, desktop/mobile overflow, console errors, and both the `GVY 主页` and `维科洛查询` destinations.

## Data Refresh

Blueprint data refreshes are handled by `.github/workflows/refresh-blueprint-data.yml`.
The normal schedule (`17 */6 * * *`, UTC) checks SCMDB every six hours and only accepts the newest stable `LIVE` release. `PTU`, `EPTU`, Tech Preview, and other test channels are never published by this site, even when SCMDB lists them first or gives them a higher version number.

The maintenance schedule (`43 17 1,15 * *`, UTC) runs twice monthly with `--force`. It rebuilds the current stable LIVE release even when the version string is unchanged, so upstream corrections, localization calibration changes, and same-version crafting changes are not missed. It also updates `.github/refresh-heartbeat.json`; do not delete this tracked file or remove it from the commit allowlist.

The header shows the active LIVE version. Hovering or keyboard-focusing the version badge reveals `dataUpdatedAt` as `更新 YYYY/MM/DD HH:mm` in Asia/Shanghai; tapping the badge provides the same information on touch devices. This timestamp changes only after a newer release or a scheduled/manual forced calibration has been fetched, localized, validated, backed up, and atomically published. Routine six-hour checks with no newer LIVE release do not change it.

If SCMDB has no newer `LIVE` version, a normal six-hour run keeps the existing data cache and makes no commit. The twice-monthly maintenance run intentionally creates a verified calibration snapshot and heartbeat commit. A stale manifest is prevented from rolling an existing `LIVE` release backward.
If a newer `LIVE` version exists, `scripts/refresh_blueprint_data.py` locks the build to that exact release, regenerates the blueprint index, applies localization in this priority order:

1. Local official Star Citizen localization package snapshot
2. FlowCLD Chinese calibration
3. Google Translate fallback cache

The same staged build also attempts to attach compact base attributes from the community-maintained `StarCitizenWiki/scunpacked-data` item export. The source commit must declare the exact same `X.Y.Z-LIVE.build` version as the SCMDB blueprint index, and matching/base-stat coverage must pass minimum thresholds before those values are accepted. A temporary source outage or a lagging community release never blocks a newer verified LIVE blueprint release: the site publishes the SCMDB quality coefficients and relative effects first, then retries the version-matched base-stat enrichment on later six-hour runs. It never combines base attributes from one game build with quality coefficients from another.

Before replacing data files, the script saves a local backup under `.data-backups/`.
Local backups are retained for 14 days and are ignored by Git.
In GitHub Actions, the backup folder is also uploaded as a workflow artifact with 14-day retention.
All staged public files are validated before same-filesystem atomic replacement. Transient SCMDB network failures are retried up to three times; if refresh still fails, the existing LIVE cache and its displayed update time remain unchanged.

The same six-hour workflow first runs `scripts/refresh_mineral_locations.py`. It fetches the current commodity/location relationships from UEX API 2.0, rebuilds all five supported location groups, applies the bundled official location localization first, and then preserves the calibrated Chinese fallbacks that are absent from the official package. The candidate must retain at least 30 materials, 25 materials with reliable locations, 100 total locations, and 100 location-specific signal mappings. It is also compared with the last verified cache, and large coverage drops are rejected. If the source data is unchanged, `retrievedAt` is not advanced and no commit is created.

After the location check, `scripts/refresh_mineral_signals.py` verifies the embedded `RADAR_DATA` published by the Shadow Guardians Mining Resource Finder, maps source aliases such as Quantanium/Quantainium, and updates only the radar base, maximum cluster, and derived values already attached to local mineral locations. Location distribution is not inferred by this signal-only step.

Mineral location and signal updates both use strict coverage checks, a 14-day backup under `.data-backups/`, and same-filesystem atomic replacement. The production build derives one frontend data revision from the exact bytes of both verified JSON files, so either a blueprint change or a mineral change automatically creates a new browser cache URL without editing application source. If either external source is unavailable, incomplete, or invalid, that step keeps the last deployed verified mineral cache; it does not block a valid newer LIVE blueprint release. The workflow is marked failed after the verified old production snapshot has been checked, so a permanently broken source cannot remain silently green. If verified values are unchanged, it makes no mineral-data commit. The mineral dialog displays the newest valid timestamp among the UEX location snapshot and signal calibration.

## Long-Term Unattended Operation

The site is designed to remain available for at least a year and to continue beyond that without routine application maintenance. It is a static site: browsing, filtering, favorites, quality controls, dismantling, and mineral dialogs do not depend on an application server, database, login provider, secret, or expiring API token at request time.

The persistence chain is:

1. GitHub Actions checks all data sources four times per day.
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
