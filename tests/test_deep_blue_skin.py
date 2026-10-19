import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeepBlueSkinTests(unittest.TestCase):
    def test_surfaces_are_uniform_navy_without_background_gradients(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        for token in ["--bg: #041322", "--bg-2: #081a2b", "--glass: #092337",
                      "--glass-strong: #0b2a43", "--row: #0d2b42"]:
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
        self.assertIn("inset 0 1px 0 var(--edge-highlight)", panel)
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
        panel = styles.split("--shadow-panel:", 1)[1].split(";", 1)[0]
        self.assertIn("inset 0 5px 6px -4px", panel)
        summary = styles.split(".summary-strip {", 1)[1].split("}", 1)[0]
        self.assertIn("box-shadow: var(--shadow-joined)", summary)
        commands = styles.split(".favorite-detail-button {", 1)[1].split("}", 1)[0]
        self.assertIn("background: var(--surface-command)", commands)
        self.assertIn("box-shadow: var(--shadow-command)", commands)

    def test_hover_and_selection_keep_distinct_approved_paint(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        hover = styles.split(".result-card:hover:not(.active) {", 1)[1].split("}", 1)[0]
        active = styles.split(".result-card.active {", 1)[1].split("}", 1)[0]
        self.assertIn("background: var(--surface-hover)", hover)
        self.assertIn("background: var(--surface-selected)", active)
        self.assertIn("box-shadow: var(--shadow-active)", active)
        self.assertIn("--shadow-hover", styles)
        self.assertIn("inset 3px 0 0 var(--cyan)", styles)
        self.assertIn(".filter-option:not(.active):hover", styles)
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
