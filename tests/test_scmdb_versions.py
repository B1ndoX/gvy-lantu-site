from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scmdb_versions import is_live_version, select_latest_live_version, version_sort_key


class ScmdbVersionTests(unittest.TestCase):
    def test_selects_live_when_newer_ptu_is_first(self) -> None:
        selected = select_latest_live_version(
            [
                {"version": "4.10.0-ptu.12409360", "file": "merged-4.10.0-ptu.12409360.json"},
                {"version": "4.9.0-live.12344265", "file": "merged-4.9.0-live.12344265.json"},
            ]
        )
        self.assertEqual(selected["version"], "4.9.0-live.12344265")

    def test_selects_newest_of_multiple_live_releases(self) -> None:
        selected = select_latest_live_version(
            [
                {"version": "4.9.0-live.12344265", "file": "merged-4.9.0-live.12344265.json"},
                {"version": "4.10.0-live.12400001", "file": "merged-4.10.0-live.12400001.json"},
                {"version": "4.11.0-eptu.12500000", "file": "merged-4.11.0-eptu.12500000.json"},
            ]
        )
        self.assertEqual(selected["version"], "4.10.0-live.12400001")

    def test_rejects_test_channels_and_missing_live(self) -> None:
        self.assertFalse(is_live_version("4.10.0-ptu.12409360"))
        self.assertFalse(is_live_version("4.11.0-eptu.12500000"))
        self.assertFalse(is_live_version("4.12.0-tech-preview.12600000"))
        with self.assertRaisesRegex(RuntimeError, "no stable LIVE"):
            select_latest_live_version(
                [{"version": "4.10.0-ptu.12409360", "file": "merged-4.10.0-ptu.12409360.json"}]
            )

    def test_versions_are_compared_numerically(self) -> None:
        self.assertGreater(
            version_sort_key("4.10.0-live.12400001"),
            version_sort_key("4.9.0-live.12344265"),
        )

    def test_rejects_unsafe_manifest_filename(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "unsafe filename"):
            select_latest_live_version(
                [{"version": "4.9.0-live.12344265", "file": "../merged-live.json"}]
            )

    def test_live_token_must_be_a_channel_token(self) -> None:
        self.assertFalse(is_live_version("4.9.0-delivery.12344265"))
        self.assertFalse(is_live_version("4.12.0-live-tech-preview.12600000"))
        self.assertFalse(is_live_version("4.12.0-live-evocati.12600000"))
        self.assertTrue(is_live_version("4.9.0-live.12344265"))


if __name__ == "__main__":
    unittest.main()
