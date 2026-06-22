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
