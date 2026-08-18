#!/usr/bin/env python3
"""Record a low-churn maintenance heartbeat for scheduled workflow continuity."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEARTBEAT_PATH = ROOT / ".github" / "refresh-heartbeat.json"
VALID_OUTCOMES = {"success", "failure", "cancelled", "skipped"}


def heartbeat_payload(
    run_id: str,
    commit: str,
    blueprint_outcome: str,
    mineral_locations_outcome: str,
    mineral_signals_outcome: str,
    now: datetime,
) -> dict:
    outcomes = {
        "blueprintRefresh": blueprint_outcome,
        "mineralLocationsRefresh": mineral_locations_outcome,
        "mineralSignalsRefresh": mineral_signals_outcome,
    }
    invalid = {name: value for name, value in outcomes.items() if value not in VALID_OUTCOMES}
    if invalid:
        raise ValueError(f"invalid refresh outcomes: {invalid}")
    return {
        **outcomes,
        "commit": commit,
        "lastMaintenanceAt": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "workflowRunId": run_id,
    }


def write_heartbeat(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.unlink(missing_ok=True)
    try:
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Record the GVY blueprint refresh maintenance heartbeat.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--blueprint-outcome", required=True, choices=sorted(VALID_OUTCOMES))
    parser.add_argument("--mineral-locations-outcome", required=True, choices=sorted(VALID_OUTCOMES))
    parser.add_argument("--mineral-signals-outcome", required=True, choices=sorted(VALID_OUTCOMES))
    args = parser.parse_args()
    payload = heartbeat_payload(
        args.run_id,
        args.commit,
        args.blueprint_outcome,
        args.mineral_locations_outcome,
        args.mineral_signals_outcome,
        datetime.now(timezone.utc),
    )
    write_heartbeat(HEARTBEAT_PATH, payload)
    print(f"maintenance heartbeat recorded: {HEARTBEAT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
