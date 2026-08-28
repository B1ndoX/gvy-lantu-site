import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from refresh_mineral_signals import (  # noqa: E402
    apply_signal_definitions,
    parse_signal_definitions,
)


SOURCE_NAMES = [
    "Quantanium",
    "Stileron",
    "Savrilium",
    "Ouratite",
    "Riccite",
    "Lindinium",
    "Beryl",
    "Taranite",
    "Borase",
    "Gold",
    "Bexalite",
    "Laranite",
    "Aslarite",
    "Titanium",
    "Tungsten",
    "Agricium",
    "Torite",
    "Hephaestanite",
    "Copper",
    "Iron",
]


def source_html(*, include_version: bool = True, base_offset: int = 0) -> str:
    rows = []
    for index, name in enumerate(SOURCE_NAMES):
        rows.append(f"{{ name: '{name}', rs: {3170 + base_offset + index * 15}, maxCluster: 5 }}")
    rows.append("{ name: 'ROC Mineables', rs: 4000, maxCluster: 999, searchOnly: true }")
    heading = "<div>RADAR SIGNATURES 4.9</div>" if include_version else "<div>Radar Signatures</div>"
    return f"""
      {heading}
      <script>
      const RADAR_DATA = [
        {','.join(rows)}
      ];
      </script>
    """


class MineralSignalRefreshTests(unittest.TestCase):
    def test_parser_maps_quantanium_and_ignores_search_entries(self):
        version, definitions = parse_signal_definitions(source_html())
        self.assertEqual(version, "4.9")
        self.assertIn("Quantainium", definitions)
        self.assertNotIn("Quantanium", definitions)
        self.assertNotIn("ROC Mineables", definitions)

    def test_parser_uses_stable_content_revision_when_version_label_is_missing(self):
        revision, definitions = parse_signal_definitions(source_html(include_version=False))
        repeated_revision, _ = parse_signal_definitions(source_html(include_version=False))
        changed_revision, _ = parse_signal_definitions(source_html(include_version=False, base_offset=1))

        self.assertRegex(revision, r"^content-[0-9a-f]{12}$")
        self.assertEqual(revision, repeated_revision)
        self.assertNotEqual(revision, changed_revision)
        self.assertIn("Quantainium", definitions)

    def test_parser_rejects_incomplete_source(self):
        with self.assertRaisesRegex(RuntimeError, "only 1 definitions"):
            parse_signal_definitions(
                "<div>RADAR SIGNATURES 4.9</div><script>const RADAR_DATA = [\n"
                "{ name: 'Tungsten', rs: 3870, maxCluster: 5 }\n];</script>"
            )

    def test_apply_updates_material_and_location_values(self):
        _, definitions = parse_signal_definitions(source_html())
        materials = {}
        for name, definition in definitions.items():
            materials[name] = {
                "signal": {"values": [1]},
                "locations": {
                    "moons": [
                        {
                            "en": f"{name} Moon",
                            "signal": {
                                "values": [1],
                                "probability": 28.5,
                                "sourceLocation": "TEST",
                            },
                        }
                        for _ in range(5)
                    ]
                },
            }
        payload = {"metadata": {}, "materials": materials}
        changed, material_count, location_count = apply_signal_definitions(
            payload,
            definitions,
            "4.9",
            datetime(2026, 8, 16, tzinfo=timezone.utc),
        )
        tungsten = payload["materials"]["Tungsten"]
        expected = [definitions["Tungsten"]["base"] * value for value in range(1, 6)]
        self.assertTrue(changed)
        self.assertEqual(material_count, 20)
        self.assertEqual(location_count, 100)
        self.assertEqual(tungsten["signal"]["values"], expected)
        self.assertEqual(tungsten["locations"]["moons"][0]["signal"]["values"], expected)
        self.assertEqual(tungsten["locations"]["moons"][0]["signal"]["probability"], 28.5)
        self.assertEqual(payload["metadata"]["signalSourceVersion"], "4.9")


if __name__ == "__main__":
    unittest.main()
