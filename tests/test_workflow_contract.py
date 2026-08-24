from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "refresh-blueprint-data.yml"


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_official_actions_use_node24_releases(self) -> None:
        for action in (
            "actions/checkout@v7",
            "actions/setup-python@v7",
            "actions/setup-node@v7",
            "actions/upload-artifact@v7",
        ):
            self.assertIn(action, self.workflow)

    def test_no_change_runs_verify_production(self) -> None:
        self.assertIn("id: production_snapshot", self.workflow)
        self.assertIn("if: steps.commit_refresh.outputs.changed != 'true'", self.workflow)
        self.assertIn("steps.production_snapshot.outcome == 'failure'", self.workflow)


if __name__ == "__main__":
    unittest.main()
