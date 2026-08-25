from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from enrich_quality_stats import enrich_index, source_sha_from_commit, validate_coverage  # noqa: E402


class EnrichQualityStatsTests(unittest.TestCase):
    def test_adds_compact_weapon_metrics_for_matching_live_version(self) -> None:
        index = {
            "version": "4.9.0-live.12344265",
            "records": [
                {
                    "name": "Example Cannon",
                    "tiers": [
                        {
                            "slots": [
                                {
                                    "modifiers": [
                                        {"propertyKey": "weapon_damage"},
                                        {"propertyKey": "weapon_firerate"},
                                    ]
                                }
                            ]
                        }
                    ],
                }
            ],
        }
        items = [
            {
                "name": "Example Cannon",
                "type": "WeaponGun",
                "stdItem": {
                    "Weapon": {
                        "RateOfFire": 250,
                        "Damage": {"AlphaTotal": 73, "Burst": 304.1},
                    }
                },
            }
        ]

        coverage = enrich_index(index, items, "4.9.0-LIVE.12344265")

        self.assertEqual(coverage["recordsWithModifiers"], 1)
        self.assertEqual(coverage["recordsWithBaseStats"], 1)
        metrics = {metric["id"]: metric for metric in index["records"][0]["qualityStats"]}
        self.assertEqual(metrics["alpha_damage"]["value"], 73)
        self.assertEqual(metrics["burst_dps"]["properties"], ["weapon_damage", "weapon_firerate"])
        self.assertEqual(metrics["fire_rate"]["value"], 250)

    def test_rejects_cross_version_stats(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "version mismatch"):
            enrich_index({"version": "4.9.0-live.12344265", "records": []}, [], "4.9.1-LIVE.12399999")

    def test_rejects_truncated_community_coverage(self) -> None:
        index = {"records": [{} for _ in range(100)]}
        with self.assertRaisesRegex(RuntimeError, "modifier coverage"):
            validate_coverage(
                index,
                {"recordsWithModifiers": 50, "matchedItems": 50, "recordsWithBaseStats": 50},
            )

    def test_requires_an_immutable_community_commit(self) -> None:
        self.assertEqual(source_sha_from_commit({"sha": "a" * 40}), "a" * 40)
        with self.assertRaisesRegex(RuntimeError, "immutable commit SHA"):
            source_sha_from_commit({"sha": "master"})


if __name__ == "__main__":
    unittest.main()
