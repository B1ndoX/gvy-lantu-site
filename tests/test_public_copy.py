from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicCopyTests(unittest.TestCase):
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
