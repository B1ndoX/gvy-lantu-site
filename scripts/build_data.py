#!/usr/bin/env python3
"""Build the public blueprint search index from SCMDB data files."""

from __future__ import annotations

import argparse
import copy
import json
import math
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

from scmdb_versions import select_latest_live_version
from scmdb_item_stats import attach_item_stats
from mission_requirements import build_requirements, validate_requirements


BASE_URL = "https://scmdb.net/data"
MISSION_REWARDS_SCHEMA = 3


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch_json(url: str, attempts: int = 3) -> Any:
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(url, headers={"User-Agent": "GVY Lantu Site/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            if attempt == attempts:
                raise
            wait_seconds = attempt * 2
            print(f"SCMDB request failed; retrying in {wait_seconds}s ({attempt}/{attempts})", file=sys.stderr)
            time.sleep(wait_seconds)
    raise RuntimeError("SCMDB request retries were exhausted")


def read_source(cache_dir: Path | None, filename: str, url: str) -> Any:
    if cache_dir:
        cached = cache_dir / filename
        if cached.exists():
            return load_json(cached)
    return fetch_json(url)


def clean(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text and text.lower() != "none" else fallback


def compact_id(value: str | None) -> str:
    return clean(value, "unknown").replace(" ", "-").replace("_", "-").lower()


def category_for(blueprint: dict[str, Any], item: dict[str, Any] | None) -> dict[str, str]:
    gear = clean(blueprint.get("gear")).lower()
    bp_type = clean(blueprint.get("type")).lower()
    subtype = clean(blueprint.get("subtype")).lower()
    attach_type = clean((item or {}).get("attachType"))
    item_type = clean((item or {}).get("itemType")).lower()

    if attach_type == "WeaponPersonal" or (gear == "fpsgear" and bp_type == "weapons"):
        return {"id": "personal_weapon", "label": "单兵武器"}
    if attach_type == "WeaponGun" or bp_type == "weapons":
        return {"id": "ship_weapon", "label": "舰船武器"}
    if attach_type == "WeaponAttachment" or bp_type == "ammo":
        return {"id": "weapon_attachment", "label": "武器配件"}
    if item_type == "shipcomponent" or gear == "vehiclegear":
        return {"id": "ship_component", "label": "舰船组件"}
    if item_type == "armor" or bp_type == "armour":
        return {"id": "armor", "label": "护甲装备"}
    if attach_type in {"WeaponMining", "TractorBeam", "SalvageHead", "SalvageModifier"}:
        return {"id": "tool_module", "label": "工具模块"}
    return {"id": "other", "label": "其他蓝图"}


def normalize_modifier(modifier: dict[str, Any]) -> dict[str, Any]:
    return {
        "propertyKey": clean(modifier.get("propertyKey")),
        "propertyName": clean(modifier.get("propertyName"), "Unknown property"),
        "startQuality": modifier.get("startQuality", 0),
        "endQuality": modifier.get("endQuality", 1000),
        "modifierAtStart": modifier.get("modifierAtStart", 1),
        "modifierAtEnd": modifier.get("modifierAtEnd", 1),
        "additive": bool(modifier.get("additive")),
    }


def normalize_slot(slot: dict[str, Any]) -> dict[str, Any]:
    options = []
    for option in slot.get("options") or []:
        label = clean(option.get("resourceName")) or clean(option.get("itemName")) or clean(option.get("name"), "Unknown material")
        options.append(
            {
                "kind": clean(option.get("type"), "material"),
                "name": label,
                "quantity": option.get("quantity", 0),
                "minQuality": option.get("minQuality", 0),
            }
        )
    return {
        "name": clean(slot.get("name"), "Material slot"),
        "options": options,
        "modifiers": [normalize_modifier(modifier) for modifier in slot.get("modifiers") or []],
    }


def normalize_tiers(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    tiers = []
    for index, tier in enumerate(blueprint.get("tiers") or [], start=1):
        slots = [normalize_slot(slot) for slot in tier.get("slots") or []]
        tiers.append(
            {
                "index": index,
                "craftTimeSeconds": tier.get("craftTimeSeconds"),
                "slots": slots,
                "slotCount": len(slots),
                "materialCount": sum(len(slot["options"]) for slot in slots),
            }
        )
    return tiers


def normalize_dismantle_config(crafting: dict[str, Any]) -> dict[str, Any]:
    raw = crafting.get("dismantle") or {}
    return {
        "efficiency": raw.get("efficiency", 0),
        "timeSeconds": raw.get("dismantleTimeSeconds", 0),
        "blacklistedResources": {
            clean(resource.get("name")) for resource in raw.get("blacklistedResources") or [] if clean(resource.get("name"))
        },
        "blacklistedItems": {
            clean(item.get("name")) for item in raw.get("blacklistedEntityClasses") or [] if clean(item.get("name"))
        },
    }


def build_dismantle_outputs(tiers: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    efficiency = config.get("efficiency") or 0
    outputs: dict[tuple[str, str], dict[str, Any]] = {}
    first_tier = tiers[0] if tiers else {}
    for slot in first_tier.get("slots") or []:
        for option in slot.get("options") or []:
            name = clean(option.get("name"))
            kind = clean(option.get("kind"))
            if not name or kind not in {"resource", "item"}:
                continue
            if kind == "resource" and name in config["blacklistedResources"]:
                continue
            if kind == "item" and name in config["blacklistedItems"]:
                continue
            quantity = (option.get("quantity") or 0) * efficiency
            if quantity <= 0:
                continue
            output = outputs.setdefault((kind, name), {"name": name, "kind": kind, "quantity": 0})
            output["quantity"] += quantity
    return {
        "efficiency": efficiency,
        "timeSeconds": config.get("timeSeconds", 0),
        "outputs": sorted(outputs.values(), key=lambda output: (output["kind"], output["name"].lower())),
    }


def faction_name(factions: dict[str, Any], guid: str | None) -> str:
    if not guid:
        return ""
    faction = factions.get(guid) or {}
    return clean(faction.get("displayName")) or clean(faction.get("name"))


def mission_systems(contract: dict[str, Any]) -> list[str]:
    systems = contract.get("systems") or contract.get("availableSystems") or []
    if not isinstance(systems, list) or any(not isinstance(name, str) or not name.strip() for name in systems):
        raise RuntimeError("invalid mission star system list")
    return systems


def build_source_maps(mission_data: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    blueprint_pools = mission_data.get("blueprintPools") or {}
    factions = mission_data.get("factions") or {}
    pool_to_contracts: dict[str, list[dict[str, Any]]] = {}

    for contract in mission_data.get("contracts") or []:
        for reward in contract.get("blueprintRewards") or []:
            pool_id = reward.get("blueprintPool")
            if not pool_id:
                continue
            pool_to_contracts.setdefault(pool_id, []).append(
                {
                    "id": clean(contract.get("id")),
                    "title": clean(contract.get("title"), clean(contract.get("debugName"), "Unknown mission")),
                    "titleKey": clean(contract.get("titleLocKey")) or clean(contract.get("titleKey")).lstrip("@"),
                    "titleTokens": copy.deepcopy(contract.get("tokenSubstitutions") or {}),
                    "category": clean(contract.get("category"), "mission"),
                    "missionType": clean(contract.get("missionType")),
                    "faction": faction_name(factions, contract.get("factionGuid")),
                    "factionKey": clean((factions.get(contract.get("factionGuid")) or {}).get("nameKey")).lstrip("@")
                    or clean(contract.get("contractorNameKey")).lstrip("@"),
                    "trigger": clean(reward.get("trigger"), "complete"),
                    "chance": reward.get("chance"),
                    "rewardUEC": contract.get("rewardUEC"),
                    "systems": mission_systems(contract),
                    "debugName": clean(contract.get("debugName")),
                }
            )

    by_record: dict[str, list[dict[str, Any]]] = {}
    pool_meta: dict[str, dict[str, Any]] = {}
    for pool_id, pool in blueprint_pools.items():
        pool_name = clean(pool.get("name"), "Blueprint reward pool")
        pool_meta[pool_id] = {"id": pool_id, "name": pool_name, "source": clean(pool.get("source"))}
        missions = pool_to_contracts.get(pool_id, [])
        for reward in pool.get("blueprints") or []:
            record = reward.get("blueprintRecord")
            if not record:
                continue
            entry = {
                "poolId": pool_id,
                "poolName": pool_name,
                "poolSource": clean(pool.get("source")),
                "weight": reward.get("weight"),
                "missions": missions,
                "missionCount": len(missions),
            }
            by_record.setdefault(record, []).append(entry)
    return by_record, pool_meta


def reward_items(reward: dict[str, Any]) -> list[dict[str, Any]]:
    if reward.get("type") == "weighted_choice":
        return [item for group in reward.get("groups") or [] for item in group.get("items") or []]
    return [reward] if reward.get("name") else []


def validate_probability(value: Any) -> None:
    if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                              or not math.isfinite(value) or not 0 <= value <= 1):
        raise RuntimeError("invalid mission reward probability")


def validate_item_rewards(items: Any) -> None:
    if not isinstance(items, list):
        raise RuntimeError("invalid mission item reward list")
    for reward in items:
        if not isinstance(reward, dict) or reward.get("type") not in (None, "weighted_choice"):
            raise RuntimeError("unsupported mission item reward structure")
        if reward.get("type") == "weighted_choice":
            groups = reward.get("groups")
            if not isinstance(groups, list) or not groups:
                raise RuntimeError("invalid mission reward choice groups")
            for group in groups:
                if not isinstance(group, dict) or not isinstance(group.get("items"), list) or not group["items"]:
                    raise RuntimeError("invalid mission reward choice items")
                validate_probability(group.get("probability"))
        if not reward_items(reward):
            raise RuntimeError("mission item reward has no items")
        for item in reward_items(reward):
            amount = item.get("amount") if isinstance(item, dict) else None
            if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"].strip() or (amount is not None and (
                isinstance(amount, bool) or not isinstance(amount, (int, float))
                or not math.isfinite(amount) or amount < 0
            )):
                raise RuntimeError("invalid mission item reward name/amount")


def build_mission_rewards(mission_data: dict[str, Any]) -> dict[str, Any]:
    missions = {}
    systems = set()
    locations = {}
    for contract in mission_data.get("contracts") or []:
        rewards = contract.get("blueprintRewards") or []
        if not rewards:
            continue
        mission_id = clean(contract.get("id"))
        if not mission_id or mission_id in missions:
            raise RuntimeError("mission rewards require unique contract IDs")
        items = copy.deepcopy(contract.get("itemRewards") or [])
        validate_item_rewards(items)
        for reward in rewards:
            pool = (mission_data.get("blueprintPools") or {}).get(reward.get("blueprintPool"))
            if not pool or not pool.get("blueprints"):
                raise RuntimeError("mission reward references a missing or empty blueprint pool")
        missions[mission_id] = {
            "pools": [{"id": reward["blueprintPool"], "chance": reward.get("chance"),
                       "trigger": clean(reward.get("trigger"), "complete")}
                      for reward in rewards if reward.get("blueprintPool")],
            "items": items,
            "requirements": build_requirements(contract, mission_data, locations),
        }
        systems.update(mission_systems(contract))
    return {"schemaVersion": MISSION_REWARDS_SCHEMA, "version": mission_data.get("version"),
            "missions": missions, "locations": locations,
            "systems": [{"name": name} for name in sorted(systems)]}


def validate_mission_rewards(index: dict[str, Any]) -> None:
    rewards = index.get("missionRewards") or {}
    if rewards.get("schemaVersion") != MISSION_REWARDS_SCHEMA or rewards.get("version") != index.get("version"):
        raise RuntimeError("mission rewards schema/version does not match blueprint index")
    missions = rewards.get("missions")
    if not isinstance(missions, dict):
        raise RuntimeError("mission rewards are missing the contract map")
    locations = rewards.get("locations") or {}
    if not isinstance(locations, dict) or any(not isinstance(place, dict) or not isinstance(place.get("name"), str)
                                               for place in locations.values()):
        raise RuntimeError("invalid mission location registry")
    for mission_id, detail in missions.items():
        if not mission_id or not isinstance(detail, dict) or not isinstance(detail.get("pools"), list) or not detail["pools"]:
            raise RuntimeError("invalid mission reward contract/pools")
        for pool in detail["pools"]:
            if not isinstance(pool, dict) or not pool.get("id"):
                raise RuntimeError("invalid mission reward pool ID")
            validate_probability(pool.get("chance"))
        validate_item_rewards(detail.get("items"))
        validate_requirements(detail.get("requirements"), locations)
    for record in index.get("records") or []:
        for source in record.get("sources") or []:
            for mission in source.get("missions") or []:
                mission_systems(mission)
                if (not isinstance(mission.get("titleKey"), str) or not isinstance(mission.get("titleTokens"), dict)
                        or any(not isinstance(key, str) or not isinstance(value, str) for key, value in mission["titleTokens"].items())):
                    raise RuntimeError("mission title localization metadata is missing or invalid")
                title_zh = mission.get("titleZh") or ""
                if re.search(r"~mission\(|\bMaster Rank\b|\bLing Family Rookie\b|Lrg。采购订单", title_zh, flags=re.IGNORECASE):
                    raise RuntimeError("mission title contains an unresolved localization template or known untranslated phrase")
                detail = missions.get(mission.get("id"))
                if not detail or source.get("poolId") not in {p.get("id") for p in detail.get("pools") or []}:
                    raise RuntimeError("mission reward contract/pool reference is missing")


def dedupe_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for source in sources:
        key = (source.get("poolId"), source.get("poolName"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(source)
    return unique


def build_index(mission_data: dict[str, Any], crafting: dict[str, Any], items_data: dict[str, Any]) -> dict[str, Any]:
    version = mission_data.get("version") or crafting.get("version") or items_data.get("version")
    mission_rewards = build_mission_rewards(mission_data)
    mission_rewards["version"] = version
    items = items_data.get("items") or []
    item_by_entity = {item.get("entityClass"): item for item in items if item.get("entityClass")}
    sources_by_record, pool_meta = build_source_maps(mission_data)
    dismantle_config = normalize_dismantle_config(crafting)

    records = []
    category_counts: dict[str, int] = {}
    manufacturer_counts: dict[str, int] = {}
    material_counts: dict[str, int] = {}

    for blueprint in crafting.get("blueprints") or []:
        product_name = clean(blueprint.get("productName"), clean(blueprint.get("suggestedName"), "Unnamed blueprint"))
        item = item_by_entity.get(blueprint.get("productEntityClass"))
        category = category_for(blueprint, item)
        tiers = normalize_tiers(blueprint)
        dismantle = build_dismantle_outputs(tiers, dismantle_config)
        first_tier = tiers[0] if tiers else {"slots": []}
        materials = []
        for slot in first_tier.get("slots") or []:
            for option in slot.get("options") or []:
                materials.append(option)
                material_counts[option["name"]] = material_counts.get(option["name"], 0) + 1

        manufacturer = clean(blueprint.get("manufacturer")) or clean((item or {}).get("manufacturer"), "Unknown")
        category_counts[category["id"]] = category_counts.get(category["id"], 0) + 1
        manufacturer_counts[manufacturer] = manufacturer_counts.get(manufacturer, 0) + 1

        sources = dedupe_sources(sources_by_record.get(blueprint.get("guid"), []))
        stats = {
            "itemType": clean((item or {}).get("itemType"), clean(blueprint.get("gear"))),
            "attachType": clean((item or {}).get("attachType")),
            "attachSubType": clean((item or {}).get("attachSubType"), clean(blueprint.get("subtype"))),
            "size": (item or {}).get("size"),
            "grade": (item or {}).get("grade"),
            "mass": (item or {}).get("mass"),
            "combatRange": (item or {}).get("combatRange"),
            "manufacturerCode": clean((item or {}).get("manufacturerCode")),
            "tags": clean((item or {}).get("tags")),
            "componentClass": (item or {}).get("componentClass"),
        }

        search_blob = " ".join(
            [
                product_name,
                manufacturer,
                category["label"],
                clean(blueprint.get("type")),
                clean(blueprint.get("subtype")),
                stats["attachType"],
                " ".join(material["name"] for material in materials),
                " ".join(source.get("poolName", "") for source in sources),
                " ".join(mission.get("title", "") for source in sources for mission in source.get("missions", [])),
            ]
        ).lower()

        records.append(
            {
                "id": blueprint.get("guid"),
                "tag": blueprint.get("tag"),
                "productEntityClass": blueprint.get("productEntityClass"),
                "name": product_name,
                "manufacturer": manufacturer,
                "category": category,
                "type": clean(blueprint.get("type"), "unknown"),
                "subtype": clean(blueprint.get("subtype"), "unknown"),
                "gear": clean(blueprint.get("gear"), "unknown"),
                "stats": stats,
                "tiers": tiers,
                "dismantle": dismantle,
                "materials": materials,
                "sources": sources,
                "sourceCount": sum(source.get("missionCount", 0) for source in sources),
                "hasKnownIssue": bool(blueprint.get("cigDataError") or blueprint.get("knownIssue")),
                "search": search_blob,
            }
        )

    records.sort(key=lambda record: (record["category"]["id"], record["name"].lower()))
    index = {
        "generatedFrom": "SCMDB public data",
        "sourcePolicy": {"schemaVersion": 1, "gameplay": "scmdb", "fallback": "verified-gaps-only"},
        "version": version,
        "missionRewards": mission_rewards,
        "counts": {
            "blueprints": len(records),
            "categories": category_counts,
            "manufacturers": manufacturer_counts,
            "materials": material_counts,
            "rewardPools": len(pool_meta),
        },
        "dismantle": {
            "efficiency": dismantle_config["efficiency"],
            "timeSeconds": dismantle_config["timeSeconds"],
        },
        "records": records,
    }
    if items_data.get("version"):
        attach_item_stats(index, items_data)
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description="Build blueprint-site/data/blueprint-index.json")
    parser.add_argument("--cache-dir", type=Path, help="Directory containing cached SCMDB JSON files")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "blueprint-index.json")
    parser.add_argument("--version", help="Exact SCMDB LIVE version selected by the refresh pipeline")
    args = parser.parse_args()

    versions = read_source(args.cache_dir, "versions.json", f"{BASE_URL}/versions.json")
    if not versions:
        print("No SCMDB versions found", file=sys.stderr)
        return 1
    if args.version:
        selected = next((entry for entry in versions if entry.get("version") == args.version), None)
        if selected is None:
            print(f"Requested SCMDB version was not found: {args.version}", file=sys.stderr)
            return 1
        try:
            selected = select_latest_live_version([selected])
        except RuntimeError as error:
            print(f"Refusing requested SCMDB version: {error}", file=sys.stderr)
            return 1
    else:
        selected = select_latest_live_version(versions)

    version = selected["version"]
    merged_file = selected["file"]

    mission_data = read_source(args.cache_dir, merged_file, f"{BASE_URL}/{merged_file}")
    crafting = read_source(args.cache_dir, f"crafting_blueprints-{version}.json", f"{BASE_URL}/crafting_blueprints-{version}.json")
    items = read_source(args.cache_dir, f"crafting_items-{version}.json", f"{BASE_URL}/crafting_items-{version}.json")
    if any(str(payload.get("version") or "").lower() != version.lower() for payload in (mission_data, crafting, items)):
        raise RuntimeError("SCMDB source versions do not match the selected LIVE")
    index = build_index(mission_data, crafting, items)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        json.dump(index, handle, ensure_ascii=False, separators=(",", ":"))
    print(f"Wrote {args.out} with {len(index['records'])} blueprints from {index['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
