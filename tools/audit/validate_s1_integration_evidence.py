#!/usr/bin/env python3
"""S1 canonical-integration evidence validator — REMEDIATION-S1-CANONICAL-INTEGRATION-001.

Why this file exists (shared-validator follow-up, governance-compliant form)
---------------------------------------------------------------------------
`tools/audit/validate_security_audit_evidence_preservation.py` is a
PROTECTED_SHARED_GOVERNANCE_FILE whose content is pinned by the frozen S0
contract (`tools/audit/validate_s0_contract_freeze.py`) to exactly the two
Human-ratified contents; any other content is "unauthorized modification — a
new Human ratification is required" (`grants_s1_permission = false`).
The S1 integration therefore does NOT modify that file. Instead:

  * the exact minimum S1-era extension is preserved as a ratification proposal
    (`docs/reports/security/decisions/S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-PROPOSAL-001.md`
    + patch), tamper-evident via the pinned post-change SHA-256 below;
  * this validator runs the ratified central module's era-agnostic S0
    protections VERBATIM (imported, unmodified code) and adds the pinned
    S1-era acceptance logic for the four era-bound sections (base/topology,
    registry growth, scope, Project-Memory chain).

Acceptance is pinned to exactly ANOX-EVENT-0055 / SEC-AUDIT-REG-0014 / the
recorded integration topology. Every acceptance condition has a paired
rejection test in tools/audit/test_s1_integration_evidence.py.
Stdlib only. Fails closed.
"""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(os.environ.get("SECURITY_AUDIT_PRESERVATION_REPO") or Path(__file__).resolve().parents[2])
CENTRAL = "tools/audit/validate_security_audit_evidence_preservation.py"
CENTRAL_TESTS = "tools/audit/test_security_audit_evidence_preservation.py"

# Ratified content of the protected shared validator (pinned by the S0 contract
# under ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001).
CENTRAL_RATIFIED_SHA256 = "89c7358fbbe61c71c8fcde114ffc8a83aa33f52bd3fb763417e00f4131d84bb7"
# Proposed post-change content (S1-era extension) awaiting Human ratification.
# The ratification package also carries the paired central-test-suite update so
# that applying the proposal leaves BOTH files green (pre-ratification
# correction REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001).
CENTRAL_PROPOSED_SHA256 = "e52f626a46f27af59b51acf2af20ec6762ab71f8c1e35239e6c59f70182af1f8"
CENTRAL_TESTS_PROPOSED_SHA256 = "c305c21c9405454067721efe7c8d0395e99aed9e6870cf49e3daedb4a3552462"
PROPOSAL_PATCH = "docs/reports/security/decisions/proposals/S1_SHARED_VALIDATOR_EXTENSION.patch"
PROPOSAL_RECORD = "docs/reports/security/decisions/S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-PROPOSAL-001.md"

S1_INTEGRATION_EVENT = {
    "event_id": "ANOX-EVENT-0055",
    "type": "remediation_session_integration",
    "task": "ANOX-TASK-REMEDIATION-S1-CANONICAL-INTEGRATION-001",
    "start_head": "29a6643189242a47c4a79c38acd04c1eca748787",
    "merged_head": "e32463ca71b0fec62a5f20026e6dc528f9bff30c",
    "merged_base": "0f932520393feee6d479cc099f179f5766323125",
    "ref": "docs/reports/security/remediation/REMEDIATION-S1-CANONICAL-INTEGRATION-001.md",
    "delivery_branch": "integration/s1-after-s0-001",
    "supersedes_provisional_event": "ANOX-EVENT-0054",
}
S1_INTEGRATION_ID = "REMEDIATION-S1-CANONICAL-INTEGRATION-001"
S1_ORIGINAL_TASK = "ANOX-TASK-REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001"
# Pinned S1 delivery commits (merge is recorded in the registry/event). A
# Human-authorized pre-ratification correction pass may append exactly one
# further task pair [D1 substantive, D2 metadata] on the same delivery branch;
# D1 is bound to CURRENT_STATE.described_head and current_task must be the
# correction task. No other chain shape is accepted.
S1_SUBSTANTIVE_SHA = "ea20aaaf330c9268448df5523e89615aa0a69074"
S1_METADATA_SHA = "573c5f58b91a1871fb6d7a6d722585a8518fa02c"
S1_CORRECTION_TASK = "ANOX-TASK-REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001"

S1_ALLOWED_EXACT = {
    ".github/workflows/ci.yml", ".gitignore", "android/build.gradle.kts",
    "crypto/rust/rust-toolchain.toml", "docs/current/REPOSITORY_SECURITY_POLICY.md",
    "docs/reports/security/retests/INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001.md",
    "docs/reports/security/remediation/REMEDIATION-S1-CANONICAL-INTEGRATION-001.md",
    PROPOSAL_RECORD, PROPOSAL_PATCH,
    "docs/security/audit-evidence/audit_registry.jsonl",
    "tools/audit/lifecycle_legality.py",
    "tools/audit/validate_s0_evidence_preservation.py",  # explicit: SEC-AUDIT-REG-0014 is not an S0 "prior" record
    "tools/audit/validate_s0_contract_freeze.py",  # explicit: S0 scope evaluated over S0's own pinned range
    "tools/audit/test_security_audit_evidence_preservation.py",  # fixture normalisation only (277 tests pinned)
    "tools/audit/test_s0_contract_freeze.py",  # paired fail-closed worktree tests (S1-PRE-RAT-CORR)
    "docs/reports/security/remediation/REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001.md",
    "tools/audit/validate_b021_verification_matrix.py",
    "tools/audit/validate_s1_build_provenance.py",
    "tools/audit/test_s1_build_provenance.py",
    "tools/audit/test_s1_retest_remediation.py",
    "tools/audit/validate_s1_integration_evidence.py",
    "tools/audit/test_s1_integration_evidence.py",
}
S1_ALLOWED_PREFIXES = (
    "android/src/main/jniLibs/",   # deletions of the committed-.so bypass only
    "tools/security/",
    "docs/security/remediation/",
)
S1_FORBIDDEN_PREFIXES = (
    "crypto/rust/src/", "android/src/main/java/", "android/src/androidTest/", "android/src/test/",
    "backend/", "supabase/", "migrations/", "docs/authority/",
)

S1_INTEGRATION_REGISTRY_REQUIRED = {
    "record_id": "SEC-AUDIT-REG-0014",
    "audit_id": S1_INTEGRATION_ID,
    "artifact_type": "SECURITY_REMEDIATION_EVIDENCE",
    "task_id": S1_INTEGRATION_EVENT["task"],
    "base_sha": S1_INTEGRATION_EVENT["start_head"],
    "s1_original_base_sha": "0f932520393feee6d479cc099f179f5766323125",
    "s1_original_substantive_sha": "fc58414b6790c07f65d1dc9f72c019abd42efc86",
    "s1_original_final_head_sha": "e32463ca71b0fec62a5f20026e6dc528f9bff30c",
    "s1_integration_merge_sha": "dd6e2c5d82f0777aedfea9fd7a2516cb83254fdb",
    "s1_provisional_event": "ANOX-EVENT-0054",
    "s1_provisional_event_status": "NONCANONICAL",
    "canonical_event": "ANOX-EVENT-0055",
    "independent_retest_id": "INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001",
    "independent_retest_result": "PASS_WITH_FINDINGS",
    "findings_final_disposition": {
        "F-1": "FIXED", "F-2": "FIXED", "F-3": "FIXED", "F-4": "FIXED", "F-5": "FIXED",
        "F-6": "FIXED", "F-7": "FIXED", "F-8": "DOCUMENTED_PIN_PROVENANCE_UNVERIFIED_PINS_UNCHANGED",
        "F-9": "FIXED",
    },
    "shared_validator_followup": "PROPOSAL_PREPARED_PENDING_HUMAN_RATIFICATION",
    "shared_validator_proposed_sha256": CENTRAL_PROPOSED_SHA256,
    "shared_validator_paired_tests_proposed_sha256": CENTRAL_TESTS_PROPOSED_SHA256,
    "medium_or_higher_open_retest_findings": 0,
    "msc_closed_by_s1": 0,
    "open_msc_units": 42,
    "security_remediation": "IN_PROGRESS",
    "b004": "NOT_STARTED",
    "b005": "NOT_STARTED",
    "product": "BLOCKED_PENDING_FINAL_AUDIT",
    "native_behavior_source_changed": "NO",
    "arm64_runtime_evidence": "IMPLEMENTER_ONLY_NOT_INDEPENDENT",
    "x86_64_runtime_evidence": "PENDING_REAL_CI_OR_INDEPENDENT_RUNTIME_EVIDENCE",
    "msc_runtime_tested_downgraded_under_exact_fcp1": ["MSC-UNIT-001", "MSC-UNIT-002"],
    "s0_files_changed_by_s1": 0,
    "previous_evidence_weakened": "NO",
    "status": "INTEGRATED_PENDING_TARGETED_INDEPENDENT_RETEST",
    "delivery_branch": S1_INTEGRATION_EVENT["delivery_branch"],
    "report_path": S1_INTEGRATION_EVENT["ref"],
    "report_sha256": "cbe0831071ea71e311cb9ad4458fd5be14a61bd2033a5ea0e9940c5321602d05",
}
S1_INTEGRATION_SOURCE_SHA256 = {
    "independent_retest": ("docs/reports/security/retests/INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001.md",
                           "c3e6a564c32992731af42358a5c42a206b76baff95a2c0408147f732b91d95ae"),
    "s1_runtime_evidence_record": ("docs/security/remediation/S1_PROVENANCE_VERIFIED_NATIVE_RUNTIME.md",
                                   "0db8adb9dc607e1e718babd7355e9e879b964270d3b1c5bd7b4fa713f58d727c"),
    "s1_task_report": ("docs/security/remediation/S1_TASK_REPORT.md", "a487f0c4b0f1fb00ca4cb79dde7a17463b3092733a2b9f804ac795e6d37ae3ca"),
}


# ---------------------------------------------------------------------------
def fail(msg, errors):
    errors.append(msg)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def has_git():
    dot_git = REPO_ROOT / ".git"
    if dot_git.is_dir():
        return True
    if dot_git.is_file():
        try:
            line = dot_git.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError):
            return False
        if line.startswith("gitdir:"):
            target = line[len("gitdir:"):].strip()
            tpath = Path(target) if Path(target).is_absolute() else REPO_ROOT / target
            return tpath.is_dir() and (tpath / "HEAD").exists()
    return False


def _git(args):
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True)


def load_central():
    """Import the ratified central validator unmodified (fail closed on drift)."""
    p = REPO_ROOT / CENTRAL
    if not p.exists():
        return None, f"protected shared validator missing: {CENTRAL}"
    digest = sha256_file(p)
    if digest != CENTRAL_RATIFIED_SHA256:
        return None, (f"protected shared validator content {digest[:16]}… is not the Human-ratified content "
                      f"{CENTRAL_RATIFIED_SHA256[:16]}… — S1 must not run on a modified shared validator")
    os.environ["SECURITY_AUDIT_PRESERVATION_REPO"] = str(REPO_ROOT)
    spec = importlib.util.spec_from_file_location("anox_central_ratified", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, None


# ---------------------------------------------------------------------------
def _s1_delivery_active(state):
    return (state.get("current_task") in (S1_INTEGRATION_EVENT["task"], S1_CORRECTION_TASK)
            and state.get("delivery_branch") == S1_INTEGRATION_EVENT["delivery_branch"])


def _is_s1_integration_event(ev):
    return (ev.get("event_id") == S1_INTEGRATION_EVENT["event_id"]
            and ev.get("type") == S1_INTEGRATION_EVENT["type"]
            and ev.get("task") == S1_INTEGRATION_EVENT["task"]
            and ev.get("start_head") == S1_INTEGRATION_EVENT["start_head"]
            and ev.get("merged_head") == S1_INTEGRATION_EVENT["merged_head"]
            and ev.get("supersedes_provisional_event") == S1_INTEGRATION_EVENT["supersedes_provisional_event"]
            and S1_INTEGRATION_EVENT["ref"] in (ev.get("refs") or []))


def validate_base_s1(central, errors):
    print("[S1-INTEGRATION] Base / integration topology")
    if not has_git():
        print("  SKIP git checks (no .git — fixture mode)")
        return
    sys.path.insert(0, str(REPO_ROOT / "tools" / "audit"))
    import lifecycle_legality as ll
    head = _git(["rev-parse", "HEAD"]).stdout.strip()
    state = json.loads((REPO_ROOT / "docs/continuity/CURRENT_STATE.json").read_text(encoding="utf-8"))
    if not _s1_delivery_active(state):
        fail("CURRENT_STATE does not declare the S1 integration delivery (current_task/delivery_branch)", errors)
        return
    described = state.get("described_head") or ""
    if not re.fullmatch(r"[0-9a-f]{40}", described):
        fail(f"CURRENT_STATE described_head is not a valid SHA: {described}", errors)
        return
    s1 = S1_INTEGRATION_EVENT
    for label, sha in (("BASE_SHA", central.BASE_SHA),
                       ("S0 successor base", central.S0_SUCCESSOR_EVENT["start_head"]),
                       ("S0 preservation base", central.S0_PRESERVATION_EVENT["start_head"])):
        if not ll._git_is_ancestor(sha, s1["start_head"], cwd=REPO_ROOT):
            fail(f"S1 integration base {s1['start_head'][:12]} does not descend from {label} {sha[:12]}", errors)
            return
    ok, merge_sha, sub, meta, reason = ll.canonical_integration_delivery(
        s1["start_head"], s1["merged_head"], s1["merged_base"], described, head,
        cwd=REPO_ROOT, metadata_allowlist=central.METADATA_ALLOWLIST,
        s1_substantive_sha=S1_SUBSTANTIVE_SHA, s1_metadata_sha=S1_METADATA_SHA,
        correction_task=S1_CORRECTION_TASK)
    if not ok:
        fail(f"canonical S1 integration delivery failed: {reason}", errors)
        return
    if head != S1_METADATA_SHA and state.get("current_task") != S1_CORRECTION_TASK:
        fail(f"correction-delivery commits present but CURRENT_STATE.current_task "
             f"{state.get('current_task')!r} is not the authorized correction task "
             f"{S1_CORRECTION_TASK}", errors)
        return
    print(f"  OK   merge {merge_sha[:12]} = ({s1['start_head'][:12]}, pinned {s1['merged_head'][:12]}); "
          f"substantive {sub[:12]}; metadata {meta[:12]}; exactly 2 task-authored commits; metadata allowlisted")


def validate_registry_s1(central, errors):
    print("\n[S1-INTEGRATION] Audit registry (S0 protections verbatim + pinned S1 record)")
    reg_path = REPO_ROOT / "docs/security/audit-evidence/audit_registry.jsonl"
    audits = {a.get("audit_id"): a for a in load_jsonl(reg_path)}
    if len(audits) != 14:
        fail(f"audit_registry.jsonl must contain exactly 14 records (13 ratified + 1 S1 integration record), found {len(audits)}", errors)
    # Run the ratified S0 registry validator unchanged on the 13-record view.
    original = central.load_jsonl

    def _view(path):
        recs = original(path)
        if Path(path).name == "audit_registry.jsonl":
            return [r for r in recs if r.get("audit_id") != S1_INTEGRATION_ID]
        return recs
    central.load_jsonl = _view
    try:
        central.validate_registry(errors)
    finally:
        central.load_jsonl = original
    rec = audits.get(S1_INTEGRATION_ID)
    if rec is None:
        fail(f"{S1_INTEGRATION_ID} registry record missing (registry must carry exactly one S1 integration evidence record)", errors)
        return
    for key, expected in S1_INTEGRATION_REGISTRY_REQUIRED.items():
        if rec.get(key) != expected:
            fail(f"{S1_INTEGRATION_ID} field {key}={rec.get(key)!r}, expected {expected!r}", errors)
    srcs = rec.get("preserved_sources") or {}
    if set(srcs) != set(S1_INTEGRATION_SOURCE_SHA256):
        fail(f"{S1_INTEGRATION_ID} preserved_sources keys {sorted(srcs)} != {sorted(S1_INTEGRATION_SOURCE_SHA256)}", errors)
    for skey, (path, expected_sha) in S1_INTEGRATION_SOURCE_SHA256.items():
        srec = srcs.get(skey) or {}
        if srec.get("path") != path or srec.get("sha256") != expected_sha:
            fail(f"{S1_INTEGRATION_ID} preserved_sources.{skey} path/sha256 mismatch", errors)
        sp = REPO_ROOT / path
        if not sp.exists():
            fail(f"{S1_INTEGRATION_ID} preserved source missing: {path}", errors)
        elif sha256_file(sp) != expected_sha:
            fail(f"{S1_INTEGRATION_ID} preserved source hash mismatch: {path}", errors)
    pp = REPO_ROOT / str(rec.get("report_path", ""))
    if not pp.exists():
        fail(f"{S1_INTEGRATION_ID} integration report missing: {rec.get('report_path')}", errors)
    elif sha256_file(pp) != rec.get("report_sha256"):
        fail(f"{S1_INTEGRATION_ID} integration report hash mismatch", errors)
    print("  OK   S0 registry protections executed verbatim on the 13-record view; SEC-AUDIT-REG-0014 pinned")


def validate_scope_s1(errors):
    print("\n[S1-INTEGRATION] Scope")
    if not has_git():
        print("  SKIP git scope (no .git — fixture mode)")
        return
    s1 = S1_INTEGRATION_EVENT
    changed = [p for p in _git(["diff", "--name-only", s1["start_head"]]).stdout.splitlines() if p]
    forbidden = sorted(p for p in changed if p.startswith(S1_FORBIDDEN_PREFIXES) or p.endswith(".sql"))
    if forbidden:
        fail(f"S1 integration changed forbidden paths (product/S2+/B004+/authority): {forbidden}", errors)
    meta = set()
    central_mod, _ = load_central()
    if central_mod is not None:
        meta = set(central_mod.METADATA_ALLOWLIST)
    outside = sorted(p for p in changed
                     if p not in S1_ALLOWED_EXACT and not p.startswith(S1_ALLOWED_PREFIXES) and p not in meta)
    if outside:
        fail(f"S1 integration changed paths outside the enumerated S1 surfaces: {outside}", errors)
    if CENTRAL in changed:
        fail(f"protected shared validator {CENTRAL} changed without Human ratification", errors)
    if _git(["ls-files", "--", "*.so"]).stdout.strip():
        fail("S1 integration leaves tracked native binaries", errors)
    rust = _git(["diff", "--name-only", s1["merged_base"], "--", "crypto/rust/src/"]).stdout.strip()
    if rust:
        fail(f"crypto/rust/src/** changed vs S1 original base (native behavior change forbidden): {rust.split()}", errors)
    ci = REPO_ROOT / ".github/workflows/ci.yml"
    text = ci.read_text(encoding="utf-8") if ci.exists() else ""
    if "tools platform-tools" in text or "packages: 'platform-tools'" not in text:
        fail("CI hotfix invariant violated: setup-android must use packages: 'platform-tools' (no 'tools platform-tools')", errors)
    print(f"  OK   {len(changed)} changed path(s) within enumerated S1 surfaces; shared validator untouched; "
          f"no tracked .so; crypto/rust/src unchanged; CI hotfix intact")


def validate_project_memory_s1(central, errors):
    print("\n[S1-INTEGRATION] Project memory chain (0052 → 0053 → 0054 → 0055)")
    state = json.loads((REPO_ROOT / "docs/continuity/CURRENT_STATE.json").read_text(encoding="utf-8"))
    ledger = load_jsonl(REPO_ROOT / "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl")
    if not ledger:
        fail("ledger empty", errors)
        return
    ids = [e.get("event_id") for e in ledger]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        fail(f"ledger contains duplicate event ids: {dupes}", errors)
    for e in ledger:
        if e.get("task") == S1_ORIGINAL_TASK:
            fail(f"ledger admits the isolated S1 provisional event {e.get('event_id')} as canonical "
                 f"(S1 is canonically recorded only by {S1_INTEGRATION_EVENT['event_id']})", errors)
        if e.get("task") == S1_INTEGRATION_EVENT["task"] and e.get("event_id") != S1_INTEGRATION_EVENT["event_id"]:
            fail(f"S1 integration recorded under wrong event id {e.get('event_id')}", errors)
    latest = ledger[-1]
    if state.get("latest_material_event_id") != latest.get("event_id"):
        fail("Project Memory stale: latest_material_event_id != last ledger event", errors)
        return
    if not _is_s1_integration_event(latest):
        fail(f"last ledger event must be the pinned S1 integration event {S1_INTEGRATION_EVENT['event_id']}, "
             f"got {latest.get('event_id')}", errors)
        return
    if not (len(ledger) >= 4 and central._is_s0_preservation_event(ledger[-2])
            and central._is_s0_successor_event(ledger[-3]) and ledger[-4].get("event_id") == central.LEDGER_EVENT):
        fail(f"{S1_INTEGRATION_EVENT['event_id']} must directly follow the pinned chain "
             f"{central.LEDGER_EVENT} → {central.S0_SUCCESSOR_EVENT['event_id']} → {central.S0_PRESERVATION_EVENT['event_id']}", errors)
    if not _s1_delivery_active(state):
        fail(f"{S1_INTEGRATION_EVENT['event_id']} recorded but CURRENT_STATE does not declare the S1 integration "
             f"delivery (task/branch) — S0 one-time exception is not reusable for S1", errors)
    raw = (REPO_ROOT / "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl").read_bytes().splitlines()
    overlong = [i + 1 for i, line in enumerate(raw) if len(line) > central.LEDGER_MAX_LINE_BYTES]
    if overlong:
        fail(f"ledger line-size violation (> {central.LEDGER_MAX_LINE_BYTES} bytes) at lines {overlong}", errors)
    if not errors:
        print(f"  OK   Project Memory synced to {latest.get('event_id')} (S1 canonical-integration successor of "
              f"{central.S0_PRESERVATION_EVENT['event_id']}; provisional isolated "
              f"{S1_INTEGRATION_EVENT['supersedes_provisional_event']} NONCANONICAL)")


def validate_ratification_proposal(errors):
    """The prepared S1-era extension is preserved tamper-evidently: applying the
    patch to the ratified content must yield exactly the proposed content hash
    for BOTH patched files (the protected validator and its paired adversarial
    test suite — the complete ratification package)."""
    print("\n[S1-INTEGRATION] Shared-validator ratification proposal integrity")
    patch = REPO_ROOT / PROPOSAL_PATCH
    record = REPO_ROOT / PROPOSAL_RECORD
    if not record.exists():
        fail(f"ratification proposal record missing: {PROPOSAL_RECORD}", errors)
    else:
        rec_text = record.read_text(encoding="utf-8")
        if CENTRAL_PROPOSED_SHA256 not in rec_text:
            fail("ratification proposal record does not carry the proposed post-change SHA-256", errors)
        if CENTRAL_TESTS_PROPOSED_SHA256 not in rec_text:
            fail("ratification proposal record does not carry the proposed paired-test-suite SHA-256", errors)
    if not patch.exists():
        fail(f"ratification proposal patch missing: {PROPOSAL_PATCH}", errors)
        return
    with tempfile.TemporaryDirectory(prefix="anox-s1-proposal-") as td:
        td = Path(td)
        subprocess.run(["git", "init", "-q"], cwd=td, check=True)
        dst = td / CENTRAL
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((REPO_ROOT / CENTRAL).read_bytes())
        tsrc = REPO_ROOT / CENTRAL_TESTS
        if not tsrc.exists():
            fail(f"paired central test suite missing: {CENTRAL_TESTS}", errors)
            return
        tdst = td / CENTRAL_TESTS
        tdst.write_bytes(tsrc.read_bytes())
        r = subprocess.run(["git", "apply", str(patch)], cwd=td, capture_output=True, text=True)
        if r.returncode != 0:
            fail(f"ratification proposal patch does not apply to the ratified content: {r.stderr.strip()[:200]}", errors)
            return
        got = sha256_file(dst)
        if got != CENTRAL_PROPOSED_SHA256:
            fail(f"ratification proposal yields {got[:16]}… != pinned proposed {CENTRAL_PROPOSED_SHA256[:16]}…", errors)
            return
        tgot = sha256_file(tdst)
        if tgot != CENTRAL_TESTS_PROPOSED_SHA256:
            fail(f"ratification proposal yields paired test suite {tgot[:16]}… != pinned proposed "
                 f"{CENTRAL_TESTS_PROPOSED_SHA256[:16]}…", errors)
            return
    print(f"  OK   proposal patch applies to ratified {CENTRAL_RATIFIED_SHA256[:12]}… and yields proposed "
          f"{CENTRAL_PROPOSED_SHA256[:12]}… + paired test suite {CENTRAL_TESTS_PROPOSED_SHA256[:12]}… "
          f"(awaiting Human ratification)")


def main():
    errors = []
    central, why = load_central()
    if central is None:
        print(f"  FAIL {why}")
        print("\nS1 INTEGRATION EVIDENCE: FAIL")
        return 1
    validate_base_s1(central, errors)
    # S0 protections — executed verbatim from the ratified module.
    print("\n[S1-INTEGRATION] Ratified S0 protections (verbatim)")
    for fn in (central.validate_reports, central.validate_traceability, central.validate_cryptojni,
               central.validate_authdpop, central.validate_androidstorage, central.validate_attackchain,
               central.validate_master_consolidation, central.validate_coverage_gate,
               central.validate_human_decision_layer, central.validate_findings, central.validate_lifecycle,
               central.validate_tasks):
        fn(errors)
    validate_registry_s1(central, errors)
    validate_scope_s1(errors)
    validate_project_memory_s1(central, errors)
    validate_ratification_proposal(errors)
    if errors:
        print("\nS1 INTEGRATION EVIDENCE: FAIL")
        for e in errors:
            print(f"  FAIL {e}")
        return 1
    print("\nS1 INTEGRATION EVIDENCE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
