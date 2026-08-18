from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_data import build_index  # noqa: E402


class BuildDataTests(unittest.TestCase):
    def test_preserves_quality_modifiers_and_derives_dismantle_outputs(self) -> None:
        crafting = {
            "version": "4.9.0-live.12344265",
            "dismantle": {
                "efficiency": 0.5,
                "dismantleTimeSeconds": 15,
                "blacklistedResources": [{"name": "Quantainium"}],
                "blacklistedEntityClasses": [{"name": "Janalite"}],
            },
            "blueprints": [
                {
                    "guid": "test-blueprint",
                    "productName": "Test Rifle",
                    "gear": "fpsgear",
                    "type": "weapons",
                    "subtype": "rifle",
                    "tiers": [
                        {
                            "craftTimeSeconds": 60,
                            "slots": [
                                {
                                    "name": "Frame",
                                    "options": [
                                        {"type": "resource", "resourceName": "Iron", "quantity": 6, "minQuality": 500},
                                        {"type": "resource", "resourceName": "Quantainium", "quantity": 2, "minQuality": 0},
                                        {"type": "item", "itemName": "Hadanite", "quantity": 1, "minQuality": 0},
                                        {"type": "item", "itemName": "Janalite", "quantity": 2, "minQuality": 0},
                                    ],
                                    "modifiers": [
                                        {
                                            "propertyKey": "weapon_damage",
                                            "propertyName": "Impact Force",
                                            "startQuality": 0,
                                            "endQuality": 1000,
                                            "modifierAtStart": 0.9,
                                            "modifierAtEnd": 1.1,
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        index = build_index({"blueprintPools": {}, "factions": {}, "contracts": []}, crafting, {"items": []})
        record = index["records"][0]

        self.assertEqual(record["tiers"][0]["slots"][0]["modifiers"][0]["propertyKey"], "weapon_damage")
        self.assertEqual(record["dismantle"]["efficiency"], 0.5)
        self.assertEqual(record["dismantle"]["timeSeconds"], 15)
        self.assertEqual(
            record["dismantle"]["outputs"],
            [
                {"name": "Hadanite", "kind": "item", "quantity": 0.5},
                {"name": "Iron", "kind": "resource", "quantity": 3.0},
            ],
        )


if __name__ == "__main__":
    unittest.main()
