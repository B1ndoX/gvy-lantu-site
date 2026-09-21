from __future__ import annotations

import copy
import gzip
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import official_localization as loc


class OfficialLocalizationTests(unittest.TestCase):
    def source(self):
        raw = b"Frontend_PU_Version=4.10: Test\nitem_name_test=Test\n"
        return raw, {"schemaVersion": 1, "sourcePath": loc.NAS_PATH,
                     "sha256": hashlib.sha256(raw).hexdigest(), "byteLength": len(raw),
                     "versionLabel": "4.10: Test", "versionPrecision": "major-minor-only"}

    def test_github_reads_two_files_from_one_immutable_commit(self):
        raw, manifest = self.source()
        commit = "a" * 40
        with patch.object(loc, "fetch_bytes", side_effect=[json.dumps({"object": {"sha": commit}}).encode(),
                          json.dumps(manifest).encode(), gzip.compress(raw)]) as fetch:
            result, meta = loc.read_github_source("4.10.1-live.12660092")
        self.assertEqual(result, raw)
        self.assertEqual(meta["inputCommit"], commit)
        self.assertTrue(all(f"/{commit}/" in call.args[0] for call in fetch.call_args_list[1:]))

    def test_github_rejects_bad_hash_length_schema_and_version(self):
        raw, manifest = self.source()
        for field, value in (("sha256", "0" * 64), ("byteLength", len(raw) + 1),
                             ("schemaVersion", 2), ("versionLabel", "4.11: Test"),
                             ("sourcePath", "/other/file")):
            with self.subTest(field=field):
                invalid = {**manifest, field: value}
                with patch.object(loc, "fetch_bytes", side_effect=[json.dumps({"object": {"sha": "a" * 40}}).encode(),
                                  json.dumps(invalid).encode(), gzip.compress(raw)]):
                    with self.assertRaises(RuntimeError):
                        loc.read_github_source("4.10.1-live.12660092")

    def test_manifest_label_must_equal_ini_label(self):
        raw, manifest = self.source()
        manifest["versionLabel"] = "4.10: Other"
        with patch.object(loc, "fetch_bytes", side_effect=[json.dumps({"object": {"sha": "a" * 40}}).encode(),
                          json.dumps(manifest).encode(), gzip.compress(raw)]):
            with self.assertRaisesRegex(RuntimeError, "differs"):
                loc.read_github_source("4.10.1-live.12660092")

    def test_ini_keeps_flags_and_embedded_equals_and_rejects_conflicts(self):
        self.assertEqual(loc.parse_ini(b"\xef\xbb\xbfKey,P=a=b\n"), {"key,p": "a=b"})
        with self.assertRaisesRegex(RuntimeError, "conflicting"):
            loc.parse_ini(b"KEY=A\nkey=B")

    def test_clean_label_only_strips_exact_english_suffix(self):
        self.assertEqual(loc.clean_label("波射石Borase", "Borase"), "波射石")
        self.assertEqual(loc.clean_label("赫 L1 绿色林地站\\nHUR-L1 Green Glade Station", "HUR-L1 Green Glade Station"), "赫 L1 绿色林地站")
        self.assertEqual(loc.clean_label("FR-66", "FR-66"), "FR-66")
        self.assertEqual(loc.clean_label("=错误", "Test"), "")
        self.assertEqual(loc.clean_label("目标<EM4>[蓝图]</EM4>", "Target"), "目标[蓝图]")

    def test_ambiguous_labels_are_not_guessed_and_stable_keys_win(self):
        names = loc.OfficialNames({"entries": {
            "manufacturer_namea": {"english": "A", "chinese": "甲", "domain": "manufacturer"},
            "manufacturer_nameb": {"english": "A", "chinese": "乙", "domain": "manufacturer"},
        }})
        self.assertIsNone(names.resolve("A", "manufacturer"))
        self.assertEqual(names.resolve("A", "manufacturer", "manufacturer_NameA"), ("甲", "manufacturer_namea"))
        self.assertIsNone(names.resolve("Aa", "manufacturer"))

    def test_slot_domain_does_not_confuse_generic_core_names(self):
        self.assertEqual(loc.domain("crafting_ui_slotname_core,P"), "slot")
        names = loc.OfficialNames({"entries": {
            "crafting_ui_slotname_core,p": {"english": "Core", "chinese": "核心", "domain": "slot"},
            "unrelated": {"english": "Core", "chinese": "其他", "domain": "other"},
        }})
        self.assertEqual(names.resolve("Core", "slot")[0], "核心")

    def test_item_full_name_does_not_conflict_with_short_or_vehicle_name(self):
        names = loc.OfficialNames({"entries": {
            "item_name_test": {"english": "Guardian", "chinese": "守卫", "domain": loc.domain("item_name_test")},
            "item_name_test_short": {"english": "Guardian", "chinese": "短名称", "domain": loc.domain("item_name_test_short")},
            "vehicle_name_test": {"english": "Guardian", "chinese": "守护者", "domain": loc.domain("vehicle_name_test")},
        }})
        self.assertEqual(names.resolve("Guardian", "item"), ("守卫", "item_name_test"))

    def test_planet_domain_does_not_confuse_company_name(self):
        self.assertEqual(loc.domain("Stanton3"), "location")
        self.assertEqual(loc.domain("manufacturer_NameARCC"), "manufacturer")

    def test_mineral_translation_preserves_signal_numbers(self):
        payload = {"materials": {"Borase": {"nameZh": "旧名", "locations": {"moons": [
            {"en": "Adir", "zh": "旧名", "signal": {"base": 3000, "values": [3000, 6000]}}
        ]}}}}
        signal = copy.deepcopy(payload["materials"]["Borase"]["locations"]["moons"][0]["signal"])
        loc.OfficialNames({"entries": {
            "items_commodities_borase": {"english": "Borase", "chinese": "波射石", "domain": "material"},
        }}).apply_minerals(payload)
        self.assertEqual(payload["materials"]["Borase"]["nameZh"], "波射石")
        self.assertEqual(payload["materials"]["Borase"]["locations"]["moons"][0]["signal"], signal)

    def test_ci_source_failure_cannot_silently_reuse_old_snapshot(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), patch.object(loc, "load_snapshot", return_value={}), \
                patch.object(loc, "read_github_source", side_effect=RuntimeError("unavailable")), \
                patch.object(loc.subprocess, "run") as ssh:
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                loc.refresh_snapshot("4.10.1-live.12660092")
            ssh.assert_not_called()

    def test_unchanged_source_preserves_snapshot_without_bridge_fetch(self):
        raw, manifest = self.source()
        current = {"metadata": {"sourceSha256": manifest["sha256"], "importedAt": "unchanged", "adapterVersion": loc.ADAPTER_VERSION}}
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), patch.object(loc, "load_snapshot", return_value=current), \
                patch.object(loc, "read_github_source", return_value=(raw, {})), \
                patch.object(loc, "validate_snapshot"), patch.object(loc, "fetch_bytes") as fetch:
            snapshot, changed = loc.refresh_snapshot("4.10.1-live.12660092")
            self.assertIs(snapshot, current)
            self.assertFalse(changed)
            fetch.assert_not_called()

    def test_snapshot_hash_and_series_must_be_valid(self):
        entries = {f"item_name_{i}": {"english": f"Item {i}", "chinese": "物品", "domain": "item"} for i in range(7000)}
        payload = {"entries": entries, "metadata": {"series": "4.10", "sourceSha256": "a" * 64, "entriesSha256": loc.entries_hash(entries)}}
        loc.validate_snapshot(payload, "4.10.1-live.1")
        with self.assertRaises(RuntimeError):
            loc.validate_snapshot(payload, "4.11.0-live.1")
        payload["entries"]["item_name_0"]["chinese"] = "坏数据"
        with self.assertRaises(RuntimeError):
            loc.validate_snapshot(payload, "4.10.1-live.1")

    def test_frontend_does_not_override_verified_material_name(self):
        app = (Path(__file__).resolve().parents[1] / "assets/app.js").read_text()
        self.assertIn('item.nameZh || flowcldMaterialLabels[item.name]', app)
        self.assertIn('info?.nameZh || flowcldMaterialLabels[name]', app)


if __name__ == "__main__":
    unittest.main()
