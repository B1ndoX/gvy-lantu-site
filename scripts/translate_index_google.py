#!/usr/bin/env python3
"""Translate the generated blueprint index to Simplified Chinese with Google Translate."""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API_URL = "https://translate.googleapis.com/translate_a/single"
SKIP_VALUES = {"", "unknown", "mission", "resource", "item", "all"}


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)


def is_translatable(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if text.lower() in SKIP_VALUES:
        return False
    if len(text) < 2:
        return False
    return any("A" <= char <= "Z" or "a" <= char <= "z" for char in text)


def add_value(values: set[str], value: Any) -> None:
    if is_translatable(value):
        values.add(value.strip())


def collect_strings(index: dict[str, Any]) -> list[str]:
    values: set[str] = set()
    for record in index.get("records", []):
        for key in ("name", "manufacturer", "type", "subtype", "gear"):
            add_value(values, record.get(key))
        stats = record.get("stats") or {}
        for key in ("itemType", "attachType", "attachSubType", "manufacturerCode", "tags"):
            add_value(values, stats.get(key))
        for tier in record.get("tiers") or []:
            for slot in tier.get("slots") or []:
                add_value(values, slot.get("name"))
                for option in slot.get("options") or []:
                    add_value(values, option.get("kind"))
                    add_value(values, option.get("name"))
        for material in record.get("materials") or []:
            add_value(values, material.get("kind"))
            add_value(values, material.get("name"))
        for source in record.get("sources") or []:
            add_value(values, source.get("poolName"))
            add_value(values, source.get("poolSource"))
            for mission in source.get("missions") or []:
                for key in ("title", "category", "faction", "trigger"):
                    add_value(values, mission.get(key))
    return sorted(values, key=lambda item: (len(item), item.lower()))


def parse_translation(payload: Any) -> str:
    parts = []
    for segment in payload[0] or []:
        if segment and segment[0]:
            parts.append(segment[0])
    return "".join(parts).strip()


def google_translate(text: str, retries: int = 3) -> str:
    params = urllib.parse.urlencode(
        {
            "client": "gtx",
            "sl": "en",
            "tl": "zh-CN",
            "dt": "t",
            "q": text,
        }
    )
    request = urllib.request.Request(f"{API_URL}?{params}", headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return parse_translation(json.loads(response.read().decode("utf-8")))
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(0.8 + attempt * 0.6)
    return text


def google_translate_batch(texts: list[str]) -> list[str]:
    joined = "\n".join(texts)
    translated = google_translate(joined)
    lines = [line.strip() for line in translated.splitlines()]
    if len(lines) == len(texts):
        return lines
    return [google_translate(text) for text in texts]


def chunk_missing(strings: list[str], batch_size: int = 18, max_chars: int = 1350) -> list[list[str]]:
    chunks: list[list[str]] = []
    current: list[str] = []
    current_chars = 0
    for text in strings:
        projected = current_chars + len(text) + 1
        if current and (len(current) >= batch_size or projected > max_chars):
            chunks.append(current)
            current = []
            current_chars = 0
        current.append(text)
        current_chars += len(text) + 1
    if current:
        chunks.append(current)
    return chunks


def translate_missing(strings: list[str], cache: dict[str, str], limit: int | None, cache_path: Path) -> int:
    missing = [text for text in strings if text not in cache]
    if limit is not None:
        missing = missing[:limit]
    translated_count = 0
    chunks = chunk_missing(missing)
    for chunk_index, chunk in enumerate(chunks, start=1):
        translations = google_translate_batch(chunk)
        for text, translated in zip(chunk, translations):
            cache[text] = translated or text
            translated_count += 1
        if chunk_index % 5 == 0 or chunk_index == len(chunks):
            save_json(cache_path, cache)
            print(f"translated {translated_count}/{len(missing)}", flush=True)
        time.sleep(0.15)
    return len(missing)


def t(cache: dict[str, str], value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return cache.get(value.strip(), value.strip())


def apply_translations(index: dict[str, Any], cache: dict[str, str]) -> None:
    index["translation"] = {
        "provider": "Google Translate",
        "target": "zh-CN",
        "cacheSize": len(cache),
    }
    for record in index.get("records", []):
        record["zh"] = {
            "name": t(cache, record.get("name")),
            "manufacturer": t(cache, record.get("manufacturer")),
            "type": t(cache, record.get("type")),
            "subtype": t(cache, record.get("subtype")),
            "gear": t(cache, record.get("gear")),
        }
        stats = record.get("stats") or {}
        stats["zh"] = {
            "itemType": t(cache, stats.get("itemType")),
            "attachType": t(cache, stats.get("attachType")),
            "attachSubType": t(cache, stats.get("attachSubType")),
            "manufacturerCode": t(cache, stats.get("manufacturerCode")),
            "tags": t(cache, stats.get("tags")),
        }
        for tier in record.get("tiers") or []:
            for slot in tier.get("slots") or []:
                slot["nameZh"] = t(cache, slot.get("name"))
                for option in slot.get("options") or []:
                    option["kindZh"] = t(cache, option.get("kind"))
                    option["nameZh"] = t(cache, option.get("name"))
        for material in record.get("materials") or []:
            material["kindZh"] = t(cache, material.get("kind"))
            material["nameZh"] = t(cache, material.get("name"))
        for source in record.get("sources") or []:
            source["poolNameZh"] = t(cache, source.get("poolName"))
            source["poolSourceZh"] = t(cache, source.get("poolSource"))
            for mission in source.get("missions") or []:
                mission["titleZh"] = t(cache, mission.get("title"))
                mission["categoryZh"] = t(cache, mission.get("category"))
                mission["factionZh"] = t(cache, mission.get("faction"))
                mission["triggerZh"] = t(cache, mission.get("trigger"))
        translated_blob = " ".join(
            [
                record["zh"]["name"],
                record["zh"]["manufacturer"],
                record["zh"]["type"],
                record["zh"]["subtype"],
                " ".join(material.get("nameZh", "") for material in record.get("materials") or []),
                " ".join(source.get("poolNameZh", "") for source in record.get("sources") or []),
                " ".join(mission.get("titleZh", "") for source in record.get("sources") or [] for mission in source.get("missions", [])),
            ]
        )
        record["search"] = f"{record.get('search', '')} {translated_blob}".lower()


def main() -> int:
    parser = argparse.ArgumentParser(description="Translate blueprint-index.json with Google Translate")
    parser.add_argument("--index", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "blueprint-index.json")
    parser.add_argument("--cache", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "google-translate-cache.json")
    parser.add_argument("--limit", type=int, help="Translate only N missing strings, for testing")
    args = parser.parse_args()

    index = load_json(args.index, {})
    cache = load_json(args.cache, {})
    strings = collect_strings(index)
    print(f"unique translatable strings: {len(strings)}; cached: {len(cache)}")
    count = translate_missing(strings, cache, args.limit, args.cache)
    apply_translations(index, cache)
    save_json(args.cache, cache)
    with args.index.open("w", encoding="utf-8") as handle:
        json.dump(index, handle, ensure_ascii=False, separators=(",", ":"))
    print(f"translated missing: {count}; wrote {args.index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
