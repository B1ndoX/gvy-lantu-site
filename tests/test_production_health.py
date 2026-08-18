from __future__ import annotations

import sys
import gzip
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_production_health import extract_asset_revisions, fetch_gzip_json, validate_production_snapshot
from write_refresh_heartbeat import heartbeat_payload


class ProductionHealthTests(unittest.TestCase):
    def blueprints(self, version: str = "4.9.0-live.12344265") -> dict:
        return {
            "version": version,
            "releaseChannel": "LIVE",
            "dataUpdatedAt": "2026-08-18T06:59:26Z",
            "records": [{"id": f"record-{index}"} for index in range(1000)],
        }

    def minerals(self) -> dict:
        materials = {}
        for material_index in range(30):
            materials[f"Material {material_index}"] = {
                "hasReliableLocations": material_index < 25,
                "locations": {
                    "moons": [
                        {"id": material_index * 4 + offset, "signal": {"base": 3185}}
                        for offset in range(4)
                    ]
                },
            }
        return {"materials": materials}

    def test_extracts_both_fingerprinted_assets(self) -> None:
        html = (
            '<link rel="stylesheet" href="./assets/styles.css?v=abc123">'
            '<script src="./assets/app.js?v=def456"></script>'
        )
        self.assertEqual(
            extract_asset_revisions(html),
            {"styles.css": "abc123", "app.js": "def456"},
        )

    def test_accepts_matching_production_snapshot(self) -> None:
        blueprints = self.blueprints()
        minerals = self.minerals()
        validate_production_snapshot(blueprints, blueprints, minerals, minerals)

    def test_rejects_test_channel_snapshot(self) -> None:
        production = self.blueprints("4.10.0-ptu.12409360")
        local = self.blueprints()
        minerals = self.minerals()
        with self.assertRaisesRegex(RuntimeError, "not stable LIVE"):
            validate_production_snapshot(production, local, minerals, minerals)

    def test_rejects_different_production_data(self) -> None:
        production = self.blueprints()
        local = self.blueprints()
        production["records"][0]["id"] = "wrong"
        minerals = self.minerals()
        with self.assertRaisesRegex(RuntimeError, "does not match"):
            validate_production_snapshot(production, local, minerals, minerals)

    def test_builds_utc_maintenance_heartbeat(self) -> None:
        now = datetime(2026, 8, 18, 8, 0, tzinfo=timezone.utc)
        payload = heartbeat_payload("123", "abc", "success", "success", "success", now)
        self.assertEqual(payload["lastMaintenanceAt"], "2026-08-18T08:00:00Z")
        self.assertEqual(payload["blueprintRefresh"], "success")
        self.assertEqual(payload["mineralLocationsRefresh"], "success")

    def test_reads_compressed_production_json(self) -> None:
        import check_production_health

        original_fetch = check_production_health.fetch_bytes
        check_production_health.fetch_bytes = lambda _url: gzip.compress(
            json.dumps({"status": "ok"}).encode("utf-8")
        )
        try:
            self.assertEqual(fetch_gzip_json("https://example.invalid/data.json.gz"), {"status": "ok"})
        finally:
            check_production_health.fetch_bytes = original_fetch


if __name__ == "__main__":
    unittest.main()
