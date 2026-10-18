from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicCopyTests(unittest.TestCase):
    def test_planner_has_scoped_compact_layout_and_independent_explanation_spacing(self) -> None:
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".mission-dialog.planner-dialog { width: min(640px,", styles)
        explanation = styles.split(".planner-dialog .plan-explanation {", 1)[1].split("}", 1)[0]
        self.assertIn("margin: 10px 0 12px", explanation)
        self.assertIn(".plan-material-table { width: 100%; border-collapse: collapse; table-layout: fixed; }", styles)
        self.assertIn("grid-template-columns: 44px 56px 44px", styles)
        self.assertIn(".plan-stepper button {", styles)
        self.assertIn("input::-webkit-inner-spin-button", styles)
        self.assertNotIn(".plan-time", styles)

    def test_base_attribute_labels_can_wrap_without_truncation(self) -> None:
        styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
        scoped_rule = styles.split(".base-stats .spec-item strong {", 1)[1].split("}", 1)[0]
        self.assertIn("white-space: normal", scoped_rule)
        self.assertIn("overflow-wrap: anywhere", scoped_rule)
        self.assertIn("overflow: visible", scoped_rule)

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
