# GVY Lantu Site

Static site for the GVY blueprint search website. This is a separate production project from the GVY official site.

The formal production entry should be deployed through Tencent Cloud EdgeOne Pages / Makers at `https://lantu.gvyvoyagers.vip`.

Do not configure GitHub Pages for this repository, and do not point DNS back to `b1ndox.github.io`.

Official fleet website content belongs in the separate `gvy-official-site` project.

## Local Preview

```bash
python3 -m http.server 8002
```

Open `http://127.0.0.1:8002/` from this directory.

## Build

No build step. The repository root is the publish directory.

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
