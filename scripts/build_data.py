#!/usr/bin/env python3
"""Build the public blueprint search index from SCMDB data files."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any


BASE_URL = "https://scmdb.net/data"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "SC Blueprint Atlas/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


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
    return {"name": clean(slot.get("name"), "Material slot"), "options": options}


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


def faction_name(factions: dict[str, Any], guid: str | None) -> str:
    if not guid:
        return ""
    faction = factions.get(guid) or {}
    return clean(faction.get("displayName")) or clean(faction.get("name"))


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
                    "title": clean(contract.get("title"), clean(contract.get("debugName"), "Unknown mission")),
                    "category": clean(contract.get("category"), "mission"),
                    "faction": faction_name(factions, contract.get("factionGuid")),
                    "trigger": clean(reward.get("trigger"), "complete"),
                    "chance": reward.get("chance"),
                    "rewardUEC": contract.get("rewardUEC"),
                    "systems": contract.get("systems") or contract.get("availableSystems") or [],
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
    items = items_data.get("items") or []
    item_by_entity = {item.get("entityClass"): item for item in items if item.get("entityClass")}
    item_by_name = {item.get("name"): item for item in items if item.get("name")}
    sources_by_record, pool_meta = build_source_maps(mission_data)

    records = []
    category_counts: dict[str, int] = {}
    manufacturer_counts: dict[str, int] = {}
    material_counts: dict[str, int] = {}

    for blueprint in crafting.get("blueprints") or []:
        product_name = clean(blueprint.get("productName"), clean(blueprint.get("suggestedName"), "Unnamed blueprint"))
        item = item_by_entity.get(blueprint.get("productEntityClass")) or item_by_name.get(product_name)
        category = category_for(blueprint, item)
        tiers = normalize_tiers(blueprint)
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
                "materials": materials,
                "sources": sources,
                "sourceCount": sum(source.get("missionCount", 0) for source in sources),
                "hasKnownIssue": bool(blueprint.get("cigDataError") or blueprint.get("knownIssue")),
                "search": search_blob,
            }
        )

    records.sort(key=lambda record: (record["category"]["id"], record["name"].lower()))
    return {
        "generatedFrom": "SCMDB public data",
        "version": mission_data.get("version") or crafting.get("version") or items_data.get("version"),
        "counts": {
            "blueprints": len(records),
            "categories": category_counts,
            "manufacturers": manufacturer_counts,
            "materials": material_counts,
            "rewardPools": len(pool_meta),
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build blueprint-site/data/blueprint-index.json")
    parser.add_argument("--cache-dir", type=Path, help="Directory containing cached SCMDB JSON files")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "blueprint-index.json")
    args = parser.parse_args()

    versions = read_source(args.cache_dir, "versions.json", f"{BASE_URL}/versions.json")
    if not versions:
        print("No SCMDB versions found", file=sys.stderr)
        return 1
    version = versions[0]["version"]
    merged_file = versions[0]["file"]

    mission_data = read_source(args.cache_dir, merged_file, f"{BASE_URL}/{merged_file}")
    crafting = read_source(args.cache_dir, f"crafting_blueprints-{version}.json", f"{BASE_URL}/crafting_blueprints-{version}.json")
    items = read_source(args.cache_dir, f"crafting_items-{version}.json", f"{BASE_URL}/crafting_items-{version}.json")
    index = build_index(mission_data, crafting, items)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        json.dump(index, handle, ensure_ascii=False, separators=(",", ":"))
    print(f"Wrote {args.out} with {len(index['records'])} blueprints from {index['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
