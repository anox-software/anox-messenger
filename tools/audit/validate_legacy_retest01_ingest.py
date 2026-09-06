#!/usr/bin/env python3
"""LEGACY-RETEST-01-INGEST deterministic validator (23 checks).

Validates that the completed read-only LEGACY-RETEST-01 (PASS, 8/8) was
canonically ingested:

- the retest identity, base SHA and FIX-01 ancestry are recorded;
- exactly the eight verified findings are Closed with complete immutable
  closure evidence (FIX-01 -> RETEST-01 chain, pinned SHAs, closure_actor);
- no unrelated finding was closed or illegally transitioned;
- severities, titles and original evidence are preserved;
- product remains BLOCKED_PENDING_FINAL_AUDIT and B-004/B-005 NOT_STARTED;
- no product/CI/backend/SQL changes in the ingest delivery;
- historical validators were hardened to lifecycle-aware semantics and still
  pass for the correct reason;
- no Claude/external audit trigger was recorded;
- the next canonical gate resolves to AUDIT-WORKFORCE-ARCHITECTURE;
- Project Memory / continuity surfaces are synchronized;
- exactly the authorized two-commit delivery exists on the ingest branch.

Adversarial regression tests live in tools/audit/test_legacy_retest01_ingest.py.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lifecycle_legality as ll  # noqa: E402

RETEST_AUDIT_ID = "LEGACY-RETEST-01"
RETEST_BASE_SHA = "3adf56c17936fdf60c864e4a26f1863243478f44"
FIX01_SUBSTANTIVE_SHA = "342d55386f1bd7ea1531fc70e0e0f14fca0f279f"
FIX01_METADATA_SHA = "37dffdb8aa9fff3dae63766f0bb45adbf52c644f"
ORIGINAL_AUDIT_SHA = "0a4910eab1a92622383721100879cda46f924ca0"
INGEST_EVENT_ID = "ANOX-EVENT-0037"
INGEST_TASK_ID = "ANOX-TASK-LEGACYRET01INGEST"
RETEST_TASK_ID = "ANOX-TASK-LEGACYRETEST01"
RETEST_RUN_ID = "ANOX-RUN-LEGACYRETEST0001"
INGEST_RUN_ID = "ANOX-RUN-LEGACYRET01INGEST0001"
NEXT_GATE = "AUDIT-WORKFORCE-ARCHITECTURE"
NEXT_TASK_ID = "ANOX-TASK-WORKFORCEARCH001"

TARGETS = {
    "ANOX-MAINARCH-019",
    "ANOX-MAINARCH-023",
    "ANOX-MAINARCH-031",
    "ANOX-LEGACY-ANDROIDSEC-001",
    "ANOX-LEGACY-CRYPTO-005",
    "ANOX-LEGACY-INTEGRATION-001",
    "ANOX-LEGACY-INTEGRATION-002",
    "ANOX-LEGACY-INTEGRATION-003",
}

EXPECTED_SEVERITIES = {
    "ANOX-MAINARCH-019": "MEDIUM",
    "ANOX-MAINARCH-023": "MEDIUM",
    "ANOX-MAINARCH-031": "LOW",
    "ANOX-LEGACY-ANDROIDSEC-001": "HIGH",
    "ANOX-LEGACY-CRYPTO-005": "HIGH",
    "ANOX-LEGACY-INTEGRATION-001": "HIGH",
    "ANOX-LEGACY-INTEGRATION-002": "HIGH",
    "ANOX-LEGACY-INTEGRATION-003": "MEDIUM",
}

EXPECTED_REMAINING_OPEN = {
    "ANOX-MAINARCH-013",
    "ANOX-MAINARCH-018",
    "ANOX-MAINARCH-030",
    "ANOX-LEGACY-INTEGRATION-005",
    "ANOX-LEGACY-B003-001",
}

PRE_INGEST_CLOSED = {
    "ANOX-MAINARCH-001", "ANOX-MAINARCH-002", "ANOX-MAINARCH-003",
    "ANOX-MAINARCH-004", "ANOX-MAINARCH-005", "ANOX-MAINARCH-006",
    "ANOX-MAINARCH-007", "ANOX-MAINARCH-008", "ANOX-MAINARCH-009",
    "ANOX-MAINARCH-010", "ANOX-MAINARCH-011", "ANOX-MAINARCH-012",
    "ANOX-MAINARCH-014", "ANOX-MAINARCH-015", "ANOX-MAINARCH-016",
    "ANOX-MAINARCH-017", "ANOX-MAINARCH-020", "ANOX-MAINARCH-021",
    "ANOX-MAINARCH-022", "ANOX-MAINARCH-024", "ANOX-MAINARCH-025",
    "ANOX-MAINARCH-026", "ANOX-MAINARCH-027", "ANOX-MAINARCH-028",
    "ANOX-MAINARCH-029", "ANOX-MAINARCH-032", "ANOX-MAINARCH-033",
    "ANOX-MAINARCH-034", "ANOX-MAINARCH-035", "ANOX-MAINARCH-036",
}

MASTER = "docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md"
IR_REG = "docs/workforce/registries/implementation_readiness.json"
MAT_REG = "docs/workforce/registries/b021_verification_matrix.jsonl"
FIX01_SUBSTANTIVE_PREFIX = "tools/audit/"

# Metadata-only surfaces allowed in the second (metadata) commit — mirrors
# validate_continuity.METADATA_ONLY_ALLOWLIST.
METADATA_ONLY_ALLOWLIST = {
    "PROJECT_STATE.md",
    "FORTSCHRITT.md",
    "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
    "docs/continuity/CURRENT_STATE.json",
    "docs/continuity/CURRENT_GIT_STATE.md",
    "docs/continuity/CURRENT_HANDOFF.md",
    "docs/continuity/CURRENT_OPEN_WORK.md",
    "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
    "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md",
    "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md",
    "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
    "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md",
    "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
    "docs/workforce/registries/decisions.jsonl",
    "docs/workforce/registries/finding_evidence.jsonl",
    "docs/workforce/registries/findings.jsonl",
    "docs/workforce/registries/tasks.jsonl",
    "docs/workforce/registries/runs.jsonl",
    "docs/workforce/registries/audits.jsonl",
    "docs/workforce/registries/derived_work.jsonl",
    "docs/workforce/WORKFORCE_STATE.json",
    "docs/workforce/WORKFORCE_STATE_SNAPSHOT.json",
}

PRODUCT_SCOPE_PATTERNS = [
    r"^android/",
    r"^crypto/",
    r"^backend/",
    r"^supabase/",
    r"^\.github/",
    r"^migrations?/",
    r"\.kt$",
    r"\.kts$",
    r"\.rs$",
    r"\.sql$",
    r"\.gradle$",
    r"^Cargo\.toml$",
    r"^local\.properties$",
    r"\.jks$",
    r"\.keystore$",
    r"\.p12$",
    r"\.pem$",
    r"\.key$",
    r"\.env",
    r"\.aab$",
    r"\.apk$",
]


def fail(msg, errors):
    errors.append(msg)
    print(f"  FAIL {msg}")


def ok(msg):
    print(f"  OK   {msg}")


def read_text(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def read_jsonl(rel):
    path = REPO / rel
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def git(args):
    try:
        return subprocess.check_output(["git"] + args, cwd=REPO, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return None


def git_is_ancestor(ancestor, descendant):
    return subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, descendant],
                          cwd=REPO, capture_output=True).returncode == 0


def _retest_record(audits):
    return next((a for a in audits if a.get("audit_id") == RETEST_AUDIT_ID), None)


# --- 1-2. Retest identity / base / ancestry ---------------------------------


def check_retest_identity(errors, audits=None):
    """1-2. The LEGACY-RETEST-01 record exists, is PASS, records the canonical
    retest base SHA, and the FIX-01 delivery SHAs are ancestors of that base."""
    if audits is None:
        audits = read_jsonl("docs/workforce/registries/audits.jsonl")
    retest = _retest_record(audits)
    if retest is None:
        fail("LEGACY-RETEST-01 audit record missing", errors)
        return None
    ok("LEGACY-RETEST-01 audit record present")
    if retest.get("canonical_sha") == RETEST_BASE_SHA:
        ok("LEGACY-RETEST-01 canonical_sha is the recorded retest base")
    else:
        fail(f"LEGACY-RETEST-01 canonical_sha {retest.get('canonical_sha')} != {RETEST_BASE_SHA}", errors)
    if not git_is_ancestor(RETEST_BASE_SHA, "HEAD"):
        fail(f"Retest base {RETEST_BASE_SHA[:12]} is not an ancestor of HEAD", errors)
    else:
        ok("Retest base is an ancestor of HEAD")
    for label, sha in (("substantive", FIX01_SUBSTANTIVE_SHA), ("metadata", FIX01_METADATA_SHA)):
        if not git_is_ancestor(sha, RETEST_BASE_SHA):
            fail(f"FIX-01 {label} commit {sha[:12]} is not an ancestor of the retest base", errors)
        else:
            ok(f"FIX-01 {label} commit {sha[:12]} is an ancestor of the retest base")
    if retest.get("fix01_substantive_sha") == FIX01_SUBSTANTIVE_SHA and \
            retest.get("fix01_metadata_sha") == FIX01_METADATA_SHA:
        ok("FIX-01 substantive/metadata SHAs recorded on the retest record")
    else:
        fail("FIX-01 substantive/metadata SHAs missing on the retest record", errors)
    return retest


# --- 3-6. Retest result content ----------------------------------------------


def check_retest_result(errors, retest):
    """3-6. Exact 8 targets; 8/8 PASS; no FAIL/PARTIAL/REGRESSION/NOT-REVIEWABLE;
    canonical report section exists."""
    if retest is None:
        fail("Cannot evaluate retest result (record missing)", errors)
        return
    if set(retest.get("finding_ids", [])) == TARGETS:
        ok("LEGACY-RETEST-01 records exactly the 8 target finding IDs")
    else:
        fail("LEGACY-RETEST-01 finding_ids mismatch", errors)
    if retest.get("result") == "PASS" and \
            set(retest.get("closure_eligible_ids", [])) == TARGETS and \
            set(retest.get("closed_findings", [])) == TARGETS:
        ok("LEGACY-RETEST-01 result PASS with 8/8 closure-eligible")
    else:
        fail("LEGACY-RETEST-01 result/closure-eligible set invalid", errors)
    empty_lists = all(
        retest.get(k) == []
        for k in ("failed_ids", "partial_ids", "regression_ids", "not_reviewable_ids")
    )
    if empty_lists:
        ok("LEGACY-RETEST-01 records zero failures/partials/regressions/not-reviewable")
    else:
        fail("LEGACY-RETEST-01 records non-empty failure/partial/regression/not-reviewable lists", errors)
    master = read_text(MASTER)
    if "## LEGACY-RETEST-01" in master:
        ok("Master report contains the canonical LEGACY-RETEST-01 section")
    else:
        fail("Master report missing LEGACY-RETEST-01 section", errors)


# --- 7-10. Finding transitions ------------------------------------------------


def check_target_closures(errors, findings=None, audits=None):
    """7-10. All 8 targets Closed with preserved severity, immutable closure
    evidence (FIX-01 + RETEST-01 + pinned SHAs + report + validators), and a
    closure actor; pre-ingest RFR state evidenced by the recorded chain."""
    if findings is None:
        findings = read_jsonl("docs/workforce/registries/findings.jsonl")
    if audits is None:
        audits = read_jsonl("docs/workforce/registries/audits.jsonl")
    by_id = {f["finding_id"]: f for f in findings}
    closed_ok = 0
    for fid in sorted(TARGETS):
        f = by_id.get(fid)
        if f is None:
            fail(f"{fid} missing from findings registry", errors)
            continue
        if f.get("status") != "Closed":
            fail(f"{fid} is not Closed (status={f.get('status')})", errors)
            continue
        if f.get("severity") != EXPECTED_SEVERITIES[fid]:
            fail(f"{fid} severity changed to {f.get('severity')}", errors)
            continue
        ev = f.get("closure_evidence", [])
        ev_blob = " ".join(ev)
        chain_ok = (
            "LEGACY-FIX-01" in ev_blob
            and "LEGACY-RETEST-01" in ev_blob
            and f"git:{FIX01_SUBSTANTIVE_SHA}" in ev_blob
            and f"git:{FIX01_METADATA_SHA}" in ev_blob
            and f"git:{RETEST_BASE_SHA}" in ev_blob
            and "validate_legacy_fix01.py" in ev_blob
            and "validate_legacy_retest01_ingest.py" in ev_blob
            and "LEGACY-RETEST-01" in ev_blob
        )
        if not chain_ok:
            fail(f"{fid} closure evidence missing FIX-01/RETEST-01/SHA/validator references", errors)
            continue
        if not f.get("closure_actor"):
            fail(f"{fid} missing closure_actor", errors)
            continue
        if "LEGACY-RETEST-01" not in f.get("remediation_refs", []):
            fail(f"{fid} remediation_refs missing LEGACY-RETEST-01 reference", errors)
            continue
        legal, reasons = ll.has_legal_closure(f, audits)
        if not legal:
            fail(f"{fid} closure chain illegal: {reasons}", errors)
            continue
        closed_ok += 1
        ok(f"{fid} Closed with preserved severity and complete immutable closure chain")
    if closed_ok == len(TARGETS):
        ok("All 8 targets Closed with complete legal closure evidence")


# --- 11-16. Non-target findings untouched -------------------------------------


def check_non_target_findings(errors, findings=None, audits=None):
    """11-16. Exactly the 5 canonical non-target findings remain Open; no
    unrelated closure; all registry findings in legal lifecycle states."""
    if findings is None:
        findings = read_jsonl("docs/workforce/registries/findings.jsonl")
    if audits is None:
        audits = read_jsonl("docs/workforce/registries/audits.jsonl")
    by_id = {f["finding_id"]: f for f in findings}
    open_ids = {f["finding_id"] for f in findings if f.get("status") == "Open"}
    if open_ids == EXPECTED_REMAINING_OPEN:
        ok(f"Exactly the 5 canonical non-target findings remain Open: {sorted(open_ids)}")
    else:
        fail(f"Open set mismatch: expected {sorted(EXPECTED_REMAINING_OPEN)}, got {sorted(open_ids)}", errors)
    closed = {f["finding_id"] for f in findings if f.get("status") == "Closed"}
    if closed == PRE_INGEST_CLOSED | TARGETS:
        ok("Closed set = 30 pre-ingest verified + 8 LEGACY-RETEST-01 verified = 38")
    else:
        fail(f"Closed set mismatch: {sorted(closed)}", errors)
    illegal = [fid for fid, f in by_id.items() if not ll.finding_status_legal(f, audits)[0]]
    if illegal:
        fail(f"Findings in illegal lifecycle states: {sorted(illegal)}", errors)
    else:
        ok("All registry findings in legal lifecycle states")
    for fid in sorted(EXPECTED_REMAINING_OPEN):
        f = by_id.get(fid)
        if f is None or f.get("status") != "Open":
            fail(f"Non-target finding {fid} changed/missing", errors)
        else:
            ok(f"Non-target {fid} remains Open")


# --- 17-19. Product / scope guards --------------------------------------------


def check_product_blocked(errors, ws=None, ir=None):
    """17-19. Product remains BLOCKED; B-004/B-005 NOT_STARTED; no product-code
    changes in the ingest delivery diff (retest base..HEAD)."""
    if ws is None:
        ws = json.loads(read_text("docs/workforce/WORKFORCE_STATE.json"))
    fpa = ws.get("final_pre_product_audit", {})
    if fpa.get("product_development_state") == "BLOCKED_PENDING_FINAL_AUDIT":
        ok("Product development remains BLOCKED_PENDING_FINAL_AUDIT")
    else:
        fail("Product development not blocked", errors)
    if fpa.get("status") == "IN_PROGRESS" and fpa.get("product_development_unblocked") is not True:
        ok("Final Pre-Product Audit remains IN PROGRESS")
    else:
        fail("Final Pre-Product Audit wrongly marked complete", errors)
    if ir is None:
        ir = json.loads(read_text(IR_REG))
    bad = []
    for d in ("B-004", "B-005"):
        dom = ir.get("domains", {}).get(d, {})
        if dom.get("architecture_state") != "FROZEN" or dom.get("implementation_state") != "NOT_STARTED":
            bad.append(d)
    if bad:
        fail(f"implementation_readiness drifted for: {bad}", errors)
    else:
        ok("B-004/B-005 remain FROZEN + NOT_STARTED")
    changed = git(["diff", "--name-only", RETEST_BASE_SHA, "HEAD"])
    if changed is None:
        fail("Could not resolve ingest delivery diff", errors)
    else:
        bad_files = [p for p in changed.splitlines()
                     if any(re.search(pat, p) for pat in PRODUCT_SCOPE_PATTERNS)]
        if bad_files:
            fail(f"Ingest delivery contains product/CI/secret-scope changes: {bad_files}", errors)
        else:
            ok("Ingest delivery contains no product/CI/backend/SQL/secret changes")


# --- 20. Historical validators still pass -------------------------------------


def check_historical_validators(errors):
    """20. The hardened historical validators pass for the correct
    lifecycle-aware reason."""
    validators = [
        "validate_legacy_audit_consolidation.py",
        "validate_legacy_fix01.py",
        "validate_mainarch_fix01.py",
        "validate_mainarch_fix02.py",
        "validate_mainarch_fix03.py",
        "validate_mainarch_retest01_ingest.py",
        "validate_mainarch_retest02_ingest.py",
    ]
    for v in validators:
        r = subprocess.run([sys.executable, str(REPO / "tools" / "audit" / v)],
                           cwd=REPO, capture_output=True, text=True)
        if r.returncode == 0:
            ok(f"Hardened {v} PASS")
        else:
            tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
            fail(f"{v} FAIL ({'; '.join(tail)})", errors)


# --- 21. No Claude/external audit triggered ------------------------------------


def check_no_claude(errors, tasks=None, audits=None, ws=None, retest=None):
    """21. No Claude/external audit trigger in structured fields; the retest
    records the required security reassessment."""
    if tasks is None:
        tasks = read_jsonl("docs/workforce/registries/tasks.jsonl")
    if audits is None:
        audits = read_jsonl("docs/workforce/registries/audits.jsonl")
    if ws is None:
        ws = json.loads(read_text("docs/workforce/WORKFORCE_STATE.json"))
    evidence = ll.detect_claude_trigger(tasks=tasks, audits=audits, workforce_state=ws)
    if evidence:
        fail(f"Claude/external audit trigger detected in structured fields: {evidence}", errors)
    else:
        ok("No Claude/external audit trigger in structured fields")
    if retest is None:
        retest = _retest_record(audits) or {}
    if "NO IMMEDIATE SECURITY AUDIT REQUIRED" in retest.get("security_reassessment", ""):
        ok("LEGACY-RETEST-01 records NO IMMEDIATE SECURITY AUDIT REQUIRED")
    else:
        fail("LEGACY-RETEST-01 missing security_reassessment", errors)


# --- 22. Next canonical gate ---------------------------------------------------


def check_next_gate(errors, ws=None, tasks=None):
    """22. The next canonical gate resolves to the first uncompleted required
    Final Pre-Product audit (AUDIT-WORKFORCE-ARCHITECTURE) and a Candidate
    task records it."""
    if ws is None:
        ws = json.loads(read_text("docs/workforce/WORKFORCE_STATE.json"))
    if tasks is None:
        tasks = read_jsonl("docs/workforce/registries/tasks.jsonl")
    nxt = ll.next_canonical_gate(ws)
    if nxt == NEXT_GATE:
        ok(f"Next canonical required audit resolves to {NEXT_GATE}")
    else:
        fail(f"Next canonical required audit is {nxt}, expected {NEXT_GATE}", errors)
    fpa = ws.get("final_pre_product_audit", {})
    if fpa.get("next_phase") == NEXT_GATE and ws.get("next_phase") == NEXT_GATE:
        ok("WORKFORCE_STATE next_phase resolves to the canonical next audit")
    else:
        fail("WORKFORCE_STATE next_phase does not resolve to AUDIT-WORKFORCE-ARCHITECTURE", errors)
    task = next((t for t in tasks if t.get("task_id") == NEXT_TASK_ID), None)
    if task is None:
        fail(f"Candidate task {NEXT_TASK_ID} missing", errors)
    elif task.get("status") != "Candidate":
        fail(f"{NEXT_TASK_ID} status is {task.get('status')}, expected Candidate (not started)", errors)
    elif "AUDIT-WORKFORCE-ARCHITECTURE" not in (task.get("title", "") + task.get("scope", "")):
        fail(f"{NEXT_TASK_ID} does not cover AUDIT-WORKFORCE-ARCHITECTURE", errors)
    else:
        ok(f"Next gate recorded as Candidate task {NEXT_TASK_ID} (not authorized)")


# --- 23. Project Memory / continuity synchronization ---------------------------


def check_memory_sync(errors):
    """23. Ledger contains the ingest event, CURRENT_STATE tracks the last
    sealed event, and described_head is recorded."""
    ledger = read_jsonl("docs/continuity/PROJECT_HISTORY_LEDGER.jsonl")
    cur = json.loads(read_text("docs/continuity/CURRENT_STATE.json"))
    has_event = any(
        e.get("event_id") == INGEST_EVENT_ID and "LEGACY-RETEST-01" in e.get("summary", "")
        for e in ledger
    )
    if has_event:
        ok(f"Project History Ledger contains {INGEST_EVENT_ID}")
    else:
        fail(f"Project History Ledger missing {INGEST_EVENT_ID}", errors)
    last_event = ledger[-1] if ledger else {}
    if cur.get("latest_material_event_id") == last_event.get("event_id") and last_event.get("event_id"):
        ok(f"CURRENT_STATE latest_material_event_id matches last sealed event {last_event.get('event_id')}")
    else:
        fail(f"latest_material_event_id={cur.get('latest_material_event_id')} vs last ledger {last_event.get('event_id')}", errors)
    dh = cur.get("described_head", "")
    if len(dh) == 40 and git_is_ancestor(dh, "HEAD"):
        ok(f"CURRENT_STATE described_head {dh[:12]} recorded and ancestor of HEAD")
    else:
        fail("CURRENT_STATE described_head missing/invalid/not ancestor of HEAD", errors)


# --- Task/run linkage (folded into checks 1-23 numbering) ----------------------


def check_task_run_linkage(errors, tasks=None, runs=None):
    """Retest task Closed, ingest task Closed, retest run PASS, ingest run
    IN_PROGRESS, all with recorded linkage."""
    if tasks is None:
        tasks = read_jsonl("docs/workforce/registries/tasks.jsonl")
    if runs is None:
        runs = read_jsonl("docs/workforce/registries/runs.jsonl")
    retest_task = next((t for t in tasks if t.get("task_id") == RETEST_TASK_ID), None)
    if retest_task and retest_task.get("status") == "Closed":
        ok("LEGACY-RETEST-01 task recorded Closed")
    else:
        fail("LEGACY-RETEST-01 task not Closed", errors)
    ingest_task = next((t for t in tasks if t.get("task_id") == INGEST_TASK_ID), None)
    if ingest_task and ingest_task.get("status") == "Closed":
        ok("LEGACY-RETEST-01-INGEST task recorded")
    else:
        fail("LEGACY-RETEST-01-INGEST task record missing/not Closed", errors)
    retest_run = next((r for r in runs if r.get("run_id") == RETEST_RUN_ID), None)
    if retest_run and retest_run.get("result") == "PASS" and retest_run.get("start_sha") == RETEST_BASE_SHA:
        ok("Retest run ANOX-RUN-LEGACYRETEST0001 recorded PASS at retest base")
    else:
        fail("Retest run record missing/invalid", errors)
    ingest_run = next((r for r in runs if r.get("run_id") == INGEST_RUN_ID), None)
    if ingest_run and ingest_run.get("remote_mutation") == "NONE":
        ok("Ingest run recorded with remote_mutation NONE")
    else:
        fail("Ingest run record missing/remote_mutation wrong", errors)


def check_two_commit_delivery(errors):
    """The ingest branch contains exactly two commits ahead of the retest base:
    a substantive commit and a metadata-only commit."""
    out = git(["rev-list", "--count", f"{RETEST_BASE_SHA}..HEAD"])
    if out != "2":
        fail(f"Expected exactly 2 commits on ingest branch, found {out}", errors)
        return
    ok("Ingest branch contains exactly 2 commits ahead of the retest base")
    # The second commit (metadata) may only touch allowlisted metadata surfaces.
    head = git(["rev-parse", "HEAD"])
    meta_files = git(["diff", "--name-only", f"{head}~1", head]) or ""
    bad = [p for p in meta_files.splitlines() if p not in METADATA_ONLY_ALLOWLIST]
    if bad:
        fail(f"Metadata commit touches non-metadata files: {bad}", errors)
    else:
        ok("Metadata commit touches only allowlisted metadata surfaces")


def main():
    print("LEGACY-RETEST-01-INGEST validator (23 checks)")
    errors = []

    audits = read_jsonl("docs/workforce/registries/audits.jsonl")
    findings = read_jsonl("docs/workforce/registries/findings.jsonl")
    tasks = read_jsonl("docs/workforce/registries/tasks.jsonl")
    runs = read_jsonl("docs/workforce/registries/runs.jsonl")
    ws = json.loads(read_text("docs/workforce/WORKFORCE_STATE.json"))
    ir = json.loads(read_text(IR_REG))

    retest = check_retest_identity(errors, audits=audits)            # checks 1-2
    check_retest_result(errors, retest)                            # checks 3-6
    check_target_closures(errors, findings=findings, audits=audits)  # checks 7-10
    check_non_target_findings(errors, findings=findings, audits=audits)  # checks 11-16
    check_product_blocked(errors, ws=ws, ir=ir)                    # checks 17-19
    check_historical_validators(errors)                            # check 20
    check_no_claude(errors, tasks=tasks, audits=audits, ws=ws, retest=retest)  # check 21
    check_next_gate(errors, ws=ws, tasks=tasks)                    # check 22
    check_task_run_linkage(errors, tasks=tasks, runs=runs)         # linkage
    check_two_commit_delivery(errors)                              # two-commit
    check_memory_sync(errors)                                      # check 23

    if errors:
        print("\nLEGACY-RETEST-01-INGEST: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nLEGACY-RETEST-01-INGEST: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
