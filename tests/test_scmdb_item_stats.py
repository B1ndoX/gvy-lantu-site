from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from scmdb_item_stats import attach_item_stats, validate_item_stats, weapon_metrics
from enrich_quality_stats import enrich_index, validate_coverage

VERSION = "4.10.2-live.12913470"


class ItemStatTests(unittest.TestCase):
    def fixture(self):
        record = {"id": "bp", "name": "Shotgun", "productEntityClass": "entity",
                  "tiers": [{"slots": [{"modifiers": [{"propertyKey": "weapon_damage"}, {"propertyKey": "weapon_firerate"}]}]}]}
        index = {"version": VERSION, "records": [record]}
        data = {"version": VERSION, "items": [{"entityClass": "entity", "name": "Shotgun", "mass": 2.37,
                                               "fireModesIndex": 0, "ammoIndex": 0, "magazineIndex": 0}],
                "fireModesPools": [[{"name": "Single", "type": "single", "fireRate": 90, "pelletCount": 8, "damageMultiplier": 1}]],
                "ammoPools": [{"damage": {"physical": 11, "energy": 0}, "speed": 225}],
                "magazinePools": [{"ammoCount": 12}]}
        return index, data

    def test_exact_entity_and_shared_zero_index_with_pellets_and_dps(self):
        index, data = self.fixture()
        before = copy.deepcopy(data)
        attach_item_stats(index, data)
        validate_item_stats(index)
        metrics = {m["id"]: m for m in index["records"][0]["qualityStats"]}
        self.assertEqual(metrics["alpha_damage"]["value"], 88)
        self.assertEqual(metrics["alpha_damage"]["label"], "整发伤害")
        self.assertEqual(metrics["pellet_damage"]["value"], 11)
        self.assertEqual(metrics["burst_dps"]["value"], 132)
        self.assertEqual(metrics["burst_dps"]["properties"], ["weapon_damage", "weapon_firerate"])
        self.assertEqual(index["itemStats"]["matchedItems"], 1)
        self.assertNotIn("Single", " ".join(index["records"][0]["baseStatNotes"]))
        self.assertIn("单发", " ".join(index["records"][0]["baseStatNotes"]))
        self.assertEqual(data, before)

    def test_name_only_or_missing_entity_never_authorizes_base_stats(self):
        index, data = self.fixture()
        index["records"][0]["productEntityClass"] = "different-entity"
        attach_item_stats(index, data)
        self.assertNotIn("qualityStats", index["records"][0])
        self.assertEqual(index["itemStats"]["matchedItems"], 0)

    def test_first_schema_migration_rejects_a_truncated_entity_export(self):
        index, data = self.fixture()
        index["records"] = [{**index["records"][0], "id": str(i)} for i in range(1000)]
        data["items"] = []
        with self.assertRaisesRegex(RuntimeError, "entity matching coverage"):
            attach_item_stats(index, data)

    def test_cross_build_missing_version_and_invalid_shared_indexes_fail_closed(self):
        for bad in ("4.10.2-live.12881860", None):
            index, data = self.fixture()
            data["version"] = bad
            with self.assertRaisesRegex(RuntimeError, "version mismatch"):
                attach_item_stats(index, data)
        for bad in (-1, True, 3, "0", 0.1):
            index, data = self.fixture()
            data["items"][0]["fireModesIndex"] = bad
            with self.assertRaisesRegex(RuntimeError, "pool reference"):
                attach_item_stats(index, data)

    def test_multiple_modes_have_unique_metrics_and_unsafe_modes_have_no_invented_dps(self):
        index, data = self.fixture()
        data["fireModesPools"][0].extend([
            {"name": "Burst", "type": "burst", "fireRate": 700, "shotCount": 3, "cooldownTime": 0.1},
            {"name": "Charge", "type": "charged", "chargeTime": 0.5},
            {"name": "Sequence", "type": "sequence", "sequenceEntries": [{"type": "single", "fireRate": 250}]},
        ])
        attach_item_stats(index, data)
        validate_item_stats(index)
        ids = {m["id"] for m in index["records"][0]["baseStats"]}
        self.assertIn("burst_dps_0", ids)
        self.assertFalse(any(f"burst_dps_{n}" in ids for n in (1, 2, 3)))
        self.assertIn("连发模式未估算", " ".join(index["records"][0]["baseStatNotes"]))

    def test_only_verified_single_looping_sequence_is_simplified(self):
        _, data = self.fixture()
        single = {**data["fireModesPools"][0][0], "delay": 90, "delayUnit": "RPM", "repetitions": 1}
        data["fireModesPools"][0] = [{"name": "Single", "type": "sequence", "sequenceMode": "Looping", "sequenceEntries": [single]}]
        metrics, _ = weapon_metrics(data["items"][0], data)
        self.assertEqual(next(m["value"] for m in metrics if m["id"] == "burst_dps"), 132)
        single["delay"] = 100
        metrics, _ = weapon_metrics(data["items"][0], data)
        self.assertFalse(any(m["id"] == "burst_dps" for m in metrics))

    def test_explosive_ammo_does_not_publish_tiny_contact_damage_as_total_damage(self):
        index, data = self.fixture()
        data["ammoPools"][0].update(damage={"energy": 0.0001}, detonationDamage={"distortion": 27})
        attach_item_stats(index, data)
        ids = {m["id"] for m in index["records"][0]["baseStats"]}
        self.assertNotIn("alpha_damage", ids)
        self.assertNotIn("burst_dps", ids)
        self.assertIn("fire_rate", ids)
        self.assertIn("包含爆炸伤害", " ".join(index["records"][0]["baseStatNotes"]))

    def test_fallback_never_erases_or_overwrites_primary_and_version_mismatch_is_atomic(self):
        index, data = self.fixture()
        attach_item_stats(index, data)
        before = copy.deepcopy(index)
        with self.assertRaises(RuntimeError):
            enrich_index(index, [], "4.10.1-live.1")
        self.assertEqual(index, before)
        enrich_index(index, [{"name": "Shotgun", "stdItem": {"Weapon": {"Damage": {"AlphaTotal": 999, "Burst": 999}, "RateOfFire": 999}}}], VERSION)
        self.assertEqual(index["records"][0]["qualityStats"], before["records"][0]["qualityStats"])
        enrich_index(index, [], VERSION)
        self.assertEqual(index["records"][0]["qualityStats"], before["records"][0]["qualityStats"])

    def test_primary_coverage_cannot_hide_a_truncated_optional_feed(self):
        index, data = self.fixture()
        attach_item_stats(index, data)
        coverage = enrich_index(index, [], VERSION)
        # Scale the fixture so integer coverage thresholds are meaningful.
        coverage.update(recordsWithModifiers=100, matchedItems=100, recordsWithBaseStats=100)
        index["records"] = index["records"] * 100
        with self.assertRaisesRegex(RuntimeError, "item matching coverage"):
            validate_coverage(index, coverage)

    def test_shield_and_temperature_zero_values_keep_properties_and_units(self):
        index, data = self.fixture()
        index["records"][0]["tiers"][0]["slots"][0]["modifiers"] = [{"propertyKey": k} for k in ("shield_maxhealth", "armor_temperaturemin")]
        data["items"][0].update(shieldHealth=7200, temperatureResistance={"min": 0, "max": 60})
        attach_item_stats(index, data)
        metrics = {m["id"]: m for m in index["records"][0]["qualityStats"]}
        self.assertEqual(metrics["shield_capacity"]["value"], 7200)
        self.assertEqual(metrics["temperature_min"]["value"], 0)
        self.assertEqual(metrics["temperature_min"]["unit"], "°C")

    def test_validation_rejects_duplicate_metric_and_nonfinite_value(self):
        index, data = self.fixture()
        attach_item_stats(index, data)
        index["records"][0]["baseStats"].append(index["records"][0]["baseStats"][0])
        with self.assertRaises(RuntimeError):
            validate_item_stats(index)
        index["records"][0]["baseStats"].pop()
        index["records"][0]["baseStats"][0]["value"] = float("nan")
        with self.assertRaises(RuntimeError):
            validate_item_stats(index)


if __name__ == "__main__":
    unittest.main()
