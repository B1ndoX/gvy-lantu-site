"""NAS localization support for the existing refresh pipeline; no standalone CLI."""

from __future__ import annotations

import gzip
import io
import hashlib
import json
import os
import re
import shlex
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/official-localization/localization/starcitizen/nas-keyed-names.json"
NAS_PATH = "/volume1/docker/starcitizen-shared-input/localization/data/localization/chinese_(simplified)/global.ini"
# This export is an English localization-key bridge, never a source of gameplay stats.
LABEL_COMMIT = "f45ee0159780acc67578ac0b006a6d37aade6884"
LABEL_VERSION = "4.10.0-LIVE.12519617"
LABEL_URL = f"https://raw.githubusercontent.com/StarCitizenWiki/scunpacked-data/{LABEL_COMMIT}/labels.json"
SOURCE_REPO = "B1ndoX/gvy-lantu-site"
SOURCE_BRANCH = "nas-localization"
MAX_SOURCE_BYTES = 20 * 1024 * 1024
ADAPTER_VERSION = 3


def fetch_bytes(url: str, limit: int = MAX_SOURCE_BYTES) -> bytes:
    headers = {"User-Agent": "GVY Lantu Site/1.0"}
    if url.startswith("https://api.github.com/") and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=90) as response:
                value = response.read(limit + 1)
            if len(value) > limit:
                raise ValueError("localization download exceeds size limit")
            return value
        except (OSError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def read_github_source(version: str) -> tuple[bytes, dict]:
    ref = json.loads(fetch_bytes(f"https://api.github.com/repos/{SOURCE_REPO}/git/ref/heads/{SOURCE_BRANCH}"))
    commit = (ref.get("object") or {}).get("sha", "")
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise RuntimeError("NAS source branch has no immutable commit SHA")
    base = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{commit}"
    manifest = json.loads(fetch_bytes(f"{base}/source.json"))
    if (manifest.get("schemaVersion") != 1 or manifest.get("sourcePath") != NAS_PATH
            or manifest.get("versionPrecision") != "major-minor-only"
            or not re.fullmatch(r"[a-f0-9]{64}", str(manifest.get("sha256", "")))
            or type(manifest.get("byteLength")) is not int
            or not 0 < manifest["byteLength"] <= MAX_SOURCE_BYTES):
        raise RuntimeError("invalid NAS source manifest")
    if series(manifest.get("versionLabel", "")) != series(version):
        raise RuntimeError("NAS source manifest series does not match selected LIVE")
    with gzip.GzipFile(fileobj=io.BytesIO(fetch_bytes(f"{base}/global.ini.gz"))) as stream:
        raw = stream.read(MAX_SOURCE_BYTES + 1)
    if len(raw) != manifest["byteLength"] or hashlib.sha256(raw).hexdigest() != manifest["sha256"]:
        raise RuntimeError("NAS source byte length or SHA256 mismatch; keeping verified cache")
    if parse_ini(raw).get("frontend_pu_version") != manifest["versionLabel"]:
        raise RuntimeError("NAS source version label differs from manifest")
    print(f"NAS input verified at {commit}: {manifest['sha256']}")
    return raw, {"inputCommit": commit, "sourceUpdatedAt": manifest.get("sourceUpdatedAt", "")}


def series(version: str) -> str:
    match = re.match(r"(\d+\.\d+)(?:\D|$)", version)
    if not match:
        raise RuntimeError(f"localization version is not identifiable: {version}")
    return match[1]


def parse_ini(raw: bytes) -> dict[str, str]:
    entries = {}
    for line in raw.decode("utf-8-sig").splitlines():
        if not line or line.startswith((";", "#")) or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().casefold()
        if key in entries and entries[key] != value.strip():
            raise RuntimeError(f"conflicting localization key: {key}")
        entries[key] = value.strip()
    return entries


def clean_label(text: str, english: str) -> str:
    text = text.replace("\\n", "\n").splitlines()[0].strip() if text else ""
    text = re.sub(r"</?EM\d+>", "", text, flags=re.IGNORECASE)
    if not text or text.startswith(("[PH]", "(PH)", "<-=", "=", "@")):
        return ""
    # The NAS package often appends the exact English label to its Chinese name.
    if re.search(r"[\u3400-\u9fff]", text):
        for suffix in (f"({english})", f"（{english}）", english):
            if suffix and text.endswith(suffix):
                text = text[:-len(suffix)].strip()
                break
    return text


def domain(key: str) -> str:
    key = key.casefold()
    if key.startswith("items_commodities_"):
        return "material"
    if key.startswith("manufacturer_name"):
        return "manufacturer"
    if key.startswith(("item_name", "item_mining_")) or (key.startswith("nozzle_") and key.endswith("_name")):
        return "item"
    if key.startswith("vehicle_name"):
        return "vehicle"
    if key.startswith("crafting_ui_slotname_"):
        return "slot"
    if key.startswith("statname_gpp_"):
        return "property"
    if key.startswith("rr_") or re.match(r"^(stanton|pyro|nyx)(\d|$|_?star$)", key) or key == "delamar":
        return "location"
    return "other"


def entries_hash(entries: dict) -> str:
    return hashlib.sha256(json.dumps(entries, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def build_snapshot(raw: bytes, labels: dict, version: str, *, label_commit: str = LABEL_COMMIT, label_version: str = LABEL_VERSION) -> dict:
    chinese = parse_ini(raw)
    declared = chinese.get("frontend_pu_version", "")
    if series(declared) != series(version) or series(label_version) != series(version):
        raise RuntimeError("NAS/English-key bridge series does not match the selected LIVE; no files replaced")
    if len(chinese) < 70000:
        raise RuntimeError("NAS localization coverage is unexpectedly low")
    entries = {}
    for key, english in labels.items():
        key = key.lstrip("\ufeff").casefold()
        if not isinstance(english, str) or not english.strip() or len(english) > 160:
            continue
        if "\n" in english or "\\n" in english or "desc" in key:
            continue
        translated = clean_label(chinese.get(key, ""), english.strip())
        if translated:
            entries[key] = {"english": english.strip(), "chinese": translated, "domain": domain(key)}
    if sum(entry["domain"] == "item" for entry in entries.values()) < 7000:
        raise RuntimeError("NAS keyed item coverage is unexpectedly low")
    return {"metadata": {
        "adapterVersion": ADAPTER_VERSION,
        "sourcePath": NAS_PATH,
        "sourceSha256": hashlib.sha256(raw).hexdigest(),
        "sourceVersionLabel": declared,
        "versionPrecision": "major-minor-only",
        "series": series(declared),
        "englishKeyCommit": label_commit,
        "englishKeyVersion": label_version,
        "englishKeyUrl": f"https://raw.githubusercontent.com/StarCitizenWiki/scunpacked-data/{label_commit}/labels.json",
        "exactBuildVerified": False,
        "entryCount": len(chinese),
        "keyedEntryCount": len(entries),
        "entriesSha256": entries_hash(entries),
        "importedAt": datetime.now(timezone.utc).isoformat(),
    }, "entries": entries}


def validate_snapshot(snapshot: dict, version: str) -> None:
    metadata = snapshot.get("metadata") or {}
    entries = snapshot.get("entries") or {}
    if metadata.get("series") != series(version):
        raise RuntimeError("verified NAS localization snapshot does not match the LIVE series; sync from NAS locally")
    if not re.fullmatch(r"[a-f0-9]{64}", metadata.get("sourceSha256", "")):
        raise RuntimeError("NAS snapshot has no verified source hash")
    if len(entries) < 7000 or entries_hash(entries) != metadata.get("entriesSha256"):
        raise RuntimeError("NAS snapshot entries are incomplete or their hash is invalid")


def load_snapshot(path: Path = SNAPSHOT) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def refresh_snapshot(version: str) -> tuple[dict, bool]:
    current = load_snapshot()
    if os.environ.get("GITHUB_ACTIONS") == "true":
        raw, provenance = read_github_source(version)
    else:
        command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "nas"]
        raw = subprocess.run([*command, f"cat {shlex.quote(NAS_PATH)}"], check=True, capture_output=True, timeout=60).stdout
        remote_hash = subprocess.run(
            [*command, f"sha256sum {shlex.quote(NAS_PATH)}"], check=True, capture_output=True, timeout=30,
        ).stdout.decode().split()[0]
        if remote_hash != hashlib.sha256(raw).hexdigest():
            raise RuntimeError("NAS localization changed during read; retry without replacing files")
        provenance = {}
    source_hash = hashlib.sha256(raw).hexdigest()
    if (source_hash == (current.get("metadata") or {}).get("sourceSha256")
            and (current.get("metadata") or {}).get("adapterVersion") == ADAPTER_VERSION):
        validate_snapshot(current, version)
        print(f"NAS localization unchanged: {source_hash}; retaining snapshot timestamp")
        return current, False
    from enrich_quality_stats import COMMIT_URL, source_sha_from_commit, source_version_from_commit
    bridge = json.loads(fetch_bytes(COMMIT_URL))
    label_commit = source_sha_from_commit(bridge)
    label_version = source_version_from_commit(bridge)
    if series(label_version) != series(version):
        raise RuntimeError("English localization-key bridge series does not match selected LIVE")
    labels = json.loads(fetch_bytes(f"https://raw.githubusercontent.com/StarCitizenWiki/scunpacked-data/{label_commit}/labels.json").decode("utf-8-sig"))
    candidate = build_snapshot(raw, labels, version, label_commit=label_commit, label_version=label_version)
    candidate["metadata"].update(provenance)
    validate_snapshot(candidate, version)
    print(f"NAS localization verified: {source_hash}; series {series(version)} only, not an exact LIVE build")
    return candidate, True


class OfficialNames:
    def __init__(self, snapshot: dict):
        self.snapshot = snapshot
        self.entries = snapshot.get("entries") or {}
        self.by_name: dict[tuple[str, str], list[tuple[str, dict]]] = {}
        for key, entry in self.entries.items():
            self.by_name.setdefault((entry["domain"], entry["english"]), []).append((key, entry))

    def resolve(self, name: str, group: str = "other", key: str = "") -> tuple[str, str] | None:
        if key and (entry := self.entries.get(key.casefold())) and entry["domain"] == group:
            return entry["chinese"], key.casefold()
        matches = self.by_name.get((group, name), [])
        if group == "item":
            full_names = [(entry_key, entry) for entry_key, entry in matches
                          if not entry_key.removesuffix(",p").endswith("_short")]
            matches = full_names or matches
        # Exact labels bridge SCMDB/UEX to game keys; conflicting keys are never guessed.
        if not matches or len({entry["chinese"] for _, entry in matches}) != 1:
            return None
        return matches[0][1]["chinese"], matches[0][0]

    def apply_index(self, index: dict) -> dict:
        changes = []
        unresolved = set()

        def assign(target, field, raw, group, key=""):
            match = self.resolve(raw, group, key)
            if not match:
                if raw:
                    unresolved.add((group, raw))
                return
            value, localization_key = match
            if target.get(field) != value:
                changes.append({"english": raw, "field": field, "before": target.get(field), "after": value, "key": localization_key})
            target[field] = value
            target[field + "LocalizationKey"] = localization_key

        for record in index.get("records") or []:
            zh = record.setdefault("zh", {})
            assign(zh, "name", record.get("name", ""), "item")
            if zh.get("nameLocalizationKey"):
                zh["nameSource"] = "nas-official-key"
            elif zh.get("nameSource") == "starcitizen-localization":
                zh["nameSource"] = "legacy-localization-fallback"
            code = (record.get("stats") or {}).get("manufacturerCode", "")
            assign(zh, "manufacturer", record.get("manufacturer", ""), "manufacturer", f"manufacturer_Name{code}" if code else "")
            stats_zh = record.setdefault("stats", {}).setdefault("zh", {})
            if zh.get("manufacturerLocalizationKey"):
                stats_zh["manufacturerCode"] = zh["manufacturer"]
                zh["manufacturerSource"] = "nas-official-key"
            for tier in record.get("tiers") or []:
                for slot in tier.get("slots") or []:
                    assign(slot, "nameZh", slot.get("name", ""), "slot")
                    for modifier in slot.get("modifiers") or []:
                        assign(modifier, "propertyNameZh", modifier.get("propertyName", ""), "property",
                               f"statname_gpp_{modifier.get('propertyKey', '')},p")
                        if modifier.get("propertyNameZhLocalizationKey"):
                            modifier["propertyNameSource"] = "nas-official-key"
                    for option in slot.get("options") or []:
                        group = "material" if option.get("kind") == "resource" or self.resolve(option.get("name", ""), "material") else "item"
                        assign(option, "nameZh", option.get("name", ""), group)
            for output in (record.get("dismantle") or {}).get("outputs") or []:
                group = "material" if output.get("kind") == "resource" or self.resolve(output.get("name", ""), "material") else "item"
                assign(output, "nameZh", output.get("name", ""), group)
            for source in record.get("sources") or []:
                for mission in source.get("missions") or []:
                    assign(mission, "titleZh", mission.get("title", ""), "other")
                    assign(mission, "factionZh", mission.get("faction", ""), "manufacturer")
        metadata = self.snapshot.get("metadata") or {}
        index.setdefault("localization", {})["nasOfficial"] = {
            key: metadata[key] for key in ("sourceSha256", "sourceVersionLabel", "versionPrecision", "exactBuildVerified", "englishKeyCommit")
        }
        return {"changes": changes, "unresolved": sorted(unresolved)}

    def apply_minerals(self, payload: dict) -> None:
        for name, material in (payload.get("materials") or {}).items():
            if match := self.resolve(name, "material"):
                material["nameZh"], material["nameLocalizationKey"] = match
            for locations in (material.get("locations") or {}).values():
                for location in locations:
                    for field, english_field in (("zh", "en"), ("systemZh", "systemEn"), ("parentZh", "parentEn")):
                        english = location.get(english_field, "")
                        if match := self.resolve(english, "location") or self.resolve(english):
                            location[field], location[field + "LocalizationKey"] = match


def apply_verified_names(index: dict, path: Path = SNAPSHOT) -> dict:
    snapshot = load_snapshot(path)
    validate_snapshot(snapshot, index["version"])
    return OfficialNames(snapshot).apply_index(index)
