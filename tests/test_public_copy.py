from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicCopyTests(unittest.TestCase):
    def test_craft_specs_replace_tags_and_footer_before_collapsed_base_then_quality(self) -> None:
        app = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
        detail = app.split("function renderDetail() {", 1)[1].split("function recordMissions", 1)[0]
        self.assertIn('const specs = manufacturingSpecifications(record);', detail)
        self.assertIn('<dl class="craft-specs" aria-label="蓝图规格">', detail)
        self.assertIn('<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd>', detail)
        self.assertLess(detail.index('<h2>'), detail.index('<h3>规格</h3>'))
        self.assertLess(detail.index('<h3>规格</h3>'), detail.index('<dl class="craft-specs"'))
        self.assertLess(detail.index('<dl class="craft-specs"'), detail.index('${renderBaseStats(record)}'))
        self.assertLess(detail.index('${renderBaseStats(record)}'), detail.index('${renderQualitySummary(record)}'))
        self.assertLess(detail.index('${renderQualitySummary(record)}'), detail.index('<h3>制作材料</h3>'))
        self.assertNotIn('detail-tags', detail)
        self.assertEqual(detail.count('<h3>规格</h3>'), 1)
        self.assertNotIn('recordManufacturer(record)', detail)

    def test_craft_specs_have_scoped_compact_columns_and_wrapping_values(self) -> None:
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        grid = styles.split('.craft-specs {', 1)[1].split('}', 1)[0]
        self.assertIn('grid-auto-flow: column', grid)
        self.assertIn('grid-auto-columns: minmax(0, 1fr)', grid)
        self.assertIn('gap: 6px', grid)
        self.assertIn('.craft-specs { grid-auto-flow: row; grid-template-columns: repeat(2, minmax(0, 1fr)); }', styles)
        value = styles.split('.craft-specs dd {', 1)[1].split('}', 1)[0]
        self.assertIn('overflow-wrap: anywhere', value)
        self.assertIn('font-size: 12px', value)

    def test_craft_material_names_are_larger_soft_green_and_wrap_without_changing_other_labels(self) -> None:
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        name = styles.split('.material-item .material-summary strong {', 1)[1].split('}', 1)[0]
        self.assertIn('color: #9de2bf', name)
        self.assertIn('font-size: 15px', name)
        self.assertIn('white-space: normal', name)
        self.assertIn('overflow-wrap: anywhere', name)
        self.assertIn('.material-item-button:hover strong {', styles)

    def test_dialog_crosses_use_shared_centering_without_native_button_padding(self) -> None:
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        cross = styles.split('.mission-close,\n.mineral-close,\n.mineral-signal-head button,\n.plan-remove {', 1)[1].split('}', 1)[0]
        self.assertIn('display: grid', cross)
        self.assertIn('place-items: center', cross)
        self.assertIn('padding: 0', cross)
        self.assertIn('font-family: Arial, sans-serif', cross)
        self.assertIn('line-height: 1', cross)

    def test_sort_options_live_in_the_filter_header_with_clear_default_label(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        summary = html.split('<section class="summary-strip">', 1)[1].split('</section>', 1)[0]
        header = html.split('<header class="filter-head">', 1)[1].split('</header>', 1)[0]
        self.assertNotIn('class="sort-group"', summary)
        self.assertIn('class="sort-group" role="group" aria-label="排序方式"', header)
        for value, label in [("relevance", "默认"), ("name", "名称"), ("sources", "来源")]:
            self.assertRegex(header, rf'data-sort="{value}"[^>]*>{label}</button>')
        self.assertLess(header.index('class="sort-group"'), header.index('class="filter-result-badge"'))
        self.assertNotIn('>推荐</button>', html)
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        self.assertIn('.filter-head .sort-group { grid-column: 1 / -1; grid-row: 2; }', styles)

    def test_detail_actions_are_grouped_in_add_favorite_share_order(self) -> None:
        app = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
        detail = app.split("function renderDetail() {", 1)[1].split("function recordMissions", 1)[0]
        header = detail.split('<div class="detail-head">', 1)[1].split('</div>', 1)[0]
        self.assertIn('class="detail-head-labels">蓝图详情 · ', header)
        self.assertNotIn('<strong>', header.split('class="detail-head-actions"', 1)[0])
        self.assertLess(header.index('data-add-plan='), header.index('data-toggle-favorite='))
        self.assertLess(header.index('data-toggle-favorite='), header.index('data-share-blueprint='))
        self.assertEqual(detail.count('data-add-plan='), 1)
        self.assertEqual(detail.count('data-share-blueprint='), 1)
        self.assertNotIn('detail-tools', detail)
        dismantle = app.split("function renderDismantleDetail(record) {", 1)[1].split("function renderDetail()", 1)[0]
        self.assertIn('class="detail-head-labels"><span>拆解详情</span><strong>', dismantle)
        self.assertLess(dismantle.index('data-toggle-favorite='), dismantle.index('data-share-blueprint='))
        self.assertNotIn('data-add-plan=', dismantle)

    def test_result_header_is_readable_and_matches_card_insets(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        header = styles.split(".result-head {", 1)[1].split("}", 1)[0]
        self.assertIn("font-size: 12px", header)
        self.assertIn("padding: 5px 23px", header)
        self.assertIn("gap: 10px", header)
        self.assertIn("物品名称 / 规格", html)
        self.assertIn(".result-head > span:last-child { text-align: center; }", styles)
        self.assertIn(".result-head { column-gap: 6px; padding-inline: 21px; }", styles)

    def test_plan_and_favorites_entries_are_larger_and_distinct_from_detail_actions(self) -> None:
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        entry = styles.split(".favorites-toggle {", 1)[1].split("}", 1)[0]
        self.assertIn("min-height: 42px", entry)
        self.assertIn("font-size: 15px", entry)
        self.assertNotIn("color:", entry)
        shared = styles.split(".favorites-toggle,", 1)[1].split("}", 1)[0]
        self.assertIn("color: var(--orange)", shared)
        self.assertNotIn("border-radius:", entry)
        count = styles.split(".summary-controls .favorites-toggle strong {", 1)[1].split("}", 1)[0]
        self.assertIn("font-size: 15px", count)
        self.assertIn("color: inherit", count)
        self.assertIn("margin: 0", count)
        self.assertNotIn("border-left", count)
        self.assertNotIn("background:", count)

    def test_ship_weapon_summaries_wrap_complete_types_without_measured_abbreviations(self) -> None:
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        app = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
        summary = styles.split(".row-main small.weapon-summary {", 1)[1].split("}", 1)[0]
        self.assertIn("white-space: normal", summary)
        self.assertIn("overflow: visible", summary)
        self.assertIn("overflow-wrap: anywhere", summary)
        self.assertNotIn("fitRecordSummaries", app)
        self.assertNotIn("data-summary-short", app)

    def test_task_source_badges_use_a_separate_color_without_changing_other_badges(self) -> None:
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        badge = styles.split('html[data-query-mode="craft"] .source-badge:not(.muted) {', 1)[1].split("}", 1)[0]
        self.assertIn("color: #9cccf5", badge)
        self.assertIn("rgba(156, 204, 245, 0.36)", badge)
        default = styles.split(".source-badge {", 1)[1].split("}", 1)[0]
        self.assertIn("color: var(--orange)", default)

    def test_planner_has_scoped_compact_layout_and_independent_explanation_spacing(self) -> None:
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".mission-dialog.planner-dialog { width: min(640px,", styles)
        explanation = styles.split(".planner-dialog .plan-explanation {", 1)[1].split("}", 1)[0]
        self.assertIn("margin: 0 0 10px", explanation)
        self.assertIn(".plan-material-table { width: 100%; border-collapse: collapse; table-layout: fixed; }", styles)
        self.assertIn("grid-template-columns: 32px 44px 32px", styles)
        self.assertIn("grid-template-columns: 40px 48px 40px", styles)
        self.assertIn(".plan-stepper button {", styles)
        self.assertIn("input::-webkit-inner-spin-button", styles)
        self.assertNotIn(".plan-time", styles)

    def test_plan_item_names_have_priority_over_secondary_totals_and_controls(self) -> None:
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        name = styles.split(".plan-row > strong {", 1)[1].split("}", 1)[0]
        self.assertIn("color: var(--orange)", name)
        self.assertIn("font-size: 16px", name)
        self.assertIn("line-height: 1.45", name)
        metadata = styles.split(".plan-item-meta {", 1)[1].split("}", 1)[0]
        self.assertIn("color: var(--muted)", metadata)
        self.assertIn("font-size: 12px", metadata)
        self.assertIn("font-weight: 400", metadata)
        summary = styles.split(".plan-summary strong {", 1)[1].split("}", 1)[0]
        self.assertIn("font-size: 14px", summary)
        self.assertNotIn("var(--cyan)", summary)
        button = styles.split(".plan-stepper button {", 1)[1].split("}", 1)[0]
        self.assertIn("width: 32px", button)
        self.assertIn("height: 32px", button)
        unit_time = styles.split(".plan-unit-time {", 1)[1].split("}", 1)[0]
        self.assertIn("color: var(--muted)", unit_time)
        self.assertIn("font-size: 12px", unit_time)
        self.assertIn("font-weight: 400", unit_time)
        controls = styles.split(".plan-controls {", 1)[1].split("}", 1)[0]
        self.assertIn("gap: 16px", controls)

    def test_base_attribute_labels_can_wrap_without_truncation(self) -> None:
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        scoped_rule = styles.split(".base-stats .spec-item strong {", 1)[1].split("}", 1)[0]
        self.assertIn("white-space: normal", scoped_rule)
        self.assertIn("overflow-wrap: anywhere", scoped_rule)
        self.assertIn("overflow: visible", scoped_rule)

    def test_plan_requirement_numbers_have_distinct_colors_but_units_remain_muted(self) -> None:
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        quality = styles.split(".plan-material-table .plan-quality-value {", 1)[1].split("}", 1)[0]
        amount = styles.split(".plan-material-table .plan-amount-value {", 1)[1].split("}", 1)[0]
        self.assertIn("color: #b8c9f1", quality)
        self.assertIn("font-size: 13px", quality)
        self.assertIn("color: #9de2bf", amount)
        self.assertIn("font-size: 14px", amount)
        self.assertIn(".plan-material-table td:last-child { color: var(--muted); }", styles)

    def test_mineral_footer_labels_data_update_not_check_time(self) -> None:
        app = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
        footer = app.split('<footer class="mineral-source">', 1)[1].split("</footer>", 1)[0]
        self.assertIn("数据更新 ${escapeHtml(updatedAt)}", footer)
        self.assertNotIn("更新时间", footer)
        self.assertNotIn("最近检查", footer)

    def test_creator_credit_is_consistent(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn('<span class="author-line">制作：Ayuan</span>', homepage)
        self.assertIn('<span class="mineral-author">制作：Ayuan</span>', app)
        for text in (homepage, app):
            self.assertNotIn("by: A Yuan", text)

    def test_public_fleet_brand_uses_xingyuan_name(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(">星远舰队</a>", homepage)
        self.assertIn("<strong>星远</strong>", homepage)
        self.assertNotIn("<strong>星远舰队</strong>", homepage)
        self.assertNotIn("<strong>星际远航者</strong>", homepage)

    def test_empty_mineral_state_does_not_name_upstream_sources(self) -> None:
        app = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
        for attribution in (
            "UEX 当前",
            "来源：UEX",
            "来源: UEX",
            "来源：SCMDB",
            "来源: SCMDB",
        ):
            self.assertNotIn(attribution, app)


if __name__ == "__main__":
    unittest.main()
