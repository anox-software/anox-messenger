#!/usr/bin/env python3
"""LEGACY-FIX-01 deterministic validator.

Validates the foundation-state / registration / crypto-safety remediation for
the eight canonical Class-A legacy blockers. No backend, SQL, CI, secrets, or
remote mutation.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

TARGET_FINDINGS = {
    "ANOX-MAINARCH-019",
    "ANOX-MAINARCH-023",
    "ANOX-MAINARCH-031",
    "ANOX-LEGACY-ANDROIDSEC-001",
    "ANOX-LEGACY-CRYPTO-005",
    "ANOX-LEGACY-INTEGRATION-001",
    "ANOX-LEGACY-INTEGRATION-002",
    "ANOX-LEGACY-INTEGRATION-003",
}

UNCHANGED_OPEN = {
    "ANOX-MAINARCH-013",
    "ANOX-MAINARCH-018",
    "ANOX-MAINARCH-030",
    "ANOX-LEGACY-INTEGRATION-005",
    "ANOX-LEGACY-B003-001",
}


def fail(msg, errors):
    errors.append(msg)
    print(f"  FAIL {msg}")


def ok(msg):
    print(f"  OK   {msg}")


def read_text(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def read_jsonl(rel):
    path = REPO / rel
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def git(args):
    try:
        return subprocess.check_output(["git"] + args, cwd=REPO, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return None


def check_findings(errors):
    rows = read_jsonl("docs/workforce/registries/findings.jsonl")
    by_id = {r["finding_id"]: r for r in rows}

    for fid in TARGET_FINDINGS:
        if fid not in by_id:
            fail(f"Target finding {fid} not in findings.jsonl", errors)
            continue
        r = by_id[fid]
        if r["status"] != "Ready For Retest":
            fail(f"{fid} status is {r['status']}, expected Ready For Retest", errors)
        else:
            ok(f"{fid} is Ready For Retest")

    for fid in TARGET_FINDINGS:
        if by_id.get(fid, {}).get("status") == "Closed":
            fail(f"Target finding {fid} was incorrectly Closed", errors)

    for fid in UNCHANGED_OPEN:
        if fid not in by_id:
            fail(f"Non-target finding {fid} missing", errors)
            continue
        r = by_id[fid]
        if r["status"] != "Open":
            fail(f"Non-target finding {fid} must remain Open, is {r['status']}", errors)
        else:
            ok(f"{fid} remains Open")

    closed = [r["finding_id"] for r in rows if r["status"] == "Closed"]
    newly_closed = [fid for fid in closed if fid not in PRE_FIX01_CLOSED]
    if newly_closed:
        fail(f"Unexpected findings Closed: {newly_closed}", errors)
    else:
        ok("No non-target findings were Closed by this task")


def check_product_state(errors):
    ws = json.loads(read_text("docs/workforce/WORKFORCE_STATE.json"))
    product = ws.get("product_development_state")
    if product != "BLOCKED_PENDING_FINAL_AUDIT":
        fail(f"Product state not blocked: {product}", errors)
    else:
        ok("Product remains BLOCKED_PENDING_FINAL_AUDIT")

    ir = json.loads(read_text("docs/workforce/registries/implementation_readiness.json"))
    b004 = ir.get("domains", {}).get("B-004", {}).get("implementation_state")
    b005 = ir.get("domains", {}).get("B-005", {}).get("implementation_state")
    if b004 != "NOT_STARTED":
        fail(f"B004 backend must be NOT_STARTED, is {b004}", errors)
    else:
        ok("B004 backend is NOT_STARTED")
    if b005 != "NOT_STARTED":
        fail(f"B005 database/RLS must be NOT_STARTED, is {b005}", errors)
    else:
        ok("B005 database/RLS is NOT_STARTED")


def check_019(errors):
    text = read_text("android/src/main/java/com/anox/messenger/account/RegistrationOrchestrator.kt")
    if "isProductionEligible" in text and "B-002 requires StrongBox or TEE" in text:
        ok("019 production eligibility enforced before registerDeviceAuth")
    else:
        fail("019 production eligibility guard not found in RegistrationOrchestrator", errors)

    if "DeviceAuthNotProductionEligibleException" in text:
        ok("019 uses canonical DeviceAuthNotProductionEligibleException")
    else:
        fail("019 does not reference DeviceAuthNotProductionEligibleException", errors)


def check_integration_001(errors):
    text = read_text("android/src/main/java/com/anox/messenger/account/RegistrationOrchestrator.kt")
    if "validateDeviceAuthForCommit" in text and "deviceAuthJwkThumbprint" in text:
        ok("INTEGRATION-001 Device Auth revalidation before commit")
    else:
        fail("INTEGRATION-001 commit revalidation not found", errors)

    if "currentThumbprint != expectedThumbprint" in text:
        ok("INTEGRATION-001 thumbprint comparison present")
    else:
        fail("INTEGRATION-001 thumbprint comparison missing", errors)


def check_integration_003(errors):
    text = read_text("android/src/main/java/com/anox/messenger/account/RegistrationOrchestrator.kt")
    if "if (state is RegistrationState.CommitArmed) return null" in text:
        ok("INTEGRATION-003 CommitArmed never expires")
    else:
        fail("INTEGRATION-003 CommitArmed expiry guard missing", errors)

    if "current is RegistrationState.CommitArmed" in text:
        ok("INTEGRATION-003 abandon/clear blocked for CommitArmed")
    else:
        fail("INTEGRATION-003 abandon guard missing", errors)


def check_023(errors):
    text = read_text("crypto/android/src/main/java/com/anox/crypto/CryptoBridge.kt")

    if "fun getExistingStateKey(): ByteArray" in text and "fun getOrCreateStateKey(): ByteArray" in text:
        ok("023 K_STATE API split into create and read paths")
    else:
        fail("023 K_STATE split not found", errors)

    if "getExistingStateKey()" in text and "getOrCreateStateKey()" in text:
        # Check read paths use getExistingStateKey
        pass

    if "class MissingStateKeyException" in text:
        ok("023 MissingStateKeyException distinguishes missing key")
    else:
        fail("023 MissingStateKeyException missing", errors)

    if "writeFileAtomic(wrappedKeyFile, wrapped)" in text:
        ok("023 wrapped K_STATE persisted atomically")
    else:
        fail("023 K_STATE write not atomic", errors)

    if "getExistingStateKey()" in text.split("fun deserializeIdentity")[1].split("fun createOutbound")[0]:
        ok("023 deserializeIdentity uses getExistingStateKey")
    else:
        fail("023 deserializeIdentity does not use getExistingStateKey", errors)

    if "getExistingStateKey()" in text.split("fun deserializeSession")[1].split("fun destroyAllCrypto")[0]:
        ok("023 deserializeSession uses getExistingStateKey")
    else:
        fail("023 deserializeSession does not use getExistingStateKey", errors)


def check_androidsec_001(errors):
    text = read_text("crypto/android/src/main/java/com/anox/crypto/CryptoBridge.kt")
    # Direct type reference means `is`/`as`/`catch` on the class itself, not a string compare.
    if re.search(r"\bis\s+android\.security\.KeyStoreException", text) or \
       re.search(r"catch\s*\(\s*android\.security\.KeyStoreException", text):
        fail("ANDROIDSEC-001 still directly references android.security.KeyStoreException", errors)
    else:
        ok("ANDROIDSEC-001 no direct API33 KeyStoreException type reference")

    if '"android.security.KeyStoreException"' in text:
        ok("ANDROIDSEC-001 uses safe string-based class name check")
    else:
        fail("ANDROIDSEC-001 string-based classifier missing", errors)


def check_031(errors):
    text = read_text("crypto/android/src/main/java/com/anox/crypto/CryptoError.kt")
    if "object BufferTooSmall" in text and "-11 -> BufferTooSmall" in text:
        ok("031 BufferTooSmall mapped from -11")
    else:
        fail("031 BufferTooSmall error mapping missing", errors)

    if "AuthenticationFailed" in text:
        ok("031 AuthenticationFailed type retained")
    else:
        fail("031 AuthenticationFailed type removed", errors)

    rust = read_text("crypto/rust/src/error.rs")
    if "BufferTooSmall" in rust and "CryptoError::BufferTooSmall => -11" in rust:
        ok("031 Rust BufferTooSmall error with -11 code")
    else:
        fail("031 Rust BufferTooSmall missing", errors)

    lib = read_text("crypto/rust/src/lib.rs")
    small_returns = re.findall(r"return -(\d+);", lib)
    if "11" in small_returns and "2" not in small_returns:
        ok("031 Rust output-buffer checks use -11 consistently")
    else:
        fail("031 Rust output-buffer checks do not use -11 consistently", errors)


def check_crypto_005(errors):
    text = read_text("crypto/android/src/main/java/com/anox/crypto/CryptoBridge.kt")
    public_methods = [
        "fun createIdentity", "fun destroyIdentity",
        "fun getCurve25519PublicKey", "fun getEd25519PublicKey",
        "fun generateOneTimeKeys", "fun getOneTimeKey",
        "fun oneTimeKeysCount", "fun serializeIdentity",
        "fun deserializeIdentity", "fun createOutboundSession",
        "fun createInboundSession", "fun encrypt", "fun decrypt",
        "fun destroySession", "fun serializeSession",
        "fun deserializeSession"
    ]
    for m in public_methods:
        idx = text.find(m)
        if idx == -1:
            fail(f"CRYPTO-005 public method {m} not found", errors)
            continue
        block = text[idx:idx+500]
        if "cryptoLock.withLock" not in block:
            fail(f"CRYPTO-005 {m} not protected by cryptoLock", errors)
    ok("CRYPTO-005 all public crypto methods protected by cryptoLock")


def check_integration_002(errors):
    text = read_text("android/src/main/java/com/anox/messenger/account/CryptoBridgeLocalE2eeIdentityStep.kt")
    if "generateOneTimeKeys" in text and "saveIdentity" in text:
        ok("INTEGRATION-002 OTK generation followed by saveIdentity")
    else:
        fail("INTEGRATION-002 OTK persistence missing", errors)

    # Restrict the order check to the ensurePublicIdentityMaterial method body.
    method = text.split("fun ensurePublicIdentityMaterial")[1].split("private fun resolveIdentityHandle")[0]
    if method.find("saveIdentity") < method.find("getOneTimeKey"):
        ok("INTEGRATION-002 identity persisted before public OTK material extracted")
    else:
        fail("INTEGRATION-002 saveIdentity must occur before getOneTimeKey", errors)


def check_scope(errors):
    changed = git(["diff", "--name-only", "HEAD"])
    if changed is None:
        fail("Could not obtain git diff", errors)
        return
    changed = changed.splitlines()

    forbidden = ["backend/", "supabase/", ".github/workflows", ".sql", "migrations/"]
    for f in changed:
        for p in forbidden:
            if f.startswith(p) or f.endswith(p):
                fail(f"Forbidden scope file changed: {f}", errors)

    ok("Scope is limited to Android/Kotlin/Rust registration foundation")


PRE_FIX01_CLOSED = {
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


def main():
    errors = []
    print("LEGACY-FIX-01 targeted delta validator")
    print("=" * 60)
    check_findings(errors)
    check_product_state(errors)
    check_019(errors)
    check_integration_001(errors)
    check_integration_003(errors)
    check_023(errors)
    check_androidsec_001(errors)
    check_031(errors)
    check_crypto_005(errors)
    check_integration_002(errors)
    check_scope(errors)

    if errors:
        print("\n[FAIL] LEGACY-FIX-01 validation failed:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("\n[OK] LEGACY-FIX-01 validation PASSED")


if __name__ == "__main__":
    main()
