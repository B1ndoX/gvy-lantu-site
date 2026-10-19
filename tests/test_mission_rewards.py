from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_data import build_mission_rewards, build_source_maps, validate_mission_rewards
from official_localization import OfficialNames
from translate_index_google import collect_strings, translate_mission_rewards


class MissionRewardTests(unittest.TestCase):
    def data(self):
        return {
            "version": "4.10.2-live.12913470",
            "blueprintPools": {"pool": {"blueprints": [{"blueprintRecord": "bp", "weight": 1}]}},
            "contracts": [
                {"id": "one", "debugName": "Same", "title": "Same title", "availableSystems": ["Nyx"],
                 "blueprintRewards": [{"blueprintPool": "pool", "chance": 1}],
                 "itemRewards": [{"name": "Test Rifle", "amount": 2, "awardOnlyToMissionOwner": True}]},
                {"id": "two", "debugName": "Same", "title": "Same title", "systems": ["Pyro", "Nyx"],
                 "blueprintRewards": [{"blueprintPool": "pool", "chance": 0.5}],
                 "itemRewards": [{"type": "weighted_choice", "awardOnlyToMissionOwner": True,
                    "groups": [{"probability": 0.5, "weighting": 1,
                                "items": [{"name": "Test Magazine", "amount": 20}]}]}]},
            ],
        }

    def test_contract_identity_system_fallback_and_pool_chance_are_preserved(self):
        data = self.data()
        before = copy.deepcopy(data)
        sources, _ = build_source_maps(data)
        rewards = build_mission_rewards(data)
        self.assertEqual([m["id"] for m in sources["bp"][0]["missions"]], ["one", "two"])
        self.assertEqual(sources["bp"][0]["missions"][0]["systems"], ["Nyx"])
        self.assertEqual(set(rewards["missions"]), {"one", "two"})
        self.assertEqual(rewards["missions"]["one"]["pools"][0]["chance"], 1)
        self.assertEqual(rewards["missions"]["two"]["items"][0]["groups"][0]["items"][0]["amount"], 20)
        self.assertTrue(rewards["missions"]["one"]["items"][0]["awardOnlyToMissionOwner"])
        self.assertEqual(data, before)
        index = {"version": data["version"], "missionRewards": rewards,
                 "records": [{"sources": sources["bp"]}]}
        validate_mission_rewards(index)
        index["missionRewards"]["missions"].pop("one")
        with self.assertRaisesRegex(RuntimeError, "reference is missing"):
            validate_mission_rewards(index)

    def test_rejects_duplicate_or_missing_contract_ids(self):
        for value in ("", "one"):
            data = self.data()
            data["contracts"][1]["id"] = value
            with self.assertRaisesRegex(RuntimeError, "unique contract IDs"):
                build_mission_rewards(data)

    def test_rejects_missing_or_empty_referenced_pools(self):
        for pools in ({}, {"pool": {"blueprints": []}}):
            data = self.data()
            data["blueprintPools"] = pools
            with self.assertRaisesRegex(RuntimeError, "missing or empty blueprint pool"):
                build_mission_rewards(data)

    def test_rejects_malformed_systems_instead_of_publishing_a_broken_ui(self):
        for systems in ("Nyx", [None], [" "]):
            data = self.data()
            data["contracts"][0]["systems"] = systems
            with self.assertRaisesRegex(RuntimeError, "star system list"):
                build_mission_rewards(data)
            with self.assertRaisesRegex(RuntimeError, "star system list"):
                build_source_maps(data)

    def test_same_title_missions_keep_their_own_explicit_reward_pools(self):
        data = self.data()
        data["blueprintPools"].update({
            "second": {"blueprints": [{"blueprintRecord": "second-bp", "weight": 1}]},
            "unrelated": {"blueprints": [{"blueprintRecord": "other-bp", "weight": 1}]},
        })
        data["contracts"][0]["blueprintRewards"].append({"blueprintPool": "second", "chance": 1})
        data["contracts"][1]["blueprintRewards"] = [{"blueprintPool": "unrelated", "chance": 1}]
        rewards = build_mission_rewards(data)
        sources, _ = build_source_maps(data)
        self.assertEqual([p["id"] for p in rewards["missions"]["one"]["pools"]], ["pool", "second"])
        self.assertEqual([p["id"] for p in rewards["missions"]["two"]["pools"]], ["unrelated"])
        self.assertEqual([m["id"] for m in sources["bp"][0]["missions"]], ["one"])
        self.assertEqual([m["id"] for m in sources["other-bp"][0]["missions"]], ["two"])

    def test_rejects_invalid_or_unknown_item_rewards(self):
        for reward in ({"type": "unknown", "name": "Test Rifle"},
                       {"name": "Test Rifle", "amount": -1},
                       {"name": "Test Rifle", "amount": float("nan")},
                       {"name": "Test Rifle", "amount": True},
                       {"type": "weighted_choice", "groups": []}):
            data = self.data()
            data["contracts"][0]["itemRewards"] = [reward]
            with self.assertRaises(RuntimeError):
                build_mission_rewards(data)

    def test_requirements_preserve_rank_sharing_and_optional_vs_required_intros(self):
        data = self.data()
        data["contracts"][0].update(
            canBeShared=True, illegal=False, personalCooldownTime=45, hasPersonalCooldown=True,
            minStanding={"name": "Neutral", "minReputation": 0, "includeWhenSharing": False},
            requiredIntros=[{"title": "Required", "debugName": "req"}],
            linkedIntros=[{"title": "Optional", "debugName": "optional"}],
            prerequisites={"locality": [{"name": "Nyx"}]}, locations=["site"])
        data["regions"] = {"Nyx": {"system": "Nyx", "locations": [{"guid": "nyx", "name": "Nyx"}]}}
        data["locationPools"] = {"site": {"name": "Station", "system": "Nyx"}}
        rewards = build_mission_rewards(data)
        req = rewards["missions"]["one"]["requirements"]
        self.assertEqual(req["minStanding"]["minReputation"], 0)
        self.assertFalse(req["minStanding"]["includeWhenSharing"])
        self.assertEqual(req["personalCooldownTime"], 45)
        self.assertEqual(req["requiredIntros"][0]["title"], "Required")
        self.assertEqual(req["linkedIntros"][0]["title"], "Optional")
        self.assertEqual(req["missionLocations"], ["site"])
        self.assertEqual(req["regions"][0]["locations"], ["nyx"])
        validate_mission_rewards({"version": data["version"], "records": [], "missionRewards": rewards})
        rewards["locations"].pop("site")
        with self.assertRaisesRegex(RuntimeError, "missing location"):
            validate_mission_rewards({"version": data["version"], "records": [], "missionRewards": rewards})

    def test_requirement_flags_times_and_old_schema_are_rejected(self):
        for field, bad in (("canBeShared", "yes"), ("personalCooldownTime", -1), ("abandonedCooldownTime", float("nan"))):
            data = self.data()
            data["contracts"][0][field] = bad
            rewards = build_mission_rewards(data)
            with self.assertRaises(RuntimeError):
                validate_mission_rewards({"version": data["version"], "records": [], "missionRewards": rewards})
        rewards = build_mission_rewards(self.data())
        rewards["schemaVersion"] = 1
        with self.assertRaises(RuntimeError):
            validate_mission_rewards({"version": rewards["version"], "records": [], "missionRewards": rewards})

    def test_excluded_completion_tags_are_not_required_predecessors(self):
        data = self.data()
        data["contracts"][0]["prerequisites"] = {"completedContractTags": {"excludedTags": ["done"]}}
        data["contracts"][1]["completionTags"] = [{"tag": "done"}]
        requirement = build_mission_rewards(data)["missions"]["one"]["requirements"]
        self.assertNotIn("completedContracts", requirement)
        self.assertEqual(requirement["excludedContracts"]["tagCount"], 1)
        self.assertEqual(requirement["excludedContracts"]["candidates"][0]["title"], "Same title")

    def test_rejects_stale_reward_schema_or_build(self):
        data = self.data()
        rewards = build_mission_rewards(data)
        rewards["version"] = "4.10.1-live.12660092"
        with self.assertRaisesRegex(RuntimeError, "schema/version"):
            validate_mission_rewards({"version": data["version"], "missionRewards": rewards})
        with self.assertRaisesRegex(RuntimeError, "schema/version"):
            validate_mission_rewards({"version": data["version"]})

    def test_validates_reward_values_after_generation(self):
        data = self.data()
        for target, field, bad in (("pools", "chance", 1.5), ("items", "amount", float("nan"))):
            rewards = build_mission_rewards(data)
            rewards["missions"]["one"][target][0][field] = bad
            with self.assertRaises(RuntimeError):
                validate_mission_rewards({"version": data["version"], "missionRewards": rewards})

    def test_reward_items_and_systems_use_official_names_after_fallback_translation(self):
        index = {"missionRewards": build_mission_rewards(self.data()), "records": []}
        self.assertIn("Test Magazine", collect_strings(index))
        translate_mission_rewards(index, {"Test Rifle": "Fallback rifle", "Test Magazine": "Fallback magazine"})
        OfficialNames({"entries": {
            "item_name_test": {"domain": "item", "english": "Test Rifle", "chinese": "官方步枪"},
            "item_name_magazine": {"domain": "item", "english": "Test Magazine", "chinese": "官方弹匣"},
            "nyx": {"domain": "location", "english": "Nyx", "chinese": "尼克斯"},
        }}).apply_index(index)
        self.assertEqual(index["missionRewards"]["missions"]["one"]["items"][0]["nameZh"], "官方步枪")
        self.assertEqual(index["missionRewards"]["missions"]["two"]["items"][0]["groups"][0]["items"][0]["nameZh"], "官方弹匣")
        self.assertEqual(index["missionRewards"]["systems"][0]["nameZh"], "尼克斯")

    def test_frontend_mission_helpers(self):
        result = subprocess.run(["node", "--test", "tests/mission_rewards.test.mjs"], cwd=ROOT,
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_frontend_usability_helpers(self):
        result = subprocess.run(["node", "--test", "tests/usability.test.mjs"], cwd=ROOT,
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_signal_popover_helpers(self):
        result = subprocess.run(["node", "--test", "tests/signal_popover.test.mjs"], cwd=ROOT,
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_task_dialog_shrinks_to_content_and_switches_column_count(self):
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        dialog = styles.split(".mission-dialog {", 1)[1].split("}", 1)[0]
        self.assertIn("height: fit-content", dialog)
        self.assertNotIn("height: auto", dialog)
        self.assertIn(".mission-blueprint-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr))", styles)
        self.assertIn(".mission-blueprint-list { grid-template-columns: minmax(0, 1fr); }", styles)


if __name__ == "__main__":
    unittest.main()
