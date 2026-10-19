import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeepBlueSkinTests(unittest.TestCase):
    def test_surfaces_are_uniform_navy_without_background_gradients(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        for token in ["--bg: #030e1c", "--bg-2: #061526", "--glass: #061c32",
                      "--glass-strong: var(--glass)", "--row: #0b243b"]:
            self.assertIn(token, styles)
        self.assertNotRegex(styles, r"(?:linear|radial|conic)-gradient\s*\(")
        self.assertIn("background: var(--bg);", styles)
        self.assertIn("background: var(--glass);", styles)
        shell = styles.split(".app-shell {", 1)[1].split("}", 1)[0]
        self.assertIn("background: transparent", shell)
        self.assertIn("box-shadow: none", shell)

    def test_elevation_uses_shared_shadows_and_thin_edge_highlights(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        panel = styles.split("--shadow-panel:", 1)[1].split(";", 1)[0]
        rim = styles.split("--shadow-panel-rim:", 1)[1].split(";", 1)[0]
        self.assertIn("var(--shadow-panel-rim)", panel)
        self.assertIn("inset 0 1px 0 var(--edge-highlight)", rim)
        for selector in [".filter-board {", ".results-panel,\n.detail-panel {",
                         ".filter-menu {", ".mineral-card {", ".mission-dialog {"]:
            rule = styles.split(selector, 1)[1].split("}", 1)[0]
            self.assertIn("var(--shadow-panel)", rule)
        self.assertIn(".quality-number input,", styles)
        self.assertIn('input[type="range"]:not(:focus)', styles)

    def test_cancelled_unit_duration_move_stays_cancelled(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        app = (ROOT / "assets/app.js").read_text(encoding="utf-8")
        unit = styles.split(".plan-unit-time {", 1)[1].split("}", 1)[0]
        self.assertIn("font-size: 12px", unit)
        self.assertIn("color: var(--muted)", unit)
        self.assertIn('<div class="plan-controls"><div class="plan-unit-time">', app)
        self.assertNotIn("plan-durations", app)

    def test_previously_unframed_primary_header_uses_the_same_surface_system(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        for selector in [".topbar {", ".summary-strip {"]:
            rule = styles.split(selector, 1)[1].split("}", 1)[0]
            self.assertIn("background: var(--glass-strong)", rule)
            self.assertIn("box-shadow:", rule)
            self.assertIn("margin-inline: clamp(0px, 2vw, 28px)", rule)
        self.assertIn(".mission-dialog-footer,", styles)
        self.assertIn(".mineral-card-head,", styles)
        self.assertIn(".plan-choice select,", styles)
        self.assertIn("minmax(160px, 1fr) max-content", styles)
        self.assertIn("minmax(92px, 1fr) minmax(142px, 1fr)", styles)

    def test_plan_materials_share_raised_row_surface_without_changing_columns(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        self.assertIn("border-collapse: separate; border-spacing: 0 4px", styles)
        row = styles.split(".plan-material-table tbody tr {", 1)[1].split("}", 1)[0]
        self.assertIn("box-shadow: var(--shadow-control-elevation)", row)
        cells = styles.split(".plan-material-table tbody th, .plan-material-table tbody td {", 1)[1].split("}", 1)[0]
        self.assertIn("background: var(--row)", cells)
        self.assertIn("box-shadow: var(--shadow-control-edge)", cells)
        self.assertNotRegex(styles, r"\.plan-material-table\s+(?:tbody\s+)?tr::?(?:before|after)")
        self.assertIn(".plan-material-name { width: 50%; }", styles)
        self.assertIn(".plan-material-quality { width: 22%; }", styles)
        self.assertIn(".plan-material-quantity { width: 28%; }", styles)

    def test_rim_light_stays_local_and_joined_header_has_no_second_top_rim(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        rim = styles.split("--shadow-panel-rim:", 1)[1].split(";", 1)[0]
        self.assertIn("inset 0 5px 6px -4px", rim)
        summary = styles.split(".summary-strip {", 1)[1].split("}", 1)[0]
        self.assertIn("box-shadow: var(--shadow-joined)", summary)
        commands = styles.split(".favorite-detail-button {", 1)[1].split("}", 1)[0]
        self.assertIn("background: var(--surface-command)", commands)
        self.assertIn("box-shadow: var(--shadow-command)", commands)

    def test_opaque_sticky_result_header_preserves_the_shared_top_rim(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        header = styles.split(".result-head {", 1)[1].split("}", 1)[0]
        self.assertIn("background: var(--surface-header)", header)
        self.assertIn("box-shadow: var(--shadow-panel-rim)", header)
        self.assertNotIn("var(--shadow-elevation)", header)

    def test_unconfirmed_placeholders_are_brighter_without_becoming_confirmed(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        self.assertIn("color: rgba(174, 208, 222, 0.65)", styles)
        self.assertIn("color: rgba(172, 183, 191, 0.78)", styles)
        self.assertIn('.material-quality .quality-number[data-confirmed="true"] { color: var(--cyan); }', styles)

    def test_nested_numeric_fields_highlight_the_wrapper_not_an_inner_box(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        for selector in [".quality-number input:focus {", ".plan-row input:focus {"]:
            rule = styles.split(selector, 1)[1].split("}", 1)[0]
            self.assertIn("outline: none", rule)
            self.assertIn("box-shadow: none", rule)
        stepper = styles.split(".plan-stepper:focus-within {", 1)[1].split("}", 1)[0]
        self.assertIn("border-color: var(--cyan)", stepper)
        self.assertIn("box-shadow: var(--shadow-hover)", stepper)
        self.assertIn(".quality-number:focus-within {", styles)

    def test_filter_menu_offset_does_not_change_its_size_or_filter_grid(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        menu = styles.split(".filter-menu {", 1)[1].split("}", 1)[0]
        self.assertIn("translateX(var(--filter-menu-offset, 0px))", menu)
        self.assertIn("width: max-content", menu)
        self.assertIn("max-width: min(360px, calc(100vw - 32px))", menu)

    def test_site_footer_matches_the_requested_unframed_wikelo_style(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        footer = styles.split(".site-footer {", 1)[1].split("}", 1)[0]
        self.assertIn("background: transparent", footer)
        self.assertIn("border-top: 1px", footer)
        self.assertIn('class="footer-beian-separator" aria-hidden="true"></span>', html)
        self.assertIn('alt="公安联网备案图标" width="15" height="17"', html)
        for url in ["https://beian.miit.gov.cn/", "https://beian.mps.gov.cn/#/query/webSearch?code=61019702000690"]:
            self.assertIn(url, html)

    def test_navy_depth_uses_blue_edges_without_changing_interaction_colors(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        self.assertIn("--edge-highlight: rgba(93, 174, 235, 0.3)", styles)
        self.assertIn("--shadow-control-edge: inset 0 1px 0 rgba(88, 163, 217, 0.23)", styles)
        self.assertIn("--surface-hover: #1b455f", styles)
        self.assertIn("--surface-selected: #164f68", styles)
        for token in ["--text: #e2f6ff", "--text-strong: #f4faff", "--muted: #aed0de",
                      "--cyan: #7eddf2", "--orange: #ffc468"]:
            self.assertIn(token, styles)

    def test_same_role_surfaces_share_tokens_without_flattening_the_hierarchy(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        for token in ["--glass-strong", "--surface-header"]:
            self.assertIn(f"{token}: var(--glass);", styles)
        self.assertIn("--group: var(--row);", styles)
        self.assertIn("--row: #0b243b;", styles)
        self.assertIn("--surface-inset: #031321;", styles)
        self.assertIn("--surface-control: #061e33;", styles)
        self.assertNotIn("--row: var(--glass);", styles)
        rows = styles.split(".plan-row,\n.quality-result-item,", 1)[1].split("}", 1)[0]
        self.assertIn("background: var(--row)", rows)
        self.assertIn("box-shadow: var(--shadow-control)", rows)

    def test_nested_groups_and_quality_fields_use_opaque_recessed_surfaces(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        groups = styles.split(".source-item,\n.mission-pool,\n.plan-stepper,", 1)[1].split("}", 1)[0]
        self.assertIn("background: var(--surface-inset)", groups)
        self.assertIn("box-shadow: var(--shadow-inset)", groups)
        quality = styles.split(".material-quality .quality-number,\n.dismantle-summary span {", 1)[1].split("}", 1)[0]
        self.assertIn("background: var(--surface-inset)", quality)
        self.assertNotIn("rgba(", quality.split("background:", 1)[1].split(";", 1)[0])

    def test_hover_and_selection_keep_distinct_approved_paint(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        hover = styles.split(".result-card:hover:not(.active) {", 1)[1].split("}", 1)[0]
        active = styles.split(".result-card.active {", 1)[1].split("}", 1)[0]
        self.assertIn("background: var(--surface-hover)", hover)
        self.assertIn("background: var(--surface-selected)", active)
        self.assertIn("box-shadow: var(--shadow-active)", active)
        self.assertIn("--shadow-hover", styles)
        self.assertIn("inset 3px 0 0 var(--cyan)", styles)
        self.assertIn(".filter-option:not(.active):not(:disabled):hover", styles)
        self.assertIn('.mineral-system-filter button:not([aria-pressed="true"]):hover', styles)
        self.assertIn("@media (hover: hover)", styles)
        self.assertNotIn(":where(button, a[href], input, select, summary):focus-visible", styles)
        self.assertIn(".base-stats > summary:hover,", styles)
        self.assertIn(".source-more > summary:hover,", styles)

    def test_material_name_hover_does_not_add_a_nested_selection_box(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        self.assertIn("button:not(:disabled):not(.material-item-button)", styles)
        self.assertNotIn(".material-item-button:hover,", styles)
        self.assertNotIn(".material-item-button:hover {", styles)
        self.assertIn(".material-item-button:hover strong {", styles)
        hover_fills = styles.split(".filter-trigger:not(:disabled):hover,", 1)[1].split("}", 1)[0]
        for selector in [".base-stats > summary:hover", ".source-more > summary:hover"]:
            self.assertNotIn(selector, hover_fills)
        self.assertIn("button.source-mission-button:hover", hover_fills)
        self.assertNotIn("select, summary):hover", styles)
        self.assertNotIn("select, summary):focus-visible", styles)


if __name__ == "__main__":
    unittest.main()
