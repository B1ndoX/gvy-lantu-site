from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from refresh_mineral_locations import comparable, ore_key, validate_candidate, zh_name  # noqa: E402


GROUPS = ("starSystems", "planets", "moons", "pointsOfInterest", "lagrangePoints")


def location(index: int, with_signal: bool = True) -> dict:
    entry = {
        "id": index,
        "zh": f"地点 {index}",
        "en": f"Location {index}",
        "systemZh": "斯坦顿",
        "systemEn": "Stanton",
        "parentZh": "",
        "parentEn": "",
    }
    if with_signal:
        entry["signal"] = {"base": 3000, "maxCluster": 5, "values": [3000, 6000]}
    return entry


def payload(*, material_count: int = 37, locations_per_material: int = 4, with_signals: bool = True) -> dict:
    materials = {}
    next_id = 1
    for material_index in range(material_count):
        groups = {name: [] for name in GROUPS}
        for entry_index in range(locations_per_material):
            groups[GROUPS[entry_index % len(GROUPS)]].append(location(next_id, with_signals))
            next_id += 1
        materials[f"Material {material_index}"] = {
            "locations": groups,
            "hasReliableLocations": locations_per_material > 0,
        }
    return {
        "metadata": {"retrievedAt": "2026-08-18T01:00:00+00:00"},
        "materials": materials,
    }


class MineralLocationRefreshTests(unittest.TestCase):
    def test_accepts_full_location_and_signal_coverage(self) -> None:
        current = payload()
        counts = validate_candidate(copy.deepcopy(current), current)
        self.assertEqual(counts, (37, 37, 148, 148))

    def test_rejects_large_location_coverage_drop(self) -> None:
        current = payload(locations_per_material=8)
        candidate = payload(locations_per_material=3)
        with self.assertRaisesRegex(RuntimeError, "location coverage dropped"):
            validate_candidate(candidate, current)

    def test_rejects_large_signal_location_drop(self) -> None:
        current = payload(locations_per_material=4, with_signals=True)
        candidate = payload(locations_per_material=4, with_signals=False)
        with self.assertRaisesRegex(RuntimeError, "signal location coverage dropped"):
            validate_candidate(candidate, current)

    def test_retrieval_timestamp_does_not_create_a_false_update(self) -> None:
        current = payload()
        candidate = copy.deepcopy(current)
        candidate["metadata"]["retrievedAt"] = "2026-08-18T02:00:00+00:00"
        self.assertEqual(comparable(candidate), comparable(current))

    def test_official_location_name_has_priority(self) -> None:
        self.assertEqual(zh_name("Yela", {"Yela": "官方耶拉"}), "官方耶拉")

    def test_pressurized_ice_uses_source_signal_key(self) -> None:
        self.assertEqual(ore_key("Pressurized Ice", "Ice (Raw)"), "ICE")


if __name__ == "__main__":
    unittest.main()
