from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from scmdb_mining import build_mining_materials, cluster_counts, validate_mining
from refresh_mineral_locations import build_candidate, comparable, payload_counts, refresh, validate_candidate

VERSION = "4.10.2-live.12913470"


def fixture():
    elements = {str(i): {"name": f"Material {i}", "resourceType": f"resource-{i}",
                         "scanSignature": 3000 + i, "groundScanSignature": 4000, "fpsScanSignature": 3000} for i in range(36)}
    compositions = {str(i): {"name": f"Deposit {i}", "parts": [{"elementGuid": str(i % 36),
                    "probability": 1, "minPercent": 10, "maxPercent": 100}]} for i in range(40)}
    locations = [{"presetFile": f"planet-{i}", "locationName": f"Planet {i}", "system": "Stanton", "locationType": "planet",
                  "groups": [{"groupName": "SpaceShip_Mineables", "groupProbability": 1,
                              "deposits": [{"relativeProbability": 1, "compositionGuid": key, "clusteringPresetGuid": "cluster"} for key in compositions]}]} for i in range(36)]
    return {"version": VERSION, "mineableElements": elements, "compositions": compositions,
            "clusteringPresets": {"cluster": {"probabilityOfClustering": 100,
                                   "params": [{"minSize": 4, "maxSize": 6, "relativeProbability": 1}]}},
            "locations": locations, "meta": {"totalElements": 36, "totalCompositions": 40, "totalClusteringPresets": 1, "totalLocations": 36}}


def normalized(source=None):
    data = source or fixture()
    materials = build_mining_materials(data, [f"Material {i}" for i in range(36)], {})
    return {"metadata": {"schemaVersion": 2, "sourceVersion": VERSION, "signalSourceVersion": VERSION, "retrievedAt": "2026-10-18T00:00:00Z"}, "materials": materials}


class MiningTests(unittest.TestCase):
    def test_same_live_schema_and_counts(self):
        validate_mining(fixture(), VERSION)
        current = normalized()
        self.assertEqual(validate_candidate(current, current), (36, 36, 1332, 1296))

    def test_exact_version_and_stable_channel(self):
        for version in ("4.10.2-live.1", "4.10.2-ptu.12913470", ""):
            data = fixture()
            data["version"] = version
            with self.assertRaisesRegex(RuntimeError, "exact blueprint LIVE"):
                validate_mining(data, VERSION)
        with self.assertRaises(RuntimeError):
            validate_mining(fixture(), "4.10.2-ptu.12913470")

    def test_count_refs_numbers_and_cluster_bounds_fail_closed(self):
        mutations = [lambda p: p["meta"].update(totalElements=1),
                     lambda p: p["compositions"]["0"]["parts"][0].update(elementGuid="missing"),
                     lambda p: p["mineableElements"]["0"].update(scanSignature=float("nan")),
                     lambda p: p["mineableElements"]["0"].update(scanSignature=True),
                     lambda p: p["clusteringPresets"]["cluster"]["params"][0].update(maxSize=1000),
                     lambda p: p["locations"][0]["groups"][0]["deposits"][0].update(clusteringPresetGuid="missing"),
                     lambda p: p["locations"].append(copy.deepcopy(p["locations"][0]))]
        for mutate in mutations:
            data = fixture(); mutate(data)
            with self.assertRaises(RuntimeError): validate_mining(data, VERSION)

    def test_cluster_counts_preserve_gaps_chance_and_zero_weights(self):
        preset = {"probabilityOfClustering": 100, "params": [{"minSize": 2, "maxSize": 3, "relativeProbability": 1},
                   {"minSize": 6, "maxSize": 6, "relativeProbability": 1}, {"minSize": 9, "maxSize": 9, "relativeProbability": 0}]}
        self.assertEqual(cluster_counts(preset), [2, 3, 6])
        self.assertEqual(cluster_counts({**preset, "probabilityOfClustering": 25}), [1, 2, 3, 6])
        self.assertEqual(cluster_counts({**preset, "probabilityOfClustering": 0}), [1])

    def test_secondary_material_uses_deposits_primary_signature(self):
        data = fixture()
        data["compositions"]["0"]["parts"].append({"elementGuid": "1", "probability": 0.5, "minPercent": 1, "maxPercent": 10})
        data["locations"][0]["groups"][0]["deposits"] = [{"relativeProbability": 1, "compositionGuid": "0", "clusteringPresetGuid": "cluster"}]
        row = build_mining_materials(data, ["Material 1"], {})["Material 1"]["locations"]["planets"][0]
        self.assertEqual(row["signals"][0]["base"], 3000)
        self.assertEqual(row["signals"][0]["primaryMaterial"], "Material 0")
        self.assertEqual(row["signals"][0]["values"], [12000, 15000, 18000])

    def test_fps_and_roc_remain_per_rock_not_multiplied(self):
        for mode, expected in (("FPS_Mineables", 3000), ("GroundVehicle_Mineables", 4000)):
            data = fixture(); data["locations"][0]["groups"][0]["groupName"] = mode
            signal = build_mining_materials(data, ["Material 0"], {})["Material 0"]["locations"]["planets"][0]["signals"][0]
            self.assertEqual(signal["values"], [expected]); self.assertTrue(signal["shared"])
            self.assertEqual(signal["clusterCounts"], [4, 5, 6])

    def test_resource_identity_not_same_name_and_explicit_zero_is_not_missing(self):
        data = fixture()
        data["mineableElements"]["alias"] = {**data["mineableElements"]["0"], "resourceType": "different", "scanSignature": 99}
        rows = build_mining_materials(data, ["Material 0"], {})["Material 0"]["locations"]["planets"]
        self.assertTrue(all(s["base"] == 3000 for row in rows for s in row["signals"]))
        data["mineableElements"]["alias"]["resourceType"] = "resource-0"
        with self.assertRaisesRegex(RuntimeError, "conflicting signatures"):
            build_mining_materials(data, ["Material 0"], {})
        data = fixture(); data["mineableElements"]["0"]["scanSignature"] = 0
        rows = build_mining_materials(data, ["Material 0"], {})["Material 0"]["locations"]["planets"]
        self.assertTrue(all(not row["signals"] for row in rows))

    def test_no_disabled_spawns_no_guessed_stations_or_coordinates(self):
        data = fixture()
        data["locations"][0].update(locationName="Lagrange A", locationType="lagrange")
        row = build_mining_materials(data, ["Material 0", "Yormandi Eye"], {})
        self.assertEqual(row["Material 0"]["locations"]["lagrangePoints"][0]["precision"], "template")
        self.assertEqual(row["Material 0"]["locations"]["lagrangePoints"][0]["coordinateStatus"], "not-provided")
        self.assertFalse(row["Yormandi Eye"]["hasReliableLocations"])
        data["locations"][0]["groups"][0]["groupProbability"] = 0
        self.assertFalse(build_mining_materials(data, ["Material 0"], {})["Material 0"]["locations"]["lagrangePoints"])

    def test_coverage_drop_and_retrieval_timestamp(self):
        current = normalized(); candidate = copy.deepcopy(current)
        candidate["metadata"]["retrievedAt"] = "2026-10-19T00:00:00Z"
        self.assertEqual(comparable(current), comparable(candidate))
        for material in candidate["materials"].values(): material["locations"]["planets"] = []
        with self.assertRaises(RuntimeError): validate_candidate(candidate, current)

    def test_failed_or_unchanged_refresh_never_writes_or_claims_new_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mineral-locations.json"
            current = normalized(); path.write_text(json.dumps(current), encoding="utf-8")
            original = path.read_bytes()
            with patch("refresh_mineral_locations.DATA_PATH", path), patch("refresh_mineral_locations.build_candidate", return_value=current), patch("refresh_mineral_locations.prune_old_backups"):
                self.assertFalse(refresh()); self.assertEqual(path.read_bytes(), original)
            with patch("refresh_mineral_locations.DATA_PATH", path), patch("refresh_mineral_locations.build_candidate", side_effect=TimeoutError("source unavailable")):
                with self.assertRaises(TimeoutError): refresh()
                self.assertEqual(path.read_bytes(), original)

    def test_same_build_signal_corrections_are_content_changes(self):
        before = normalized(); source = fixture(); source["mineableElements"]["0"]["scanSignature"] = 3100
        after = normalized(source)
        self.assertNotEqual(comparable(before), comparable(after))


if __name__ == "__main__": unittest.main()
