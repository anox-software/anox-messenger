#!/usr/bin/env python3
"""Consolidate the six-session legacy audit set into canonical findings, audit records, and workforce state.

This is a one-time ingest script for LEGACY-AUDIT-SET-FREEZE. It reads the canonical
consolidation data from tools/audit/legacy_audit_set_freeze_data.json and applies the
changes to the tracked registries and reports. It does not perform validation; that is
done by tools/audit/validate_legacy_audit_consolidation.py.

Usage:
    python3 tools/audit/consolidate_legacy_audit_set.py
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = REPO_ROOT / "tools" / "audit" / "legacy_audit_set_freeze_data.json"


def load_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def save_jsonl(path, items):
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    base_sha = data["base_sha"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ------------------------------------------------------------------
    # 1. Update findings.jsonl
    # ------------------------------------------------------------------
    findings_path = REPO_ROOT / "docs" / "workforce" / "registries" / "findings.jsonl"
    findings = load_jsonl(findings_path)

    updated = {f["finding_id"]: f for f in findings}

    for fid, patch in data["updated_findings"].items():
        if fid not in updated:
            raise RuntimeError(f"Cannot update missing finding {fid}")
        item = updated[fid]
        if "evidence_refs_to_add" in patch:
            item.setdefault("evidence_refs", []).extend(patch["evidence_refs_to_add"])
        if "note_append" in patch:
            notes = item.get("notes", "")
            sep = "\n" if notes else ""
            item["notes"] = notes + sep + patch["note_append"]

    # Add new legacy findings
    for new in data["new_findings"]:
        updated[new["finding_id"]] = new

    # Preserve order: existing first, then new legacy appended
    new_findings = data["new_findings"]
    final_findings = findings + new_findings
    save_jsonl(findings_path, final_findings)

    # ------------------------------------------------------------------
    # 2. Append legacy audit records to audits.jsonl
    # ------------------------------------------------------------------
    audits_path = REPO_ROOT / "docs" / "workforce" / "registries" / "audits.jsonl"
    audits = load_jsonl(audits_path)
    audits.extend(data["audit_records"])
    save_jsonl(audits_path, audits)

    # ------------------------------------------------------------------
    # 3. Update audit-result schema to allow PASS_WITH_FINDINGS
    # ------------------------------------------------------------------
    schema_path = REPO_ROOT / "docs" / "workforce" / "schemas" / "audit-result.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    result_enum = schema["properties"]["result"]["enum"]
    if "PASS_WITH_FINDINGS" not in result_enum:
        result_enum.append("PASS_WITH_FINDINGS")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # ------------------------------------------------------------------
    # 4. Update WORKFORCE_STATE.json
    # ------------------------------------------------------------------
    workforce_path = REPO_ROOT / "docs" / "workforce" / "WORKFORCE_STATE.json"
    with open(workforce_path, "r", encoding="utf-8") as f:
        workforce = json.load(f)

    wu = data["workforce_state_updates"]
    workforce["current_gate"] = wu["current_gate"]
    workforce["product_development_state"] = wu["product_development_state"]
    workforce["next_phase"] = wu["next_phase"]
    workforce["main_architecture_audit"] = wu["main_architecture_audit"]
    workforce["main_architecture_remediation_phase"] = wu["main_architecture_remediation_phase"]
    workforce["legacy_audit_set_status"] = wu["legacy_audit_set_status"]
    workforce["latest_finding_id"] = "ANOX-LEGACY-B003-001"
    workforce["latest_run_id"] = data["run_id"]
    workforce["current_writer"] = {
        "task_id": data["next_task"]["task_id"],
        "role_id": "ROLE-009",
        "branch": "audit/legacy-audit-set-freeze-consolidation"
    }
    workforce.setdefault("final_pre_product_audit", {})["legacy_audit_set_status"] = "6/6 COMPLETE"

    note = (
        f"LEGACY-AUDIT-SET-FREEZE ({data['run_id']}) on {base_sha}: six legacy audits 6/6 COMPLETE; "
        f"{data['promoted_count']} audit-local candidates promoted to canonical Legacy findings; "
        f"Product remains BLOCKED_PENDING_FINAL_AUDIT; next task {data['next_task']['task_id']}."
    )
    workforce.setdefault("notes", []).append(note)

    with open(workforce_path, "w", encoding="utf-8") as f:
        json.dump(workforce, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # ------------------------------------------------------------------
    # 5. Update FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md
    # ------------------------------------------------------------------
    master_path = REPO_ROOT / "docs" / "reports" / "FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md"
    with open(master_path, "r", encoding="utf-8") as f:
        master_text = f.read()

    legacy_section = f"""\n## LEGACY-AUDIT-SET-FREEZE — Six-Session Legacy Audit Consolidation\n\n**Status:** COMPLETE\n**Mode:** READ-ONLY LEGACY FINDINGS FREEZE\n**Canonical base SHA:** `{base_sha}`\n**Ending SHA (all six audits):** `{data['ending_sha_per_audit']}`\n**Model:** `{data['model']}`\n**Run:** `{data['run_id']}`\n**Result:** PASS WITH FINDINGS\n**Repository modified:** NO\n**Remote mutation:** NONE\n**Claude audit triggered:** NO\n\n### Legacy audit set completion\n\nAll six canonical legacy audits were executed on the frozen base SHA:\n\n1. `LEGACY-AUDIT-B002` — Device Authentication\n2. `LEGACY-AUDIT-B003` — Account / License / Registration\n3. `LEGACY-AUDIT-CRYPTO` — Cryptography / vodozemac / JNI\n4. `LEGACY-AUDIT-ANDROID-SEC` — Android local security\n5. `LEGACY-AUDIT-BUILD` — Build / supply chain / native artifacts\n6. `LEGACY-AUDIT-INTEGRATION` — Cross-domain integration\n\n**Set state:** 6 / 6 COMPLETE\n\n### Existing MAIN findings revalidated\n\nThe six remaining Open MAIN findings were revalidated and remain Open:\n\n- `ANOX-MAINARCH-013` — build/provenance (Class D)\n- `ANOX-MAINARCH-018` — physical GrapheneOS/StrongBox verification (Class E, `PHYSICAL_VERIFICATION_REQUIRED`)\n- `ANOX-MAINARCH-019` — Device Auth production eligibility not enforced (Class A)\n- `ANOX-MAINARCH-023` — K_STATE read-path silent recreation (Class A)\n- `ANOX-MAINARCH-030` — B-009/B-013 wipe/session persistence (Class C)\n- `ANOX-MAINARCH-031` — JNI output-buffer error mapping (Class A)\n\n### Promoted canonical Legacy findings\n\n{data['promoted_count']} audit-local candidates were promoted to canonical Open findings:\n\n- `ANOX-LEGACY-ANDROIDSEC-001` — API 26–32 KeyStoreException crash (HIGH, Class A)\n- `ANOX-LEGACY-CRYPTO-005` — unsafe concurrent `&mut` native Identity/Session access (HIGH, Class A)\n- `ANOX-LEGACY-INTEGRATION-001` — Device Auth key not re-verified before commit (HIGH, Class A)\n- `ANOX-LEGACY-INTEGRATION-002` — OTK private state not persisted after generation (HIGH, Class A)\n- `ANOX-LEGACY-INTEGRATION-003` — `CommitArmed` / binding-store divergence (MEDIUM, Class A)\n- `ANOX-LEGACY-INTEGRATION-005` — native Identity handle leak (MEDIUM, Class F)\n- `ANOX-LEGACY-B003-001` — UUIDv4 variant not verified (LOW, Class F)\n\n### Candidate disposition summary\n\n| Disposition | Count | Items |\n|---|---|---|\n| `PROMOTE_CANONICAL` | {data['promoted_count']} | {', '.join([c['candidate_id'] for c in data['candidate_dispositions'] if c['disposition'] == 'PROMOTE_CANONICAL'])} |\n| `MERGE_INTO_EXISTING` | {data['merged_count']} | {', '.join([c['candidate_id'] for c in data['candidate_dispositions'] if c['disposition'] == 'MERGE_INTO_EXISTING'])} |\n| `DEFER_AS_FUTURE_WORK` | {data['deferred_future_count']} | {', '.join([c['candidate_id'] for c in data['candidate_dispositions'] if c['disposition'] == 'DEFER_AS_FUTURE_WORK'])} |\n| `VERIFICATION_GAP_ONLY` | {data['verification_gap_count']} | {', '.join([c['candidate_id'] for c in data['candidate_dispositions'] if c['disposition'] == 'VERIFICATION_GAP_ONLY'])} |\n| `DOCUMENTATION_CLEANUP` | {data['documentation_cleanup_count']} | {', '.join([c['candidate_id'] for c in data['candidate_dispositions'] if c['disposition'] == 'DOCUMENTATION_CLEANUP'])} |\n| `NOT_A_FINDING` | {data['not_a_finding_count']} | {', '.join([c['candidate_id'] for c in data['candidate_dispositions'] if c['disposition'] == 'NOT_A_FINDING'])} |\n| `REQUIRES_SCOPE_DECISION` | {data['requires_scope_decision_count']} | {', '.join([c['candidate_id'] for c in data['candidate_dispositions'] if c['disposition'] == 'REQUIRES_SCOPE_DECISION'])} |\n\n### MAINARCH-030 current-vs-future decomposition\n\n`ANOX-MAINARCH-030` is resolved as **Class C** (implement with B-008/B-009/B-013). The current `wipeLocalCrypto()` correctly removes the currently existing file-based crypto state. DB/WAL/SHM/attachments/temp, `preferred_session_id`, and per-peer session persistence are future Product implementation items, not current foundation defects.\n\n### INTEGRATION-004 32-bit ABI scope decision\n\n`ANOX-LEGACY-INTEGRATION-004` (missing 32-bit ABI `.so` artifacts) is **not auto-promoted**. `minSdk=26` is an API-level declaration, not a supported-CPU promise. The frozen product boundary names GrapheneOS (64-bit Pixel) as the primary V1 target. A human/scope decision is required before this becomes a release or build finding.\n\n### Pre-B004 foundation blockers (Class A)\n\n{', '.join(data['pre_b004_blockers'])}\n\n### Release blockers\n\n{', '.join(data['release_blockers'])}\n\n### Physical verification blockers\n\n{', '.join(data['physical_verification_blockers'])}\n\n### Milestone security-review flags (preserved)\n\n{', '.join(data['milestone_flags'])}\n\n### Product development state\n\n`BLOCKED_PENDING_FINAL_AUDIT` (unchanged). The next authorized task is `{data['next_task']['task_id']}` — dependency-sorted remediation of the Class-A legacy blockers.\n\n### Constraints observed\n\nNo product code, Rust, Android, backend, SQL, Supabase, messaging, Device Auth, crypto, or `.so` changes. No CI workflow changes. No signing keys created or imported. No secrets touched. No GitHub repository/configuration changes. No remote mutation. **CLAUDE AUDIT TRIGGERED: NO.**\n\n### Consolidation artifacts\n\n- `docs/workforce/registries/findings.jsonl` — existing Open MAIN findings updated; 7 canonical Legacy findings appended.\n- `docs/workforce/registries/audits.jsonl` — 6 legacy audit records appended.\n- `docs/workforce/schemas/audit-result.schema.json` — `PASS_WITH_FINDINGS` added to result enum.\n- `docs/workforce/WORKFORCE_STATE.json` — legacy audit set 6/6 complete; next task recorded.\n- `docs/reports/FINAL_PRE_PRODUCT_LEGACY_AUDIT_CONSOLIDATION.md` — full consolidation report.\n- `tools/audit/consolidate_legacy_audit_set.py` — this one-time ingest script.\n- `tools/audit/validate_legacy_audit_consolidation.py` — consolidation validator plus adversarial tests.\n"""

    marker = "**Next task:** first required specialized session per canonical `docs/workforce/audits/legacy-audit-plan.json` — `LEGACY-AUDIT-B002` (Legacy / Build / Hardware verification phase), pending human authorization."
    if marker not in master_text:
        raise RuntimeError("Could not locate insertion marker in master audit report")
    master_text = master_text.replace(marker, marker + legacy_section)

    with open(master_path, "w", encoding="utf-8") as f:
        f.write(master_text)

    # ------------------------------------------------------------------
    # 6. Write consolidated legacy audit report
    # ------------------------------------------------------------------
    report_path = REPO_ROOT / "docs" / "reports" / "FINAL_PRE_PRODUCT_LEGACY_AUDIT_CONSOLIDATION.md"

    promoted = [
        f"| `{f['finding_id']}` | {f['severity']} | {f['affected_scope']} | {f.get('notes','').split(';')[0].replace('class=','')} |"
        for f in data["new_findings"]
    ]

    disposition_rows = [
        f"| `{c['candidate_id']}` | {c['source_audit']} | {c['severity_source']} | `{c['disposition']}` | `{c.get('canonical_id') or ''}` | {c['notes']} |"
        for c in data["candidate_dispositions"]
    ]

    root_cause_rows = [
        f"| `{f['finding_id']}` | `{f['severity']}` | {f['affected_scope']} | Class A" if f['finding_id'] in data['pre_b004_blockers'] else f"| `{f['finding_id']}` | `{f['severity']}` | {f['affected_scope']} | — |"
        for f in data['new_findings']
    ]

    report = f"""# FINAL PRE-PRODUCT LEGACY AUDIT CONSOLIDATION\n\n**Status:** COMPLETE\n**Audit set:** LEGACY-AUDIT-SET-FREEZE\n**Mode:** READ-ONLY\n**Model:** `{data['model']}`\n**Canonical base SHA (all six audits):** `{base_sha}`\n**Ending SHA:** `{data['ending_sha_per_audit']}`\n**Repository modified:** NO (ingest is part of committed consolidation)\n**Remote mutation:** NONE\n**Claude audit triggered:** NO\n\n## 1. Frozen baseline\n\nAll six legacy audits used exactly:\n\n```\nf245dc429a9e4bd10f51692eb452d03ccb9a6749\n```\n\n`git status --short` was clean at start and end of every session.\n\n## 2. Canonical preconditions\n\n- `validate_mainarch_retest03_ingest.py`: PASS\n- `validate_b027_integrity.py`: PASS\n- `b017_lite_policy_validator.py`: PASS\n- `validate_continuity.py --mode live`: PASS\n- MAIN architecture audit: COMPLETE\n- MAIN architecture remediation: COMPLETE\n- MAIN findings: 30 Closed, 6 Open\n- Product: `BLOCKED_PENDING_FINAL_AUDIT`\n- B-004/B-005: `NOT_STARTED`\n\n## 3. Six-audit set completion\n\n| # | Audit ID | Result | Model | Base SHA | Ending SHA |\n|---|---|---|---|---|---|\n| 1 | `LEGACY-AUDIT-B002` | `PASS WITH FINDINGS` | `{data['model']}` | `{base_sha}` | `{data['ending_sha_per_audit']}` |\n| 2 | `LEGACY-AUDIT-B003` | `PASS WITH FINDINGS` | `{data['model']}` | `{base_sha}` | `{data['ending_sha_per_audit']}` |\n| 3 | `LEGACY-AUDIT-CRYPTO` | `PASS WITH FINDINGS` | `{data['model']}` | `{base_sha}` | `{data['ending_sha_per_audit']}` |\n| 4 | `LEGACY-AUDIT-ANDROID-SEC` | `PASS WITH FINDINGS` | `{data['model']}` | `{base_sha}` | `{data['ending_sha_per_audit']}` |\n| 5 | `LEGACY-AUDIT-BUILD` | `PASS WITH FINDINGS` | `{data['model']}` | `{base_sha}` | `{data['ending_sha_per_audit']}` |\n| 6 | `LEGACY-AUDIT-INTEGRATION` | `PASS WITH FINDINGS` | `{data['model']}` | `{base_sha}` | `{data['ending_sha_per_audit']}` |\n\n**Set state:** 6 / 6 COMPLETE\n\n## 4. Existing MAIN findings revalidated\n\n| ID | Title | Disposition | Class |\n|---|---|---|---|\n| `ANOX-MAINARCH-013` | Build / supply-chain / native artifact provenance | Revalidated; new byte-reproducibility evidence appended; remains Open | D |\n| `ANOX-MAINARCH-018` | Physical GrapheneOS / StrongBox verification | Revalidated; `PHYSICAL_VERIFICATION_REQUIRED` preserved | E |\n| `ANOX-MAINARCH-019` | Device Auth production eligibility not enforced by RegistrationOrchestrator | Revalidated; Class A blocker | A |\n| `ANOX-MAINARCH-023` | K_STATE read-path silent recreation | Revalidated; narrow hypothesis confirmed; Class A blocker | A |\n| `ANOX-MAINARCH-030` | Local wipe / session-persistence forward-model gap | Revalidated; decomposed into current (none) and future B-009/B-013 | C |\n| `ANOX-MAINARCH-031` | Rust/JNI output-buffer error mapping | Revalidated; Class A blocker | A |\n\n## 5. Candidate dispositions\n\n| Candidate ID | Source | Severity | Disposition | Canonical ID / Merged into | Rationale |\n|---|---|---|---|---|---|\n{chr(10).join(disposition_rows)}\n\n## 6. Promoted canonical Legacy findings\n\n| ID | Severity | Affected scope | Root-cause class |\n|---|---|---|---|\n{chr(10).join(promoted)}\n\n## 7. Root-cause consolidation\n\n### Canonical Open findings after freeze\n\n**Six existing MAIN findings** (preserved Open):\n\n- `ANOX-MAINARCH-013`\n- `ANOX-MAINARCH-018`\n- `ANOX-MAINARCH-019`\n- `ANOX-MAINARCH-023`\n- `ANOX-MAINARCH-030`\n- `ANOX-MAINARCH-031`\n\n**Seven new Legacy findings** (promoted Open):\n\n- `ANOX-LEGACY-ANDROIDSEC-001`\n- `ANOX-LEGACY-CRYPTO-005`\n- `ANOX-LEGACY-INTEGRATION-001`\n- `ANOX-LEGACY-INTEGRATION-002`\n- `ANOX-LEGACY-INTEGRATION-003`\n- `ANOX-LEGACY-INTEGRATION-005`\n- `ANOX-LEGACY-B003-001`\n\n**No duplicate root causes.** `CRYPTO-001/002/003/004` and `BUILD-001` were merged into existing MAIN findings rather than promoted.\n\n## 8. Remediation classification\n\n### Class A — foundation fix before B-004/B-005 implementation\n\n{', '.join(data['class_a'])}\n\n### Class B — implement with B-004/B-005/B-006\n\n{chr(10).join('- ' + x for x in data['class_b'])}\n\n### Class C — implement with B-008/B-009/B-013\n\n{chr(10).join('- ' + x for x in data['class_c'])}\n\n### Class D — release / build gate\n\n{chr(10).join('- ' + x for x in data['class_d'])}\n\n### Class E — physical verification\n\n{chr(10).join('- ' + x for x in data['class_e'])}\n\n### Class F — non-blocking cleanup / verification debt\n\n{chr(10).join('- ' + x for x in data['class_f'])}\n\n## 9. Pre-B004 foundation blockers\n\n{chr(10).join('- ' + x for x in data['pre_b004_blockers'])}\n\n## 10. Release blockers\n\n{chr(10).join('- ' + x for x in data['release_blockers'])}\n\n## 11. Physical verification blockers\n\n{chr(10).join('- ' + x for x in data['physical_verification_blockers'])}\n\n## 12. MAINARCH-030 current-vs-future decomposition\n\n- **Current foundation:** `wipeLocalCrypto()` correctly removes existing local crypto files.\n- **Future B-009/B-013:** DB/WAL/SHM/attachments/temp cleanup, `preferred_session_id`, per-peer session persistence.\n\nNo current product path invokes a false complete-wipe.\n\n## 13. INTEGRATION-004 32-bit ABI scope decision\n\n`ANOX-LEGACY-INTEGRATION-004` is **not promoted** without a product-device-scope decision. `minSdk=26` is an API-level floor, not a CPU-ABI guarantee. The frozen product boundary names GrapheneOS (64-bit Pixel) as the primary target. If a future authority explicitly promises 32-bit production support, this can be re-evaluated.\n\n## 14. Milestone security-review flags\n\nPreserved Open:\n\n- `ANOX-MAINARCH-003` (server ↔ DB/RLS)\n- `ANOX-MAINARCH-007` (server ↔ backup/PITR)\n- `ANOX-MAINARCH-024` (signing/release custody + incident-response trust boundary)\n\n## 15. Additional milestone security coverage\n\nNONE. No new Product trust boundary was introduced by this consolidation.\n\n## 16. Test / instrumentation status\n\n- JVM unit tests: 161 passed, 0 failed (local `testDebugUnitTest` on baseline)\n- Rust tests: 15 passed, 0 failed (`cargo test --locked`)\n- Android instrumentation: `NOT_RUN` (device/emulator not available)\n- True cross-domain integration test: ABSENT\n- B-021 matrix: updated with `ANOX-EVENT-0035`; several client rows remain `NOT_RUN`\n\n## 17. Next task\n\n`{data['next_task']['task_id']}` — `{data['next_task']['title']}`\n\n{data['next_task']['scope']}\n\n**Priority:** {data['next_task']['next_task_priority']}\n\n## 18. Handoff and cold recovery\n\nRun `python3 tools/continuity/generate_handoff.py` after the metadata commit to produce the cold-recovery archive. The archive must include the `ANOX-EVENT-0035` ledger event, the canonical findings set, the disposition map, and the Class-A remediation batch.\n"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print("LEGACY-AUDIT-SET-FREEZE consolidation applied.")
    print(f"  - findings.jsonl: {len(final_findings)} rows")
    print(f"  - audits.jsonl: {len(audits)} rows")
    print(f"  - new canonical findings: {len(new_findings)}")
    print(f"  - consolidated report: {report_path}")
    print(f"  - master report updated")


if __name__ == "__main__":
    main()
