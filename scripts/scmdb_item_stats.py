"""Extract conservative, entity-matched base metrics from the selected LIVE export."""

from __future__ import annotations

import math
from typing import Any

from enrich_quality_stats import add_metric, modifier_keys, number_at

ITEM_STATS_SCHEMA = 1


def pool_value(data: dict, item: dict, field: str, pool: str, expected: type) -> Any:
    index = item.get(field)
    if index is None:
        return None
    values = data.get(pool)
    if (type(index) is not int or not isinstance(values, list) or not 0 <= index < len(values)
            or not isinstance(values[index], expected)):
        raise RuntimeError(f"invalid item stat pool reference: {field}")
    return values[index]


def weapon_metrics(item: dict, data: dict) -> tuple[list[dict], list[str]]:
    modes = pool_value(data, item, "fireModesIndex", "fireModesPools", list) or []
    ammo = pool_value(data, item, "ammoIndex", "ammoPools", dict) or {}
    magazine = pool_value(data, item, "magazineIndex", "magazinePools", dict) or {}
    metrics: list[dict] = []
    notes = []
    damage = ammo.get("damage") or {}
    damage_values = [number_at(damage, key) for key in damage]
    projectile_damage = sum(damage_values) if damage_values and all(v is not None and v >= 0 for v in damage_values) else None
    explosive = bool(ammo.get("detonationDamage"))
    add_metric(metrics, "magazine", "弹药容量", number_at(magazine, "ammoCount"), [], "发", 0)
    add_metric(metrics, "projectile_speed", "弹丸速度", number_at(ammo, "speed"), [], "m/s", 0)
    for index, raw in enumerate(modes):
        if not isinstance(raw, dict):
            raise RuntimeError("invalid weapon fire mode")
        mode = raw
        # Only a one-entry looping sequence with the same RPM is a simple mode.
        if raw.get("type") == "sequence":
            entries = raw.get("sequenceEntries") or []
            if (len(entries) == 1 and entries[0].get("type") in {"single", "rapid"}
                    and raw.get("sequenceMode") == "Looping" and entries[0].get("repetitions") == 1
                    and entries[0].get("delayUnit") == "RPM"
                    and number_at(entries[0], "delay") == number_at(entries[0], "fireRate")):
                mode = entries[0]
        kind = mode.get("type")
        names = {"single": "单发", "rapid": "自动", "burst": "连发", "charged": "蓄力", "beam": "光束", "sequence": "序列"}
        name = names.get(kind, str(raw.get("name") or "未知模式"))
        prefix = f"{name} · " if len(modes) > 1 else ""
        suffix = f"_{index}" if len(modes) > 1 else ""
        pellets = number_at(mode, "pelletCount")
        multiplier = number_at(mode, "damageMultiplier")
        rate = number_at(mode, "fireRate")
        simple = kind in {"single", "rapid"}
        if simple and not explosive and pellets is not None and pellets >= 1 and pellets.is_integer() and multiplier is not None and multiplier >= 0 and projectile_damage is not None:
            shot = projectile_damage * pellets * multiplier
            add_metric(metrics, f"alpha_damage{suffix}", f"{prefix}{'整发伤害' if pellets > 1 else '单发伤害'}", shot, ["weapon_damage"])
            if pellets > 1:
                add_metric(metrics, f"pellet_damage{suffix}", f"{prefix}单弹丸伤害", projectile_damage * multiplier, ["weapon_damage"])
                add_metric(metrics, f"pellets{suffix}", f"{prefix}弹丸数", pellets, [], "颗/发", 0)
            if rate is not None and rate > 0:
                add_metric(metrics, f"burst_dps{suffix}", f"{prefix}理论 DPS", shot * rate / 60, ["weapon_damage", "weapon_firerate"])
        if simple:
            add_metric(metrics, f"fire_rate{suffix}", f"{prefix}射速", rate, ["weapon_firerate"], "RPM", 0)
        else:
            notes.append(f"{name}模式未估算单发伤害和 DPS")
        for key, label in (("chargeTime", "蓄力时间"), ("cooldownTime", "模式冷却")):
            add_metric(metrics, f"{key}_{index}", f"{prefix}{label}", number_at(mode, key), [], "秒")
    if modes:
        mode_labels = {"Single": "单发", "Rapid": "自动", "Burst": "连发", "Charge": "蓄力", "Sequence": "序列", "Damage Beam": "伤害光束", "Shotgun": "霰弹"}
        kind_labels = {"single": "单发", "rapid": "自动", "burst": "连发", "charged": "蓄力", "sequence": "序列", "beam": "光束"}
        notes.insert(0, "射击模式：" + " / ".join(mode_labels.get(m.get("name")) or kind_labels.get(m.get("type"), "未知模式") for m in modes))
    if explosive:
        notes.append("包含爆炸伤害，未估算合并伤害与 DPS")
    if any(m["id"].startswith("burst_dps") for m in metrics):
        notes.append("理论伤害按全部弹丸命中计算，未计距离衰减、护甲、换弹和蓄力周期")
    return metrics, notes


def item_metrics(item: dict, data: dict) -> tuple[list[dict], list[str]]:
    metrics, notes = weapon_metrics(item, data)
    fields = [
        ("health", "integrity", "结构完整度", ["health_maxhealth"], "", 0),
        ("shieldHealth", "shield_capacity", "护盾容量", ["shield_maxhealth"], "", 0),
        ("shieldRegen", "shield_regen", "护盾恢复", [], "/秒", 0),
        ("coolingRate", "coolant_generation", "冷却生成", ["itemresource_coolantgeneration"], "", 0),
        ("powerOutput", "power_generation", "电力格", ["itemresource_powergeneration"], "", 0),
        ("minAimAssistRange", "radar_aim_min", "辅助瞄准起始", ["radar_minaimassistdistance"], "m", 0),
        ("maxAimAssistRange", "radar_aim_max", "辅助瞄准上限", ["radar_maxaimassistdistance"], "m", 0),
        ("maxForce", "tractor_force", "牵引力", ["weapon_tractor_force"], "N", 0),
        ("maxDistance", "tractor_max_distance", "最大距离", ["weapon_tractor_maxdist"], "m", 0),
        ("fullStrengthDistance", "tractor_full_strength", "全功率距离", ["weapon_tractor_fullstrengthdist"], "m", 0),
        ("maxVolume", "tractor_volume", "最大牵引体积", ["weapon_tractor_maxvolume"], "m³", 0),
        ("mass", "mass", "质量", [], "kg", 2),
    ]
    for field, metric_id, label, properties, unit, digits in fields:
        add_metric(metrics, metric_id, label, number_at(item, field), properties, unit, digits)
    for field, metric_id, label, property_key, factor, unit in (
        ("driveSpeed", "quantum_speed", "量子速度", "quantum_speed", 0.001, "km/s"),
        ("salvageSpeedMultiplier", "scraping_speed", "刮削速度", "weapon_hullscraping_speed", 1, "×"),
        ("radiusMultiplier", "scraping_radius", "刮削范围", "weapon_hullscraping_radius", 1, "×"),
        ("extractionEfficiency", "scraping_efficiency", "回收效率", "weapon_hullscraping_efficiency", 100, "%"),
    ):
        value = number_at(item, field)
        add_metric(metrics, metric_id, label, value * factor if value is not None else None, [property_key], unit)
    # Fuel coefficient units are not declared by this export; do not invent SCU/10 GM.
    for field, metric_id, label, prop, unit in (
        ("temperatureResistance.min", "temperature_min", "最低耐温", "armor_temperaturemin", "°C"),
        ("temperatureResistance.max", "temperature_max", "最高耐温", "armor_temperaturemax", "°C"),
        ("radiationResistance.dissipationRate", "radiation_dissipation", "辐射消散", "armor_radiationdissipation", ""),
    ):
        add_metric(metrics, metric_id, label, number_at(item, *field.split(".")), [prop], unit)
    for beam in item.get("beams") or []:
        if beam.get("hitType") == "ElectricArc":
            add_metric(metrics, "mining_power", "采矿功率", number_at(beam, "dps"), ["weapon_damage"], digits=0)
            break
    return metrics, notes


def attach_item_stats(index: dict, items_data: dict) -> None:
    version = str(index.get("version") or "")
    if str(items_data.get("version") or "").lower() != version.lower():
        raise RuntimeError("SCMDB item stats version mismatch")
    items = items_data.get("items")
    if not isinstance(items, list):
        raise RuntimeError("SCMDB item stats require an item list")
    by_entity = {}
    for item in items:
        entity = item.get("entityClass")
        if entity:
            if entity in by_entity:
                raise RuntimeError("duplicate SCMDB item entity")
            by_entity[entity] = item
    matched = 0
    for record in index.get("records") or []:
        item = by_entity.get(record.get("productEntityClass"))
        record.pop("baseStats", None)
        record.pop("baseStatNotes", None)
        record.pop("qualityStats", None)
        if not item:
            continue
        matched += 1
        metrics, notes = item_metrics(item, items_data)
        keys = modifier_keys(record)
        record["baseStats"] = metrics
        record["baseStatNotes"] = notes
        quality = []
        for metric in metrics:
            properties = [key for key in metric["properties"] if key in keys]
            if properties:
                quality.append({**metric, "properties": properties})
        if quality:
            record["qualityStats"] = quality
    records = index.get("records") or []
    if len(records) >= 1000 and matched < int(len(records) * 0.8):
        raise RuntimeError("SCMDB entity matching coverage is unexpectedly low")
    index["itemStats"] = {"schemaVersion": ITEM_STATS_SCHEMA, "version": version,
                          "matchedItems": matched, "recordsWithBaseStats": sum(bool(r.get("baseStats")) for r in records)}
    modifier_records = [r for r in records if modifier_keys(r)]
    index["qualityEffects"] = {"version": version, "source": "scmdb", "recordsWithModifiers": len(modifier_records),
                               "matchedItems": sum(r.get("productEntityClass") in by_entity for r in modifier_records),
                               "recordsWithBaseStats": sum(bool(r.get("qualityStats")) for r in records)}


def validate_item_stats(index: dict) -> None:
    meta = index.get("itemStats") or {}
    if meta.get("schemaVersion") != ITEM_STATS_SCHEMA or meta.get("version") != index.get("version"):
        raise RuntimeError("SCMDB item stats schema/version mismatch")
    records = index.get("records") or []
    if any(type(meta.get(key)) is not int for key in ("recordsWithBaseStats", "matchedItems")):
        raise RuntimeError("invalid SCMDB item stat coverage")
    if not 0 <= meta.get("recordsWithBaseStats", -1) <= meta.get("matchedItems", -1) <= len(records):
        raise RuntimeError("invalid SCMDB item stat coverage")
    if sum(bool(r.get("baseStats")) for r in records) != meta["recordsWithBaseStats"]:
        raise RuntimeError("SCMDB item stat coverage does not match records")
    for record in records:
        for field in ("baseStats", "qualityStats"):
            ids = set()
            for metric in record.get(field) or []:
                value = metric.get("value")
                if (not metric.get("id") or metric["id"] in ids or not metric.get("label")
                        or type(value) not in (int, float) or not math.isfinite(value)
                        or not isinstance(metric.get("properties"), list)
                        or any(not isinstance(key, str) or not key for key in metric["properties"])
                        or type(metric.get("digits", 2)) is not int or not 0 <= metric.get("digits", 2) <= 6
                        or not isinstance(metric.get("unit", ""), str)):
                    raise RuntimeError("invalid SCMDB base metric")
                ids.add(metric["id"])
