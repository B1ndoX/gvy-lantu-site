"""Normalize exact-LIVE mining presets without inventing spawn points or radar totals."""

from __future__ import annotations

import math
from typing import Any

from scmdb_versions import is_live_version

SCHEMA_VERSION = 2
GROUPS = ("starSystems", "planets", "moons", "pointsOfInterest", "lagrangePoints")
MODES = {
    "SpaceShip_Mineables": ("ship", "scanSignature"),
    "SpaceShip_Mineables_Rare": ("ship", "scanSignature"),
    "GroundVehicle_Mineables": ("roc", "groundScanSignature"),
    "FPS_Mineables": ("fps", "fpsScanSignature"),
}
ALIASES = {"Saldynium": "Saldynium (Ore)"}
LOCATION_NAMES = {
    "Stanton": "斯坦顿", "Pyro": "派罗", "Nyx": "尼克斯",
    "Breaker Stations Interior": "破碎站内部", "Breaker Stations Large Geode": "破碎站大型晶洞",
    "Glaciem Ring": "冰川环", "Keeger Belt": "基格带", "Akiro Cluster": "阿基罗矿区",
    "Aaron Halo": "亚伦环", "Yela Asteroid Belt": "耶拉小行星带",
    "Asteroid Cluster (Low Yield)": "小行星群（低产出区域）",
    "Asteroid Cluster (Medium Yield)": "小行星群（中产出区域）",
    "Pyro Deep Space Asteroids": "派罗深空小行星区", "Hathor Caves": "哈索尔洞穴",
    "Lagrange (Occupied)": "拉格朗日点（已占用区域模板）",
    **{f"Lagrange {letter}": f"拉格朗日区域模板 {letter}" for letter in "ABCDEFG"},
    **{f"Pyro Belt ({kind} {n})": f"派罗矿带（{zh}区 {n}）"
       for kind, zh in (("Cool", "冷"), ("Warm", "暖")) for n in (1, 2)},
}
LOCATION_ALIASES = {
    "Pyro II (Monox)": "Monox", "Pyro III (Bloom)": "Bloom", "Pyro VI (Terminus)": "Terminus",
    "Pyro V-a (Ignis)": "Ignis", "Pyro V-b (Vatra)": "Vatra", "Pyro V-c (Adir)": "Adir",
    "Pyro V-d (Fairo)": "Fairo", "Pyro V-e (Fuego)": "Fuego", "Pyro V-f (Vuur)": "Vuur",
}
MOON_PARENTS = {
    **{name: "Pyro V" for name in ("Ignis", "Vatra", "Adir", "Fairo", "Fuego", "Vuur")},
    **{name: "Hurston" for name in ("Arial", "Aberdeen", "Magda", "Ita")},
    **{name: "Crusader" for name in ("Cellin", "Daymar", "Yela")},
    "Lyria": "ArcCorp", "Wala": "ArcCorp",
    **{name: "microTech" for name in ("Calliope", "Clio", "Euterpe")},
}


def number(value: Any, label: str, minimum: float = 0, maximum: float = math.inf) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise RuntimeError(f"invalid mining {label}")
    if not minimum <= value <= maximum:
        raise RuntimeError(f"out-of-range mining {label}")
    return value


def material_name(element: dict) -> str:
    name = element.get("name") or ""
    if name.endswith(" (Pure)"):
        return ""
    return element.get("materialName") or ALIASES.get(name, name)


def validate_mining(payload: dict, version: str) -> None:
    if not is_live_version(version) or payload.get("version") != version:
        raise RuntimeError("mining data must match the exact blueprint LIVE version")
    elements, compositions = payload.get("mineableElements"), payload.get("compositions")
    presets, locations = payload.get("clusteringPresets"), payload.get("locations")
    if not all(isinstance(table, dict) for table in (elements, compositions, presets)) or not isinstance(locations, list):
        raise RuntimeError("invalid mining data tables")
    if len(elements) < 30 or len(compositions) < 40 or len(locations) < 30:
        raise RuntimeError("mining source coverage is unexpectedly low")
    for field, actual in (("totalLocations", len(locations)), ("totalElements", len(elements)),
                          ("totalCompositions", len(compositions)), ("totalClusteringPresets", len(presets))):
        if (payload.get("meta") or {}).get(field) != actual:
            raise RuntimeError(f"mining source count mismatch: {field}")
    for element in elements.values():
        if not isinstance(element, dict) or not element.get("name") or not element.get("resourceType"):
            raise RuntimeError("invalid mining element identity")
        for field in ("scanSignature", "groundScanSignature", "fpsScanSignature"):
            if element.get(field) is not None:
                number(element[field], field, 0, 1_000_000)
    for composition in compositions.values():
        if not isinstance(composition.get("parts"), list) or not composition["parts"]:
            raise RuntimeError("mining composition has no parts")
        for part in composition["parts"]:
            if part.get("elementGuid") not in elements:
                raise RuntimeError("mining composition refers to a missing element")
            number(part.get("probability"), "element probability", 0, 1)
            low = number(part.get("minPercent"), "minimum composition", 0, 100)
            number(part.get("maxPercent"), "maximum composition", low, 100)
    for preset in presets.values():
        number(preset.get("probabilityOfClustering"), "cluster probability", 0, 100)
        if not isinstance(preset.get("params"), list):
            raise RuntimeError("invalid mining cluster parameters")
        for row in preset["params"]:
            low = number(row.get("minSize"), "minimum cluster", 1, 100)
            high = number(row.get("maxSize"), "maximum cluster", low, 100)
            if int(low) != low or int(high) != high:
                raise RuntimeError("mining cluster sizes must be integers")
            number(row.get("relativeProbability"), "cluster weight")
    seen = set()
    for location in locations:
        identity = (location.get("system"), location.get("presetFile"))
        if not all(identity) or identity in seen or not location.get("locationName"):
            raise RuntimeError("invalid or duplicate mining location")
        seen.add(identity)
        if not isinstance(location.get("groups"), list):
            raise RuntimeError("invalid mining location groups")
        for group in location["groups"]:
            number(group.get("groupProbability"), "group weight")
            for deposit in group.get("deposits") or []:
                number(deposit.get("relativeProbability"), "deposit weight")
                if group.get("groupName") not in MODES:
                    continue
                if deposit.get("compositionGuid") not in compositions:
                    raise RuntimeError("mining deposit refers to a missing composition")
                if deposit.get("clusteringPresetGuid") and deposit["clusteringPresetGuid"] not in presets:
                    raise RuntimeError("mining deposit refers to a missing clustering preset")


def cluster_counts(preset: dict | None) -> list[int]:
    if not preset:
        return [1]
    chance = preset["probabilityOfClustering"]
    counts = set()
    if chance > 0:
        for row in preset["params"]:
            if row["relativeProbability"] > 0:
                counts.update(range(int(row["minSize"]), int(row["maxSize"]) + 1))
    if not counts or chance < 100:
        counts.add(1)
    return sorted(counts)


def build_mining_materials(payload: dict, names: list[str], localized: dict[str, str]) -> dict:
    elements = payload["mineableElements"]
    # Only identical resource IDs may provide missing mode signatures. A same-name
    # pure variant is not evidence for the raw material's signature.
    signatures: dict[tuple[str, str], int] = {}
    for element in elements.values():
        for _, field in MODES.values():
            value = element.get(field)
            if value is not None:
                key = (element["resourceType"], field)
                if key in signatures and signatures[key] != value:
                    raise RuntimeError("conflicting signatures for the same mining resource")
                signatures[key] = value

    def zh(name: str) -> str:
        return localized.get(name) or LOCATION_NAMES.get(name) or name

    result = {name: {"locations": {key: [] for key in GROUPS}, "hasReliableLocations": False,
                     "status": "unmapped", "sourceVersion": payload["version"]} for name in names}
    for location in payload["locations"]:
        found: dict[str, dict] = {}
        for group in location["groups"]:
            mode = MODES.get(group["groupName"])
            if not mode or group["groupProbability"] <= 0:
                continue
            for deposit in group.get("deposits") or []:
                if deposit["relativeProbability"] <= 0:
                    continue
                composition = payload["compositions"][deposit["compositionGuid"]]
                parts = [p for p in composition["parts"] if p["probability"] > 0 and p["maxPercent"] > 0]
                if not parts:
                    continue
                primary = elements[max(parts, key=lambda p: p["probability"])["elementGuid"]]
                base = signatures.get((primary["resourceType"], mode[1]))
                preset = payload["clusteringPresets"].get(deposit.get("clusteringPresetGuid"))
                counts = cluster_counts(preset)
                signal = {"mode": mode[0], "base": base, "primaryMaterial": material_name(primary),
                          "compositionId": deposit["compositionGuid"], "clusterCounts": counts,
                          "clusterKnown": bool(preset and preset["params"]),
                          "clusterChance": preset["probabilityOfClustering"] if preset else None,
                          "shared": mode[0] != "ship",
                          "values": ([base * count for count in counts] if mode[0] == "ship" else [base]) if base else []}
                for name in {material_name(elements[p["elementGuid"]]) for p in parts} & result.keys():
                    item = found.setdefault(name, {"signals": [], "modes": set(), "compositionIds": set()})
                    item["modes"].add(mode[0])
                    item["compositionIds"].add(deposit["compositionGuid"])
                    if base and signal not in item["signals"]:
                        item["signals"].append(signal)
        for name, details in found.items():
            en = LOCATION_ALIASES.get(location["locationName"], location["locationName"])
            kind = location["locationType"]
            group_name = {"planet": "planets", "moon": "moons", "lagrange": "lagrangePoints"}.get(kind, "pointsOfInterest")
            parent = MOON_PARENTS.get(en, "")
            entry = {"id": f"scmdb:{location['presetFile']}", "en": en, "zh": zh(en),
                     "systemEn": location["system"], "systemZh": zh(location["system"]),
                     "parentEn": parent, "parentZh": zh(parent), "locationType": kind,
                     "precision": "template" if kind in {"lagrange", "cluster"} or en.startswith("Pyro Belt (") else "area",
                     "coordinateStatus": "not-provided", "modes": sorted(details["modes"]),
                     "compositionIds": sorted(details["compositionIds"]),
                     "signals": sorted(details["signals"], key=lambda s: (s["mode"], s["base"], s["compositionId"]))}
            result[name]["locations"][group_name].append(entry)
    for material in result.values():
        systems = sorted({entry["systemEn"] for rows in material["locations"].values() for entry in rows})
        material["locations"]["starSystems"] = [{"id": f"scmdb:system:{system}", "en": system, "zh": zh(system)} for system in systems]
        for rows in material["locations"].values():
            rows.sort(key=lambda entry: (entry.get("systemEn", ""), entry["en"], entry["id"]))
        material["hasReliableLocations"] = bool(systems)
        material["status"] = "current" if systems else "unmapped"
    return result
