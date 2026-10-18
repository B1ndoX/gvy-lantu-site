#!/usr/bin/env python3
"""Refresh mineral distributions and signals together from the selected SCMDB LIVE."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from build_data import BASE_URL, fetch_json, load_json
from official_localization import OfficialNames, load_snapshot, validate_snapshot
from refresh_blueprint_data import BACKUP_DIR, prune_old_backups, replace_if_exists
from scmdb_mining import GROUPS, SCHEMA_VERSION, build_mining_materials, validate_mining

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/mineral-locations.json"
BLUEPRINT_INDEX = ROOT / "data/blueprint-index.json"
LOCATION_NAMES_PATH = ROOT / "data/official-localization/localization/starcitizen/bot/location-names.json"
MIN_MATERIALS, MIN_RELIABLE_MATERIALS, MIN_TOTAL_LOCATIONS, MIN_LOCATION_SIGNALS = 30, 25, 100, 100


def payload_counts(payload: dict) -> tuple[int, int, int, int]:
    materials = payload.get("materials") or {}
    entries = [entry for material in materials.values() for rows in material.get("locations", {}).values() for entry in rows]
    return (len(materials), sum(bool(m.get("hasReliableLocations")) for m in materials.values()), len(entries),
            sum(bool(e.get("signals") or e.get("signal")) for e in entries))


def build_candidate(current: dict, synced_at: datetime, mining: dict | None = None) -> dict:
    index = load_json(BLUEPRINT_INDEX)
    version = index["version"]
    url = f"{BASE_URL}/mining_data-{version}.json"
    mining = mining if mining is not None else fetch_json(url)
    validate_mining(mining, version)
    localized = load_json(LOCATION_NAMES_PATH)
    if not isinstance(localized, dict) or len(localized) < 250:
        raise RuntimeError("location localization coverage is unexpectedly low")
    names = sorted({option["name"] for record in index["records"] for tier in record.get("tiers") or []
                    for slot in tier.get("slots") or [] for option in slot.get("options") or [] if option.get("name")})
    materials = build_mining_materials(mining, names, localized)
    candidate = {"metadata": {"schemaVersion": SCHEMA_VERSION, "source": "SCMDB", "sourceUrl": url,
                              "sourceVersion": version, "signalSourceVersion": version,
                              "retrievedAt": synced_at.isoformat()}, "materials": materials}
    official = load_snapshot()
    validate_snapshot(official, version)
    OfficialNames(official).apply_minerals(candidate)
    for material in materials.values():
        for rows in material["locations"].values():
            for entry in rows:
                for signal in entry.get("signals") or []:
                    primary = materials.get(signal["primaryMaterial"], {})
                    signal["primaryMaterialZh"] = primary.get("nameZh") or signal["primaryMaterial"]
    return candidate


def validate_candidate(candidate: dict, current: dict) -> tuple[int, int, int, int]:
    counts, old = payload_counts(candidate), payload_counts(current)
    if any(value < minimum for value, minimum in zip(counts, (MIN_MATERIALS, MIN_RELIABLE_MATERIALS, MIN_TOTAL_LOCATIONS, MIN_LOCATION_SIGNALS))):
        raise RuntimeError(f"mineral source coverage is too low: {counts}")
    # Migration removes unverifiable legacy stations, not primary evidence.
    # Later refreshes must retain the verified primary-source coverage.
    compare_locations = (current.get("metadata") or {}).get("schemaVersion") == SCHEMA_VERSION
    for i, ratio in enumerate((0.8, 0.8, 0.7, 0.7)):
        if old[i] and (i < 2 or compare_locations) and counts[i] < int(old[i] * ratio):
            raise RuntimeError(f"mineral coverage dropped unexpectedly: {old} -> {counts}")
    metadata = candidate.get("metadata") or {}
    if metadata.get("schemaVersion") != SCHEMA_VERSION or metadata.get("sourceVersion") != metadata.get("signalSourceVersion"):
        raise RuntimeError("invalid mineral source schema/version")
    for name, material in candidate["materials"].items():
        if set(material.get("locations") or {}) != set(GROUPS):
            raise RuntimeError(f"invalid location groups for {name}")
        if material.get("sourceVersion") != metadata["sourceVersion"]:
            raise RuntimeError("mixed mineral source versions")
        for group, entries in material["locations"].items():
            seen = set()
            for entry in entries:
                if not entry.get("en") or not entry.get("zh") or not entry.get("id") or entry["id"] in seen:
                    raise RuntimeError(f"invalid or duplicate location: {name}/{group}")
                seen.add(entry["id"])
                for signal in entry.get("signals") or []:
                    base, counts_ = signal["base"], signal["clusterCounts"]
                    expected = [base * n for n in counts_] if signal["mode"] == "ship" else [base]
                    if signal["mode"] not in {"ship", "roc", "fps"} or not base or signal["values"] != expected:
                        raise RuntimeError("invalid normalized mining signature")
    return counts


def comparable(payload: dict) -> dict:
    result = copy.deepcopy(payload)
    result.get("metadata", {}).pop("retrievedAt", None)
    return result


def refresh(check_only: bool = False, mining_path: Path | None = None) -> bool:
    current = load_json(DATA_PATH)
    now = datetime.now(timezone.utc)
    candidate = build_candidate(current, now, load_json(mining_path) if mining_path else None)
    counts = validate_candidate(candidate, current)
    print(f"verified exact-LIVE mining: {counts[0]} materials, {counts[1]} located, {counts[2]} entries, {counts[3]} signal locations")
    if comparable(candidate) == comparable(current):
        prune_old_backups(now)
        print("mineral distributions/signals unchanged; keeping the existing cache and timestamp")
        return False
    if check_only:
        print("mineral update available; check-only mode left files unchanged")
        return True
    with tempfile.TemporaryDirectory(prefix="gvy-lantu-mining-") as tmp:
        staged = Path(tmp) / DATA_PATH.name
        staged.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        backup = BACKUP_DIR / f"{now.strftime('%Y%m%dT%H%M%S%fZ')}-mining"
        backup.mkdir(parents=True)
        shutil.copy2(DATA_PATH, backup / DATA_PATH.name)
        (backup / "backup-meta.json").write_text(json.dumps({"createdAt": now.isoformat(), "reason": "SCMDB mineral distribution and signal refresh", "retentionDays": 14}), encoding="utf-8")
        replace_if_exists(staged, DATA_PATH)
    prune_old_backups(now)
    print(f"mineral distributions and signals updated atomically; backup: {backup}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--validate-only", action="store_true", help="Validate the cached paired snapshots without network access.")
    parser.add_argument("--mining-file", type=Path, help="Previously downloaded exact-LIVE export for local validation.")
    args = parser.parse_args()
    if args.validate_only:
        current = load_json(DATA_PATH)
        validate_candidate(current, current)
        if current["metadata"]["sourceVersion"] != load_json(BLUEPRINT_INDEX)["version"]:
            raise RuntimeError("cached mining and blueprint LIVE versions do not match")
        print("cached blueprint/mining version pair and coverage are valid")
        return 0
    refresh(args.check_only, args.mining_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
