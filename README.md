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
The scheduled run checks SCMDB every Monday at 01:00 Asia/Shanghai.

If SCMDB has no newer version, the workflow keeps the existing data cache and makes no commit.
If a newer version exists, `scripts/refresh_blueprint_data.py` regenerates the blueprint index, applies localization in this priority order:

1. Local official Star Citizen localization package snapshot
2. FlowCLD Chinese calibration
3. Google Translate fallback cache

Before replacing data files, the script saves a local backup under `.data-backups/`.
Local backups are retained for 14 days and are ignored by Git.
In GitHub Actions, the backup folder is also uploaded as a workflow artifact with 14-day retention.
