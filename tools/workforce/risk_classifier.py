#!/usr/bin/env python3
"""B-028 deterministic risk classifier.

Computes the required audit depth for a task from:

    tier = max(severity_tier, domain_tier)

- ``severity_tier`` derives from the task's ``security_class`` (S0/S1 -> SEC-A,
  S2/S3 -> SEC-B, S4 -> SEC-C).
- ``domain_tier`` is the highest tier across all ``domain_tiers.json`` domains
  whose globs match the union of the task's declared ``allowed_paths`` and
  the paths actually changed. Unmatched paths classify UNKNOWN -> SEC-C
  (fail closed). ``CONTROL_SURFACE`` always yields SEC-C.
- A declared-vs-actual scope mismatch (a changed path outside every declared
  allowed pattern, beyond metadata allowlists) is reported as BLOCKED —
  never silently upgraded.

Outputs a JSON verdict. Python 3 standard library only; offline.
"""

import argparse
import fnmatch
import json
import sys
from pathlib import Path

TIERS_PATH = "docs/workforce/registries/domain_tiers.json"
TIER_ORDER = {"SEC-A": 0, "SEC-B": 1, "SEC-C": 2}

SEVERITY_MAP = {"S0": "SEC-A", "S1": "SEC-A", "S2": "SEC-B", "S3": "SEC-B", "S4": "SEC-C"}

# Metadata surfaces legitimately touched by every delivery even when not
# individually re-declared; they never lower or raise the verdict alone.
METADATA_ALLOWLIST = {
    "docs/continuity/CURRENT_STATE.json",
    "docs/continuity/CURRENT_GIT_STATE.md",
    "docs/continuity/CURRENT_HANDOFF.md",
    "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md",
    "docs/continuity/CURRENT_OPEN_WORK.md",
    "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
    "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md",
    "docs/workforce/WORKFORCE_STATE.json",
    "PROJECT_STATE.md",
    "FORTSCHRITT.md",
    "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
}


def load_tiers(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != "B028-DT-v1":
        raise ValueError(f"unknown domain_tiers schema_version: {data.get('schema_version')}")
    return data


def _match(path, pattern):
    path = path.replace("\\", "/")
    return fnmatch.fnmatch(path, pattern)


def domain_for(path, tiers):
    """Highest-tier domain whose globs match path; None if unmatched."""
    best = None
    for domain in tiers["domains"]:
        if any(_match(path, g) for g in domain["globs"]):
            if best is None or TIER_ORDER[domain["tier"]] > TIER_ORDER[best["tier"]]:
                best = domain
    return best


def _declared(path, allowed):
    return any(_match(path, pat) or path == pat.rstrip("/")
               for pat in allowed)


def classify(task, changed_paths, tiers_path=None, check_scope=True):
    """Return a verdict dict. Never raises on bad input — fail closed."""
    problems = []
    try:
        tiers = load_tiers(tiers_path or TIERS_PATH)
    except (OSError, ValueError) as exc:
        return {"result": "BLOCKED", "tier": "SEC-C", "problems": [str(exc)]}

    security_class = task.get("security_class")
    severity_tier = SEVERITY_MAP.get(security_class)
    if severity_tier is None:
        problems.append(f"unknown security_class: {security_class}")
        severity_tier = "SEC-C"

    allowed = task.get("allowed_paths") or []
    if not allowed:
        problems.append("task declares no allowed_paths — fail closed")

    declared_domains = set()
    for path in allowed:
        dom = domain_for(path, tiers)
        declared_domains.add(dom["domain"] if dom else "UNKNOWN")

    changed = list(changed_paths or [])
    changed_domains = {}
    for path in changed:
        dom = domain_for(path, tiers)
        changed_domains[path] = dom["domain"] if dom else "UNKNOWN"
        if check_scope and path not in METADATA_ALLOWLIST and not _declared(path, allowed):
            problems.append(f"changed path outside declared scope: {path}")

    if "UNKNOWN" in declared_domains or "UNKNOWN" in changed_domains.values():
        domain_tier = "SEC-C"
        unknown = [p for p, d in changed_domains.items() if d == "UNKNOWN"]
        if unknown:
            problems.append(f"unclassified paths (fail closed SEC-C): {sorted(unknown)}")
    else:
        def _tier_of(name):
            for d in tiers["domains"]:
                if d["domain"] == name:
                    return d["tier"]
            return "SEC-C"
        domain_tier = max(
            (_tier_of(d) for d in declared_domains | set(changed_domains.values())),
            key=lambda t: TIER_ORDER[t], default="SEC-C",
        )

    tier = max((severity_tier, domain_tier), key=lambda t: TIER_ORDER[t])
    control_surface = "CONTROL_SURFACE" in declared_domains or \
        "CONTROL_SURFACE" in changed_domains.values()

    return {
        "result": "BLOCKED" if problems else "CLASSIFIED",
        "task_id": task.get("task_id"),
        "severity_tier": severity_tier,
        "domain_tier": domain_tier,
        "tier": tier,
        "control_surface": control_surface,
        "requires_independent_review": tier == "SEC-C" or control_surface,
        "declared_domains": sorted(declared_domains),
        "changed_domains": changed_domains,
        "problems": problems,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="task package JSON file")
    parser.add_argument("--changed", nargs="*", default=[],
                        help="paths actually changed by the delivery")
    parser.add_argument("--tiers", default=None)
    args = parser.parse_args(argv)
    try:
        task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(json.dumps({"result": "BLOCKED", "problems": [str(exc)]}))
        return 1
    verdict = classify(task, args.changed, tiers_path=args.tiers)
    print(json.dumps(verdict, indent=1, ensure_ascii=False))
    return 0 if verdict["result"] == "CLASSIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
