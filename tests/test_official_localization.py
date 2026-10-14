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

    def test_github_accepts_official_alpha_label_without_rewriting_source(self):
        raw, manifest = self.source()
        raw = raw.replace(b"4.10: Test", "Alpha 4.10：奥里森之围".encode())
        manifest.update(sha256=hashlib.sha256(raw).hexdigest(), byteLength=len(raw),
                        versionLabel="Alpha 4.10：奥里森之围")
        with patch.object(loc, "fetch_bytes", side_effect=[json.dumps({"object": {"sha": "a" * 40}}).encode(),
                          json.dumps(manifest).encode(), gzip.compress(raw)]):
            result, _ = loc.read_github_source("4.10.1-live.12660092")
        self.assertEqual(result, raw)
        self.assertEqual(loc.series(manifest["versionLabel"]), "4.10")
        for invalid in ("Alpha", "Alpha 4", "Unknown 4.10", "Alpha 4.x"):
            with self.assertRaises(RuntimeError):
                loc.series(invalid)

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

    def test_bilingual_labels_choose_chinese_in_either_order(self):
        for text in ("Borase\\n波射石", "波射石\\nBorase", "Borase\n波射石"):
            with self.subTest(text=text):
                self.assertEqual(loc.clean_label(text, "Borase"), "波射石")
        self.assertEqual(loc.clean_label("Agricium\\n艾格瑞金属", "Agricium"), "艾格瑞金属")
        self.assertEqual(loc.clean_label("Fixed Mav Thruster\\n联合式机动推进器", "Fixed Mav Thruster"), "联合式机动推进器")
        self.assertEqual(loc.clean_label("Pyro [派罗]", "Pyro"), "派罗")
        self.assertEqual(loc.clean_label("Delamar\\n德拉玛(Delamar)", "Delamar"), "德拉玛")
        self.assertEqual(loc.clean_label("<EM4>Borase</EM4>\\n<EM4>波射石</EM4>", "Borase"), "波射石")

    def test_bilingual_labels_keep_models_and_skip_untranslated_duplicates(self):
        self.assertEqual(loc.clean_label("Constellation Mk IV Nightbreak Livery\\n星座 Mk IV 夜影涂装", "Constellation Mk IV Nightbreak Livery"), "星座 Mk IV 夜影涂装")
        self.assertEqual(loc.clean_label("柳叶刀MH1 采矿激光器", "Lancet MH1 Mining Laser"), "柳叶刀MH1 采矿激光器")
        self.assertEqual(loc.clean_label("蓝三角股份有限公司", "Blue Triangle Inc."), "蓝三角股份有限公司")
        self.assertEqual(loc.clean_label("FR-66 [FR-66]", "FR-66"), "FR-66")
        self.assertEqual(loc.clean_label("Monolith Armor Core\\nMonolith Armor Core", "Monolith Armor Core"), "")
        self.assertEqual(loc.clean_label("DCSR2\\nDCSR2", "DCSR2"), "")
        self.assertEqual(loc.clean_label("<-=MISSING=->\\n<-=MISSING=->", "Missing"), "")

    def test_ambiguous_labels_are_not_guessed_and_stable_keys_win(self):
        names = loc.OfficialNames({"entries": {
            "manufacturer_namea": {"english": "A", "chinese": "甲", "domain": "manufacturer"},
            "manufacturer_nameb": {"english": "A", "chinese": "乙", "domain": "manufacturer"},
        }})
        self.assertIsNone(names.resolve("A", "manufacturer"))
        self.assertEqual(names.resolve("A", "manufacturer", "manufacturer_NameA"), ("甲", "manufacturer_namea"))
        self.assertIsNone(names.resolve("Aa", "manufacturer"))

    def test_component_specs_are_not_names_and_models_are_preserved(self):
        for english, annotation in (("VK-00", "[量子 S1 军用 A]"),
                                    ("FR-66", "[护盾 S1 军用 A]"),
                                    ("JS-300", "[发电 S1 军用 A]"),
                                    ("SNS-R6", "[雷达 S1 竞赛 C]")):
            for text in (f"{english}\\n{annotation}", f"{annotation}\\n{english}",
                         f"{english}\n{annotation}"):
                with self.subTest(text=text):
                    self.assertEqual(loc.clean_label(text, english, group="item"), english)
        self.assertEqual(loc.clean_label("[量子 S1 军用 A]", "VK-00", group="item"), "")
        self.assertEqual(loc.clean_label("[-30%抗性|+20%绿区速度]\\n霍夫斯泰德",
                                        "Hofstede", group="item"), "霍夫斯泰德")

    def test_item_short_english_tail_is_removed_without_losing_model_tokens(self):
        examples = (("霍夫斯泰德-S1 型采矿激光器Hofstede-S1", "Hofstede-S1 Mining Laser", "霍夫斯泰德-S1 型采矿激光器"),
                    ("克莱恩-S2 型采矿激光器Klein-S2", "Klein-S2 Mining Laser", "克莱恩-S2 型采矿激光器"),
                    ("柳叶刀 MH1 型采矿激光器Lancet MH1", "Lancet MH1 Mining Laser", "柳叶刀 MH1 型采矿激光器"),
                    ("劳森采矿激光器Lawson", "Lawson Mining Laser", "劳森采矿激光器"),
                    ("S00 霍夫斯泰德Hofstede", "S00 Hofstede", "S00 霍夫斯泰德"),
                    ("5CA 阿库拉Akura", "5CA 'Akura'", "5CA 阿库拉"),
                    ("净采 模组Clearcut", "Clearcut Module", "净采 模组"),
                    ("狐火Foxfire", "FoxFire", "狐火"),
                    ("低温之星SL CryoStarSL", "Cryo-Star SL", "低温之星SL"),
                    ("离子奔涌Pro IonSurgePro", "IonSurge Pro", "离子奔涌Pro"))
        for text, english, expected in examples:
            with self.subTest(english=english):
                self.assertEqual(loc.clean_label(text, english, group="item"), expected)

    def test_item_cleaning_preserves_legitimate_mixed_names_and_unknown_suffixes(self):
        for text, english in (("德尔塔Max", "DeltaMax"), ("寒霜之星EX", "Frost-Star EX"),
                              ("四相电池MT", "QuadraCell MT"), ("星座 Mk IV 夜影涂装", "Constellation Mk IV Nightbreak Livery"),
                              ("[截面]火花 I-G", "Spark I-G"), ("劳森采矿激光器LawsonOther", "Lawson Mining Laser"),
                              ("劳森采矿激光器SuperLawson", "Lawson Mining Laser"), ("狐火SuperFoxFire", "FoxFire")):
            with self.subTest(text=text):
                self.assertEqual(loc.clean_label(text, english, group="item"), text)
        self.assertEqual(loc.clean_label("目标[蓝图]", "Target", group="other"), "目标[蓝图]")
        self.assertEqual(loc.clean_label("阿尔法 Alpha", "Alph", group="item"), "阿尔法 Alpha")

    def test_build_snapshot_uses_item_context_and_preserves_flagged_keys(self):
        entries = {"frontend_pu_version": "4.10.2"}
        labels = {}
        for i in range(70000):
            key = f"item_name_{i}" if i < 7000 else f"other_{i}"
            entries[key] = "物品"
            labels[key] = f"Item {i}"
        entries["item_name_qdrv,p"] = "VK-00\\n[量子 S1 军用 A]"
        labels["item_name_qdrv,p"] = "VK-00"
        entries["item_mining_laser"] = "劳森采矿激光器Lawson\\n[+30%不稳定|-40%抗性]"
        labels["item_mining_laser"] = "Lawson Mining Laser"
        with patch.object(loc, "parse_ini", return_value=entries):
            result = loc.build_snapshot(b"fixture", labels, "4.10.2-live.12881860")
        self.assertEqual(result["entries"]["item_name_qdrv,p"]["chinese"], "VK-00")
        self.assertEqual(result["entries"]["item_mining_laser"]["chinese"], "劳森采矿激光器")
        loc.validate_snapshot(result, "4.10.2-live.12881860")

    def test_item_cleaning_never_removes_the_only_variant_identifier(self):
        for text, english in (("柳叶刀Lancet MH2", "Lancet MH2 Mining Laser"),
                              ("螺旋Helix II", "Helix II Mining Laser"),
                              ("低温之星CryoStarSL", "Cryo-Star SL"),
                              ("离子奔涌IonSurgePro", "IonSurge Pro"),
                              ("柳叶刀(Lancet MH2 Mining Laser)", "Lancet MH2 Mining Laser")):
            with self.subTest(text=text):
                self.assertEqual(loc.clean_label(text, english, group="item"), text)

    def test_snapshot_rejects_specification_only_item_names_even_with_valid_hash(self):
        entries = {f"item_name_{i}": {"english": f"Item {i}", "chinese": "物品", "domain": "item"}
                   for i in range(7000)}
        entries["item_name_0"]["chinese"] = "[量子 S1 军用 A]"
        payload = {"entries": entries, "metadata": {"series": "4.10", "sourceSha256": "a" * 64,
                                                   "entriesSha256": loc.entries_hash(entries)}}
        with self.assertRaisesRegex(RuntimeError, "specification"):
            loc.validate_snapshot(payload, "4.10.2-live.12881860")

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

    def test_new_source_or_adapter_revision_rebuilds_snapshot(self):
        raw, manifest = self.source()
        for source_hash, adapter in (("0" * 64, loc.ADAPTER_VERSION),
                                     (manifest["sha256"], loc.ADAPTER_VERSION - 1)):
            with self.subTest(source_hash=source_hash, adapter=adapter):
                current = {"metadata": {"sourceSha256": source_hash, "adapterVersion": adapter}}
                candidate = {"metadata": {}}
                with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), \
                        patch.object(loc, "load_snapshot", return_value=current), \
                        patch.object(loc, "read_github_source", return_value=(raw, {"inputCommit": "a" * 40})), \
                        patch.object(loc, "fetch_bytes", return_value=b"{}"), \
                        patch("enrich_quality_stats.source_sha_from_commit", return_value="b" * 40), \
                        patch("enrich_quality_stats.source_version_from_commit", return_value="4.10.1-live.1"), \
                        patch.object(loc, "build_snapshot", return_value=candidate) as build, \
                        patch.object(loc, "validate_snapshot"):
                    result, changed = loc.refresh_snapshot("4.10.2-live.12881860")
                self.assertTrue(changed)
                self.assertIs(result, candidate)
                self.assertEqual(result["metadata"]["inputCommit"], "a" * 40)
                build.assert_called_once()

    def test_enhanced_fully_chinese_enhanced_round_trip_uses_current_hash_only(self):
        enhanced = "Frontend_PU_Version=4.10: Test\nitems_commodities_borase=波射石Borase\n".encode()
        fully_chinese = "Frontend_PU_Version=Alpha 4.10: Test\nitems_commodities_borase=波射石\n".encode()
        current = {}

        def build(raw, labels, version, **kwargs):
            return {"metadata": {"adapterVersion": loc.ADAPTER_VERSION,
                                 "sourceSha256": hashlib.sha256(raw).hexdigest(),
                                 "importedAt": "preserved"},
                    "entries": {"items_commodities_borase": {"chinese": loc.clean_label(
                        loc.parse_ini(raw)["items_commodities_borase"], "Borase")}}}

        for raw in (enhanced, fully_chinese, enhanced):
            with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), \
                    patch.object(loc, "load_snapshot", return_value=current), \
                    patch.object(loc, "read_github_source", return_value=(raw, {})), \
                    patch.object(loc, "fetch_bytes", return_value=b"{}"), \
                    patch("enrich_quality_stats.source_sha_from_commit", return_value="a" * 40), \
                    patch("enrich_quality_stats.source_version_from_commit", return_value="4.10.1-live.1"), \
                    patch.object(loc, "build_snapshot", side_effect=build), \
                    patch.object(loc, "validate_snapshot"):
                current, changed = loc.refresh_snapshot("4.10.2-live.12881860")
            self.assertTrue(changed)
            self.assertEqual(current["entries"]["items_commodities_borase"]["chinese"], "波射石")
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), \
                patch.object(loc, "load_snapshot", return_value=current), \
                patch.object(loc, "read_github_source", return_value=(enhanced, {"sourceUpdatedAt": "new-mtime"})), \
                patch.object(loc, "validate_snapshot"), patch.object(loc, "fetch_bytes") as fetch:
            unchanged, changed = loc.refresh_snapshot("4.10.2-live.12881860")
        self.assertFalse(changed)
        self.assertIs(unchanged, current)
        self.assertEqual(unchanged["metadata"]["importedAt"], "preserved")
        fetch.assert_not_called()

    def test_source_policy_accepts_chinese_packs_and_rejects_english_first_bilingual(self):
        labels = {f"item_name_test_{i}": f"Item {i}" for i in range(150)}
        for template in ("物品{index}", "物品{index}Item {index}", "物品{index}\\nItem {index}"):
            chinese = {key: template.format(index=i) for i, key in enumerate(labels)}
            result = loc.validate_chinese_source(chinese, labels)
            self.assertEqual(result["englishFirstBilingualCount"], 0)
        bilingual = {key: f"{english}\\n物品" for key, english in labels.items()}
        with self.assertRaisesRegex(RuntimeError, "not a permitted"):
            loc.validate_chinese_source(bilingual, labels)
        # English model names with Chinese metadata are not bilingual translations.
        metadata_only = {key: f"{english}\\n[量子 S1 军用 A]" for key, english in labels.items()}
        self.assertEqual(loc.validate_chinese_source(metadata_only, labels)["chineseNameCount"], 0)

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
