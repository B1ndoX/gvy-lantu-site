#!/usr/bin/env python3
"""Refresh verified mineral radar values without replacing location data."""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "mineral-locations.json"
BACKUP_DIR = ROOT / ".data-backups"
SOURCE_URL = "https://sg-mining-finder.pages.dev/"
BACKUP_RETENTION_DAYS = 14
MIN_SIGNAL_DEFINITIONS = 20
MIN_LOCATION_SIGNALS = 100
NAME_ALIASES = {
    "Aluminium": "Aluminum",
    "Ice": "Pressurized Ice",
    "Quantanium": "Quantainium",
}
REQUIRED_MATERIALS = {"Copper", "Iron", "Laranite", "Quantainium", "Tungsten"}


class ScriptCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self._parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script":
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._parts is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._parts is not None:
            self.scripts.append("".join(self._parts))
            self._parts = None


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def fetch_source_html(attempts: int = 3) -> str:
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "GVY Lantu Site/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read().decode("utf-8")
        except Exception:
            if attempt == attempts:
                raise
            wait_seconds = attempt * 2
            print(f"mineral signal source failed; retrying in {wait_seconds}s ({attempt}/{attempts})")
            time.sleep(wait_seconds)
    raise RuntimeError("mineral signal source retries were exhausted")


def parse_signal_definitions(html: str) -> tuple[str, dict[str, dict[str, int]]]:
    version_match = re.search(r"RADAR\s+SIGNATURES\s+([0-9]+(?:\.[0-9]+)+)", html, flags=re.IGNORECASE)
    if not version_match:
        raise RuntimeError("mineral signal source has no version label")

    collector = ScriptCollector()
    collector.feed(html)
    script = next((value for value in collector.scripts if "const RADAR_DATA" in value), "")
    block_match = re.search(r"const\s+RADAR_DATA\s*=\s*\[(.*?)\n\s*\];", script, flags=re.DOTALL)
    if not block_match:
        raise RuntimeError("mineral signal source has no RADAR_DATA block")

    definitions: dict[str, dict[str, int]] = {}
    for object_match in re.finditer(r"\{([^{}]+)\}", block_match.group(1), flags=re.DOTALL):
        body = object_match.group(1)
        if re.search(r"\bsearchOnly\s*:\s*true\b", body):
            continue
        name_match = re.search(r"\bname\s*:\s*'([^']+)'", body)
        base_match = re.search(r"\brs\s*:\s*(\d+)", body)
        cluster_match = re.search(r"\bmaxCluster\s*:\s*(\d+)", body)
        if not (name_match and base_match and cluster_match):
            continue

        name = NAME_ALIASES.get(name_match.group(1), name_match.group(1))
        base = int(base_match.group(1))
        max_cluster = int(cluster_match.group(1))
        if name in definitions:
            raise RuntimeError(f"mineral signal source contains duplicate material: {name}")
        if not 2500 <= base <= 5000:
            raise RuntimeError(f"mineral signal base is outside the accepted range: {name}={base}")
        if not 1 <= max_cluster <= 8:
            raise RuntimeError(f"mineral signal cluster count is outside the accepted range: {name}={max_cluster}")
        definitions[name] = {"base": base, "maxCluster": max_cluster}

    if len(definitions) < MIN_SIGNAL_DEFINITIONS:
        raise RuntimeError(f"mineral signal source returned only {len(definitions)} definitions")
    missing = sorted(REQUIRED_MATERIALS - definitions.keys())
    if missing:
        raise RuntimeError(f"mineral signal source is missing required materials: {', '.join(missing)}")
    return version_match.group(1), definitions


def expected_values(definition: dict[str, int]) -> list[int]:
    base = definition["base"]
    return [base * multiplier for multiplier in range(1, definition["maxCluster"] + 1)]


def update_signal(signal: dict[str, Any], definition: dict[str, int]) -> bool:
    next_fields: dict[str, Any] = {
        "base": definition["base"],
        "maxCluster": definition["maxCluster"],
        "values": expected_values(definition),
    }
    changed = any(signal.get(key) != value for key, value in next_fields.items())
    signal.update(next_fields)
    return changed


def apply_signal_definitions(
    payload: dict[str, Any],
    definitions: dict[str, dict[str, int]],
    source_version: str,
    synced_at: datetime,
) -> tuple[bool, int, int]:
    materials = payload.get("materials") or {}
    changed = False
    matched_materials = 0
    location_signals = 0

    for name, item in materials.items():
        definition = definitions.get(name)
        if not definition:
            continue
        matched_materials += 1
        signal = item.setdefault("signal", {})
        changed = update_signal(signal, definition) or changed

        for locations in (item.get("locations") or {}).values():
            for location in locations or []:
                location_signal = location.get("signal")
                if not location_signal:
                    continue
                location_signals += 1
                changed = update_signal(location_signal, definition) or changed

    if matched_materials < MIN_SIGNAL_DEFINITIONS:
        raise RuntimeError(f"only {matched_materials} signal materials matched the local dataset")
    if location_signals < MIN_LOCATION_SIGNALS:
        raise RuntimeError(f"only {location_signals} location signals matched the local dataset")

    metadata = payload.setdefault("metadata", {})
    metadata_fields = {
        "signalSource": "Shadow Guardians Mining Resource Finder",
        "locationSignalSource": SOURCE_URL,
        "signalSourceVersion": source_version,
    }
    metadata_changed = any(metadata.get(key) != value for key, value in metadata_fields.items())
    if changed or metadata_changed:
        metadata.update(metadata_fields)
        metadata["signalUpdatedAt"] = synced_at.date().isoformat()
        metadata["signalSyncedAt"] = synced_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        changed = True

    return changed, matched_materials, location_signals


def validate_payload(payload: dict[str, Any], definitions: dict[str, dict[str, int]]) -> None:
    matched_materials = 0
    location_signals = 0
    for name, item in (payload.get("materials") or {}).items():
        definition = definitions.get(name)
        if not definition:
            continue
        matched_materials += 1
        expected = expected_values(definition)
        signal = item.get("signal") or {}
        if signal.get("base") != definition["base"] or signal.get("maxCluster") != definition["maxCluster"]:
            raise RuntimeError(f"invalid material signal metadata: {name}")
        if signal.get("values") != expected:
            raise RuntimeError(f"invalid material signal values: {name}")

        for locations in (item.get("locations") or {}).values():
            for location in locations or []:
                location_signal = location.get("signal")
                if not location_signal:
                    continue
                location_signals += 1
                if location_signal.get("values") != expected:
                    raise RuntimeError(f"invalid location signal values: {name}/{location.get('en') or location.get('zh')}")
                if location_signal.get("base") != definition["base"]:
                    raise RuntimeError(f"invalid location signal base: {name}/{location.get('en') or location.get('zh')}")
                if location_signal.get("maxCluster") != definition["maxCluster"]:
                    raise RuntimeError(f"invalid location signal cluster count: {name}/{location.get('en') or location.get('zh')}")

    if matched_materials < MIN_SIGNAL_DEFINITIONS or location_signals < MIN_LOCATION_SIGNALS:
        raise RuntimeError("validated mineral signal coverage is unexpectedly low")


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


def backup_current_data(now: datetime) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / f"{now.strftime('%Y%m%dT%H%M%SZ')}-mineral-signals"
    target.mkdir(parents=True, exist_ok=False)
    shutil.copy2(DATA_PATH, target / DATA_PATH.name)
    (target / "backup-meta.json").write_text(
        json.dumps(
            {
                "createdAt": now.isoformat(),
                "reason": "mineral signal refresh",
                "retentionDays": BACKUP_RETENTION_DAYS,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    prune_old_backups(now)
    return target


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.signal-refresh-tmp")
    temporary.unlink(missing_ok=True)
    try:
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def refresh(check_only: bool = False) -> bool:
    source_version, definitions = parse_signal_definitions(fetch_source_html())
    current = load_json(DATA_PATH)
    candidate = copy.deepcopy(current)
    synced_at = datetime.now(timezone.utc)
    changed, material_count, location_count = apply_signal_definitions(
        candidate,
        definitions,
        source_version,
        synced_at,
    )
    validate_payload(candidate, definitions)
    print(
        f"verified mineral signals v{source_version}: "
        f"{material_count} materials, {location_count} location signals"
    )
    if not changed:
        prune_old_backups(synced_at)
        print("mineral signal values unchanged; keeping existing cache")
        return False
    if check_only:
        print("mineral signal update available; check-only mode left files unchanged")
        return True

    backup = backup_current_data(synced_at)
    write_json_atomic(DATA_PATH, candidate)
    print(f"mineral signals updated; backup saved: {backup}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh verified Star Citizen mineral radar values.")
    parser.add_argument("--check-only", action="store_true", help="Report changes without writing files.")
    args = parser.parse_args()
    refresh(check_only=args.check_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
