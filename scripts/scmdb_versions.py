#!/usr/bin/env python3
"""Select stable LIVE releases from the SCMDB version manifest."""

from __future__ import annotations

import re
from typing import Any, Iterable


LIVE_TOKEN = "live"
TEST_CHANNEL_TOKENS = {"ptu", "eptu", "tech", "preview", "techpreview", "evocati"}


def version_tokens(version: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", version.casefold()) if token]


def is_live_version(version: str) -> bool:
    tokens = version_tokens(version)
    return LIVE_TOKEN in tokens and not TEST_CHANNEL_TOKENS.intersection(tokens)


def version_sort_key(version: str) -> tuple[int, ...]:
    """Sort release and build numbers numerically, not lexicographically."""
    return tuple(int(value) for value in re.findall(r"\d+", version))


def select_latest_live_version(versions: Iterable[dict[str, Any]]) -> dict[str, str]:
    candidates: list[dict[str, str]] = []
    for entry in versions:
        version = str(entry.get("version") or "").strip()
        filename = str(entry.get("file") or "").strip()
        if not is_live_version(version) or not filename:
            continue
        if "/" in filename or "\\" in filename or not filename.endswith(".json"):
            raise RuntimeError(f"SCMDB returned an unsafe filename for {version}: {filename}")
        candidates.append({"version": version, "file": filename})

    if not candidates:
        raise RuntimeError("SCMDB versions.json contains no stable LIVE release")
    return max(candidates, key=lambda entry: version_sort_key(entry["version"]))
