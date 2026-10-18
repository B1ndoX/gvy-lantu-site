#!/usr/bin/env python3
"""Continuously refresh GVY blueprints from the latest stable SCMDB LIVE release."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scmdb_versions import is_live_version, select_latest_live_version, version_sort_key
from build_data import fetch_json, reward_items, validate_mission_rewards
from scmdb_item_stats import validate_item_stats
from official_localization import SNAPSHOT, refresh_snapshot


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BACKUP_DIR = ROOT / ".data-backups"
SCMDB_VERSIONS_URL = "https://scmdb.net/data/versions.json"
OFFICIAL_LOCALIZATION_ASSETS = DATA_DIR / "official-localization"
OFFICIAL_LOCALIZATION_SOURCE = "data/official-localization/localization/starcitizen"
BACKUP_RETENTION_DAYS = 14
MIN_BLUEPRINT_RECORDS = 1000
MIN_OFFICIAL_LOCALIZATION_COUNT = 7000
MIN_FLOWCLD_RECORDS = 1000
MIN_FLOWCLD_LOCALIZED_RECORDS = 1000
PUBLIC_RECORD_FIELDS_TO_REMOVE = {
    "search",
    "materials",
    "productEntityClass",
    "hasKnownIssue",
    "tag",
}


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json_compact(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")


def fetch_latest_live_scmdb_version(attempts: int = 3) -> str:
    versions = fetch_json(SCMDB_VERSIONS_URL, attempts)
    if not versions:
        raise RuntimeError("SCMDB versions.json returned no versions")
    return select_latest_live_version(versions)["version"]


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


def replace_if_exists(source: Path, target: Path) -> None:
    """Publish a staged file atomically on the destination filesystem."""
    if not source.exists():
        return
    temporary_target = target.with_name(f".{target.name}.refresh-tmp")
    temporary_target.unlink(missing_ok=True)
    try:
        shutil.copy2(source, temporary_target)
        temporary_target.replace(target)
    finally:
        temporary_target.unlink(missing_ok=True)


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
    copy_if_exists(SNAPSHOT, target / SNAPSHOT.name)
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


def annotate_localization_metadata(index_path: Path) -> None:
    index = load_json(index_path, {})
    localization = index.setdefault("localization", {})
    localization["priority"] = ["NAS 官方汉化精确 key 快照", "旧汉化及 FlowCLD 校准回退", "Google Translate 兜底"]
    localization["officialLocalizationSource"] = OFFICIAL_LOCALIZATION_SOURCE
    write_json_compact(index_path, index)


def annotate_refresh_metadata(index_path: Path, version: str, updated_at: datetime) -> None:
    index = load_json(index_path, {})
    index["releaseChannel"] = "LIVE"
    index["dataUpdatedAt"] = updated_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    index["version"] = version
    write_json_compact(index_path, index)


def validate_flowcld_calibration(path: Path, cached_path: Path | None = None) -> None:
    payload = load_json(path, {})
    item_count = int(payload.get("itemCount") or len(payload.get("items") or []))
    localized_count = int(payload.get("localizedCount") or 0)
    if item_count < MIN_FLOWCLD_RECORDS or localized_count < MIN_FLOWCLD_LOCALIZED_RECORDS:
        raise RuntimeError(
            f"FlowCLD calibration coverage is too low: {item_count} records, {localized_count} localized"
        )
    if cached_path and cached_path.exists():
        cached = load_json(cached_path, {})
        cached_items = int(cached.get("itemCount") or len(cached.get("items") or []))
        cached_localized = int(cached.get("localizedCount") or 0)
        if cached_items and item_count < int(cached_items * 0.8):
            raise RuntimeError(f"FlowCLD record coverage dropped unexpectedly: {cached_items} -> {item_count}")
        if cached_localized and localized_count < int(cached_localized * 0.8):
            raise RuntimeError(
                f"FlowCLD localization coverage dropped unexpectedly: {cached_localized} -> {localized_count}"
            )


def compact_public_index(index_path: Path) -> int:
    """Remove pipeline-only fields after localization has finished."""
    index = load_json(index_path, {})
    removed = 0
    for record in index.get("records") or []:
        for field in PUBLIC_RECORD_FIELDS_TO_REMOVE:
            if field in record:
                record.pop(field)
                removed += 1
    if removed:
        write_json_compact(index_path, index)
    return removed


def mission_coverage(index: dict[str, Any]) -> dict[str, int]:
    missions = set()
    pools = set()
    records_with_missions = 0
    for record in index.get("records") or []:
        has_missions = False
        for source in record.get("sources") or []:
            for mission in source.get("missions") or []:
                identity = mission.get("id") or json.dumps(
                    [mission.get(key) for key in ("debugName", "title", "faction", "rewardUEC", "systems")],
                    sort_keys=True,
                )
                missions.add(identity)
                pools.add(source.get("poolId"))
                has_missions = True
        records_with_missions += has_missions
    rewards = (index.get("missionRewards") or {}).get("missions") or {}
    return {"contracts": len(missions), "pools": len(pools), "blueprints": records_with_missions,
            "conditions": sum(any(key in (detail.get("requirements") or {}) for key in ("canBeShared", "minStanding", "crimeStat")) for detail in rewards.values()),
            "locations": len((index.get("missionRewards") or {}).get("locations") or {}),
            "itemRewards": sum(len(reward_items(reward)) for detail in rewards.values()
                               for reward in detail.get("items") or [])}


def validate_mission_coverage(index: dict[str, Any], previous: dict[str, Any]) -> None:
    current_counts = mission_coverage(index)
    for label, old_count in mission_coverage(previous).items():
        if old_count and current_counts[label] < old_count * 0.8:
            raise RuntimeError(f"mission reward {label} coverage dropped unexpectedly: {old_count} -> {current_counts[label]}")


def validate_index(path: Path, expected_version: str, previous: dict[str, Any] | None = None) -> None:
    index = load_json(path, {})
    records = index.get("records") or []
    counts = index.get("counts") or {}
    localization = index.get("localization") or {}
    if not is_live_version(expected_version):
        raise RuntimeError(f"refresh target is not a stable LIVE version: {expected_version}")
    if index.get("version") != expected_version:
        raise RuntimeError(f"generated version {index.get('version')} does not match latest LIVE {expected_version}")
    if not is_live_version(str(index.get("version") or "")):
        raise RuntimeError(f"generated index is not from a stable LIVE version: {index.get('version')}")
    if index.get("releaseChannel") != "LIVE":
        raise RuntimeError(f"generated index has invalid release channel: {index.get('releaseChannel')}")
    updated_at = str(index.get("dataUpdatedAt") or "")
    try:
        parsed_updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeError("generated index has no valid dataUpdatedAt timestamp") from error
    if parsed_updated_at.tzinfo is None:
        raise RuntimeError("generated index dataUpdatedAt must include a timezone")
    if len(records) < MIN_BLUEPRINT_RECORDS:
        raise RuntimeError(f"generated blueprint index has too few records: {len(records)}")
    if counts.get("blueprints") != len(records):
        raise RuntimeError("blueprint count does not match records length")
    record_ids = [str(record.get("id") or "") for record in records]
    if any(not record_id for record_id in record_ids):
        raise RuntimeError("generated blueprint index contains a record without an id")
    if len(set(record_ids)) != len(record_ids):
        raise RuntimeError("generated blueprint index contains duplicate record ids")
    if sum((counts.get("categories") or {}).values()) != len(records):
        raise RuntimeError("blueprint category counts do not match records length")
    if any(not str(record.get("name") or "").strip() for record in records):
        raise RuntimeError("generated blueprint index contains an unnamed record")
    if any(
        (record.get("sourceCount") or 0)
        != sum((source.get("missionCount") or 0) for source in record.get("sources") or [])
        for record in records
    ):
        raise RuntimeError("blueprint source counts do not match source missions")
    for record in records:
        for tier in record.get("tiers") or []:
            for slot in tier.get("slots") or []:
                for option in slot.get("options") or []:
                    minimum = option.get("minQuality", 0)
                    quantity = option.get("quantity")
                    if (isinstance(minimum, bool) or not isinstance(minimum, (int, float)) or not math.isfinite(minimum)
                            or int(minimum) != minimum or not 0 <= minimum <= 1000):
                        raise RuntimeError("invalid material quality range")
                    if (isinstance(quantity, bool) or not isinstance(quantity, (int, float)) or not math.isfinite(quantity) or quantity < 0):
                        raise RuntimeError("invalid crafting material quantity")
    validate_mission_rewards(index)
    validate_item_stats(index)
    if previous is not None:
        validate_mission_coverage(index, previous)
        old_stats = previous.get("itemStats") or {}
        for key in ("matchedItems", "recordsWithBaseStats"):
            if index["itemStats"][key] < int(old_stats.get(key, 0) * 0.8):
                raise RuntimeError(f"SCMDB item stat {key} coverage dropped unexpectedly")
    if int(localization.get("starCitizenLocalizationCount") or 0) < MIN_OFFICIAL_LOCALIZATION_COUNT:
        raise RuntimeError("official Star Citizen localization coverage is unexpectedly low")
    quality_effects = index.get("qualityEffects")
    if quality_effects:
        quality_version = str(quality_effects.get("version") or "")
        if quality_version.lower() != expected_version.lower():
            raise RuntimeError(
                f"quality base stats {quality_version} do not match blueprint version {expected_version}"
            )
        modifier_count = int(quality_effects.get("recordsWithModifiers") or 0)
        matched_count = int(quality_effects.get("matchedItems") or 0)
        base_count = int(quality_effects.get("recordsWithBaseStats") or 0)
        if not (0 <= base_count <= matched_count <= modifier_count <= len(records)):
            raise RuntimeError("quality coverage metadata is inconsistent")
        actual_modifier_count = sum(
            any(
                slot.get("modifiers")
                for slot in ((record.get("tiers") or [{}])[0].get("slots") or [])
            )
            for record in records
        )
        actual_base_count = sum(bool(record.get("qualityStats")) for record in records)
        if actual_modifier_count != modifier_count or actual_base_count != base_count:
            raise RuntimeError("quality coverage metadata does not match blueprint records")
        if previous and previous.get("itemStats"):
            old_base_count = (previous.get("qualityEffects") or {}).get("recordsWithBaseStats", 0)
            if base_count < int(old_base_count * 0.8):
                raise RuntimeError("quality base-stat coverage dropped unexpectedly")
        if any(
            isinstance(metric.get("value"), bool)
            or not isinstance(metric.get("value"), (int, float))
            or not math.isfinite(float(metric.get("value")))
            for record in records
            for metric in record.get("qualityStats") or []
        ):
            raise RuntimeError("quality base stats contain a non-numeric value")


def refresh(force: bool) -> bool:
    current = load_json(DATA_DIR / "blueprint-index.json", {})
    current_version = str(current.get("version") or "")
    latest_version = fetch_latest_live_scmdb_version()
    print(f"current SCMDB version: {current_version or 'none'}")
    print(f"latest LIVE version:   {latest_version}")
    if is_live_version(current_version) and version_sort_key(current_version) > version_sort_key(latest_version):
        raise RuntimeError(
            f"refusing LIVE rollback from {current_version} to stale manifest version {latest_version}"
        )
    official_snapshot, snapshot_changed = refresh_snapshot(latest_version)
    applied_hash = ((current.get("localization") or {}).get("nasOfficial") or {}).get("sourceSha256")
    force = force or snapshot_changed or applied_hash != official_snapshot["metadata"]["sourceSha256"]
    force = force or (current.get("sourcePolicy") or {}).get("schemaVersion") != 1
    try:
        validate_mission_rewards(current)
        validate_item_stats(current)
    except RuntimeError:
        print("Mission/item-stat schema is missing or outdated; rebuilding the selected LIVE snapshot.")
        force = True
    if current_version == latest_version and not force:
        removed = compact_public_index(DATA_DIR / "blueprint-index.json")
        if removed:
            print(f"SCMDB version unchanged; removed {removed} pipeline-only fields from the public index.")
        else:
            print("SCMDB version unchanged; keeping existing data cache.")
        prune_old_backups(datetime.now(timezone.utc))
        return removed > 0

    with tempfile.TemporaryDirectory(prefix="gvy-lantu-refresh-") as tmp_name:
        tmp = Path(tmp_name)
        index_path = tmp / "blueprint-index.json"
        google_cache = tmp / "google-translate-cache.json"
        flowcld = tmp / "flowcld-blueprint-calibration.json"
        local_names = tmp / "local-polish-names.json"
        official_assets = tmp / "official-localization"
        shutil.copytree(OFFICIAL_LOCALIZATION_ASSETS, official_assets)
        staged_snapshot = official_assets / "localization/starcitizen" / SNAPSHOT.name
        write_json_compact(staged_snapshot, official_snapshot)

        copy_if_exists(DATA_DIR / "google-translate-cache.json", google_cache)
        copy_if_exists(DATA_DIR / "flowcld-blueprint-calibration.json", flowcld)
        copy_if_exists(DATA_DIR / "local-polish-names.json", local_names)

        run(
            [
                sys.executable,
                "scripts/build_data.py",
                "--out",
                str(index_path),
                "--version",
                latest_version,
            ]
        )
        translate_args = [
            sys.executable,
            "scripts/translate_index_google.py",
            "--index",
            str(index_path),
            "--cache",
            str(google_cache),
        ]
        if not run(translate_args, allow_failure=True):
            print("warning: Google Translate unavailable; applying the existing fallback cache", file=sys.stderr)
            run([*translate_args, "--cache-only"])

        # The cached calibration is a language fallback only. SCMDB already
        # supplies gameplay fields; fetching a second copy cannot improve them.

        run(
            [
                sys.executable,
                "scripts/apply_local_polish.py",
                "--index",
                str(index_path),
                "--bot-assets",
                str(official_assets),
                "--local-names",
                str(local_names),
                "--flowcld-calibration",
                str(flowcld),
            ]
        )
        annotate_localization_metadata(index_path)
        compact_public_index(index_path)
        completed_at = datetime.now(timezone.utc)
        annotate_refresh_metadata(index_path, latest_version, completed_at)
        validate_index(index_path, latest_version, previous=current)

        backup_current_data(current_version or "none", datetime.now(timezone.utc))
        replace_if_exists(staged_snapshot, SNAPSHOT)
        replace_if_exists(index_path, DATA_DIR / "blueprint-index.json")
        replace_if_exists(google_cache, DATA_DIR / "google-translate-cache.json")
        replace_if_exists(flowcld, DATA_DIR / "flowcld-blueprint-calibration.json")
        replace_if_exists(local_names, DATA_DIR / "local-polish-names.json")

    print(f"updated blueprint data to {latest_version}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh GVY blueprint data from the latest stable SCMDB LIVE release.")
    parser.add_argument("--force", action="store_true", help="Rebuild the current LIVE release even when unchanged.")
    args = parser.parse_args()
    refresh(args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
