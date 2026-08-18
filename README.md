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

After every deployment, verify the production domain directly, including the page version, filter interactions, desktop/mobile overflow, console errors, and both the `GVY 主页` and `维科洛查询` destinations. A successful Git push alone is not proof that production deployment has completed.

## Data Refresh

Blueprint data refreshes are handled by `.github/workflows/refresh-blueprint-data.yml`.
The scheduled run checks SCMDB every six hours and only accepts the newest stable `LIVE` release. `PTU`, `EPTU`, Tech Preview, and other test channels are never published by this site, even when SCMDB lists them first or gives them a higher version number.

The header shows the active LIVE version. Hovering or keyboard-focusing the version badge reveals `dataUpdatedAt` as `更新 YYYY/MM/DD HH:mm` in Asia/Shanghai; tapping the badge provides the same information on touch devices. This timestamp changes only after a new dataset has been fetched, localized, validated, backed up, and atomically published; routine checks with no newer LIVE release do not change it.

If SCMDB has no newer `LIVE` version, the workflow keeps the existing data cache and makes no commit. A stale manifest is also prevented from rolling an existing `LIVE` release backward.
If a newer `LIVE` version exists, `scripts/refresh_blueprint_data.py` locks the build to that exact release, regenerates the blueprint index, applies localization in this priority order:

1. Local official Star Citizen localization package snapshot
2. FlowCLD Chinese calibration
3. Google Translate fallback cache

Before replacing data files, the script saves a local backup under `.data-backups/`.
Local backups are retained for 14 days and are ignored by Git.
In GitHub Actions, the backup folder is also uploaded as a workflow artifact with 14-day retention.
All staged public files are validated before same-filesystem atomic replacement. Transient SCMDB network failures are retried up to three times; if refresh still fails, the existing LIVE cache and its displayed update time remain unchanged.

The same six-hour workflow first runs `scripts/refresh_mineral_locations.py`. It fetches the current commodity/location relationships from UEX API 2.0, rebuilds all five supported location groups, applies the bundled official location localization first, and then preserves the calibrated Chinese fallbacks that are absent from the official package. The candidate must retain at least 30 materials, 25 materials with reliable locations, 100 total locations, and 100 location-specific signal mappings. It is also compared with the last verified cache, and large coverage drops are rejected. If the source data is unchanged, `retrievedAt` is not advanced and no commit is created.

After the location check, `scripts/refresh_mineral_signals.py` verifies the embedded `RADAR_DATA` published by the Shadow Guardians Mining Resource Finder, maps source aliases such as Quantanium/Quantainium, and updates only the radar base, maximum cluster, and derived values already attached to local mineral locations. Location distribution is not inferred by this signal-only step.

Mineral location and signal updates both use strict coverage checks, a 14-day backup under `.data-backups/`, same-filesystem atomic replacement, and a new frontend data cache key. If either external source is unavailable, incomplete, or invalid, that step keeps the last deployed verified mineral cache; it does not block a valid newer LIVE blueprint release. If verified values are unchanged, it makes no mineral-data commit.

## Blueprint Tools: Favorites, Quality, and Dismantling

The `我的蓝图` filter is deliberately browser-local. A user can save or remove a blueprint with the detail-panel button; the saved IDs live in `localStorage` under `gvy-lantu-favorite-blueprints-v1`. There is no account, cloud profile, or cross-device synchronization, so the interface must never imply that a login is available or required.

Each material card reads its slot's `modifiers` from the selected LIVE SCMDB crafting dataset and contains a compact quality slider plus the linearly interpolated property coefficient or additive adjustment. Quality is intentionally kept inside the corresponding material card rather than rendered as a separate section. It does not invent a final weapon/component stat, because the crafting source does not provide the complete base-stat model required for an exact aggregate calculation.

Manufacturing and dismantling are separate query modes selected from the prominent centered mode switch in the summary strip, between the result count and sorting controls. The manufacturing mode keeps material quality controls inside their corresponding material cards. The dismantling mode only lists records with verified recoverable outputs, changes the material filter to recovered output, hides mission-only controls, and renders a dedicated dismantling detail view.

Production builds fingerprint `assets/styles.css` and `assets/app.js` in the generated `dist/index.html`. This is required because EdgeOne serves assets with a long immutable cache lifetime; every CSS or JavaScript change therefore receives a new URL automatically. Blueprint and mineral JSON requests use the generated `DATA_VERSION` query key and retain the previous verified cache when refresh validation fails.

Dismantling is derived from the same LIVE dataset: it takes the first blueprint tier's resource and item inputs, applies the separate SCMDB resource/entity-class blacklists, and then applies the published dismantle efficiency and time. Resource quantities are displayed in SCU; recoverable item quantities are displayed as item counts. Do not silently substitute UEX, PTU, or manually estimated values for these outputs; if a future verified source adds exact per-item dismantling recipes, introduce it as an explicit versioned data adapter with validation and a visible source label.
