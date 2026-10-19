import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LinkedFilterTests(unittest.TestCase):
    def test_frontend_filter_contracts(self):
        result = subprocess.run(["node", "--test", "tests/filtering.test.mjs"], cwd=ROOT,
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_watermark_is_decorative_and_retains_opaque_surfaces(self):
        styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        watermark = styles.split("body::before,", 1)[1].split("}", 1)[0]
        self.assertIn("pointer-events: none", watermark)
        self.assertIn("z-index: -1", watermark)
        self.assertIn('background: url("./fleet-watermark.png") center / contain no-repeat', watermark)
        self.assertIn("opacity: 0.04", watermark)
        self.assertNotIn("mask:", watermark)
        self.assertNotIn("filter:", watermark)
        self.assertNotIn("blend-mode:", watermark)
        self.assertNotIn(".plan-material-table", watermark)
        dialog_watermark = styles.split(".mission-dialog::before,", 2)[2].split("}", 1)[0]
        self.assertIn("opacity: 0.03", dialog_watermark)
        self.assertIn("width: min(86%, 640px)", dialog_watermark)
        self.assertTrue((ROOT / "assets/fleet-watermark.png").is_file())


if __name__ == "__main__":
    unittest.main()
