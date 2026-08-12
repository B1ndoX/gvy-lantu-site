from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from refresh_blueprint_data import validate_index


class RefreshValidationTests(unittest.TestCase):
    def write_index(self, payload: dict) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "blueprint-index.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def valid_index(self) -> dict:
        return {
            "version": "4.9.0-live.12344265",
            "releaseChannel": "LIVE",
            "dataUpdatedAt": "2026-08-12T01:44:08Z",
            "records": [{"id": "example"}],
            "counts": {"blueprints": 1},
            "localization": {"starCitizenLocalizationCount": 1},
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


if __name__ == "__main__":
    unittest.main()
