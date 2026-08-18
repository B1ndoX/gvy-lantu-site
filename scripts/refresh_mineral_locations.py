#!/usr/bin/env python3
"""Refresh UEX mineral locations without risking the verified local cache."""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from refresh_blueprint_data import update_data_version


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "mineral-locations.json"
BLUEPRINT_INDEX = ROOT / "data" / "blueprint-index.json"
LOCATION_NAMES_PATH = (
    ROOT
    / "data"
    / "official-localization"
    / "localization"
    / "starcitizen"
    / "bot"
    / "location-names.json"
)
BACKUP_DIR = ROOT / ".data-backups"
API_BASE = "https://api.uexcorp.uk/2.0"
SIGNAL_LOCATION_URL = "https://sg-mining-finder.pages.dev/"
BACKUP_RETENTION_DAYS = 14
MIN_MATERIALS = 30
MIN_RELIABLE_MATERIALS = 25
MIN_TOTAL_LOCATIONS = 100
MIN_LOCATION_SIGNALS = 100

RESOURCE_PATHS = {
    "commodities": "commodities",
    "starSystems": "star_systems",
    "planets": "planets",
    "moons": "moons",
    "pointsOfInterest": "poi",
    "orbits": "orbits",
    "spaceStations": "space_stations",
}

MATERIAL_ALIASES = {"Pressurized Ice": "Ice"}
SIGNAL_NAME_ALIASES = {
    "Aluminium": "Aluminum",
    "Quantanium": "Quantainium",
}

# The official localization package has priority. These are only missing location
# labels required by the mining data sources.
LOCATION_FALLBACK_ZH = {
    "Nyx": "尼克斯",
    "Pyro": "派罗",
    "MicroTech": "微科星",
    "Pyro I": "派罗 I",
    "Monox": "莫诺克斯",
    "Bloom": "盛放星",
    "Pyro IV": "派罗 IV",
    "Pyro V": "派罗 V",
    "Terminus": "终点星",
    "Delamar": "戴拉玛",
    "Aaron Halo": "亚伦环",
    "Keeger Belt": "基格带",
    "Glaciem Ring": "冰川环",
    "Pyro Asteroid Clusters": "派罗小行星群",
    "Pyro Clusters": "派罗小行星群",
    "OV Breaker Stations": "OV 破碎站",
    "Yela Ring": "耶拉环带",
}

LAGRANGE_PREFIXES = {
    "ArcCorp": "ARC",
    "Crusader": "CRU",
    "Hurston": "HUR",
    "microTech": "MIC",
}

STATION_FALLBACK_ZH = {
    "ARC-L1 Wide Forest Station": "弧L1 广袤森林站",
    "CRU-L1 Ambitious Dream Station": "十L1 雄心伟梦站",
    "CRU-L4 Shallow Fields Station": "十L4 轻浅田野站",
    "HUR-L1 Green Glade Station": "赫L1 绿色林地",
    "HUR-L2 Faithful Dream Station": "赫L2 坚贞梦想站",
    "HUR-L4 Melodic Fields Station": "赫L4 旋律领域站",
    "MIC-L2 Long Forest Station": "微L2 长林站",
    "MIC-L5 Modern Icarus Station": "微L5 现代伊卡洛斯站",
}


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def fetch_json(resource: str, attempts: int = 3) -> list[dict[str, Any]]:
    url = f"{API_BASE}/{resource}/"
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(url, headers={"User-Agent": "GVY Lantu Site/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if payload.get("status") != "ok" or not isinstance(payload.get("data"), list):
                raise RuntimeError(f"UEX returned an invalid response for {resource}")
            return payload["data"]
        except Exception:
            if attempt == attempts:
                raise
            wait_seconds = attempt * 2
            print(f"UEX {resource} failed; retrying in {wait_seconds}s ({attempt}/{attempts})")
            time.sleep(wait_seconds)
    raise RuntimeError(f"UEX retries were exhausted for {resource}")


def fetch_text(url: str, attempts: int = 3) -> str:
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(url, headers={"User-Agent": "GVY Lantu Site/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read().decode("utf-8", "ignore")
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(attempt * 2)
    raise RuntimeError("text source retries were exhausted")


def parse_ids(value: object) -> list[int]:
    if value in (None, ""):
        return []
    return [int(part) for part in str(value).split(",") if part.strip()]


def official_location_names() -> dict[str, str]:
    payload = load_json(LOCATION_NAMES_PATH, {})
    if not isinstance(payload, dict) or len(payload) < 250:
        raise RuntimeError("official location localization coverage is unexpectedly low")
    return {str(key): str(value) for key, value in payload.items() if key and value}


def zh_name(name: str | None, localized: dict[str, str]) -> str:
    if not name:
        return "未知"
    return localized.get(name) or LOCATION_FALLBACK_ZH.get(name) or name


def lagrange_label(
    name: str,
    code: str | None,
    localized: dict[str, str],
    station: dict[str, Any] | None = None,
) -> tuple[str, str]:
    if station:
        station_name = str(station.get("name") or name)
        return (
            localized.get(station_name)
            or STATION_FALLBACK_ZH.get(station_name)
            or station.get("nickname")
            or zh_name(station_name, localized),
            station_name,
        )
    for prefix, short in LAGRANGE_PREFIXES.items():
        marker = f"{prefix} Lagrange Point "
        if name.startswith(marker):
            return f"{short}-L{name.removeprefix(marker)}", name
    return (code or zh_name(name, localized), name)


def location_entry(
    item: dict[str, Any],
    kind: str,
    localized: dict[str, str],
    station_by_orbit: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    name = str(item.get("nickname") or item.get("name") or "Unknown")
    if kind == "lagrangePoints":
        zh, en = lagrange_label(name, item.get("code"), localized, station_by_orbit.get(item.get("id")))
    else:
        en = name
        zh = zh_name(name, localized)
    return {
        "id": item.get("id"),
        "zh": zh,
        "en": en,
        "systemZh": zh_name(item.get("star_system_name"), localized),
        "systemEn": item.get("star_system_name") or "",
        "parentZh": zh_name(item.get("planet_name") or item.get("orbit_name"), localized),
        "parentEn": item.get("planet_name") or item.get("orbit_name") or "",
    }


def first_with_locations(candidates: list[dict[str, Any] | None]) -> dict[str, Any] | None:
    location_fields = ("ids_star_systems", "ids_planets", "ids_moons", "ids_poi", "ids_orbits")
    for candidate in candidates:
        if candidate and any(candidate.get(field) for field in location_fields):
            return candidate
    return next((candidate for candidate in candidates if candidate), None)


def raw_commodity_for(
    name: str,
    by_name: dict[str, dict[str, Any]],
    by_id: dict[int, dict[str, Any]],
) -> dict[str, Any] | None:
    base = MATERIAL_ALIASES.get(name, name)
    current = by_name.get(base) or by_name.get(name)
    candidates: list[dict[str, Any] | None] = []
    if current:
        if current.get("is_raw"):
            candidates.append(current)
        candidates.append(by_id.get(current.get("id_parent")))
    for suffix in (" (Raw)", " (Ore)", " (Pure)"):
        candidates.append(by_name.get(base + suffix))
    return first_with_locations(candidates) or current


def js_object_source(html: str, const_name: str) -> str:
    marker = f"const {const_name} = "
    start = html.index(marker) + len(marker)
    while start < len(html) and html[start].isspace():
        start += 1
    opening = html[start]
    closing = "}" if opening == "{" else "]"
    depth = 0
    in_string: str | None = None
    escaped = False
    for index in range(start, len(html)):
        char = html[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = None
            continue
        if char in ("'", '"'):
            in_string = char
            continue
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return html[start : index + 1]
    raise RuntimeError(f"unable to parse {const_name}")


def load_signal_location_data() -> dict[str, Any]:
    html = fetch_text(SIGNAL_LOCATION_URL)
    location_names = json.loads(js_object_source(html, "LOCATION_NAMES"))
    ship_source = re.sub(r"//.*", "", js_object_source(html, "SHIP_DATA_47"))
    ship_data = json.loads(ship_source)
    radar_source = js_object_source(html, "RADAR_DATA")
    radar: dict[str, dict[str, Any]] = {}
    for match in re.finditer(r"name:\s*'([^']+)'\s*,\s*rs:\s*(\d+).*?maxCluster:\s*(\d+)", radar_source, re.S):
        source_name, base, max_cluster = match.groups()
        name = SIGNAL_NAME_ALIASES.get(source_name, source_name)
        signal_key = "ICE" if source_name == "Ice" else re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").upper()
        radar[signal_key] = {
            "base": int(base),
            "maxCluster": int(max_cluster),
            "values": [int(base) * count for count in range(1, int(max_cluster) + 1)],
        }
    if len(location_names) < 100 or len(ship_data) < 30 or len(radar) < 20:
        raise RuntimeError("mineral signal location source coverage is unexpectedly low")
    locations_by_name = {value: re.sub(r"-\d+$", "", key) for key, value in location_names.items()}
    locations_by_name.update(
        {
            "Yela Ring": "YELB",
            "Yela Belt": "YELB",
            "Glaciem Ring": "GLACIUM",
            "Pyro Clusters": "PYRO_DEEP",
        }
    )
    return {"locationsByName": locations_by_name, "shipData": ship_data, "radar": radar}


def ore_key(material_name: str, commodity_name: str | None) -> str:
    base = MATERIAL_ALIASES.get(material_name, material_name)
    if base == "Ice" or commodity_name == "Ice (Raw)":
        return "ICE"
    if base in {"Quantainium", "Quantanium"}:
        return "QUANTAINIUM"
    return re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_").upper()


def signal_location_code(location: dict[str, Any], signal_data: dict[str, Any]) -> str | None:
    en = str(location.get("en") or "")
    zh = str(location.get("zh") or "")
    if en in signal_data["locationsByName"]:
        return signal_data["locationsByName"][en]
    if zh in signal_data["shipData"]:
        return zh
    match = re.match(r"([A-Z]{3}-L\d)\b", en) or re.match(r"([A-Z]{3}-L\d)\b", zh)
    if match and match.group(1) in signal_data["shipData"]:
        return match.group(1)
    return None


def signal_for_location(
    location: dict[str, Any],
    material_key: str,
    signal_data: dict[str, Any],
) -> dict[str, Any] | None:
    code = signal_location_code(location, signal_data)
    if not code:
        return None
    row = next((item for item in signal_data["shipData"].get(code, []) if item[0] == material_key), None)
    radar = signal_data["radar"].get(material_key)
    if not row or not radar:
        return None
    return {**radar, "probability": row[1], "sourceLocation": code}


def existing_signal_map(payload: dict[str, Any]) -> dict[tuple[str, str, object], dict[str, Any]]:
    result: dict[tuple[str, str, object], dict[str, Any]] = {}
    for material_name, material in (payload.get("materials") or {}).items():
        for group_name, locations in (material.get("locations") or {}).items():
            for location in locations or []:
                signal = location.get("signal")
                if not signal:
                    continue
                key_value: object = location.get("id")
                if key_value is None:
                    key_value = (location.get("en"), location.get("systemEn"), location.get("parentEn"))
                result[(material_name, group_name, key_value)] = copy.deepcopy(signal)
    return result


def material_names_from_blueprints() -> list[str]:
    index = load_json(BLUEPRINT_INDEX, {})
    names = {
        option["name"]
        for record in index.get("records") or []
        for tier in record.get("tiers") or []
        for slot in tier.get("slots") or []
        for option in slot.get("options") or []
        if option.get("name")
    }
    if len(names) < MIN_MATERIALS:
        raise RuntimeError("blueprint material coverage is unexpectedly low")
    return sorted(names)


def build_candidate(current: dict[str, Any], synced_at: datetime) -> dict[str, Any]:
    resources = {key: fetch_json(path) for key, path in RESOURCE_PATHS.items()}
    if len(resources["commodities"]) < 150 or len(resources["orbits"]) < 200:
        raise RuntimeError("UEX resource coverage is unexpectedly low")
    lookup = {
        key: {item["id"]: item for item in rows}
        for key, rows in resources.items()
        if key not in {"commodities", "spaceStations"}
    }
    station_by_orbit = {
        item["id_orbit"]: item for item in resources["spaceStations"] if item.get("id_orbit")
    }
    localized = official_location_names()
    commodities = resources["commodities"]
    by_name = {item["name"]: item for item in commodities}
    by_id = {item["id"]: item for item in commodities}
    preserved_signals = existing_signal_map(current)

    try:
        signal_data = load_signal_location_data()
    except Exception as error:
        print(f"warning: signal location source unavailable; preserving matched cached signals ({error})")
        signal_data = None

    materials: dict[str, Any] = {}
    for name in material_names_from_blueprints():
        commodity = raw_commodity_for(name, by_name, by_id)
        groups: dict[str, list[dict[str, Any]]] = {
            "starSystems": [
                location_entry(lookup["starSystems"][item_id], "starSystems", localized, station_by_orbit)
                for item_id in parse_ids(commodity.get("ids_star_systems") if commodity else None)
                if item_id in lookup["starSystems"]
            ],
            "planets": [
                location_entry(lookup["planets"][item_id], "planets", localized, station_by_orbit)
                for item_id in parse_ids(commodity.get("ids_planets") if commodity else None)
                if item_id in lookup["planets"]
            ],
            "moons": [
                location_entry(lookup["moons"][item_id], "moons", localized, station_by_orbit)
                for item_id in parse_ids(commodity.get("ids_moons") if commodity else None)
                if item_id in lookup["moons"]
            ],
            "pointsOfInterest": [
                location_entry(lookup["pointsOfInterest"][item_id], "pointsOfInterest", localized, station_by_orbit)
                for item_id in parse_ids(commodity.get("ids_poi") if commodity else None)
                if item_id in lookup["pointsOfInterest"]
            ],
            "lagrangePoints": [
                location_entry(lookup["orbits"][item_id], "lagrangePoints", localized, station_by_orbit)
                for item_id in parse_ids(commodity.get("ids_orbits") if commodity else None)
                if item_id in lookup["orbits"]
            ],
        }
        material_key = ore_key(name, commodity.get("name") if commodity else None)
        for group_name, locations in groups.items():
            for location in locations:
                signal = signal_for_location(location, material_key, signal_data) if signal_data else None
                if not signal:
                    key_value: object = location.get("id")
                    if key_value is None:
                        key_value = (location.get("en"), location.get("systemEn"), location.get("parentEn"))
                    signal = preserved_signals.get((name, group_name, key_value))
                if signal:
                    location["signal"] = signal

        previous_material = (current.get("materials") or {}).get(name) or {}
        materials[name] = {
            "commodityId": commodity.get("id") if commodity else None,
            "commodityName": commodity.get("name") if commodity else None,
            "commodityCode": commodity.get("code") if commodity else None,
            "sourceUrl": (
                "https://uexcorp.space/mining/locations/commodity/"
                + re.sub(r"[^a-z0-9-]+", "", re.sub(r"\s+", "-", str(commodity.get("name") or name).lower()))
                + "/"
                if commodity
                else ""
            ),
            "locations": groups,
            "signal": copy.deepcopy(previous_material.get("signal") or {}),
            "hasReliableLocations": any(groups.values()),
        }

    previous_metadata = current.get("metadata") or {}
    metadata = {
        "name": "Star Citizen mineral locations",
        "source": "UEX API 2.0",
        "sourceUrl": f"{API_BASE}/",
        "signalSource": previous_metadata.get("signalSource") or "Shadow Guardians Mining Resource Finder",
        "locationSignalSource": SIGNAL_LOCATION_URL,
        "signalUpdatedAt": previous_metadata.get("signalUpdatedAt") or "",
        "signalSourceVersion": previous_metadata.get("signalSourceVersion") or "",
        "signalSyncedAt": previous_metadata.get("signalSyncedAt") or "",
        "retrievedAt": synced_at.isoformat(),
        "note": (
            "UEX data is community-maintained and may not reflect live servers. "
            "Empty entries are shown as no reliable mining location instead of inferred locations."
        ),
    }
    return {"metadata": metadata, "materials": materials}


def payload_counts(payload: dict[str, Any]) -> tuple[int, int, int, int]:
    materials = payload.get("materials") or {}
    reliable = sum(bool(item.get("hasReliableLocations")) for item in materials.values())
    locations = sum(
        len(group)
        for item in materials.values()
        for group in (item.get("locations") or {}).values()
    )
    signals = sum(
        1
        for item in materials.values()
        for group in (item.get("locations") or {}).values()
        for location in group
        if location.get("signal")
    )
    return len(materials), reliable, locations, signals


def validate_candidate(candidate: dict[str, Any], current: dict[str, Any]) -> tuple[int, int, int, int]:
    counts = payload_counts(candidate)
    old_counts = payload_counts(current)
    materials, reliable, locations, signals = counts
    if materials < MIN_MATERIALS or reliable < MIN_RELIABLE_MATERIALS or locations < MIN_TOTAL_LOCATIONS:
        raise RuntimeError(
            f"mineral location coverage is too low: {materials} materials, {reliable} reliable, {locations} locations"
        )
    if old_counts[0] and materials < int(old_counts[0] * 0.8):
        raise RuntimeError(f"mineral material coverage dropped unexpectedly: {old_counts[0]} -> {materials}")
    if old_counts[1] and reliable < int(old_counts[1] * 0.8):
        raise RuntimeError(f"reliable mineral coverage dropped unexpectedly: {old_counts[1]} -> {reliable}")
    if old_counts[2] and locations < int(old_counts[2] * 0.7):
        raise RuntimeError(f"mineral location coverage dropped unexpectedly: {old_counts[2]} -> {locations}")
    if old_counts[3] >= MIN_LOCATION_SIGNALS and signals < max(MIN_LOCATION_SIGNALS, int(old_counts[3] * 0.7)):
        raise RuntimeError(f"mineral signal location coverage dropped unexpectedly: {old_counts[3]} -> {signals}")

    expected_groups = {"starSystems", "planets", "moons", "pointsOfInterest", "lagrangePoints"}
    for material_name, item in (candidate.get("materials") or {}).items():
        groups = item.get("locations") or {}
        if set(groups) != expected_groups:
            raise RuntimeError(f"invalid location groups for {material_name}")
        for group_name, entries in groups.items():
            keys: set[tuple[object, ...]] = set()
            for entry in entries:
                if not entry.get("en") or not entry.get("zh"):
                    raise RuntimeError(f"location is missing a name: {material_name}/{group_name}")
                key = (entry.get("id"), entry.get("en"), entry.get("systemEn"), entry.get("parentEn"))
                if key in keys:
                    raise RuntimeError(f"duplicate location: {material_name}/{group_name}/{entry.get('en')}")
                keys.add(key)
    return counts


def comparable(payload: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(payload)
    (value.get("metadata") or {}).pop("retrievedAt", None)
    return value


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
    target = BACKUP_DIR / f"{now.strftime('%Y%m%dT%H%M%SZ')}-mineral-locations"
    target.mkdir(parents=True, exist_ok=False)
    shutil.copy2(DATA_PATH, target / DATA_PATH.name)
    (target / "backup-meta.json").write_text(
        json.dumps(
            {
                "createdAt": now.isoformat(),
                "reason": "UEX mineral location refresh",
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
    temporary = path.with_name(f".{path.name}.location-refresh-tmp")
    temporary.unlink(missing_ok=True)
    try:
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def refresh(check_only: bool = False) -> bool:
    current = load_json(DATA_PATH, {})
    if not current:
        raise RuntimeError("the verified mineral location cache is missing")
    synced_at = datetime.now(timezone.utc)
    candidate = build_candidate(current, synced_at)
    counts = validate_candidate(candidate, current)
    print(
        "verified UEX mineral locations: "
        f"{counts[0]} materials, {counts[1]} reliable, {counts[2]} locations, {counts[3]} location signals"
    )
    if comparable(candidate) == comparable(current):
        prune_old_backups(synced_at)
        print("mineral locations unchanged; keeping existing cache")
        return False
    if check_only:
        print("mineral location update available; check-only mode left files unchanged")
        return True

    backup = backup_current_data(synced_at)
    write_json_atomic(DATA_PATH, candidate)
    blueprint_version = str(load_json(BLUEPRINT_INDEX, {}).get("version") or "mineral-locations")
    update_data_version(blueprint_version, synced_at)
    print(f"mineral locations updated; backup saved: {backup}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh verified Star Citizen mineral locations from UEX.")
    parser.add_argument("--check-only", action="store_true", help="Report changes without writing files.")
    args = parser.parse_args()
    refresh(check_only=args.check_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
