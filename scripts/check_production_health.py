#!/usr/bin/env python3
"""Verify that EdgeOne serves the exact validated local production snapshot."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from scmdb_versions import is_live_version


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://lantu.gvyvoyagers.vip"
MIN_BLUEPRINT_RECORDS = 1000
MIN_MINERAL_MATERIALS = 30
MIN_RELIABLE_MINERALS = 25
MIN_MINERAL_LOCATIONS = 100
MIN_LOCATION_SIGNALS = 100
ASSET_PATTERN = re.compile(r"(?:\./|/)?assets/(styles\.css|app\.js)\?v=([^\"'&]+)")
DATA_VERSION_PATTERN = re.compile(r'const DATA_VERSION = "(data-[0-9a-f]{16})";')
DATA_FILES = ("blueprint-index.json", "mineral-locations.json")


def canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def extract_asset_revisions(html: str) -> dict[str, str]:
    revisions = {name: revision for name, revision in ASSET_PATTERN.findall(html)}
    if set(revisions) != {"styles.css", "app.js"}:
        raise RuntimeError("page does not reference both fingerprinted production assets")
    return revisions


def build_data_revision(blueprint_bytes: bytes, mineral_bytes: bytes) -> str:
    digest = hashlib.sha256()
    for name, contents in zip(DATA_FILES, (blueprint_bytes, mineral_bytes)):
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(contents)
        digest.update(b"\0")
    return f"data-{digest.hexdigest()[:16]}"


def extract_data_revision(script: str) -> str:
    match = DATA_VERSION_PATTERN.search(script)
    if not match:
        raise RuntimeError("app.js does not contain a built data revision")
    return match.group(1)


def mineral_coverage(payload: dict[str, Any]) -> tuple[int, int, int, int]:
    materials = payload.get("materials") or {}
    reliable = 0
    locations = 0
    signals = 0
    for material in materials.values():
        material_locations = [
            location
            for group in (material.get("locations") or {}).values()
            for location in (group or [])
        ]
        if material.get("hasReliableLocations") and material_locations:
            reliable += 1
        locations += len(material_locations)
        signals += sum(1 for location in material_locations if location.get("signal"))
    return len(materials), reliable, locations, signals


def validate_production_snapshot(
    production_blueprints: dict[str, Any],
    local_blueprints: dict[str, Any],
    production_minerals: dict[str, Any],
    local_minerals: dict[str, Any],
) -> None:
    version = str(production_blueprints.get("version") or "")
    records = production_blueprints.get("records") or []
    if not is_live_version(version) or production_blueprints.get("releaseChannel") != "LIVE":
        raise RuntimeError(f"production blueprint channel is not stable LIVE: {version or 'missing'}")
    if len(records) < MIN_BLUEPRINT_RECORDS:
        raise RuntimeError(f"production blueprint record count is too low: {len(records)}")
    if production_blueprints.get("dataUpdatedAt") != local_blueprints.get("dataUpdatedAt"):
        raise RuntimeError("production blueprint update timestamp does not match the committed snapshot")
    if canonical_hash(production_blueprints) != canonical_hash(local_blueprints):
        raise RuntimeError("production blueprint data does not match the committed snapshot")

    coverage = mineral_coverage(production_minerals)
    minimums = (
        MIN_MINERAL_MATERIALS,
        MIN_RELIABLE_MINERALS,
        MIN_MINERAL_LOCATIONS,
        MIN_LOCATION_SIGNALS,
    )
    if any(actual < minimum for actual, minimum in zip(coverage, minimums)):
        raise RuntimeError(
            "production mineral coverage is too low: "
            f"{coverage[0]} materials, {coverage[1]} reliable, "
            f"{coverage[2]} locations, {coverage[3]} signals"
        )
    if canonical_hash(production_minerals) != canonical_hash(local_minerals):
        raise RuntimeError("production mineral data does not match the committed snapshot")


def cache_busted_url(base_url: str, path: str, nonce: str) -> str:
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("health", nonce))
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment)
    )


def versioned_url(base_url: str, path: str, revision: str) -> str:
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("v", revision))
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment)
    )


def fetch_bytes(url: str, attempts: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "GVY Lantu Production Health/1.0",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                if response.status != 200:
                    raise RuntimeError(f"unexpected HTTP status {response.status}")
                return response.read()
        except Exception as error:
            last_error = error
            if attempt < attempts:
                time.sleep(attempt * 2)
    raise RuntimeError(f"failed to fetch {url} after {attempts} attempts: {last_error}")


def fetch_json(url: str) -> dict[str, Any]:
    return json.loads(fetch_bytes(url).decode("utf-8-sig"))


def fetch_gzip_json(url: str) -> dict[str, Any]:
    try:
        return json.loads(gzip.decompress(fetch_bytes(url)).decode("utf-8-sig"))
    except (gzip.BadGzipFile, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RuntimeError(f"invalid compressed JSON from {url}: {error}") from error


def check_once(
    base_url: str,
    expected_assets: dict[str, str],
    expected_data_revision: str,
    local_blueprints: dict[str, Any],
    local_minerals: dict[str, Any],
) -> None:
    nonce = str(time.time_ns())
    html = fetch_bytes(cache_busted_url(base_url, "/", nonce)).decode("utf-8")
    production_assets = extract_asset_revisions(html)
    if production_assets != expected_assets:
        raise RuntimeError(
            f"EdgeOne is still serving a previous asset revision: {production_assets} != {expected_assets}"
        )

    production_app = b""
    for name, revision in expected_assets.items():
        asset = fetch_bytes(versioned_url(base_url, f"/assets/{name}", revision))
        if len(asset) < 100:
            raise RuntimeError(f"production asset is unexpectedly small: {name}")
        if name == "app.js":
            production_app = asset

    production_data_revision = extract_data_revision(production_app.decode("utf-8"))
    if production_data_revision != expected_data_revision:
        raise RuntimeError(
            "production app data revision does not match the committed data: "
            f"{production_data_revision} != {expected_data_revision}"
        )

    production_blueprints = fetch_gzip_json(
        versioned_url(base_url, "/data/blueprint-index.json.gz", production_data_revision)
    )
    production_minerals = fetch_gzip_json(
        versioned_url(base_url, "/data/mineral-locations.json.gz", production_data_revision)
    )
    validate_production_snapshot(
        production_blueprints,
        local_blueprints,
        production_minerals,
        local_minerals,
    )

    fallback_blueprints = fetch_json(
        versioned_url(base_url, "/data/blueprint-index.json", production_data_revision)
    )
    fallback_minerals = fetch_json(
        versioned_url(base_url, "/data/mineral-locations.json", production_data_revision)
    )
    validate_production_snapshot(
        fallback_blueprints,
        local_blueprints,
        fallback_minerals,
        local_minerals,
    )


def wait_for_production(base_url: str, timeout: int, interval: int) -> None:
    expected_assets = extract_asset_revisions((ROOT / "dist" / "index.html").read_text(encoding="utf-8"))
    blueprint_bytes = (ROOT / "data" / "blueprint-index.json").read_bytes()
    mineral_bytes = (ROOT / "data" / "mineral-locations.json").read_bytes()
    local_blueprints = json.loads(blueprint_bytes.decode("utf-8-sig"))
    local_minerals = json.loads(mineral_bytes.decode("utf-8-sig"))
    expected_data_revision = build_data_revision(blueprint_bytes, mineral_bytes)
    built_data_revision = extract_data_revision(
        (ROOT / "dist" / "assets" / "app.js").read_text(encoding="utf-8")
    )
    if built_data_revision != expected_data_revision:
        raise RuntimeError(
            "local production build embeds a stale data revision: "
            f"{built_data_revision} != {expected_data_revision}"
        )
    deadline = time.monotonic() + max(timeout, 0)
    last_error = "production check did not run"
    attempt = 0
    while True:
        attempt += 1
        try:
            check_once(
                base_url,
                expected_assets,
                expected_data_revision,
                local_blueprints,
                local_minerals,
            )
            print(
                "EdgeOne production verified: "
                f"{local_blueprints.get('version')} / "
                f"{len(local_blueprints.get('records') or [])} blueprints / "
                f"data {expected_data_revision} / assets {expected_assets}"
            )
            return
        except Exception as error:
            last_error = str(error)
            print(f"production check {attempt} pending: {last_error}", file=sys.stderr)
        if time.monotonic() >= deadline:
            raise RuntimeError(f"EdgeOne production did not become healthy before timeout: {last_error}")
        time.sleep(max(interval, 1))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the GVY blueprint production deployment.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=int, default=900, help="Maximum deployment wait in seconds.")
    parser.add_argument("--interval", type=int, default=15, help="Seconds between deployment checks.")
    args = parser.parse_args()
    wait_for_production(args.base_url, args.timeout, args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
