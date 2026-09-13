#!/usr/bin/env python3
"""Security Hardening audit evidence-preservation validator.

Fail-closed verification for SECURITY-AUDIT-EVIDENCE-PRESERVATION-001,
-002 and -003: the seven preserved audit reports (including
AUDIT-SECURITY-CRYPTO-JNI-001 and AUDIT-SECURITY-AUTH-DPOP-001), the
audit-evidence registry, the traceability layer (including cryptojni and
authdpop candidates/gaps, specialist relations, severity overlays,
provenance limitation, temp-build evidence, the ABI revision record,
coverage/test evidence, remediation coverage and specialist handoffs),
and the lifecycle state that must remain unchanged.

Set SECURITY_AUDIT_PRESERVATION_REPO to validate an alternate tree
(test fixtures); git-dependent checks are skipped when no .git exists.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(os.environ.get("SECURITY_AUDIT_PRESERVATION_REPO") or Path(__file__).resolve().parents[2])
EVIDENCE_DIR = REPO_ROOT / "docs" / "security" / "audit-evidence"
REPORTS_DIR = REPO_ROOT / "docs" / "reports" / "security" / "audits"
REGISTRY_DIR = REPO_ROOT / "docs" / "workforce" / "registries"
WAVE_BASE_SHA = "869b99acac040412a29bbaadc76342070fb2085c"
CRYPTOJNI_AUDIT_SHA = "a79166ab7e65db71ba70e3a427df2ad017dc9225"
BASE_SHA = "638e63a22c91ca81365bf55c8a59ec47878dd7fd"
DELIVERY_BRANCH = "governance/security-audit-evidence-preservation-003"
TASK_ID = "ANOX-TASK-SECURITY-AUDIT-EVIDENCE-PRESERVATION-003"
NEXT_GATE_ID = "AUDIT-SECURITY-ANDROID-STORAGE-001"
LEDGER_EVENT = "ANOX-EVENT-0047"

EXPECTED_REPORTS = {
    "AUDIT-SECURITY-ARCHITECTURE": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-ARCHITECTURE.md",
        "sha256": "da230ac1a3f623eba559c31641e52ffd2fc5487502d4c6ad2ccbbc1f9eb6dfe6",
    },
    "AUDIT-SECURITY-CODEBASE-001": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-001.md",
        "sha256": "122d0aae9c1b64d060010092bea77f4d9c3466c5df2d10ccf56955bc4987f153",
    },
    "AUDIT-SECURITY-CODEBASE-002": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-002.md",
        "sha256": "2ce279637bea62c79ced6614318c1fe79fcdc1b30b33519aeb7b2d426d4c09d5",
    },
    "CODEBASE-SECURITY-CONSENSUS-001": {
        "path": "docs/reports/security/audits/CODEBASE-SECURITY-CONSENSUS-001.md",
        "sha256": "66ea13d75982e83fdb9b316f3b95c0aef4b1fae9604d5e6457abb33e40898f8c",
    },
    "AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001.md",
        "sha256": "6afdd091d64ec9a30d40f8ba4e0fbe73bfb4812f105993bdbb42b49895acda1a",
    },
    "AUDIT-SECURITY-CRYPTO-JNI-001": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-CRYPTO-JNI-001.md",
        "sha256": "c7367e3419b709d9675b16ddcf1fee23fd114283482523ee036be99e4ecc836b",
    },
    "AUDIT-SECURITY-AUTH-DPOP-001": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-AUTH-DPOP-001.md",
        "sha256": "57516d7d47e56447b7ab7a91aadaa2b7c3acdeda71e572b2b4366d2a6526b18e",
    },
}

EXPECTED_AUDITS = {
    "ANOX-AUDIT-SECURITY-ARCH-001": {
        "audit_type": "FINAL_PRE_PRODUCT_SECURITY_ARCHITECTURE_AUDIT",
        "provider": "Anthropic via Devin CLI / Cognition",
        "actual_model": "Claude Opus 5 High",
        "audited_sha": "c653a1d6a302758c0e006225987281643957f752",
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 11, "critical_count": 0, "high_count": 5,
        "medium_count": 3, "low_count": 2, "info_count": 1,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-CODEBASE-001": {
        "audit_type": "READ_ONLY_FULL_EXISTING_CODEBASE_SECURITY_AUDIT",
        "provider": "Anthropic",
        "actual_model": "Claude Opus 5 Medium",
        "requested_model": "Claude Fable 5.1 High",
        "audited_sha": WAVE_BASE_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 21, "critical_count": 1, "high_count": 3,
        "medium_count": 8, "low_count": 7, "info_count": 2,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-CODEBASE-002": {
        "audit_type": "READ_ONLY_BLIND_INDEPENDENT_FULL_CODEBASE_SECURITY_AUDIT",
        "provider": "Anthropic",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "audited_sha": WAVE_BASE_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 17, "critical_count": 0, "high_count": 3,
        "medium_count": 6, "low_count": 6, "info_count": 2,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "YES", "blindness_status_prefix": "PRESERVED",
    },
    "CODEBASE-SECURITY-CONSENSUS-001": {
        "audit_type": "CONSENSUS_ANALYSIS_AND_ARBITRATION",
        "provider": "Anthropic",
        "actual_model": "Claude Opus 5 High",
        "audited_sha": WAVE_BASE_SHA,
        "result": "PASS",
        "candidate_count": 18,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001": {
        "audit_type": "READ_ONLY_BUILD_NATIVE_PROVENANCE_SUPPLY_CHAIN_SECURITY_AUDIT",
        "provider": "Anthropic",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "audited_sha": WAVE_BASE_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 12, "critical_count": 0, "high_count": 3,
        "medium_count": 5, "low_count": 3, "info_count": 1,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-CRYPTO-JNI-001": {
        "audit_type": "security_specialist_crypto_jni",
        "provider": "Anthropic",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "model_requirement_status": "SATISFIED",
        "audited_sha": CRYPTOJNI_AUDIT_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 6, "critical_count": 0, "high_count": 1,
        "medium_count": 3, "low_count": 1, "info_count": 1,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-AUTH-DPOP-001": {
        "audit_type": "security_specialist_device_auth_dpop",
        "provider": "Devin CLI (Cognition) session runtime",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "model_requirement_status": "SATISFIED",
        "audited_sha": BASE_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 3, "architecture_gap_count": 3,
        "critical_count": 0, "high_count": 0,
        "medium_count": 1, "low_count": 2, "info_count": 0,
        "b002_production_files": "29/29 (100%)",
        "b002_relevant_test_files": "14/14 (100%)",
        "architecture_requirements": 40, "architecture_unmapped": 0,
        "focused_relevant_test_inventory": 155,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
}

A1_SEVERITY = {"C-003": "CRITICAL"}
for _c in ("C-001", "C-002", "C-004"):
    A1_SEVERITY[_c] = "HIGH"
for _c in ("C-005", "C-006", "C-007", "C-008", "C-009", "C-010", "C-011", "C-012"):
    A1_SEVERITY[_c] = "MEDIUM"
for _c in ("C-013", "C-014", "C-015", "C-016", "C-017", "C-018", "C-019"):
    A1_SEVERITY[_c] = "LOW"
for _c in ("C-020", "C-021"):
    A1_SEVERITY[_c] = "INFO"
A1_IDS = {f"C-{i:03d}" for i in range(1, 22)}

A2_SEVERITY = {"C-001": "HIGH", "C-002": "HIGH", "C-003": "HIGH"}
for _c in ("C-004", "C-005", "C-006", "C-007", "C-008", "C-009"):
    A2_SEVERITY[_c] = "MEDIUM"
for _c in ("C-010", "C-011", "C-012", "C-013", "C-014", "C-015"):
    A2_SEVERITY[_c] = "LOW"
for _c in ("C-016", "C-017"):
    A2_SEVERITY[_c] = "INFO"
A2_IDS = {f"C-{i:03d}" for i in range(1, 18)}

ROOT_IDS = {f"ROOT-{i:03d}" for i in range(1, 19)}
PRE_B004_ROOTS = [
    "ROOT-001", "ROOT-002", "ROOT-003", "ROOT-004", "ROOT-005", "ROOT-006",
    "ROOT-007", "ROOT-008", "ROOT-009", "ROOT-013", "ROOT-014", "ROOT-017",
]
B008_B009_ROOTS = ["ROOT-010", "ROOT-011", "ROOT-012"]
FPG_ROOTS = ["ROOT-012", "ROOT-015"]

BUILDSC_SEVERITY = {
    "ANOX-BUILDSC-CANDIDATE-001": "HIGH", "ANOX-BUILDSC-CANDIDATE-002": "HIGH",
    "ANOX-BUILDSC-CANDIDATE-003": "HIGH",
    "ANOX-BUILDSC-CANDIDATE-004": "MEDIUM", "ANOX-BUILDSC-CANDIDATE-005": "MEDIUM",
    "ANOX-BUILDSC-CANDIDATE-006": "MEDIUM", "ANOX-BUILDSC-CANDIDATE-007": "MEDIUM",
    "ANOX-BUILDSC-CANDIDATE-008": "MEDIUM",
    "ANOX-BUILDSC-CANDIDATE-009": "LOW", "ANOX-BUILDSC-CANDIDATE-010": "LOW",
    "ANOX-BUILDSC-CANDIDATE-011": "LOW", "ANOX-BUILDSC-CANDIDATE-012": "INFO",
}
BUILDSC_IDS = set(BUILDSC_SEVERITY)

CRYPTOJNI_SEVERITY = {
    "ANOX-CRYPTOJNI-CANDIDATE-001": "HIGH",
    "ANOX-CRYPTOJNI-CANDIDATE-002": "MEDIUM",
    "ANOX-CRYPTOJNI-CANDIDATE-003": "MEDIUM",
    "ANOX-CRYPTOJNI-CANDIDATE-004": "MEDIUM",
    "ANOX-CRYPTOJNI-CANDIDATE-005": "LOW",
    "ANOX-CRYPTOJNI-CANDIDATE-006": "INFO",
}
CRYPTOJNI_IDS = set(CRYPTOJNI_SEVERITY)
CRYPTOJNI_PRE_B004 = {"ANOX-CRYPTOJNI-CANDIDATE-001", "ANOX-CRYPTOJNI-CANDIDATE-003"}
CRYPTOJNI_RELATIONS = {
    "ROOT-002": "CONFIRMED", "ROOT-014": "CONFIRMED",
    "ROOT-003": "CONFIRMED_AND_EXPANDED", "ROOT-004": "CONFIRMED_AND_EXPANDED",
    "ROOT-005": "CONFIRMED_AND_EXPANDED", "ROOT-013": "CONFIRMED_AND_EXPANDED",
    "ROOT-010": "ADJACENT_EXPANDED", "ROOT-011": "CONFIRMED_NO_EXPANSION",
}
PRE_B004_CRYPTOJNI_GATE = [
    "ROOT-002", "ROOT-003", "ROOT-004", "ROOT-005", "ROOT-013", "ROOT-014",
    "ANOX-CRYPTOJNI-CANDIDATE-001", "ANOX-CRYPTOJNI-CANDIDATE-003",
]
B008_B009_CRYPTOJNI_GATE = [
    "ANOX-CRYPTOJNI-CANDIDATE-002", "ANOX-CRYPTOJNI-CANDIDATE-004",
    "ANOX-CRYPTOJNI-CANDIDATE-005", "ROOT-010", "ROOT-011",
]
TEMP_BUILD_HASHES = {
    "arm64-v8a": "05f3f40cd4122ddd4286c513470f8bb6cdf54ca69b4c1879e53cb6a8ba22d7a2",
    "x86_64": "c002cc420813f3b8473be7aa82eb0af334bd73e6847cd1c893ce500845dfe798",
}

AUTHDPOP_ID = "AUDIT-SECURITY-AUTH-DPOP-001"
AUTHDPOP_REPORT_SHA = "57516d7d47e56447b7ab7a91aadaa2b7c3acdeda71e572b2b4366d2a6526b18e"
AUTHDPOP_SEVERITY = {
    "ANOX-AUTHDPOP-CANDIDATE-001": "MEDIUM",
    "ANOX-AUTHDPOP-CANDIDATE-002": "LOW",
    "ANOX-AUTHDPOP-CANDIDATE-003": "LOW",
}
AUTHDPOP_CANDIDATE_IDS = set(AUTHDPOP_SEVERITY)
AUTHDPOP_GAP_IDS = {"ANOX-AUTHDPOP-GAP-001", "ANOX-AUTHDPOP-GAP-002", "ANOX-AUTHDPOP-GAP-003"}
AUTHDPOP_RELATIONS = {
    "ROOT-006": "CONFIRMED", "ROOT-007": "CONFIRMED",
    "ROOT-008": "CONFIRMED_AND_EXPANDED", "ROOT-009": "CONFIRMED_AND_EXPANDED",
}
PRE_B004_AUTHDPOP_GATE = [
    "ROOT-006", "ROOT-007", "ROOT-008", "ROOT-009",
    "ANOX-AUTHDPOP-CANDIDATE-001",
    "ANOX-AUTHDPOP-GAP-001", "ANOX-AUTHDPOP-GAP-002", "ANOX-AUTHDPOP-GAP-003",
]
LATER_AUTHDPOP_GATE = [
    "ANOX-AUTHDPOP-CANDIDATE-002 (fix inside AD-A during B-004 Device-Auth wiring; NON_BLOCKING)",
    "ANOX-AUTHDPOP-CANDIDATE-003 (B-004 backend verifier implementation gate; contract entry in GAP-002 now)",
    "ANOX-MAINARCH-018 (physical StrongBox/TEE/Keystore semantics — Final Product Gate on provenance-verified binary)",
    "logout/wipe/revoke Device-Auth behaviour (B-013 lifecycle gate)",
    "instrumented DeviceAuth suites in CI (ROOT-017 track)",
]
AUTHDPOP_HIST_RELATIONS = {
    "ANOX-LEGACY-INTEGRATION-001": ("PARTIALLY_EFFECTIVE", "Closed"),
    "ANOX-LEGACY-INTEGRATION-003": ("STILL_EFFECTIVE", "Closed"),
    "ANOX-MAINARCH-019": ("STILL_EFFECTIVE", "Closed"),
    "ANOX-MAINARCH-008": ("STILL_EFFECTIVE_DOC_LAYER_RELATED_NEW_ROOT_CAUSE", "Closed"),
    "ANOX-SECURITY-ARCH-006": ("STILL_EFFECTIVE_OPEN", "Open"),
    "ANOX-SECURITY-ARCH-003": ("RELATED_NEW_ROOT_CAUSE", "Open"),
    "ANOX-SECURITY-ARCH-007": ("INEFFECTIVE_REMEDIATION_SCOPE", "Open"),
    "ANOX-MAINARCH-005": ("STILL_EFFECTIVE", "Closed"),
    "ANOX-MAINARCH-014": ("NO_LONGER_APPLICABLE", "Closed"),
}
AUTHDPOP_COVERAGE_COUNTS = {
    "IMPLEMENTED_AND_VERIFIED": 15, "IMPLEMENTED_NOT_VERIFIED": 7,
    "PARTIALLY_IMPLEMENTED": 6, "IMPLEMENTATION_DRIFT": 6,
    "MISSING": 3, "NOT_APPLICABLE_YET": 3,
    "PHYSICAL_VERIFICATION_REQUIRED": 2, "UNMAPPED": 0,
}
AUTHDPOP_GROUPS = {"AD-A", "AD-B", "AD-C", "AD-D", "AD-E", "AD-F"}

METADATA_ALLOWLIST = {
    "PROJECT_STATE.md", "FORTSCHRITT.md", "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
    "docs/continuity/CURRENT_STATE.json", "docs/continuity/CURRENT_GIT_STATE.md",
    "docs/continuity/CURRENT_HANDOFF.md", "docs/continuity/CURRENT_OPEN_WORK.md",
    "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
    "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md",
    "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md",
    "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
    "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md",
    "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
    "docs/workforce/registries/decisions.jsonl", "docs/workforce/registries/findings.jsonl",
    "docs/workforce/registries/tasks.jsonl", "docs/workforce/registries/runs.jsonl",
    "docs/workforce/registries/audits.jsonl", "docs/workforce/registries/derived_work.jsonl",
    "docs/workforce/WORKFORCE_STATE.json", "docs/workforce/WORKFORCE_STATE_SNAPSHOT.json",
}
FORBIDDEN_PREFIXES = ("android/", "crypto/rust/", "backend/", ".github/workflows/", "supabase/", "migrations/")


def fail(msg, errors):
    errors.append(msg)


def load_jsonl(path):
    r = []
    if not path.exists():
        return r
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r.append(json.loads(line))
    return r


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _rev_parse(ref):
    out = subprocess.run(["git", "rev-parse", ref], cwd=REPO_ROOT, capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def has_git():
    return (REPO_ROOT / ".git").is_dir()


def validate_base(errors):
    if not has_git():
        print("  SKIP git checks (no .git — fixture mode)")
        return
    sys.path.insert(0, str(REPO_ROOT / "tools" / "audit"))
    import lifecycle_legality as ll
    head = _rev_parse("HEAD")
    if not ll._git_is_ancestor(BASE_SHA, head, cwd=REPO_ROOT):
        fail(f"base {BASE_SHA} not ancestor of {head}", errors)
        return
    print(f"  OK   base {BASE_SHA[:12]} is ancestor of {head[:12]}")
    state = load_json(REPO_ROOT / "docs" / "continuity" / "CURRENT_STATE.json")
    described = state.get("described_head") or ""
    if not re.fullmatch(r"[0-9a-f]{40}", described):
        fail(f"CURRENT_STATE described_head is not a valid SHA: {described}", errors)
        return
    ok, _, _, reason = ll.canonical_two_commit_delivery(
        BASE_SHA, described, head,
        canonical_branch="main", delivery_branch=DELIVERY_BRANCH,
        cwd=REPO_ROOT, metadata_allowlist=METADATA_ALLOWLIST,
    )
    if not ok:
        fail(f"canonical two-commit delivery failed: {reason}", errors)
        return
    print("  OK   exactly 2 task-authored commits above base (merge-aware)")


def validate_reports(errors):
    hashes = {}
    hpath = EVIDENCE_DIR / "evidence_hashes.json"
    if not hpath.exists():
        fail("evidence_hashes.json missing", errors)
    else:
        try:
            hashes = (load_json(hpath).get("reports") or {})
        except Exception as e:
            fail(f"evidence_hashes.json unreadable: {e}", errors)
    for name, spec in EXPECTED_REPORTS.items():
        p = REPO_ROOT / spec["path"]
        if not p.exists():
            fail(f"preserved report missing: {spec['path']}", errors)
            continue
        actual = sha256_file(p)
        if actual != spec["sha256"]:
            fail(f"report {name} hash mismatch: {actual} != {spec['sha256']}", errors)
            continue
        rec = hashes.get(name) or {}
        if rec.get("sha256") != spec["sha256"]:
            fail(f"evidence_hashes.json entry for {name} mismatched/missing", errors)
        elif rec.get("source_present") != "YES":
            fail(f"evidence_hashes.json {name} source_present != YES", errors)
        else:
            print(f"  OK   {name} preserved byte-exact ({spec['sha256'][:16]}...)")
    src = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl") if (EVIDENCE_DIR / "audit_traceability.jsonl").exists() else []
    src_recs = [r for r in src if r.get("record_type") == "source_status"]
    for name in EXPECTED_REPORTS:
        rec = next((r for r in src_recs if r.get("audit_name") == name or r.get("audit_id") == name or EXPECTED_AUDITS.get(r.get("audit_id"), {}).get("audit_name") == name or r.get("audit_id") == EXPECTED_AUDITS.get(name, {}).get("audit_id")), None)
        if rec is None:
            # match by preserved_path
            rec = next((r for r in src_recs if r.get("preserved_path") == EXPECTED_REPORTS[name]["path"]), None)
        if rec is None:
            fail(f"source_status record missing for {name}", errors)
        elif rec.get("source_present") != "YES":
            fail(f"source_status for {name} is not YES", errors)


def validate_registry(errors):
    audits = {a.get("audit_id"): a for a in load_jsonl(EVIDENCE_DIR / "audit_registry.jsonl")}
    if not audits:
        fail("audit_registry.jsonl missing or empty", errors)
        return
    if len(audits) != 7:
        fail(f"audit_registry.jsonl must contain exactly 7 audits, found {len(audits)}", errors)
    for aid, spec in EXPECTED_AUDITS.items():
        rec = audits.get(aid)
        if rec is None:
            fail(f"audit registry missing {aid}", errors)
            continue
        for key, expected in spec.items():
            if key == "blindness_status_prefix":
                if not str(rec.get("blindness_status", "")).startswith(expected):
                    fail(f"{aid} blindness_status {rec.get('blindness_status')!r} lacks prefix {expected!r}", errors)
                continue
            if rec.get(key) != expected:
                fail(f"{aid} {key}={rec.get(key)!r}, expected {expected!r}", errors)
        rep = rec.get("report_path")
        if rep not in {s["path"] for s in EXPECTED_REPORTS.values()}:
            fail(f"{aid} report_path not a preserved report: {rep!r}", errors)
        if rec.get("report_sha256") != EXPECTED_REPORTS.get(rec.get("audit_name", ""), {}).get("sha256"):
            fail(f"{aid} report_sha256 mismatch vs evidence_hashes expectation", errors)
    a1 = audits.get("AUDIT-SECURITY-CODEBASE-001") or {}
    if "MODEL_DEVIATION" not in str(a1.get("model_requirement_status", "")):
        fail("AUDIT-SECURITY-CODEBASE-001 model_requirement_status must record MODEL_DEVIATION", errors)
    a2 = audits.get("AUDIT-SECURITY-CODEBASE-002") or {}
    if a2.get("blindness_status", "").startswith("PRESERVED"):
        print("  OK   Audit-002 blindness preserved")
    else:
        fail("AUDIT-SECURITY-CODEBASE-002 blindness_status must start with PRESERVED", errors)
    print("  OK   audit registry records verified")


def validate_traceability(errors):
    recs = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl")
    if not recs:
        fail("audit_traceability.jsonl missing or empty", errors)
        return

    a1 = [r for r in recs if r.get("record_type") == "audit001_candidate"]
    a1_refs = {r.get("consensus_ref") for r in a1}
    if len(a1) != 21 or a1_refs != A1_IDS:
        fail(f"Audit-001 traceability must cover 21/21 candidates; got {len(a1)}", errors)
    else:
        print("  OK   Audit-001 21/21 candidates traced")
    for r in a1:
        cref = r.get("consensus_ref")
        if A1_SEVERITY.get(cref) != r.get("severity"):
            fail(f"Audit-001 {cref} severity {r.get('severity')!r} != {A1_SEVERITY.get(cref)!r}", errors)
        if not r.get("consensus_roots"):
            fail(f"Audit-001 {cref} has no consensus_roots", errors)
    c19 = next((r for r in a1 if r.get("consensus_ref") == "C-019"), None)
    if c19 is None:
        fail("Audit-001 C-019 candidate missing from traceability", errors)
    elif c19.get("candidate_id") != "ANOX-CODESEC-CANDIDATE-019" or "ROOT-008" not in c19.get("consensus_roots", []):
        fail("Audit-001 C-019 traceability content wrong", errors)
    else:
        print("  OK   Audit-001 C-019 present and mapped")

    a2 = [r for r in recs if r.get("record_type") == "audit002_candidate"]
    a2_local = {r.get("audit_local_id") for r in a2}
    if len(a2) != 17 or a2_local != A2_IDS:
        fail(f"Audit-002 traceability must cover 17/17 candidates; got {len(a2)}", errors)
    else:
        print("  OK   Audit-002 17/17 candidates traced")
    for r in a2:
        lid = r.get("audit_local_id")
        if A2_SEVERITY.get(lid) != r.get("severity"):
            fail(f"Audit-002 {lid} severity {r.get('severity')!r} != {A2_SEVERITY.get(lid)!r}", errors)
        if not r.get("consensus_roots"):
            fail(f"Audit-002 {lid} has no consensus_roots", errors)

    roots = {r.get("root_id"): r for r in recs if r.get("record_type") == "consensus_root"}
    if set(roots) != ROOT_IDS:
        fail(f"consensus roots must be exactly ROOT-001..018; got {sorted(roots)}", errors)
    else:
        print("  OK   18 consensus roots ROOT-001..018")
    r5 = roots.get("ROOT-005") or {}
    if r5.get("audit001_sources"):
        fail("ROOT-005 has a fabricated Audit-001 source candidate", errors)
    elif r5.get("audit002_sources") != ["C-003"]:
        fail("ROOT-005 audit002_sources must be [C-003]", errors)
    else:
        print("  OK   ROOT-005 has no Audit-001 source (SINGLE_AUDIT_CONFIRMED_BY_ARBITER)")
    r16 = roots.get("ROOT-016") or {}
    if r16.get("status") != "REJECTED_NOT_A_FINDING" or r16.get("severity") != "NONE":
        fail("ROOT-016 must remain REJECTED_NOT_A_FINDING / severity NONE", errors)
    else:
        print("  OK   ROOT-016 remains rejected, not a real finding")
    for rid in ("ROOT-001", "ROOT-002", "ROOT-003", "ROOT-004", "ROOT-005"):
        if (roots.get(rid) or {}).get("severity") != "HIGH":
            fail(f"{rid} must be HIGH", errors)

    gates = {g.get("gate"): g for g in recs if g.get("record_type") == "gate_set"}
    pre = gates.get("PRE_B004_ROOTS") or {}
    if sorted(pre.get("roots") or []) != sorted(PRE_B004_ROOTS):
        fail(f"PRE_B004_ROOTS set wrong: {pre.get('roots')}", errors)
    else:
        print("  OK   12-root Pre-B004 set exact")
    if sorted((gates.get("B008_B009_ROOTS") or {}).get("roots") or []) != sorted(B008_B009_ROOTS):
        fail("B008_B009_ROOTS set wrong", errors)
    if sorted((gates.get("FINAL_PRODUCT_GATE_ROOTS") or {}).get("roots") or []) != sorted(FPG_ROOTS):
        fail("FINAL_PRODUCT_GATE_ROOTS set wrong", errors)

    bs = {r.get("candidate_id"): r for r in recs if r.get("record_type") == "buildsc_candidate"}
    if set(bs) != BUILDSC_IDS:
        fail(f"Build/Supply traceability must cover 12/12 candidates; got {sorted(bs)}", errors)
    else:
        print("  OK   Build/Supply 12/12 candidates traced")
    for cid, sev in BUILDSC_SEVERITY.items():
        if (bs.get(cid) or {}).get("severity") != sev:
            fail(f"{cid} severity {(bs.get(cid) or {}).get('severity')!r} != {sev!r}", errors)
    b1 = bs.get("ANOX-BUILDSC-CANDIDATE-001") or {}
    if b1.get("evidence_integrity") != "CRITICAL":
        fail("ANOX-BUILDSC-CANDIDATE-001 must carry EVIDENCE_INTEGRITY=CRITICAL", errors)
    else:
        print("  OK   BUILDSC-001 EVIDENCE_INTEGRITY=CRITICAL preserved")

    rels = {r.get("finding_id"): r for r in recs if r.get("record_type") == "historical_relation"}
    c5 = rels.get("ANOX-LEGACY-CRYPTO-005") or {}
    if c5.get("relationship") != "LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION" or c5.get("canonical_status") != "Closed":
        fail("historical relation ANOX-LEGACY-CRYPTO-005 must be Closed + LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION", errors)
    i5 = rels.get("ANOX-LEGACY-INTEGRATION-005") or {}
    if i5.get("relationship") != "NEW_ROOT_CAUSE_RELATED_TO_HISTORICAL_FINDING" or i5.get("canonical_status") != "Open":
        fail("historical relation ANOX-LEGACY-INTEGRATION-005 must be Open + NEW_ROOT_CAUSE_RELATED_TO_HISTORICAL_FINDING", errors)

    ng = next((r for r in recs if r.get("record_type") == "next_gate"), None)
    if not ng or ng.get("gate") != NEXT_GATE_ID or "NOT_EXECUTED" not in str(ng.get("status", "")):
        fail(f"next_gate record must be {NEXT_GATE_ID} CANDIDATE / NOT_EXECUTED", errors)


def validate_cryptojni(errors):
    recs = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl")

    cj = {r.get("candidate_id"): r for r in recs if r.get("record_type") == "cryptojni_candidate"}
    if set(cj) != CRYPTOJNI_IDS:
        fail(f"Crypto/JNI traceability must cover exactly 6 candidates; got {sorted(cj)}", errors)
    else:
        print("  OK   Crypto/JNI 6/6 candidates traced")
    for cid, sev in CRYPTOJNI_SEVERITY.items():
        r = cj.get(cid) or {}
        if r.get("severity") != sev:
            fail(f"{cid} severity {r.get('severity')!r} != {sev!r}", errors)
        if r.get("source_audit_id") != "AUDIT-SECURITY-CRYPTO-JNI-001":
            fail(f"{cid} source_audit_id wrong: {r.get('source_audit_id')!r}", errors)
        if r.get("status") != "Open":
            fail(f"{cid} must remain Open (candidate), got {r.get('status')!r}", errors)
        want_pre = cid in CRYPTOJNI_PRE_B004
        if bool(r.get("pre_b004_blocker")) != want_pre:
            fail(f"{cid} pre_b004_blocker={r.get('pre_b004_blocker')!r}, expected {want_pre}", errors)

    rels = {r.get("root_id"): r for r in recs if r.get("record_type") == "specialist_relation" and r.get("source_audit_id") == "AUDIT-SECURITY-CRYPTO-JNI-001"}
    if set(rels) != set(CRYPTOJNI_RELATIONS):
        fail(f"specialist_relation roots must be exactly {sorted(CRYPTOJNI_RELATIONS)}; got {sorted(rels)}", errors)
    for rid, rel in CRYPTOJNI_RELATIONS.items():
        if (rels.get(rid) or {}).get("relation") != rel:
            fail(f"specialist_relation {rid} relation {(rels.get(rid) or {}).get('relation')!r} != {rel!r}", errors)

    ov = next((r for r in recs if r.get("record_type") == "severity_overlay" and r.get("root_id") == "ROOT-013"), None)
    if ov is None:
        fail("ROOT-013 severity overlay record missing", errors)
    else:
        if ov.get("prior_severity") != "LOW" or ov.get("proposed_severity") != "MEDIUM":
            fail("ROOT-013 overlay must record prior LOW -> proposed MEDIUM", errors)
        if ov.get("status") != "PENDING_SPECIALIST_CONSOLIDATION":
            fail("ROOT-013 overlay status must be PENDING_SPECIALIST_CONSOLIDATION", errors)
    roots = {r.get("root_id"): r for r in recs if r.get("record_type") == "consensus_root"}
    if (roots.get("ROOT-013") or {}).get("severity") != "LOW":
        fail("consensus_root ROOT-013 severity was silently overwritten (must remain LOW; overlay only)", errors)
    else:
        print("  OK   ROOT-013 overlay pending consolidation; consensus severity untouched")

    gsets = {r.get("gate_set"): r for r in recs if r.get("record_type") == "gate_set" and r.get("gate_set")}
    pre = gsets.get("PRE_B004_CRYPTOJNI") or {}
    if sorted(pre.get("members") or []) != sorted(PRE_B004_CRYPTOJNI_GATE):
        fail(f"PRE_B004_CRYPTOJNI members wrong: {pre.get('members')}", errors)
    else:
        print("  OK   PRE_B004_CRYPTOJNI 8-member gate set exact")
    b89 = gsets.get("B008_B009_CRYPTOJNI") or {}
    if sorted(b89.get("members") or []) != sorted(B008_B009_CRYPTOJNI_GATE):
        fail(f"B008_B009_CRYPTOJNI members wrong: {b89.get('members')}", errors)
    else:
        print("  OK   B008_B009_CRYPTOJNI 5-member gate set exact")

    prov = next((r for r in recs if r.get("record_type") == "provenance_limitation"), None)
    if prov is None:
        fail("provenance_limitation record missing", errors)
    else:
        for k, h in (("committed_arm64", "11a958a5f8b653692fdbf189dd42fa373cff729fdfef0cc5748afc5bfd3ea6c3"),
                     ("committed_x86_64", "ecf9fdc1e83e419f1e1b9da6e83e184f5b3dfe694ee5de13529d68fc60653c88"),
                     ("temp_arm64", TEMP_BUILD_HASHES["arm64-v8a"]),
                     ("temp_x86_64", TEMP_BUILD_HASHES["x86_64"])):
            if prov.get(k) != h:
                fail(f"provenance_limitation {k} hash wrong", errors)
        if "TEMP_CURRENT_SOURCE_BUILD_EVIDENCE" not in str(prov.get("runtime_policy", "")):
            fail("provenance_limitation must restrict runtime claims to TEMP_CURRENT_SOURCE_BUILD_EVIDENCE", errors)
        if "PROVENANCE_VERIFIED_CANONICAL_BINARY" not in str(prov.get("runtime_policy", "")):
            fail("provenance_limitation must require PROVENANCE_VERIFIED_CANONICAL_BINARY for final closure", errors)
        if "7db20fa4df8dc70392afd803fabaaf20c0b50d7d" not in str(prov.get("binary_source_commit", "")):
            fail("provenance_limitation must record committed .so source commit 7db20fa", errors)

    tb = next((r for r in recs if r.get("record_type") == "temp_build_evidence"), None)
    if tb is None:
        fail("temp_build_evidence record missing", errors)
    else:
        outs = tb.get("outputs") or {}
        for abi, h in TEMP_BUILD_HASHES.items():
            if (outs.get(abi) or {}).get("sha256") != h:
                fail(f"temp_build_evidence {abi} hash wrong/missing", errors)
        if tb.get("audited_sha") != CRYPTOJNI_AUDIT_SHA:
            fail("temp_build_evidence audited_sha must equal audited SHA a79166ab", errors)
        if "NOT" not in str(tb.get("canonicality", "")):
            fail("temp_build_evidence must record non-canonical / temporary status", errors)

    abi = next((r for r in recs if r.get("record_type") == "abi_revision"), None)
    if abi is None:
        fail("abi_revision record missing", errors)
    else:
        if abi.get("jni_abi_revision") != "YES":
            fail("abi_revision must record JNI_ABI_REVISION=YES", errors)
        if abi.get("sec_c_required") != "NO":
            fail("abi_revision must record SEC_C_REQUIRED=NO", errors)
        if abi.get("architecture_verdict") != "COMPONENT_INTERNAL_REDESIGN_ONLY":
            fail("abi_revision verdict must be COMPONENT_INTERNAL_REDESIGN_ONLY", errors)

    coupling = {(r.get("list")): r for r in recs if r.get("record_type") == "fix_coupling"}
    if "MUST_FIX_TOGETHER" not in coupling or "MUST_NOT_FIX_ALONE" not in coupling:
        fail("fix_coupling records (MUST_FIX_TOGETHER / MUST_NOT_FIX_ALONE) missing", errors)
    else:
        print("  OK   Crypto/JNI provenance limitation, temp-build evidence, ABI revision, fix couplings recorded")


def validate_authdpop(errors):
    recs = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl")

    cands = {r.get("candidate_id"): r for r in recs if r.get("record_type") == "authdpop_candidate"}
    if set(cands) != AUTHDPOP_CANDIDATE_IDS:
        fail(f"Auth/DPoP traceability must cover exactly 3 candidates; got {sorted(cands)}", errors)
    else:
        print("  OK   Auth/DPoP 3/3 candidates traced")
    for cid, sev in AUTHDPOP_SEVERITY.items():
        r = cands.get(cid) or {}
        if r.get("severity") != sev:
            fail(f"{cid} severity {r.get('severity')!r} != {sev!r}", errors)
        if r.get("source_audit_id") != AUTHDPOP_ID:
            fail(f"{cid} source_audit_id wrong: {r.get('source_audit_id')!r}", errors)
        if r.get("status") != "Open" or r.get("disposition") != "OPEN_PENDING_CONSOLIDATION":
            fail(f"{cid} must remain Open/OPEN_PENDING_CONSOLIDATION", errors)
        want_pre = cid == "ANOX-AUTHDPOP-CANDIDATE-001"
        if bool(r.get("pre_b004_blocker")) != want_pre:
            fail(f"{cid} pre_b004_blocker={r.get('pre_b004_blocker')!r}, expected {want_pre}", errors)
        if not (r.get("group") or r.get("remediation_group")):
            fail(f"{cid} missing remediation-coverage group", errors)
        if r.get("retest_required") != "YES" or not r.get("independent_retest_owner"):
            fail(f"{cid} missing independent retest requirement", errors)
    if (cands.get("ANOX-AUTHDPOP-CANDIDATE-001") or {}).get("pre_b004_blocker") is True:
        print("  OK   CANDIDATE-001 is the sole Pre-B004 blocker candidate")

    gaps = {r.get("gap_id"): r for r in recs if r.get("record_type") == "authdpop_gap"}
    if set(gaps) != AUTHDPOP_GAP_IDS:
        fail(f"Auth/DPoP gaps must be exactly GAP-001..003; got {sorted(gaps)}", errors)
    else:
        print("  OK   Auth/DPoP 3/3 architecture gaps traced")
    for gid in AUTHDPOP_GAP_IDS:
        r = gaps.get(gid) or {}
        if r.get("source_audit_id") != AUTHDPOP_ID or r.get("status") != "Open":
            fail(f"{gid} source/status wrong", errors)
        if r.get("pre_b004_contract_freeze") is not True:
            fail(f"{gid} must record pre_b004_contract_freeze=True", errors)

    rels = {r.get("root_id"): r for r in recs
            if r.get("record_type") == "specialist_relation" and r.get("source_audit_id") == AUTHDPOP_ID}
    if set(rels) != set(AUTHDPOP_RELATIONS):
        fail(f"Auth/DPoP specialist_relation roots must be exactly {sorted(AUTHDPOP_RELATIONS)}; got {sorted(rels)}", errors)
    for rid, rel in AUTHDPOP_RELATIONS.items():
        if (rels.get(rid) or {}).get("relation") != rel:
            fail(f"specialist_relation {rid} relation {(rels.get(rid) or {}).get('relation')!r} != {rel!r}", errors)
    roots = {r.get("root_id"): r for r in recs if r.get("record_type") == "consensus_root"}
    for rid in AUTHDPOP_RELATIONS:
        if rid not in roots:
            fail(f"specialist_relation {rid} points at a consensus root that does not exist", errors)
    if (roots.get("ROOT-016") or {}).get("status") != "REJECTED_NOT_A_FINDING":
        fail("ROOT-016 must remain REJECTED_NOT_A_FINDING (Auth/DPoP CANDIDATE-002 must not revive it)", errors)
    else:
        print("  OK   ROOT-016 remains rejected; Auth/DPoP relations exact (006/007 CONFIRMED, 008/009 CONFIRMED_AND_EXPANDED)")

    gsets = {r.get("gate_set"): r for r in recs if r.get("record_type") == "gate_set" and r.get("gate_set")}
    pre = gsets.get("PRE_B004_AUTHDPOP") or {}
    if sorted(pre.get("members") or []) != sorted(PRE_B004_AUTHDPOP_GATE):
        fail(f"PRE_B004_AUTHDPOP members wrong: {pre.get('members')}", errors)
    else:
        print("  OK   PRE_B004_AUTHDPOP 8-member gate set exact")
    lat = gsets.get("LATER_AUTHDPOP") or {}
    if sorted(lat.get("members") or []) != sorted(LATER_AUTHDPOP_GATE):
        fail(f"LATER_AUTHDPOP members wrong: {lat.get('members')}", errors)
    else:
        print("  OK   LATER_AUTHDPOP 5-item gate set exact")

    relmap = {r.get("finding_id"): r for r in recs
              if r.get("record_type") == "historical_relation" and r.get("source_audit_id") == AUTHDPOP_ID}
    if set(relmap) != set(AUTHDPOP_HIST_RELATIONS):
        fail(f"Auth/DPoP historical_relation records must cover {sorted(AUTHDPOP_HIST_RELATIONS)}; got {sorted(relmap)}", errors)
    for fid, (rel, st) in AUTHDPOP_HIST_RELATIONS.items():
        r = relmap.get(fid) or {}
        if r.get("relationship") != rel or r.get("canonical_status") != st:
            fail(f"historical_relation {fid}: relationship {r.get('relationship')!r}/{r.get('canonical_status')!r} != {rel!r}/{st!r}", errors)
    reval = next((r for r in recs if r.get("record_type") == "authdpop_historical_revalidation"
                  and r.get("source_audit_id") == AUTHDPOP_ID), None)
    if reval is None or len(reval.get("rows") or []) != 17:
        fail("authdpop_historical_revalidation record missing or must contain the 17 revalidation rows", errors)
    else:
        print("  OK   Auth/DPoP historical revalidation table preserved (17 rows)")

    cov = next((r for r in recs if r.get("record_type") == "authdpop_coverage"
                and r.get("source_audit_id") == AUTHDPOP_ID), None)
    if cov is None:
        fail("authdpop_coverage record missing", errors)
    else:
        if (cov.get("b002_production_files_reviewed"), cov.get("b002_production_files_discovered")) != (29, 29):
            fail("authdpop_coverage must record 29/29 production files", errors)
        if (cov.get("b002_relevant_test_files_reviewed"), cov.get("b002_relevant_test_files_discovered")) != (14, 14):
            fail("authdpop_coverage must record 14/14 relevant test files", errors)
        if cov.get("architecture_requirements_total") != 40:
            fail("authdpop_coverage must record 40 architecture requirements", errors)
        if cov.get("status_counts") != AUTHDPOP_COVERAGE_COUNTS:
            fail(f"authdpop_coverage status_counts wrong: {cov.get('status_counts')}", errors)
        inv = cov.get("focused_test_inventory") or {}
        if (inv.get("total"), inv.get("jvm"), inv.get("instrumented"), inv.get("physical")) != (155, 128, 27, 0):
            fail("authdpop_coverage focused_test_inventory must be 155 (128 JVM / 27 instrumented / 0 physical)", errors)
        ex = cov.get("audit_test_execution") or {}
        if (ex.get("executed"), ex.get("passed"), ex.get("failed"), ex.get("errors"), ex.get("skipped")) != (173, 173, 0, 0, 0):
            fail("authdpop_coverage audit_test_execution must record 173/173 PASS", errors)
        if (cov.get("adversarial_harness") or {}).get("cases") != 22:
            fail("authdpop_coverage must record 22 adversarial cases", errors)
        else:
            print("  OK   Auth/DPoP coverage 29/29 + 14/14 + 40 reqs (0 unmapped); inventory 155; executed 173/173; 22 adversarial cases")

    phys = next((r for r in recs if r.get("record_type") == "physical_evidence_requirements"
                 and r.get("source_audit_id") == AUTHDPOP_ID), None)
    if phys is None or "NOT_EXECUTED" not in str(phys.get("status", "")):
        fail("physical_evidence_requirements record missing or not NOT_EXECUTED", errors)
    else:
        print("  OK   Auth/DPoP physical evidence requirements recorded as NOT_EXECUTED")

    rem = next((r for r in recs if r.get("record_type") == "authdpop_remediation"
                and r.get("source_audit_id") == AUTHDPOP_ID), None)
    if rem is None:
        fail("authdpop_remediation record missing", errors)
    else:
        if set(rem.get("groups") or {}) != AUTHDPOP_GROUPS:
            fail(f"authdpop_remediation groups must be AD-A..AD-F; got {sorted(rem.get('groups') or {})}", errors)
        if rem.get("sec_c_required") != "NO" or rem.get("architecture_verdict") != "COMPONENT_INTERNAL_REDESIGN_ONLY":
            fail("authdpop_remediation SEC-C=NO / COMPONENT_INTERNAL_REDESIGN_ONLY verdict wrong", errors)
        else:
            print("  OK   Auth/DPoP remediation groups AD-A..AD-F; SEC-C=NO; COMPONENT_INTERNAL_REDESIGN_ONLY")

    coupling = {(r.get("list"), r.get("source_audit_id")): r for r in recs if r.get("record_type") == "authdpop_fix_coupling"}
    if ("MUST_FIX_TOGETHER", AUTHDPOP_ID) not in coupling or ("MUST_NOT_FIX_ALONE", AUTHDPOP_ID) not in coupling:
        fail("Auth/DPoP fix_coupling records (MUST_FIX_TOGETHER / MUST_NOT_FIX_ALONE) missing", errors)

    for rt in ("attackchain_handoff", "android_storage_handoff"):
        h = next((r for r in recs if r.get("record_type") == rt and r.get("source_audit_id") == AUTHDPOP_ID), None)
        if h is None or "NOT_EXECUTED" not in str(h.get("status", "")):
            fail(f"{rt} record missing or not CANDIDATE/NOT_EXECUTED", errors)
    print("  OK   Auth/DPoP fix couplings + Android/Storage + Attackchain handoffs recorded")


def validate_findings(errors):
    findings = load_jsonl(REGISTRY_DIR / "findings.jsonl")
    f5 = next((f for f in findings if f.get("finding_id") == "ANOX-LEGACY-CRYPTO-005"), None)
    if f5 is None:
        fail("ANOX-LEGACY-CRYPTO-005 missing from findings.jsonl", errors)
    else:
        if f5.get("status") != "Closed":
            fail(f"ANOX-LEGACY-CRYPTO-005 must remain Closed, got {f5.get('status')!r}", errors)
        if not f5.get("closure_actor") or not f5.get("closure_evidence"):
            fail("ANOX-LEGACY-CRYPTO-005 closure evidence/actor removed", errors)
        if "LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION" not in str(f5.get("notes", "")):
            fail("ANOX-LEGACY-CRYPTO-005 lacks the preserved LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION relationship note", errors)
        if f5.get("status") == "Closed":
            print("  OK   ANOX-LEGACY-CRYPTO-005 remains Closed with preserved relationship")
    i5 = next((f for f in findings if f.get("finding_id") == "ANOX-LEGACY-INTEGRATION-005"), None)
    if i5 is None or i5.get("status") != "Open":
        fail("ANOX-LEGACY-INTEGRATION-005 must remain Open", errors)
    else:
        print("  OK   ANOX-LEGACY-INTEGRATION-005 remains Open")
    for fid in ("ANOX-MAINARCH-013", "ANOX-MAINARCH-018", "ANOX-MAINARCH-030", "ANOX-LEGACY-B003-001"):
        f = next((x for x in findings if x.get("finding_id") == fid), None)
        if f is None or f.get("status") not in ("Open", "Ready For Retest"):
            fail(f"existing product finding {fid} must remain Open/Ready For Retest", errors)
    for fid, want in (("ANOX-LEGACY-CRYPTO-005", "Closed"), ("ANOX-LEGACY-INTEGRATION-005", "Open"),
                      ("ANOX-MAINARCH-031", "Closed"), ("ANOX-SECURITY-ARCH-001", "Open"),
                      ("ANOX-SECURITY-ARCH-007", "Open"), ("ANOX-SECURITY-ARCH-008", "Open")):
        f = next((x for x in findings if x.get("finding_id") == fid), None)
        if f is None or f.get("status") != want:
            fail(f"EVENT-0046 finding {fid} must remain {want}, got {(f or {}).get('status')!r}", errors)
        elif "ANOX-EVENT-0046" not in str(f.get("notes", "")):
            fail(f"{fid} lacks the preserved ANOX-EVENT-0046 relationship note", errors)
    for fid, want in (("ANOX-LEGACY-INTEGRATION-001", "Closed"), ("ANOX-LEGACY-INTEGRATION-003", "Closed"),
                      ("ANOX-MAINARCH-019", "Closed"), ("ANOX-MAINARCH-008", "Closed"),
                      ("ANOX-SECURITY-ARCH-006", "Open"), ("ANOX-SECURITY-ARCH-003", "Open"),
                      ("ANOX-SECURITY-ARCH-007", "Open"), ("ANOX-MAINARCH-018", "Open"),
                      ("ANOX-MAINARCH-005", "Closed"), ("ANOX-MAINARCH-014", "Closed")):
        f = next((x for x in findings if x.get("finding_id") == fid), None)
        if f is None or f.get("status") != want:
            fail(f"EVENT-0047 finding {fid} must remain {want}, got {(f or {}).get('status')!r}", errors)
        elif "ANOX-EVENT-0047" not in str(f.get("notes", "")):
            fail(f"{fid} lacks the preserved ANOX-EVENT-0047 relationship note", errors)


def validate_lifecycle(errors):
    ws_path = REGISTRY_DIR.parent / "WORKFORCE_STATE.json"
    if not ws_path.exists():
        fail("WORKFORCE_STATE.json missing", errors)
        return
    ws = load_json(ws_path)
    if ws.get("product_development_state") != "BLOCKED_PENDING_FINAL_AUDIT":
        fail("product_development_state must remain BLOCKED_PENDING_FINAL_AUDIT", errors)
    else:
        print("  OK   product remains BLOCKED_PENDING_FINAL_AUDIT")
    ir = load_json(REGISTRY_DIR / "implementation_readiness.json")
    for dom in ("B-004", "B-005"):
        st = ((ir.get("domains") or {}).get(dom) or {}).get("implementation_state")
        if st != "NOT_STARTED":
            fail(f"{dom} implementation_state must remain NOT_STARTED, got {st!r}", errors)
    print("  OK   B-004 and B-005 remain NOT_STARTED")
    nxt = ws.get("next_phase") or (ws.get("final_pre_product_audit") or {}).get("next_phase")
    if nxt != NEXT_GATE_ID:
        fail(f"next_phase must be {NEXT_GATE_ID}, got {nxt!r}", errors)
    else:
        print(f"  OK   next gate {NEXT_GATE_ID} recorded")
    completed = set((ws.get("final_pre_product_audit") or {}).get("completed_audit_ids") or [])
    if NEXT_GATE_ID in completed:
        fail(f"{NEXT_GATE_ID} must not be in completed_audit_ids", errors)
    post = (ws.get("post_merge_state") or {}).get("current_gate", "")
    if NEXT_GATE_ID not in post or "CANDIDATE" not in post.upper() and "Candidate" not in post:
        fail(f"post_merge_state gate must record {NEXT_GATE_ID} as Candidate", errors)
    completed = set((ws.get("final_pre_product_audit") or {}).get("completed_audit_ids") or [])
    if "AUDIT-SECURITY-CRYPTO-JNI-001" not in completed:
        fail("completed_audit_ids must record AUDIT-SECURITY-CRYPTO-JNI-001 as executed+preserved", errors)
    if "AUDIT-SECURITY-AUTH-DPOP-001" not in completed:
        fail("completed_audit_ids must record AUDIT-SECURITY-AUTH-DPOP-001 as executed+preserved", errors)
    for gid in ("AUDIT-SECURITY-ANDROID-STORAGE-001", "AUDIT-SECURITY-ATTACKCHAIN-001"):
        if gid in completed:
            fail(f"{gid} must NOT be in completed_audit_ids", errors)


def validate_tasks(errors):
    tasks = load_jsonl(REGISTRY_DIR / "tasks.jsonl")
    t = next((x for x in tasks if x.get("task_id") == TASK_ID), None)
    if t is None:
        fail(f"{TASK_ID} missing from tasks.jsonl", errors)
    else:
        if t.get("status") != "Ready For Remote":
            fail(f"{TASK_ID} status {t.get('status')!r}, expected Ready For Remote", errors)
        if t.get("start_sha") != BASE_SHA:
            fail(f"{TASK_ID} start_sha must be {BASE_SHA}", errors)
        if t.get("branch") != DELIVERY_BRANCH:
            fail(f"{TASK_ID} branch must be {DELIVERY_BRANCH}", errors)
    for x in tasks:
        if x.get("task_id") == TASK_ID or str(x.get("task_id", "")).startswith("ANOX-TASK-SECURITY-AUDIT-EVIDENCE-PRESERVATION-"):
            continue
        blob = (x.get("task_id", "") + " " + x.get("title", "")).upper()
        audit_markers = ("CRYPTO-JNI", "CRYPTO_JNI", "CRYPTOJNI", "AUTH-DPOP", "AUTH_DPOP", "AUTHDPOP",
                         "ANDROID-STORAGE", "ANDROID_STORAGE", "ATTACKCHAIN")
        if any(m in blob for m in audit_markers):
            if x.get("status") not in ("Candidate",):
                fail(f"Specialist audit task {x.get('task_id')} is {x.get('status')!r} — specialist audits are evidence-preserved via the audit-evidence registry, not executed task records; must remain Candidate/NOT_EXECUTED", errors)
    print("  OK   next specialist gates are candidates, not executed")


def validate_no_product_changes(errors):
    if not has_git():
        return
    out = subprocess.run(["git", "diff", "--name-only", BASE_SHA], cwd=REPO_ROOT, capture_output=True, text=True)
    changed = out.stdout.strip().splitlines()
    forbidden = [p for p in changed if p.startswith(FORBIDDEN_PREFIXES) or p.endswith(".sql")]
    jni = [p for p in changed
           if not p.startswith("docs/")
           and ("jni" in p.lower() or "AndroidManifest" in p or p.endswith(".so") or "gradle" in p.lower())]
    bad = sorted(set(forbidden + jni))
    if bad:
        fail(f"product/CI/native paths changed: {bad}", errors)
    else:
        print("  OK   no product/CI/native changes")


def validate_project_memory(errors):
    state_path = REPO_ROOT / "docs" / "continuity" / "CURRENT_STATE.json"
    ledger_path = REPO_ROOT / "docs" / "continuity" / "PROJECT_HISTORY_LEDGER.jsonl"
    if not state_path.exists() or not ledger_path.exists():
        fail("continuity surfaces missing", errors)
        return
    state = load_json(state_path)
    ledger = load_jsonl(ledger_path)
    if not ledger:
        fail("ledger empty", errors)
        return
    latest = ledger[-1]
    if state.get("latest_material_event_id") != latest.get("event_id"):
        fail("Project Memory stale: latest_material_event_id != last ledger event", errors)
    elif latest.get("event_id") != LEDGER_EVENT:
        fail(f"last ledger event must be {LEDGER_EVENT}, got {latest.get('event_id')}", errors)
    else:
        print(f"  OK   Project Memory synced to {latest.get('event_id')}")


def main():
    errors = []
    print("[EVIDENCE-PRESERVATION] Base / delivery")
    validate_base(errors)
    print("\n[EVIDENCE-PRESERVATION] Preserved reports / hashes / source status")
    validate_reports(errors)
    print("\n[EVIDENCE-PRESERVATION] Audit registry")
    validate_registry(errors)
    print("\n[EVIDENCE-PRESERVATION] Traceability / roots / gates")
    validate_traceability(errors)
    print("\n[EVIDENCE-PRESERVATION] Crypto/JNI specialist evidence")
    validate_cryptojni(errors)
    print("\n[EVIDENCE-PRESERVATION] Auth/DPoP specialist evidence")
    validate_authdpop(errors)
    print("\n[EVIDENCE-PRESERVATION] Canonical findings / historical relations")
    validate_findings(errors)
    print("\n[EVIDENCE-PRESERVATION] Lifecycle state")
    validate_lifecycle(errors)
    validate_tasks(errors)
    print("\n[EVIDENCE-PRESERVATION] Scope / memory")
    validate_no_product_changes(errors)
    validate_project_memory(errors)
    if errors:
        print("\nSECURITY AUDIT EVIDENCE PRESERVATION: FAIL")
        for e in errors:
            print(f"  FAIL {e}")
        return 1
    print("\nSECURITY AUDIT EVIDENCE PRESERVATION: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
