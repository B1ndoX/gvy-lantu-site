import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from official_localization import OfficialNames, clean_label
from build_data import build_mission_rewards, build_source_maps, validate_mission_rewards
from apply_local_polish import STAT_TERMS


class MissionLocalizationTests(unittest.TestCase):
    def names(self):
        return OfficialNames({'entries': {
            'haul_title': {'domain': 'other', 'english': '~mission(ReputationRank) Rank - Direct ~mission(CargoGradeToken) Cargo Haul',
                           'chinese': '~mission(ReputationRank) 级别 - 直达 ~mission(CargoGradeToken) 货物运输'},
            'rank6': {'domain': 'other', 'english': 'Master', 'chinese': 'lv.6 航道领袖'},
            'bulk': {'domain': 'other', 'english': 'Bulk', 'chinese': '大宗'},
            'ling_title': {'domain': 'other', 'english': 'Ling Family ~mission(ReputationRank) Cargo Haul - ~mission(CargoGradeToken) Scale',
                           'chinese': '玲家 ~mission(ReputationRank) 货物运输 - ~mission(CargoGradeToken) 级别'},
            'rank1': {'domain': 'other', 'english': 'Rookie', 'chinese': '速递新秀'},
            'medium': {'domain': 'other', 'english': 'Medium', 'chinese': '中型'},
            'ling_faction': {'domain': 'other', 'english': 'Ling Family Hauling', 'chinese': '玲家快递'},
            'location_title': {'domain': 'other', 'english': 'Take Outlaws at ~mission(Location) Offline',
                               'chinese': '让 ~mission(Location) 的不法分子下线[蓝图]'},
            'ambiguous_a': {'domain': 'other', 'english': 'Lrg. Purchase Order', 'chinese': '大批量采购订单[蓝图]'},
            'ambiguous_b': {'domain': 'other', 'english': 'Lrg. Purchase Order', 'chinese': '大批量采购订单'},
            'items_commodities_corundum': {'domain': 'material', 'english': 'Corundum', 'chinese': '刚玉Corundom'},
        }})

    def test_template_and_all_rank_material_tokens_use_verified_keys(self):
        mission = {'title': 'Master Rank - Direct Bulk Cargo Haul', 'titleKey': '@HAUL_TITLE',
                   'titleTokens': {'ReputationRank': '@Rank6', 'CargoGradeToken': '@BULK'}}
        before = copy.deepcopy(mission)
        self.assertEqual(self.names().resolve_mission_title(mission), ('lv.6 航道领袖 级别 - 直达 大宗 货物运输', 'haul_title'))
        self.assertEqual(mission, before)

    def test_ling_family_dynamic_title_does_not_reuse_partial_machine_translation(self):
        mission = {'title': 'Ling Family Rookie Cargo Haul - Medium Scale', 'titleKey': 'ling_title',
                   'titleTokens': {'ReputationRank': '@rank1', 'CargoGradeToken': '@medium'},
                   'titleZh': 'Ling Family Rookie 货运 - 中型', 'faction': 'Ling Family Hauling', 'factionKey': 'ling_faction'}
        index = {'records': [{'sources': [{'missions': [mission]}]}]}
        self.names().apply_index(index)
        self.assertEqual(mission['titleZh'], '玲家 速递新秀 货物运输 - 中型 级别')
        self.assertEqual(mission['titleZhSource'], 'nas-official-mission')
        self.assertEqual(mission['factionZh'], '玲家快递')

    def test_runtime_placeholders_are_preserved_not_replaced_with_guessed_sites(self):
        names = self.names()
        title = {'title': 'Take Outlaws at [LOCATION] Offline', 'titleKey': 'location_title'}
        self.assertEqual(names.resolve_mission_title(title)[0], '让 [地点] 的不法分子下线[蓝图]')
        title['title'] = 'Take Outlaws at Unverified Base Offline'
        self.assertIsNone(names.resolve_mission_title(title))

    def test_missing_mismatched_or_nested_token_keys_do_not_publish_partial_templates(self):
        for tokens in ({'ReputationRank': '@missing', 'CargoGradeToken': '@bulk'},
                       {'ReputationRank': '@rank1', 'CargoGradeToken': '@bulk'}):
            mission = {'title': 'Master Rank - Direct Bulk Cargo Haul', 'titleKey': 'haul_title', 'titleTokens': tokens}
            self.assertIsNone(self.names().resolve_mission_title(mission))
        names = self.names()
        names.entries['rank6']['chinese'] = '~mission(AnotherRank)'
        self.assertIsNone(names.resolve_mission_title({'title': 'Master Rank - Direct Bulk Cargo Haul', 'titleKey': 'haul_title',
                                                       'titleTokens': {'ReputationRank': '@rank6', 'CargoGradeToken': '@bulk'}}))

    def test_same_english_text_uses_contract_key_not_ambiguous_name_lookup(self):
        names = self.names()
        self.assertIsNone(names.resolve_mission_title({'title': 'Lrg. Purchase Order'}))
        self.assertEqual(names.resolve_mission_title({'title': 'Lrg. Purchase Order', 'titleKey': 'ambiguous_a'})[0], '大批量采购订单[蓝图]')
        self.assertEqual(names.resolve_mission_title({'title': 'Lrg. Purchase Order', 'titleKey': 'ambiguous_b'})[0], '大批量采购订单')

    def test_faction_is_not_replaced_by_a_different_contractor_key(self):
        mission = {'title': 'Missing', 'faction': 'Other Faction', 'factionKey': 'ling_faction', 'factionZh': '原派系'}
        self.names().apply_index({'records': [{'sources': [{'missions': [mission]}]}]})
        self.assertEqual(mission['factionZh'], '原派系')

    def test_fallback_only_localizes_known_placeholders_without_claiming_an_official_match(self):
        mission = {'title': 'Missing [LOCATION]', 'titleZh': '未知任务 [LOCATION] [UNKNOWN]',
                   'titleZhLocalizationKey': 'stale_key'}
        self.names().apply_index({'records': [{'sources': [{'missions': [mission]}]}]})
        self.assertEqual(mission['titleZh'], '未知任务 [地点] [UNKNOWN]')
        self.assertEqual(mission['titleZhSource'], 'translation-fallback')
        self.assertNotIn('titleZhLocalizationKey', mission)

    def test_condition_intro_titles_use_the_same_verified_template(self):
        intro = {'title': 'Master Rank - Direct Bulk Cargo Haul', 'titleKey': 'haul_title',
                 'titleTokens': {'ReputationRank': '@rank6', 'CargoGradeToken': '@bulk'}}
        index = {'missionRewards': {'missions': {'id': {'requirements': {'requiredIntros': [intro]}}}}}
        self.names().apply_index(index)
        self.assertEqual(intro['titleZh'], 'lv.6 航道领袖 级别 - 直达 大宗 货物运输')

    def test_corundum_typo_cleanup_is_scoped_and_other_models_are_preserved(self):
        self.assertEqual(self.names().resolve('Corundum', 'material')[0], '刚玉')
        self.assertEqual(clean_label('刚玉Corundom', 'Corundum', group='item'), '刚玉Corundom')
        self.assertEqual(clean_label('刚玉CorundomOther', 'Corundum', group='material'), '刚玉CorundomOther')
        self.assertEqual(clean_label('SNS-R6', 'SNS-R6', group='item'), 'SNS-R6')

    def test_generator_preserves_keys_tokens_and_faction_identity(self):
        data = {'version': '4.10.2-live.12913470', 'blueprintPools': {'pool': {'blueprints': [{'blueprintRecord': 'bp'}]}},
                'factions': {'f': {'name': 'Ling Family Hauling', 'nameKey': '@ling_faction'}},
                'contracts': [{'id': 'm', 'title': 'Ling Family Rookie Cargo Haul - Medium Scale', 'titleLocKey': 'ling_title',
                               'tokenSubstitutions': {'ReputationRank': '@rank1', 'CargoGradeToken': '@medium'},
                               'factionGuid': 'f', 'contractorNameKey': '@different_sender', 'systems': ['Nyx'],
                               'blueprintRewards': [{'blueprintPool': 'pool', 'chance': 1}]}]}
        sources, _ = build_source_maps(data)
        mission = sources['bp'][0]['missions'][0]
        self.assertEqual(mission['factionKey'], 'ling_faction')
        self.assertEqual(mission['titleTokens']['ReputationRank'], '@rank1')
        index = {'version': data['version'], 'records': [{'sources': sources['bp']}], 'missionRewards': build_mission_rewards(data)}
        self.names().apply_index(index)
        validate_mission_rewards(index)
        mission['titleZh'] = 'Master Rank - 直接散货运输'
        with self.assertRaisesRegex(RuntimeError, 'known untranslated phrase'):
            validate_mission_rewards(index)

    def test_known_armor_and_clothing_attachment_enums_are_chinese(self):
        for name in ('Char_Armor_Helmet','Char_Armor_Arms','Char_Armor_Torso','Char_Armor_Legs','Char_Armor_Undersuit',
                     'Char_Clothing_Torso_0','Char_Clothing_Torso_1','Char_Clothing_Legs'):
            self.assertNotIn('Char_', STAT_TERMS[name])


if __name__ == '__main__':
    unittest.main()
