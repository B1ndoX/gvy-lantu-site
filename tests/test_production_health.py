from __future__ import annotations

import sys
import errno
import gzip
import io
import json
import socket
import ssl
import tempfile
import unittest
import urllib.error
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_production_health import (
    build_data_revision,
    extract_asset_revisions,
    extract_data_revision,
    check_once,
    fetch_bytes,
    fetch_gzip_json,
    is_transient_network_error,
    TransientNetworkError,
    validate_production_snapshot,
    wait_for_production,
)
from write_refresh_heartbeat import heartbeat_payload


class ProductionHealthTests(unittest.TestCase):
    def blueprints(self, version: str = "4.9.0-live.12344265") -> dict:
        return {
            "version": version,
            "releaseChannel": "LIVE",
            "dataUpdatedAt": "2026-08-18T06:59:26Z",
            "records": [{"id": f"record-{index}"} for index in range(1000)],
        }

    def minerals(self) -> dict:
        materials = {}
        for material_index in range(30):
            materials[f"Material {material_index}"] = {
                "hasReliableLocations": material_index < 25,
                "locations": {
                    "moons": [
                        {"id": material_index * 4 + offset, "signal": {"base": 3185}}
                        for offset in range(4)
                    ]
                },
            }
        return {"materials": materials}

    def test_extracts_both_fingerprinted_assets(self) -> None:
        html = (
            '<link rel="stylesheet" href="./assets/styles.css?v=abc123">'
            '<script src="./assets/app.js?v=def456"></script>'
        )
        self.assertEqual(
            extract_asset_revisions(html),
            {"styles.css": "abc123", "app.js": "def456"},
        )

    def test_extracts_built_data_revision(self) -> None:
        script = 'const DATA_VERSION = "data-0123456789abcdef";'
        self.assertEqual(extract_data_revision(script), "data-0123456789abcdef")

    def test_data_revision_changes_for_either_snapshot(self) -> None:
        baseline = build_data_revision(b'{"blueprints":1}', b'{"minerals":1}')
        changed_blueprints = build_data_revision(b'{"blueprints":2}', b'{"minerals":1}')
        changed_minerals = build_data_revision(b'{"blueprints":1}', b'{"minerals":2}')
        self.assertNotEqual(baseline, changed_blueprints)
        self.assertNotEqual(baseline, changed_minerals)

    def test_rejects_unbuilt_data_revision_placeholder(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "built data revision"):
            extract_data_revision('const DATA_VERSION = "__BUILD_DATA_VERSION__";')

    def test_accepts_matching_production_snapshot(self) -> None:
        blueprints = self.blueprints()
        minerals = self.minerals()
        validate_production_snapshot(blueprints, blueprints, minerals, minerals)

    def test_primary_mining_cannot_match_itself_but_mismatch_blueprint_build(self) -> None:
        blueprints = self.blueprints()
        minerals = self.minerals()
        minerals["metadata"] = {"schemaVersion": 2, "sourceVersion": "4.10.2-live.12913470"}
        with self.assertRaisesRegex(RuntimeError, "mining data does not match the blueprint LIVE"):
            validate_production_snapshot(blueprints, blueprints, minerals, minerals)

    def test_rejects_test_channel_snapshot(self) -> None:
        production = self.blueprints("4.10.0-ptu.12409360")
        local = self.blueprints()
        minerals = self.minerals()
        with self.assertRaisesRegex(RuntimeError, "not stable LIVE"):
            validate_production_snapshot(production, local, minerals, minerals)

    def test_rejects_different_production_data(self) -> None:
        production = self.blueprints()
        local = self.blueprints()
        production["records"][0]["id"] = "wrong"
        minerals = self.minerals()
        with self.assertRaisesRegex(RuntimeError, "does not match"):
            validate_production_snapshot(production, local, minerals, minerals)

    def test_rejects_stale_quality_enrichment(self) -> None:
        production = self.blueprints()
        local = self.blueprints()
        production["records"][0]["qualityStats"] = {"integrity": 640}
        local["records"][0]["qualityStats"] = {"integrity": 768}
        minerals = self.minerals()
        with self.assertRaisesRegex(RuntimeError, "does not match"):
            validate_production_snapshot(production, local, minerals, minerals)

    def test_rejects_stale_mission_reward_payload(self) -> None:
        production = self.blueprints()
        local = self.blueprints()
        production["missionRewards"] = {"missions": {}}
        local["missionRewards"] = {"missions": {"task": {"items": [{"name": "Rifle", "amount": 2}]}}}
        minerals = self.minerals()
        with self.assertRaisesRegex(RuntimeError, "does not match"):
            validate_production_snapshot(production, local, minerals, minerals)

    def test_builds_utc_maintenance_heartbeat(self) -> None:
        now = datetime(2026, 8, 18, 8, 0, tzinfo=timezone.utc)
        payload = heartbeat_payload("123", "abc", "success", "success", "success", now)
        self.assertEqual(payload["lastMaintenanceAt"], "2026-08-18T08:00:00Z")
        self.assertEqual(payload["blueprintRefresh"], "success")
        self.assertEqual(payload["mineralLocationsRefresh"], "success")

    def test_reads_compressed_production_json(self) -> None:
        import check_production_health

        original_fetch = check_production_health.fetch_bytes
        check_production_health.fetch_bytes = lambda _url, **_kwargs: gzip.compress(
            json.dumps({"status": "ok"}).encode("utf-8")
        )
        try:
            self.assertEqual(fetch_gzip_json("https://example.invalid/data.json.gz"), {"status": "ok"})
        finally:
            check_production_health.fetch_bytes = original_fetch

    @contextmanager
    def simulated_check(self, effects):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "dist" / "assets").mkdir(parents=True)
            blueprint_bytes = json.dumps(self.blueprints()).encode()
            mineral_bytes = json.dumps(self.minerals()).encode()
            (root / "data" / "blueprint-index.json").write_bytes(blueprint_bytes)
            (root / "data" / "mineral-locations.json").write_bytes(mineral_bytes)
            (root / "dist" / "index.html").write_text(
                '<link href="/assets/styles.css?v=abc"><script src="/assets/app.js?v=def"></script>'
            )
            revision = build_data_revision(blueprint_bytes, mineral_bytes)
            (root / "dist" / "assets" / "app.js").write_text(f'const DATA_VERSION = "{revision}";')
            elapsed = [0.0]

            def advance(seconds):
                elapsed[0] += seconds

            with (
                patch("check_production_health.ROOT", root),
                patch("check_production_health.time.monotonic", side_effect=lambda: elapsed[0]),
                patch("check_production_health.time.sleep", side_effect=advance) as sleep,
                patch("check_production_health.check_once", side_effect=effects) as probe,
                patch("sys.stdout", new_callable=io.StringIO) as output,
                patch("sys.stderr", new_callable=io.StringIO),
            ):
                yield probe, sleep, output

    def test_no_change_network_blip_recovers_and_requires_full_check(self) -> None:
        with self.simulated_check([TransientNetworkError("network unreachable"), None]) as (probe, sleep, output):
            wait_for_production("https://example.invalid", 0, 15)
            self.assertEqual(probe.call_count, 2)
            sleep.assert_called_once_with(5)
            self.assertIn("full snapshot verified", output.getvalue())
            self.assertEqual(probe.call_args.kwargs["deadline"], 300)

    def test_persistent_network_failure_still_fails_with_bounded_wait(self) -> None:
        with self.simulated_check(TransientNetworkError("network unreachable")) as (probe, sleep, _):
            with self.assertRaisesRegex(RuntimeError, "network check failed.*network unreachable"):
                wait_for_production("https://example.invalid", 0, 15, 120)
            self.assertEqual(probe.call_count, 6)
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [5, 10, 20, 30, 30, 25])

    def test_no_change_snapshot_mismatch_does_not_use_network_grace(self) -> None:
        with self.simulated_check(RuntimeError("wrong data hash")) as (probe, sleep, _):
            with self.assertRaisesRegex(RuntimeError, "snapshot check failed.*wrong data hash"):
                wait_for_production("https://example.invalid", 0, 15, 300)
            probe.assert_called_once()
            sleep.assert_not_called()

    def test_network_recovery_cannot_hide_subsequent_content_failure(self) -> None:
        effects = [TransientNetworkError("reset"), RuntimeError("invalid JSON")]
        with self.simulated_check(effects) as (probe, sleep, _):
            with self.assertRaisesRegex(RuntimeError, "snapshot check failed.*invalid JSON"):
                wait_for_production("https://example.invalid", 0, 15, 300)
            self.assertEqual(probe.call_count, 2)
            sleep.assert_called_once_with(5)

    def test_changed_deployment_still_waits_for_matching_snapshot(self) -> None:
        with self.simulated_check([RuntimeError("previous revision"), None]) as (probe, sleep, _):
            wait_for_production("https://example.invalid", 900, 15, 300)
            self.assertEqual(probe.call_count, 2)
            sleep.assert_called_once_with(15)
            self.assertEqual(probe.call_args.kwargs["deadline"], 900)

    def test_persistent_deployment_mismatch_still_fails(self) -> None:
        with self.simulated_check(RuntimeError("previous revision")) as (probe, sleep, _):
            with self.assertRaisesRegex(RuntimeError, "snapshot check failed.*previous revision"):
                wait_for_production("https://example.invalid", 20, 15, 300)
            self.assertEqual(probe.call_count, 2)
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [15, 5])

    def test_alternating_failures_do_not_restart_deadlines(self) -> None:
        effects = [TransientNetworkError("reset"), RuntimeError("wrong hash"), TransientNetworkError("reset")]
        with self.simulated_check(effects) as (probe, sleep, _):
            with self.assertRaisesRegex(RuntimeError, "network check failed"):
                wait_for_production("https://example.invalid", 20, 5, 12)
            self.assertEqual(probe.call_count, 3)
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [5, 5, 10])

    def test_healthy_snapshot_returns_immediately(self) -> None:
        with self.simulated_check([None]) as (probe, sleep, output):
            wait_for_production("https://example.invalid", 0, 15, 300)
            probe.assert_called_once()
            sleep.assert_not_called()
            self.assertNotIn("recovered", output.getvalue())

    def test_zero_network_window_preserves_strict_single_probe(self) -> None:
        with self.simulated_check(TransientNetworkError("reset")) as (probe, sleep, _):
            with self.assertRaisesRegex(RuntimeError, "network check failed"):
                wait_for_production("https://example.invalid", 0, 15, 0)
            probe.assert_called_once()
            sleep.assert_not_called()

    def test_recognizes_only_transient_request_failures(self) -> None:
        transient = [
            urllib.error.URLError(OSError(errno.ENETUNREACH, "Network is unreachable")),
            urllib.error.URLError(socket.gaierror(socket.EAI_AGAIN, "try again")),
            TimeoutError("timeout"), socket.timeout("socket timeout"), ConnectionResetError("reset"),
            urllib.error.HTTPError("https://example.invalid", 503, "unavailable", {}, None),
            urllib.error.HTTPError("https://example.invalid", 429, "rate limited", {}, None),
        ]
        permanent = [
            urllib.error.HTTPError("https://example.invalid", 403, "forbidden", {}, None),
            urllib.error.HTTPError("https://example.invalid", 404, "not found", {}, None),
            urllib.error.URLError(ssl.SSLCertVerificationError("invalid certificate")),
            RuntimeError("wrong snapshot"), ValueError("invalid JSON"),
        ]
        for error in transient:
            with self.subTest(error=error):
                self.assertTrue(is_transient_network_error(error))
        for error in permanent:
            with self.subTest(error=error):
                self.assertFalse(is_transient_network_error(error))

    def test_fetch_classifies_transport_errors_without_swallowing_permanent_errors(self) -> None:
        errors = [
            (urllib.error.URLError(TimeoutError("timeout")), TransientNetworkError),
            (urllib.error.HTTPError("https://example.invalid", 503, "unavailable", {}, None), TransientNetworkError),
            (urllib.error.URLError(ssl.SSLCertVerificationError("invalid certificate")), RuntimeError),
        ]
        for error, kind in errors:
            with self.subTest(error=error), patch("check_production_health.urllib.request.urlopen", side_effect=error):
                with self.assertRaises(kind) as raised:
                    fetch_bytes("https://example.invalid")
                self.assertIs(type(raised.exception), kind)

    def test_request_timeout_is_capped_by_remaining_budget(self) -> None:
        response = MagicMock(status=200)
        response.read.return_value = b"ok"
        response.__enter__.return_value = response
        with patch("check_production_health.time.monotonic", return_value=98), patch(
            "check_production_health.urllib.request.urlopen", return_value=response
        ) as urlopen:
            self.assertEqual(fetch_bytes("https://example.invalid", deadline=100), b"ok")
            self.assertEqual(urlopen.call_args.kwargs["timeout"], 2)
        with patch("check_production_health.time.monotonic", return_value=100), patch(
            "check_production_health.urllib.request.urlopen"
        ) as urlopen:
            with self.assertRaisesRegex(TransientNetworkError, "budget exhausted"):
                fetch_bytes("https://example.invalid", deadline=100)
            urlopen.assert_not_called()

    def test_complete_probe_uses_exact_client_keys_and_checks_both_json_forms(self) -> None:
        blueprints = self.blueprints()
        minerals = self.minerals()
        revision = "data-0123456789abcdef"
        html = '<link href="/assets/styles.css?v=abc"><script src="/assets/app.js?v=def"></script>'
        script = f'const DATA_VERSION = "{revision}";' + " " * 100
        payloads = [
            html.encode(), b"x" * 100, script.encode(),
            gzip.compress(json.dumps(blueprints).encode()), gzip.compress(json.dumps(minerals).encode()),
            json.dumps(blueprints).encode(), json.dumps(minerals).encode(),
        ]
        with patch("check_production_health.fetch_bytes", side_effect=payloads) as fetch:
            check_once("https://example.invalid", {"styles.css": "abc", "app.js": "def"},
                       revision, blueprints, minerals, deadline=300)
        urls = [call.args[0] for call in fetch.call_args_list]
        self.assertEqual(len(urls), 7)
        self.assertTrue(all("health=" not in url for url in urls[1:]))
        self.assertTrue(all(url.endswith(f"?v={revision}") for url in urls[3:]))
        self.assertTrue(all(call.kwargs["deadline"] == 300 for call in fetch.call_args_list))

        payloads[-1] = json.dumps({"materials": {}}).encode()
        with patch("check_production_health.fetch_bytes", side_effect=payloads):
            with self.assertRaisesRegex(RuntimeError, "coverage is too low"):
                check_once("https://example.invalid", {"styles.css": "abc", "app.js": "def"},
                           revision, blueprints, minerals)


if __name__ == "__main__":
    unittest.main()
