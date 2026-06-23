#!/usr/bin/env python3
"""Refresh GVY blueprint data only when SCMDB publishes a newer version."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
APP_JS = ROOT / "assets" / "app.js"
INDEX_HTML = ROOT / "index.html"
BACKUP_DIR = ROOT / ".data-backups"
SCMDB_VERSIONS_URL = "https://scmdb.net/data/versions.json"
OFFICIAL_LOCALIZATION_SOURCE = "sc-spectrum-qq-bot/assets/localization/starcitizen"
BACKUP_RETENTION_DAYS = 14


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json_compact(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def fetch_latest_scmdb_version() -> str:
    request = urllib.request.Request(SCMDB_VERSIONS_URL, headers={"User-Agent": "GVY Lantu Site/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        versions = json.loads(response.read().decode("utf-8"))
    if not versions:
        raise RuntimeError("SCMDB versions.json returned no versions")
    return str(versions[0]["version"])


def run(args: list[str], *, allow_failure: bool = False) -> bool:
    print("+", " ".join(args))
    result = subprocess.run(args, cwd=ROOT)
    if result.returncode == 0:
        return True
    if allow_failure:
        print(f"warning: command failed with exit {result.returncode}: {' '.join(args)}", file=sys.stderr)
        return False
    raise subprocess.CalledProcessError(result.returncode, args)


def copy_if_exists(source: Path, target: Path) -> None:
    if source.exists():
        shutil.copy2(source, target)


def clean_version_slug(version: str) -> str:
    safe = "".join(char if char.isalnum() or char in "._-" else "-" for char in version)
    return safe.strip("-") or "unknown"


def prune_old_backups(now: datetime) -> None:
    if not BACKUP_DIR.exists():
        return
    cutoff = now - timedelta(days=BACKUP_RETENTION_DAYS)
    for child in BACKUP_DIR.iterdir():
        if not child.is_dir():
            continue
        try:
            created = datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if created < cutoff:
            shutil.rmtree(child)


def backup_current_data(current_version: str, now: datetime) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_name = f"{now.strftime('%Y%m%dT%H%M%SZ')}-{clean_version_slug(current_version)}"
    target = BACKUP_DIR / backup_name
    target.mkdir(parents=True, exist_ok=False)
    for relative in (
        "blueprint-index.json",
        "mineral-locations.json",
        "google-translate-cache.json",
        "flowcld-blueprint-calibration.json",
        "local-polish-names.json",
    ):
        copy_if_exists(DATA_DIR / relative, target / relative)
    (target / "backup-meta.json").write_text(
        json.dumps(
            {
                "createdAt": now.isoformat(),
                "version": current_version,
                "retentionDays": BACKUP_RETENTION_DAYS,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"backup saved: {target}")
    prune_old_backups(now)
    return target


def update_data_version(version: str) -> None:
    text = APP_JS.read_text(encoding="utf-8")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    next_value = f"{stamp}-{version.replace('.', '-').replace('+', '-')}"
    old = 'const DATA_VERSION = "'
    start = text.find(old)
    if start < 0:
        raise RuntimeError("DATA_VERSION declaration not found in assets/app.js")
    start += len(old)
    end = text.find('"', start)
    if end < 0:
        raise RuntimeError("DATA_VERSION declaration is malformed")
    APP_JS.write_text(text[:start] + next_value + text[end:], encoding="utf-8")

    html = INDEX_HTML.read_text(encoding="utf-8")
    html = re.sub(r"assets/app\.js\?v=[^\"']+", f"assets/app.js?v={next_value}", html)
    INDEX_HTML.write_text(html, encoding="utf-8")


def annotate_localization_metadata(index_path: Path) -> None:
    index = load_json(index_path, {})
    localization = index.setdefault("localization", {})
    localization["priority"] = ["本地官方汉化总包", "FlowCLD 中文校准", "Google Translate 兜底"]
    localization["officialLocalizationSource"] = OFFICIAL_LOCALIZATION_SOURCE
    write_json_compact(index_path, index)


def validate_index(path: Path, expected_version: str) -> None:
    index = load_json(path, {})
    records = index.get("records") or []
    counts = index.get("counts") or {}
    if index.get("version") != expected_version:
        raise RuntimeError(f"generated version {index.get('version')} does not match latest {expected_version}")
    if not records:
        raise RuntimeError("generated blueprint index has no records")
    if counts.get("blueprints") != len(records):
        raise RuntimeError("blueprint count does not match records length")


def refresh(force: bool) -> bool:
    current = load_json(DATA_DIR / "blueprint-index.json", {})
    current_version = str(current.get("version") or "")
    latest_version = fetch_latest_scmdb_version()
    print(f"current SCMDB version: {current_version or 'none'}")
    print(f"latest SCMDB version:  {latest_version}")
    if current_version == latest_version and not force:
        print("SCMDB version unchanged; keeping existing data cache.")
        prune_old_backups(datetime.now(timezone.utc))
        return False

    with tempfile.TemporaryDirectory(prefix="gvy-lantu-refresh-") as tmp_name:
        tmp = Path(tmp_name)
        index_path = tmp / "blueprint-index.json"
        google_cache = tmp / "google-translate-cache.json"
        flowcld = tmp / "flowcld-blueprint-calibration.json"
        local_names = tmp / "local-polish-names.json"

        copy_if_exists(DATA_DIR / "google-translate-cache.json", google_cache)
        copy_if_exists(DATA_DIR / "flowcld-blueprint-calibration.json", flowcld)
        copy_if_exists(DATA_DIR / "local-polish-names.json", local_names)

        run([sys.executable, "scripts/build_data.py", "--out", str(index_path)])
        run([sys.executable, "scripts/translate_index_google.py", "--index", str(index_path), "--cache", str(google_cache)])

        fresh_flowcld = tmp / "flowcld-blueprint-calibration.fresh.json"
        if run(
            [
                sys.executable,
                "scripts/fetch_flowcld_calibration.py",
                "--output",
                str(fresh_flowcld),
                "--delay",
                "0.1",
            ],
            allow_failure=True,
        ):
            shutil.move(str(fresh_flowcld), flowcld)
        elif not flowcld.exists():
            raise RuntimeError("FlowCLD refresh failed and no cached calibration exists")

        run(
            [
                sys.executable,
                "scripts/apply_local_polish.py",
                "--index",
                str(index_path),
                "--local-names",
                str(local_names),
                "--flowcld-calibration",
                str(flowcld),
            ]
        )
        annotate_localization_metadata(index_path)
        validate_index(index_path, latest_version)

        backup_current_data(current_version or "none", datetime.now(timezone.utc))
        shutil.copy2(index_path, DATA_DIR / "blueprint-index.json")
        copy_if_exists(google_cache, DATA_DIR / "google-translate-cache.json")
        copy_if_exists(flowcld, DATA_DIR / "flowcld-blueprint-calibration.json")
        copy_if_exists(local_names, DATA_DIR / "local-polish-names.json")
        update_data_version(latest_version)

    print(f"updated blueprint data to {latest_version}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh GVY blueprint data when SCMDB publishes a new version.")
    parser.add_argument("--force", action="store_true", help="Refresh even when SCMDB version is unchanged.")
    args = parser.parse_args()
    refresh(args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
