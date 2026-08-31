from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicCopyTests(unittest.TestCase):
    def test_public_fleet_brand_uses_xingyuan_name(self) -> None:
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(">星远舰队</a>", homepage)
        self.assertIn("<strong>星远舰队</strong>", homepage)
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
