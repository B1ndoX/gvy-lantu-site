#!/usr/bin/env python3
"""Apply local Star Citizen bot localization over machine translated blueprint data."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


MANUFACTURERS = {
    "Aegis Dynamics": "圣盾动力",
    "Anvil Aerospace": "铁砧航天",
    "Aopoa": "奥波亚",
    "Argo Astronautics": "ARGO 航天",
    "Behring": "贝林",
    "Drake Interplanetary": "德雷克星际",
    "Esperia": "埃斯佩里亚",
    "Gemini": "双子星",
    "GNP": "GNP",
    "GRNP": "GNP",
    "Greycat Industrial": "灰猫工业",
    "Hurston Dynamics": "赫斯顿动力",
    "Kastak Arms": "卡斯塔克武器",
    "Klaus & Werner": "克劳斯&维尔纳",
    "KnightBridge Arms": "骑士桥武器",
    "Kruger Intergalactic": "克鲁格星际",
    "LBCO": "LBCO",
    "Lightning Power Ltd.": "闪电动力",
    "Mirai": "未来",
    "Musashi Industrial & Starflight Concern": "武藏工业与星航集团",
    "Origin Jumpworks": "起源跃动",
    "Roberts Space Industries": "罗伯茨航天工业",
    "Shubin Interstellar": "舒宾星际",
    "Tarsus": "塔尔苏斯",
    "Thermyte Concern": "Thermyte 集团",
    "Unknown": "未知",
    "VOLT": "VOLT",
    "Wei-Tek": "维泰克",
    "WillsOp": "WillsOp",
}

TYPE_WORDS = {
    "Ballistic Gatling": "实弹加特林",
    "Ballistic Repeater": "实弹速射炮",
    "Cannon": "加农炮",
    "Repeater": "速射炮",
    "Scattergun": "散射炮",
    "Gatling": "加特林",
    "Distortion Repeater": "畸变速射炮",
    "Distortion Cannon": "畸变加农炮",
    "Laser Cannon": "激光加农炮",
    "Laser Repeater": "激光速射炮",
    "Sniper Rifle": "狙击步枪",
    "Pistol": "手枪",
    "Rifle": "步枪",
    "Shotgun": "霰弹枪",
    "SMG": "冲锋枪",
    "LMG": "轻机枪",
    "Magazine": "弹匣",
    "Battery": "电池",
}

STAT_TERMS = {
    "weapon": "武器",
    "weapons": "武器",
    "shipcomponent": "舰船部件",
    "cooler": "冷却器",
    "powerplant": "电源",
    "shield": "护盾",
    "radar": "雷达",
    "quantumdrive": "量子驱动器",
    "ammo": "弹药",
    "mininglaser": "采矿激光器",
    "tractorbeam": "牵引光束",
    "salvage": "打捞模块",
    "refuelling": "加油模块",
    "armor": "护甲",
    "armour": "护甲",
    "fpsgear": "单兵装备",
    "vehiclegear": "载具装备",
    "WeaponPersonal": "单兵武器",
    "WeaponGun": "舰船武器",
    "WeaponAttachment": "武器配件",
    "WeaponMining": "采矿激光器",
    "PowerPlant": "电源",
    "Cooler": "冷却器",
    "Shield": "护盾",
    "Radar": "雷达",
    "QuantumDrive": "量子驱动器",
    "TractorBeam": "牵引光束",
    "SalvageHead": "打捞头",
    "SalvageModifier": "打捞模块",
    "resource": "资源",
    "item": "物品",
    "missionitems": "任务物品",
}

SLOT_TERMS = {
    "Assembly": "总成",
    "Barrel": "炮管",
    "Capacitor": "电容器",
    "Circuit": "电路",
    "Coolant": "冷却剂",
    "Core": "核心",
    "Casing": "外壳",
    "Coil": "线圈",
    "Conduit": "导管",
    "Controller": "控制器",
    "Cycler": "循环器",
    "Emitter": "发射器",
    "Field Array": "场阵列",
    "Filter": "滤芯",
    "Frame": "框架",
    "Frequency Controller": "频率控制器",
    "Fuel Cell": "燃料电池",
    "Housing": "外壳",
    "Lens": "镜片",
    "Lattice": "晶格",
    "Magazine": "弹匣",
    "Matrix": "矩阵",
    "Precision Parts": "精密部件",
    "Receiver": "机匣",
    "Regulator": "调节器",
    "Shell": "外壳",
    "Shield Emitter": "护盾发射器",
    "Substrate": "基底",
    "Wiring": "接线",
}

SUBTYPE_TERMS = {
    "ballistic": "实弹",
    "laser": "激光",
    "distortion": "畸变",
    "plasma": "等离子",
    "electron": "电子",
    "pistol": "手枪",
    "rifle": "步枪",
    "sniper": "狙击",
    "shotgun": "霰弹",
    "smg": "冲锋枪",
    "lmg": "轻机枪",
    "size0": "0 号",
    "size1": "1 号",
    "size2": "2 号",
    "size3": "3 号",
    "size4": "4 号",
}

MATERIALS = {
    "Agricium": "艾瑞格金属",
    "Aluminum": "铝",
    "Aphorite": "紫钠水晶",
    "Aslarite": "阿斯莱晶体",
    "Beradom": "冰蓝珀",
    "Beryl": "绿柱石",
    "Bexalite": "贝沙电气石",
    "Borase": "波射矿石",
    "Carinite": "肯瑞特矿石",
    "Copper": "铜",
    "Corundum": "刚玉",
    "Diamond": "钻石",
    "Dolivine": "暗橄榄石",
    "Feynmaline": "费恩麻林",
    "Glacosite": "格拉科石",
    "Gold": "金",
    "Hadanite": "哈丹水晶",
    "Hephaestanite": "火神石",
    "Hydrogen": "氢",
    "Inert Materials": "惰性材料",
    "Iron": "铁",
    "Janalite": "加纳石",
    "Laranite": "砬兰石",
    "Lindinium": "林登金",
    "Ouratite": "欧特拉烃",
    "Pressurized Ice": "压缩冰",
    "Quartz": "石英",
    "Quantanium": "量子矿",
    "Quantainium": "量子矿",
    "Riccite": "愈金",
    "Sadaryx": "萨达瑞晶",
    "Saldynium": "烁迪银",
    "Saldynium Ore": "烁迪银",
    "Savrilium": "萨维里金属",
    "Silicon": "硅",
    "Stileron": "稀钛铁",
    "Taranite": "塔兰导电石",
    "Tin": "锡",
    "Titanium": "钛",
    "Torite": "托瑞特金属",
    "Tungsten": "钨",
}

COMPONENT_CLASSES = {
    "Military": "军用",
    "Civilian": "民用",
    "Stealth": "隐形",
    "Competition": "竞赛",
    "Industrial": "工业",
}

MISSION_TYPES = {
    "Mercenary": "雇佣兵",
    "Ship Mining": "舰船采矿",
    "Hauling - Interstellar": "星际货运",
    "Hauling - Stellar": "星际货运",
    "Refueling": "Refueling",
    "Hauling": "货运",
    "Delivery": "快递",
    "Courier": "快递",
    "Salvage": "打捞",
    "Bounty Hunter": "赏金猎人",
    "Investigation": "调查",
    "Collection": "采集",
    "Other": "其他",
}


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def clean_localized_name(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text == "<-=MISSING=->":
        return ""
    if text.startswith("[PH]") or text.startswith("(PH)"):
        return ""
    if "\n" in text:
        text = text.splitlines()[0].strip()
    return text


def add_plain_names(names: dict[str, str], payload: Any) -> int:
    if not isinstance(payload, dict):
        return 0
    added = 0
    for key, value in payload.items():
        clean_key = normalize_name(str(key or ""))
        clean_value = clean_localized_name(value)
        if clean_key and clean_value:
            names[clean_key] = clean_value
            added += 1
    return added


def add_item_name_records(names: dict[str, str], payload: Any) -> int:
    if not isinstance(payload, dict):
        return 0
    added = 0
    for value in payload.values():
        if not isinstance(value, dict):
            continue
        english = normalize_name(str(value.get("english") or ""))
        chinese = clean_localized_name(value.get("chinese"))
        if not english or not chinese:
            continue
        if chinese.startswith("[") and chinese.endswith("]"):
            continue
        names[english] = chinese
        added += 1
    return added


def load_star_citizen_localization(bot_assets: Path) -> tuple[dict[str, str], dict[str, int]]:
    base = bot_assets / "localization" / "starcitizen"
    names: dict[str, str] = {}
    if not base.exists():
        return names, {}

    counts: dict[str, int] = {}
    for source_name, relative in (
        ("starcitizenItemsByEnglish", "items/by-english.json"),
        ("starcitizenComponentCandidates", "items/component-candidates.json"),
        ("starcitizenBotComponents", "bot/component-names.json"),
        ("starcitizenBotShips", "bot/ship-names.json"),
        ("starcitizenShips", "ships/names.json"),
    ):
        counts[source_name] = add_plain_names(names, load_json(base / relative, {}))
    counts["starcitizenItemRecords"] = add_item_name_records(names, load_json(base / "items/names.json", {}))
    counts["starcitizenTotal"] = len(names)
    return names, counts


def load_bot_names(bot_assets: Path) -> dict[str, str]:
    names: dict[str, str] = {}
    for filename in ("component-name-n55.json", "component-name-local.json", "ship-name-zh.json"):
        payload = load_json(bot_assets / filename, {})
        if isinstance(payload, dict):
            for key, value in payload.items():
                if key.startswith("_") or not value:
                    continue
                names[str(key).strip()] = str(value).strip()
    matrix = load_json(bot_assets / "component-matrix-erkul.json", {})
    for category in (matrix.get("categories") or {}).values():
        columns = [str(col[0]) for col in category.get("columns") or [] if isinstance(col, list) and col]
        try:
            english_index = columns.index("英文名")
            chinese_index = columns.index("中文名")
        except ValueError:
            continue
        for row in category.get("rows") or []:
            values = row.get("values") or []
            if english_index >= len(values) or chinese_index >= len(values):
                continue
            english = str(values[english_index]).strip()
            chinese = str(values[chinese_index]).strip()
            if english and chinese and english != chinese:
                names[english] = chinese
    starcitizen_names, _counts = load_star_citizen_localization(bot_assets)
    names.update(starcitizen_names)
    return names


def load_names(bot_assets: Path, fallback_path: Path) -> dict[str, str]:
    names = load_bot_names(bot_assets) if bot_assets.exists() else {}
    if names:
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        with fallback_path.open("w", encoding="utf-8") as handle:
            json.dump(names, handle, ensure_ascii=False, indent=2, sort_keys=True)
        return names
    fallback = load_json(fallback_path, {})
    if isinstance(fallback, dict):
        return {str(key): str(value) for key, value in fallback.items() if value}
    return {}


def split_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item or "").strip()]
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item or "").strip()]
            except json.JSONDecodeError:
                pass
        return [part.strip().strip('"') for part in text.split(",") if part.strip()]
    return []


def load_flowcld_calibration(path: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(path, {})
    records = payload.get("items") if isinstance(payload, dict) else []
    by_id: dict[str, str] = {}
    by_name: dict[str, str] = {}
    by_internal: dict[str, str] = {}
    items_by_id: dict[str, dict[str, Any]] = {}
    for item in records or []:
        if not isinstance(item, dict):
            continue
        cn_name = str(item.get("blueprintNameCn") or "").strip()
        record_id = str(item.get("recordGuid") or "").strip()
        internal_name = normalize_name(str(item.get("internalName") or ""))
        en_name = normalize_name(str(item.get("blueprintName") or ""))
        compact_meta: dict[str, Any] = {}
        for key in (
            "recordGuid",
            "internalName",
            "blueprintName",
            "blueprintNameCn",
            "categoryName",
            "subcategory",
            "manufacturer",
            "grade",
            "itemClass",
            "isReward",
            "rewardMissionCount",
            "craftTimeSeconds",
        ):
            value = item.get(key)
            if value is not None and str(value).strip():
                compact_meta[key] = value
        reward_types = split_list(item.get("rewardMissionTypes"))
        reward_types_cn = split_list(item.get("rewardMissionTypesCn"))
        if reward_types:
            compact_meta["rewardMissionTypes"] = reward_types
            compact_meta["rewardMissionTypesCn"] = [
                MISSION_TYPES.get(name) or (reward_types_cn[index] if index < len(reward_types_cn) and reward_types_cn[index] else name)
                for index, name in enumerate(reward_types)
            ]
        if record_id and compact_meta:
            items_by_id[record_id] = compact_meta
        if record_id and cn_name:
            by_id[record_id] = cn_name
        if internal_name and cn_name:
            by_internal[internal_name] = cn_name
        if en_name and cn_name:
            by_name[en_name] = cn_name
    return {"by_id": by_id, "by_name": by_name, "by_internal": by_internal, "items_by_id": items_by_id}


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.replace("’", "'").replace("“", '"').replace("”", '"')).strip()


def compact_size_tokens(text: str) -> str:
    value = str(text or "")
    value = re.sub(r"^RADR_[A-Z0-9]+_S0?\d+_[A-Za-z0-9]+(?:_TEMP)?\s*", "雷达 ", value)
    value = re.sub(r"[（(]\s*S0*(\d+)\s*尺寸\s*[）)]", r"(S\1)", value, flags=re.I)
    value = re.sub(r"S0*(\d+)\s*尺寸", r"S\1", value, flags=re.I)
    value = re.sub(r"\bS0+(\d+)\s*尺寸\b", r"S\1", value, flags=re.I)
    value = re.sub(r"\bS0+(\d+)\b", r"S\1", value)
    value = re.sub(r"^S00(?=\D)", "S0 ", value)
    value = re.sub(r"\s{2,}", " ", value)
    return value.strip()


def strip_suffix(name: str) -> tuple[str, str]:
    for suffix in sorted(TYPE_WORDS, key=len, reverse=True):
        if name.endswith(f" {suffix}"):
            return name[: -len(suffix) - 1], suffix
    return name, ""


def localize_product_name(name: str, local_names: dict[str, str]) -> str | None:
    clean = normalize_name(name)
    if clean in local_names:
        return local_names[clean]
    base, suffix = strip_suffix(clean)
    if base in local_names and suffix:
        cn_suffix = TYPE_WORDS.get(suffix, suffix)
        return f"{local_names[base]} {cn_suffix}"

    attachment = re.match(r"^(.+?) (Magazine|Battery) \((\d+) cap\)$", clean)
    if attachment:
        base_name, kind, cap = attachment.groups()
        localized_base = localize_product_name(base_name, local_names) or local_names.get(base_name)
        if localized_base:
            return f"{localized_base}{TYPE_WORDS[kind]}（{cap} 发）"

    quoted = re.match(r"^(.+?) \"(.+?)\" (.+)$", clean)
    if quoted:
        prefix, skin, suffix = quoted.groups()
        prefix_cn = local_names.get(prefix, prefix)
        suffix_cn = TYPE_WORDS.get(suffix, suffix)
        return f"{prefix_cn}“{skin}”{suffix_cn}"
    return None


def flowcld_name(record: dict[str, Any], calibration: dict[str, dict[str, str]]) -> str | None:
    by_id = calibration.get("by_id") or {}
    by_name = calibration.get("by_name") or {}
    by_internal = calibration.get("by_internal") or {}
    record_id = str(record.get("id") or "").strip()
    clean_name = normalize_name(str(record.get("name") or ""))
    product_entity_class = normalize_name(str(record.get("productEntityClass") or ""))
    tag = normalize_name(str(record.get("tag") or ""))
    return by_id.get(record_id) or by_name.get(clean_name) or by_internal.get(product_entity_class) or by_internal.get(tag)


def flowcld_item(record: dict[str, Any], calibration: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    by_id = calibration.get("items_by_id") or {}
    record_id = str(record.get("id") or "").strip()
    item = by_id.get(record_id)
    if isinstance(item, dict):
        return item
    return None


def apply_flowcld_metadata(record: dict[str, Any], item: dict[str, Any] | None) -> None:
    if not item:
        return
    meta: dict[str, Any] = {}
    for key in (
        "categoryName",
        "subcategory",
        "manufacturer",
        "grade",
        "itemClass",
        "isReward",
        "rewardMissionCount",
        "craftTimeSeconds",
    ):
        value = item.get(key)
        if value is not None and str(value).strip():
            meta[key] = value
    item_class = str(meta.get("itemClass") or "")
    if item_class in COMPONENT_CLASSES:
        meta["itemClassCn"] = COMPONENT_CLASSES[item_class]
    reward_types = split_list(item.get("rewardMissionTypes"))
    reward_types_cn = split_list(item.get("rewardMissionTypesCn"))
    if reward_types:
        meta["rewardMissionTypes"] = reward_types
        meta["rewardMissionTypesCn"] = [
            MISSION_TYPES.get(name) or (reward_types_cn[index] if index < len(reward_types_cn) and reward_types_cn[index] else name)
            for index, name in enumerate(reward_types)
        ]
    if meta:
        record["flowcld"] = meta


def polish_machine_text(text: str) -> str:
    replacements = {
        "门闩": "死锁",
        "中继器": "速射炮",
        "大刀炮": "阔剑加农炮",
        "长剑炮": "长剑加农炮",
        "巨剑炮": "巨剑加农炮",
        "粒": "发",
        "帽": "发",
        "盖": "发",
        "克劳斯和维尔纳": "克劳斯&维尔纳",
        "卡斯塔克阿姆斯": "卡斯塔克武器",
        "骑士桥武器公司": "骑士桥武器",
        "国民生产总值": "GNP",
        "遗嘱操作": "WillsOp",
        "壳牌": "外壳",
        "桶": "炮管",
        "循环仪": "循环器",
        "频率控制器": "频率控制器",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return compact_size_tokens(text)


def apply(index: dict[str, Any], local_names: dict[str, str], flowcld_calibration: dict[str, dict[str, Any]], bot_assets: Path) -> None:
    starcitizen_names, starcitizen_counts = load_star_citizen_localization(bot_assets)
    polish_meta = index.setdefault("localization", {})
    polish_meta.update(
        {
            "polishSource": "sc-spectrum-qq-bot Star Citizen localization package",
            "localNameCount": len(local_names),
            "starCitizenLocalizationCount": len(starcitizen_names),
            "starCitizenLocalizationCounts": starcitizen_counts,
            "flowcldCalibrationCount": len(flowcld_calibration.get("by_id") or {}),
            "flowcldMetadataCount": len(flowcld_calibration.get("items_by_id") or {}),
            "flowcldCalibrationSource": "https://flowcld.xyz/tools/blueprint",
        }
    )
    for record in index.get("records") or []:
        zh = record.setdefault("zh", {})
        local_name = localize_product_name(str(record.get("name") or ""), local_names)
        calibrated_name = flowcld_name(record, flowcld_calibration)
        calibrated_item = flowcld_item(record, flowcld_calibration)
        apply_flowcld_metadata(record, calibrated_item)
        if local_name:
            zh["name"] = local_name
            zh["nameSource"] = "starcitizen-localization"
        elif calibrated_name:
            zh["name"] = polish_machine_text(calibrated_name)
            zh["nameSource"] = "flowcld-calibration"
        else:
            zh["name"] = polish_machine_text(str(zh.get("name") or record.get("name") or ""))
            zh["nameSource"] = zh.get("nameSource") or "google-polished"

        manufacturer = str(record.get("manufacturer") or "")
        if manufacturer in MANUFACTURERS:
            zh["manufacturer"] = MANUFACTURERS[manufacturer]
            zh["manufacturerSource"] = "local"
        elif zh.get("manufacturer"):
            zh["manufacturer"] = polish_machine_text(str(zh["manufacturer"]))

        for key in ("type", "subtype", "gear"):
            raw = str(record.get(key) or "")
            if raw in STAT_TERMS:
                zh[key] = STAT_TERMS[raw]
            elif raw in SUBTYPE_TERMS:
                zh[key] = SUBTYPE_TERMS[raw]
            elif zh.get(key):
                zh[key] = polish_machine_text(str(zh[key]))

        stats = record.get("stats") or {}
        stats_zh = stats.setdefault("zh", {})
        for key, value in stats.items():
            if key == "zh":
                continue
            raw = str(value)
            if raw in STAT_TERMS:
                stats_zh[key] = STAT_TERMS[raw]
            elif raw in SUBTYPE_TERMS:
                stats_zh[key] = SUBTYPE_TERMS[raw]
            elif raw in MANUFACTURERS:
                stats_zh[key] = MANUFACTURERS[raw]
            elif stats_zh.get(key):
                stats_zh[key] = polish_machine_text(str(stats_zh[key]))

        for tier in record.get("tiers") or []:
            for slot in tier.get("slots") or []:
                raw_slot = str(slot.get("name") or "")
                if raw_slot in SLOT_TERMS:
                    slot["nameZh"] = SLOT_TERMS[raw_slot]
                if slot.get("nameZh"):
                    slot["nameZh"] = polish_machine_text(str(slot["nameZh"]))
                for option in slot.get("options") or []:
                    raw_name = str(option.get("name") or "")
                    if raw_name in MATERIALS:
                        option["nameZh"] = MATERIALS[raw_name]
                        option["nameSource"] = "local"
                    elif option.get("nameZh"):
                        option["nameZh"] = polish_machine_text(str(option["nameZh"]))
                    raw_kind = str(option.get("kind") or "")
                    if raw_kind in STAT_TERMS:
                        option["kindZh"] = STAT_TERMS[raw_kind]

        for material in record.get("materials") or []:
            raw_name = str(material.get("name") or "")
            if raw_name in MATERIALS:
                material["nameZh"] = MATERIALS[raw_name]
                material["nameSource"] = "local"
            elif material.get("nameZh"):
                material["nameZh"] = polish_machine_text(str(material["nameZh"]))
            raw_kind = str(material.get("kind") or "")
            if raw_kind in STAT_TERMS:
                material["kindZh"] = STAT_TERMS[raw_kind]

        for source in record.get("sources") or []:
            if source.get("poolNameZh"):
                source["poolNameZh"] = polish_machine_text(str(source["poolNameZh"]))
            for mission in source.get("missions") or []:
                if mission.get("titleZh"):
                    mission["titleZh"] = polish_machine_text(str(mission["titleZh"]))
                faction = str(mission.get("faction") or "")
                if faction in MANUFACTURERS:
                    mission["factionZh"] = MANUFACTURERS[faction]

        translated_blob = " ".join(
            [
                str(zh.get("name") or ""),
                str(zh.get("manufacturer") or ""),
                " ".join(str(material.get("nameZh") or "") for material in record.get("materials") or []),
                str((record.get("flowcld") or {}).get("itemClassCn") or ""),
                " ".join(str(value) for value in (record.get("flowcld") or {}).get("rewardMissionTypesCn") or []),
            ]
        )
        search_base = polish_machine_text(str(record.get("search") or ""))
        record["search"] = f"{search_base} {translated_blob}".lower()


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply local bot localization to blueprint-index.json")
    parser.add_argument("--index", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "blueprint-index.json")
    parser.add_argument(
        "--bot-assets",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "work" / "sc-spectrum-qq-bot-handoff" / "sc-spectrum-qq-bot" / "assets",
    )
    parser.add_argument(
        "--local-names",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "local-polish-names.json",
    )
    parser.add_argument(
        "--flowcld-calibration",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "flowcld-blueprint-calibration.json",
    )
    args = parser.parse_args()
    index = load_json(args.index, {})
    local_names = load_names(args.bot_assets, args.local_names)
    flowcld_calibration = load_flowcld_calibration(args.flowcld_calibration)
    apply(index, local_names, flowcld_calibration, args.bot_assets)
    with args.index.open("w", encoding="utf-8") as handle:
        json.dump(index, handle, ensure_ascii=False, separators=(",", ":"))
    print(
        f"Applied {len(local_names)} local names and "
        f"{len(flowcld_calibration.get('by_id') or {})} FlowCLD calibration names to {args.index}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
