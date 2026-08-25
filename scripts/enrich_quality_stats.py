#!/usr/bin/env python3
"""Attach compact, version-matched base stats used by the quality preview."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


ITEMS_URL = "https://raw.githubusercontent.com/StarCitizenWiki/scunpacked-data/{commit}/items.json"
COMMIT_URL = "https://api.github.com/repos/StarCitizenWiki/scunpacked-data/commits/master"
VERSION_PATTERN = re.compile(r"\b\d+\.\d+\.\d+-LIVE\.\d+\b", re.IGNORECASE)
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json_compact(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")


def fetch_json(url: str, attempts: int = 3) -> Any:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "GVY Lantu Site/1.0"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(attempt * 2)
    raise RuntimeError("community item data request retries were exhausted")


def normalize_version(value: str) -> str:
    return value.strip().lower()


def source_version_from_commit(payload: dict[str, Any]) -> str:
    message = str(((payload.get("commit") or {}).get("message")) or "")
    match = VERSION_PATTERN.search(message)
    if not match:
        raise RuntimeError("community item data commit does not declare a LIVE version")
    return match.group(0)


def source_sha_from_commit(payload: dict[str, Any]) -> str:
    commit = str(payload.get("sha") or "")
    if not COMMIT_PATTERN.fullmatch(commit):
        raise RuntimeError("community item data response has no immutable commit SHA")
    return commit


def number_at(payload: dict[str, Any], *path: str) -> float | None:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return None
    return float(value)


def add_metric(
    metrics: list[dict[str, Any]],
    metric_id: str,
    label: str,
    value: float | None,
    properties: list[str],
    unit: str = "",
    digits: int = 2,
) -> None:
    if value is None:
        return
    metrics.append(
        {
            "id": metric_id,
            "label": label,
            "value": value,
            "unit": unit,
            "digits": digits,
            "properties": properties,
        }
    )


def modifier_keys(record: dict[str, Any]) -> set[str]:
    tiers = record.get("tiers") or []
    slots = (tiers[0].get("slots") or []) if tiers else []
    return {
        str(modifier.get("propertyKey"))
        for slot in slots
        for modifier in slot.get("modifiers") or []
        if modifier.get("propertyKey")
    }


def extract_quality_metrics(item: dict[str, Any], keys: set[str]) -> list[dict[str, Any]]:
    std = item.get("stdItem") or {}
    metrics: list[dict[str, Any]] = []

    if "health_maxhealth" in keys:
        add_metric(metrics, "integrity", "结构完整度", number_at(std, "Durability", "Health"), ["health_maxhealth"], digits=0)

    if "weapon_damage" in keys:
        if item.get("type") == "WeaponMining":
            add_metric(metrics, "mining_power", "采矿功率", number_at(std, "MiningLaser", "PowerTransfer"), ["weapon_damage"], digits=0)
        else:
            add_metric(metrics, "alpha_damage", "单发伤害", number_at(std, "Weapon", "Damage", "AlphaTotal"), ["weapon_damage"])
            dps_properties = [key for key in ("weapon_damage", "weapon_firerate") if key in keys]
            add_metric(metrics, "burst_dps", "爆发 DPS", number_at(std, "Weapon", "Damage", "Burst"), dps_properties)

    if "weapon_firerate" in keys:
        add_metric(metrics, "fire_rate", "射速", number_at(std, "Weapon", "RateOfFire"), ["weapon_firerate"], "RPM", 0)

    if "shield_maxhealth" in keys:
        add_metric(metrics, "shield_capacity", "护盾容量", number_at(std, "Shield", "MaxShieldHealth"), ["shield_maxhealth"], digits=0)

    if "itemresource_coolantgeneration" in keys:
        add_metric(
            metrics,
            "coolant_generation",
            "冷却生成",
            number_at(std, "ResourceNetwork", "Generation", "Coolant"),
            ["itemresource_coolantgeneration"],
            digits=0,
        )

    if "itemresource_powergeneration" in keys:
        add_metric(
            metrics,
            "power_generation",
            "电力格",
            number_at(std, "ResourceNetwork", "Generation", "Power"),
            ["itemresource_powergeneration"],
            digits=0,
        )

    if "quantum_speed" in keys:
        speed = number_at(std, "QuantumDrive", "StandardJump", "DriveSpeed")
        add_metric(metrics, "quantum_speed", "量子速度", speed / 1000 if speed is not None else None, ["quantum_speed"], "km/s", 0)

    if "quantum_fuelrequirement" in keys:
        add_metric(
            metrics,
            "quantum_fuel",
            "10 GM 耗油",
            number_at(std, "QuantumDrive", "FuelRequirement10GM"),
            ["quantum_fuelrequirement"],
            "SCU",
            3,
        )

    if "radar_minaimassistdistance" in keys:
        add_metric(
            metrics,
            "radar_aim_min",
            "辅助瞄准起始",
            number_at(std, "Radar", "AimAssist", "DistanceMinAssignment"),
            ["radar_minaimassistdistance"],
            "m",
            0,
        )

    if "radar_maxaimassistdistance" in keys:
        add_metric(
            metrics,
            "radar_aim_max",
            "辅助瞄准上限",
            number_at(std, "Radar", "AimAssist", "DistanceMaxAssignment"),
            ["radar_maxaimassistdistance"],
            "m",
            0,
        )

    if "armor_temperaturemin" in keys:
        add_metric(metrics, "temperature_min", "最低耐温", number_at(std, "TemperatureResistance", "Minimum"), ["armor_temperaturemin"], "°C", 0)
    if "armor_temperaturemax" in keys:
        add_metric(metrics, "temperature_max", "最高耐温", number_at(std, "TemperatureResistance", "Maximum"), ["armor_temperaturemax"], "°C", 0)
    if "armor_radiationdissipation" in keys:
        add_metric(
            metrics,
            "radiation_dissipation",
            "辐射消散",
            number_at(std, "RadiationResistance", "RadiationDissipationRate"),
            ["armor_radiationdissipation"],
        )

    salvage = std.get("SalvageModifier") or {}
    if "weapon_hullscraping_efficiency" in keys:
        efficiency = number_at(salvage, "ExtractionEfficiency")
        add_metric(
            metrics,
            "scraping_efficiency",
            "回收效率",
            efficiency * 100 if efficiency is not None else None,
            ["weapon_hullscraping_efficiency"],
            "%",
        )
    if "weapon_hullscraping_radius" in keys:
        add_metric(metrics, "scraping_radius", "刮削范围", number_at(salvage, "RadiusMultiplier"), ["weapon_hullscraping_radius"], "×")
    if "weapon_hullscraping_speed" in keys:
        add_metric(metrics, "scraping_speed", "刮削速度", number_at(salvage, "SalvageSpeedMultiplier"), ["weapon_hullscraping_speed"], "×")

    tractor = std.get("TractorBeam") or {}
    if "weapon_tractor_force" in keys:
        add_metric(metrics, "tractor_force", "牵引力", number_at(tractor, "MaxForce"), ["weapon_tractor_force"], "N", 0)
    if "weapon_tractor_fullstrengthdist" in keys:
        add_metric(
            metrics,
            "tractor_full_strength",
            "全功率距离",
            number_at(tractor, "FullStrengthDistance"),
            ["weapon_tractor_fullstrengthdist"],
            "m",
        )
    if "weapon_tractor_maxdist" in keys:
        add_metric(metrics, "tractor_max_distance", "最大距离", number_at(tractor, "MaxDistance"), ["weapon_tractor_maxdist"], "m")

    return metrics


def enrich_index(index: dict[str, Any], items: list[dict[str, Any]], source_version: str) -> dict[str, int]:
    index_version = str(index.get("version") or "")
    if normalize_version(index_version) != normalize_version(source_version):
        raise RuntimeError(f"quality data version mismatch: index={index_version}, community={source_version}")

    by_name = {str(item.get("name")): item for item in items if item.get("name")}
    records_with_modifiers = 0
    matched_items = 0
    records_with_base_stats = 0

    for record in index.get("records") or []:
        record.pop("qualityStats", None)
        keys = modifier_keys(record)
        if not keys:
            continue
        records_with_modifiers += 1
        item = by_name.get(str(record.get("name") or ""))
        if not item:
            continue
        matched_items += 1
        metrics = extract_quality_metrics(item, keys)
        if metrics:
            record["qualityStats"] = metrics
            records_with_base_stats += 1

    coverage = {
        "recordsWithModifiers": records_with_modifiers,
        "matchedItems": matched_items,
        "recordsWithBaseStats": records_with_base_stats,
    }
    index["qualityEffects"] = {"version": source_version, **coverage}
    return coverage


def validate_coverage(index: dict[str, Any], coverage: dict[str, int]) -> None:
    record_count = len(index.get("records") or [])
    modifier_count = coverage["recordsWithModifiers"]
    matched_count = coverage["matchedItems"]
    base_count = coverage["recordsWithBaseStats"]
    if not record_count or modifier_count < int(record_count * 0.7):
        raise RuntimeError(
            f"quality modifier coverage is unexpectedly low: {modifier_count}/{record_count}"
        )
    if matched_count < int(modifier_count * 0.8):
        raise RuntimeError(
            f"quality item matching coverage is unexpectedly low: {matched_count}/{modifier_count}"
        )
    if base_count < int(modifier_count * 0.75):
        raise RuntimeError(
            f"quality base-stat coverage is unexpectedly low: {base_count}/{modifier_count}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Add compact quality base stats to a GVY blueprint index.")
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--items-file", type=Path)
    parser.add_argument("--source-version")
    args = parser.parse_args()

    index = load_json(args.index)
    if args.items_file:
        items = load_json(args.items_file)
        source_version = args.source_version
        if not source_version:
            raise RuntimeError("--source-version is required with --items-file")
    else:
        commit_payload = fetch_json(COMMIT_URL)
        source_version = source_version_from_commit(commit_payload)
        source_sha = source_sha_from_commit(commit_payload)
        items = fetch_json(ITEMS_URL.format(commit=source_sha))

    if not isinstance(items, list):
        raise RuntimeError("community item data is not an item list")
    coverage = enrich_index(index, items, source_version)
    validate_coverage(index, coverage)
    write_json_compact(args.index, index)
    print(
        "quality stats enriched: "
        f"{coverage['recordsWithBaseStats']} base panels / "
        f"{coverage['recordsWithModifiers']} modifier records"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"quality stats enrichment failed: {error}", file=sys.stderr)
        raise
