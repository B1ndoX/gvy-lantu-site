"""Preserve task requirements without conflating entry points with prerequisites."""

from __future__ import annotations

import copy
import math

BOOLEAN_FIELDS = ("canBeShared", "illegal", "onceOnly", "canReacceptAfterAbandoning",
                  "canReacceptAfterFailing", "hasPersonalCooldown", "hideInMobiGlas")
NUMBER_FIELDS = ("personalCooldownTime", "abandonedCooldownTime")


def build_requirements(contract: dict, data: dict, locations: dict) -> dict:
    result = {key: contract[key] for key in (*BOOLEAN_FIELDS, *NUMBER_FIELDS)
              if contract.get(key) is not None}
    for key in ("minStanding", "maxStanding"):
        standing = contract.get(key)
        if standing is not None:
            result[key] = {k: standing[k] for k in ("name", "nameKey", "minReputation", "includeWhenSharing") if k in standing}
    contracts = data.get("contracts") or []
    by_debug = {c.get("debugName"): c for c in contracts}
    for field in ("requiredIntros", "linkedIntros"):
        intros = []
        for intro in contract.get(field) or []:
            original = by_debug.get(intro.get("debugName"), intro)
            intros.append({"title": intro.get("title") or original.get("title") or intro.get("debugName"),
                           "titleKey": original.get("titleLocKey") or original.get("titleKey", ""),
                           "titleTokens": copy.deepcopy(original.get("tokenSubstitutions") or {})})
        if intros:
            result[field] = intros

    def register(value: dict, identity: str, system: str = "") -> str:
        name = value.get("name")
        if not isinstance(name, str) or not name.strip():
            raise RuntimeError("mission location is missing its name")
        locations.setdefault(identity, {"name": name, "system": value.get("system") or system,
                                        "type": value.get("type") or value.get("navIcon") or ""})
        return identity

    prerequisite = contract.get("prerequisites") or {}
    result["regions"] = []
    for locality in prerequisite.get("locality") or []:
        name = locality.get("name")
        region = (data.get("regions") or {}).get(name)
        system = (region or {}).get("system", "")
        # The contract explicitly identifies these codes as Pyro regions.
        if not region and name in {f"Region{code}" for code in contract.get("pyroRegion") or []}:
            region = (data.get("pyroRegions") or {}).get(name.removeprefix("Region"))
            system = "Pyro"
        ids = [register(place, place["guid"], system) for place in (region or {}).get("locations") or []]
        result["regions"].append({"name": name, "system": system, "locations": list(dict.fromkeys(ids))})

    places = []
    for i, place in enumerate(prerequisite.get("location") or []):
        places.append(register(place, place.get("guid") or f"{contract['id']}:location:{i}"))
    for i, place in enumerate((prerequisite.get("locationProperty") or {}).get("resolvedLocations") or []):
        places.append(register(place, place.get("guid") or f"{contract['id']}:property:{i}"))
    for i, place in enumerate(prerequisite.get("tagSearchLocations") or []):
        if place.get("planet") or place.get("system"):
            places.append(register({"name": place.get("planet") or place["system"], "system": place.get("system")},
                                   f"{contract['id']}:tag:{i}"))
    if places:
        result["acceptLocations"] = list(dict.fromkeys(places))
    candidates = []
    unresolved = 0
    for identity in contract.get("locations") or []:
        place = (data.get("locationPools") or {}).get(identity)
        if place:
            candidates.append(register(place, identity))
        else:
            unresolved += 1
    if candidates:
        result["missionLocations"] = list(dict.fromkeys(candidates))
    if unresolved:
        result["unresolvedLocations"] = unresolved
    if prerequisite.get("crimeStat") is not None:
        result["crimeStat"] = copy.deepcopy(prerequisite["crimeStat"])
    completion = prerequisite.get("completedContractTags")
    if completion:
        for source, target in (("tags", "completedContracts"), ("excludedTags", "excludedContracts")):
            tags = set(completion.get(source) or [])
            if not tags:
                continue
            titles = [{"title": c.get("title") or c.get("debugName"), "titleKey": c.get("titleLocKey") or c.get("titleKey", ""),
                       "titleTokens": copy.deepcopy(c.get("tokenSubstitutions") or {})}
                      for c in contracts if any(t.get("tag") in tags for t in c.get("completionTags") or [])]
            result[target] = {"tagCount": len(tags), "candidates": titles}
            if source == "tags":
                result[target]["requiredCount"] = completion.get("requiredCountValue")
    # Preserve additional restrictions as a disclosure, never as guessed eligibility.
    extra = []
    if contract.get("reputationLockout"):
        extra.append("reputationLockout")
    if contract.get("requiredScenarios"):
        extra.append("requiredScenarios")
    if prerequisite.get("subLocationVariants"):
        extra.append("subLocationVariants")
    known = {"location", "locality", "locationProperty", "tagSearchLocations", "crimeStat", "completedContractTags", "subLocationVariants"}
    extra.extend(sorted(set(prerequisite) - known))
    if extra:
        result["additionalRestrictions"] = extra
    return result


def validate_requirements(value: dict, locations: dict) -> None:
    if not isinstance(value, dict):
        raise RuntimeError("invalid mission requirements")
    for field in BOOLEAN_FIELDS:
        if field in value and type(value[field]) is not bool:
            raise RuntimeError(f"invalid mission requirement boolean: {field}")
    for field in NUMBER_FIELDS:
        if field in value and (type(value[field]) not in (int, float) or not math.isfinite(value[field]) or value[field] < 0):
            raise RuntimeError(f"invalid mission requirement time: {field}")
    for field in ("minStanding", "maxStanding"):
        if field not in value:
            continue
        standing = value[field]
        if not isinstance(standing, dict) or not isinstance(standing.get("name"), str):
            raise RuntimeError("invalid mission standing")
        xp = standing.get("minReputation")
        if xp is not None and (type(xp) not in (int, float) or not math.isfinite(xp)):
            raise RuntimeError("invalid mission standing XP")
        if "includeWhenSharing" in standing and type(standing["includeWhenSharing"]) is not bool:
            raise RuntimeError("invalid shared mission standing")
    crime = value.get("crimeStat")
    if crime is not None:
        if not isinstance(crime, dict) or any(type(crime.get(k)) not in (int, float) or not math.isfinite(crime[k]) for k in ("min", "max")) or crime["min"] > crime["max"]:
            raise RuntimeError("invalid mission crime stat range")
    refs = []
    for field in ("acceptLocations", "missionLocations"):
        ids = value.get(field) or []
        if not isinstance(ids, list):
            raise RuntimeError("invalid mission location references")
        refs.extend(ids)
    regions = value.get("regions")
    if not isinstance(regions, list):
        raise RuntimeError("invalid mission regions")
    for region in regions:
        if not isinstance(region, dict) or not isinstance(region.get("name"), str) or not isinstance(region.get("locations"), list):
            raise RuntimeError("invalid mission region")
        refs.extend(region["locations"])
    if any(not isinstance(identity, str) or identity not in locations for identity in refs):
        raise RuntimeError("mission requirement references a missing location")
    for field in ("requiredIntros", "linkedIntros"):
        if field in value and (not isinstance(value[field], list) or any(not isinstance(i, dict) or not isinstance(i.get("title"), str) for i in value[field])):
            raise RuntimeError("invalid mission intro requirements")
    completed = value.get("completedContracts")
    if completed and (not isinstance(completed, dict) or (completed.get("requiredCount") is not None and (type(completed["requiredCount"]) is not int or completed["requiredCount"] < 0))
                      or not isinstance(completed.get("candidates"), list)):
        raise RuntimeError("invalid mission completion requirements")
    excluded = value.get("excludedContracts")
    if excluded and (not isinstance(excluded, dict) or type(excluded.get("tagCount")) is not int or excluded["tagCount"] < 1
                     or not isinstance(excluded.get("candidates"), list)):
        raise RuntimeError("invalid mission excluded completion requirements")
