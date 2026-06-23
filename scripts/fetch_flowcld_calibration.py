#!/usr/bin/env python3
"""Fetch compact Chinese blueprint calibration data from FlowCLD."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ENDPOINT = "https://flowcld.xyz/app-api/product/blueprint/page"


def fetch_page(page_num: int, page_size: int, timeout: float) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "pageNo": page_num,
            "pageSize": page_size,
            "language": "CN",
        }
    )
    request = urllib.request.Request(
        f"{ENDPOINT}?{params}",
        headers={
            "Accept": "application/json",
            "User-Agent": "curl/8.7.1",
        },
    )
    url = f"{ENDPOINT}?{params}"
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        result = subprocess.run(
            ["curl", "-L", "-sS", "--fail", url],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return json.loads(result.stdout)


def compact_scalar(value: Any) -> str | int | bool | None:
    if value is None:
        return None
    if isinstance(value, (bool, int)):
        return value
    text = str(value).strip()
    return text or None


def compact_list(value: Any) -> list[str]:
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


def compact_item(item: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "recordGuid": item.get("recordGuid"),
        "internalName": item.get("internalName"),
        "blueprintName": item.get("blueprintName"),
        "blueprintNameCn": item.get("blueprintNameCn"),
        "categoryName": item.get("categoryName"),
        "subcategory": item.get("subcategory"),
        "manufacturer": item.get("manufacturer"),
        "grade": item.get("grade"),
        "itemClass": item.get("itemClass"),
        "isReward": item.get("isReward"),
        "rewardMissionCount": item.get("rewardMissionCount"),
        "craftTimeSeconds": item.get("craftTimeSeconds"),
        "rewardMissionTypes": compact_list(item.get("rewardMissionTypes")),
        "rewardMissionTypesCn": compact_list(item.get("rewardMissionTypesCn")),
    }
    compacted: dict[str, Any] = {}
    for key, value in fields.items():
        if isinstance(value, list):
            if value:
                compacted[key] = value
            continue
        scalar = compact_scalar(value)
        if scalar is not None:
            compacted[key] = scalar
    return compacted


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch FlowCLD blueprint Chinese-name calibration data")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "flowcld-blueprint-calibration.json")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-pages", type=int, default=0, help="0 means fetch all pages reported by the endpoint")
    args = parser.parse_args()

    page_num = 1
    total = None
    items: list[dict[str, str]] = []

    while True:
        payload = fetch_page(page_num, args.page_size, args.timeout)
        if payload.get("code") != 0:
            raise RuntimeError(f"FlowCLD returned code={payload.get('code')}: {payload.get('msg')}")
        data = payload.get("data") or {}
        page_items = data.get("list") or []
        if total is None:
            total = int(data.get("total") or 0)

        for item in page_items:
            compact = compact_item(item)
            if compact:
                items.append(compact)

        fetched = page_num * args.page_size
        if not page_items or fetched >= total:
            break
        if args.max_pages and page_num >= args.max_pages:
            break

        page_num += 1
        time.sleep(args.delay)

    output = {
        "source": "https://flowcld.xyz/tools/blueprint",
        "endpoint": ENDPOINT,
        "language": "CN",
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "totalReported": total or 0,
        "itemCount": len(items),
        "localizedCount": sum(1 for item in items if item.get("blueprintNameCn")),
        "items": items,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)

    print(
        f"Saved {len(items)} FlowCLD records "
        f"({output['localizedCount']} localized names) from {total or 0} listed records to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
