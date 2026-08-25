from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from refresh_blueprint_data import validate_flowcld_calibration, validate_index


class RefreshValidationTests(unittest.TestCase):
    def write_index(self, payload: dict) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "blueprint-index.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def valid_index(self) -> dict:
        records = [
            {
                "id": f"example-{index}",
                "name": f"Example {index}",
                "sourceCount": 0,
                "sources": [],
            }
            for index in range(1000)
        ]
        return {
            "version": "4.9.0-live.12344265",
            "releaseChannel": "LIVE",
            "dataUpdatedAt": "2026-08-12T01:44:08Z",
            "records": records,
            "counts": {"blueprints": len(records), "categories": {"other": len(records)}},
            "localization": {"starCitizenLocalizationCount": 7000},
        }

    def test_accepts_live_index_with_timestamp(self) -> None:
        validate_index(self.write_index(self.valid_index()), "4.9.0-live.12344265")

    def test_rejects_missing_update_timestamp(self) -> None:
        payload = self.valid_index()
        payload.pop("dataUpdatedAt")
        with self.assertRaisesRegex(RuntimeError, "dataUpdatedAt"):
            validate_index(self.write_index(payload), "4.9.0-live.12344265")

    def test_rejects_non_live_index(self) -> None:
        payload = self.valid_index()
        payload["version"] = "4.10.0-ptu.12409360"
        with self.assertRaisesRegex(RuntimeError, "not a stable LIVE"):
            validate_index(self.write_index(payload), "4.10.0-ptu.12409360")

    def test_rejects_duplicate_record_ids(self) -> None:
        payload = self.valid_index()
        payload["records"][1]["id"] = payload["records"][0]["id"]
        with self.assertRaisesRegex(RuntimeError, "duplicate record ids"):
            validate_index(self.write_index(payload), payload["version"])

    def test_rejects_low_official_localization_coverage(self) -> None:
        payload = self.valid_index()
        payload["localization"]["starCitizenLocalizationCount"] = 12
        with self.assertRaisesRegex(RuntimeError, "coverage is unexpectedly low"):
            validate_index(self.write_index(payload), payload["version"])

    def test_accepts_consistent_quality_metadata(self) -> None:
        payload = self.valid_index()
        payload["records"][0]["tiers"] = [{"slots": [{"modifiers": [{"propertyKey": "weapon_damage"}]}]}]
        payload["records"][0]["qualityStats"] = [{"value": 10}]
        payload["qualityEffects"] = {
            "version": payload["version"].upper(),
            "recordsWithModifiers": 1,
            "matchedItems": 1,
            "recordsWithBaseStats": 1,
        }
        validate_index(self.write_index(payload), payload["version"])

    def test_rejects_cross_version_quality_metadata(self) -> None:
        payload = self.valid_index()
        payload["qualityEffects"] = {
            "version": "4.9.1-LIVE.12399999",
            "recordsWithModifiers": 0,
            "matchedItems": 0,
            "recordsWithBaseStats": 0,
        }
        with self.assertRaisesRegex(RuntimeError, "do not match blueprint version"):
            validate_index(self.write_index(payload), payload["version"])

    def test_rejects_quality_metadata_that_disagrees_with_records(self) -> None:
        payload = self.valid_index()
        payload["qualityEffects"] = {
            "version": payload["version"],
            "recordsWithModifiers": 1,
            "matchedItems": 1,
            "recordsWithBaseStats": 1,
        }
        with self.assertRaisesRegex(RuntimeError, "does not match blueprint records"):
            validate_index(self.write_index(payload), payload["version"])

    def test_rejects_incomplete_flowcld_calibration(self) -> None:
        path = self.write_index({"itemCount": 40, "localizedCount": 20, "items": []})
        with self.assertRaisesRegex(RuntimeError, "coverage is too low"):
            validate_flowcld_calibration(path)

    def test_accepts_complete_flowcld_calibration(self) -> None:
        path = self.write_index({"itemCount": 1594, "localizedCount": 1557, "items": []})
        validate_flowcld_calibration(path)


if __name__ == "__main__":
    unittest.main()
