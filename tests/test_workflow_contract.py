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

    def test_network_grace_preserves_deployment_checks_and_failure_reporting(self) -> None:
        for name, timeout in (
            ("Verify current EdgeOne production snapshot", 0),
            ("Verify EdgeOne production deployment", 900),
            ("Roll back an unhealthy automated refresh", 900),
        ):
            step = self.workflow.split(f"- name: {name}", 1)[1].split("- name:", 1)[0]
            self.assertIn(f"--timeout {timeout}", step)
            self.assertIn("--network-timeout 300", step)
        report = self.workflow.split("- name: Report refresh source failure", 1)[1]
        for step in ("blueprint_refresh", "mineral_locations", "production_health", "production_snapshot"):
            self.assertIn(f"steps.{step}.outcome == 'failure'", report)
        self.assertIn("exit 1", report)
        self.assertIn('git revert --no-edit "${{ steps.commit_refresh.outputs.commit_sha }}"', self.workflow)

    def test_backup_upload_includes_hidden_directory_with_two_week_retention(self) -> None:
        upload = self.workflow.split("- name: Upload data backup", 1)[1].split("- name:", 1)[0]
        self.assertIn("path: .data-backups/", upload)
        self.assertIn("include-hidden-files: true", upload)
        self.assertIn("retention-days: 14", upload)

    def test_refresh_commit_only_stages_generated_data(self) -> None:
        git_add_line = next(
            line.strip()
            for line in self.workflow.splitlines()
            if line.strip().startswith("git add ")
        )
        self.assertNotIn("index.html", git_add_line)
        self.assertNotIn("assets/app.js", git_add_line)
        self.assertIn("data/blueprint-index.json", git_add_line)
        self.assertIn("data/mineral-locations.json", git_add_line)

    def test_scheduled_workflow_does_not_refresh_mineral_signals(self) -> None:
        self.assertNotIn("python scripts/refresh_mineral_signals.py", self.workflow)
        self.assertNotIn("steps.mineral_signals.outcome", self.workflow)
        self.assertIn('--mineral-signals-outcome "skipped"', self.workflow)


if __name__ == "__main__":
    unittest.main()
