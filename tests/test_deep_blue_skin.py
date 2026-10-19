import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeepBlueSkinTests(unittest.TestCase):
    def test_surfaces_are_uniform_navy_without_background_gradients(self) -> None:
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        for token in ["--bg: #050b14", "--bg-2: #081321", "--glass: #0e2a40",
                      "--glass-strong: #102f48", "--row: #0b2439"]:
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
        self.assertIn(".plan-material-table tbody tr { box-shadow: var(--shadow-control)", styles)
        self.assertIn(".plan-material-name { width: 50%; }", styles)
        self.assertIn(".plan-material-quality { width: 22%; }", styles)
        self.assertIn(".plan-material-quantity { width: 28%; }", styles)


if __name__ == "__main__":
    unittest.main()
