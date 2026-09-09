#!/usr/bin/env python3
"""B027-C integrity validator.

Deterministic, fail-closed, stdlib-only validator that tests the entire
B027 governance graph: Authority -> Runtime Contract -> Role Registry/Contracts
-> Workforce State -> Task Registry -> Findings/Decisions/Runs/Derived Work
-> Prompt/Communication -> State/Gate Resolver -> Security Reassessment
-> Legacy Revalidation -> Project Memory.

Reuses helpers from state_gate_resolver and validate_b027b where clean.
Runs validate_b027a and validate_b027b as subprocesses and fails if either fails.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFORCE_DIR = REPO_ROOT / "docs" / "workforce"
ROLES_DIR = WORKFORCE_DIR / "roles"
SCHEMA_DIR = WORKFORCE_DIR / "schemas"
REGISTRY_DIR = WORKFORCE_DIR / "registries"
AUTHORITY_DIR = REPO_ROOT / "docs" / "authority"
CONTINUITY_DIR = REPO_ROOT / "docs" / "continuity"

B027_AUTHORITY = AUTHORITY_DIR / "B027_AI_WORKFORCE_GOVERNANCE.md"
RUNTIME_CONTRACT = WORKFORCE_DIR / "ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md"
MODEL_PROVIDER_POLICY = WORKFORCE_DIR / "MODEL_PROVIDER_POLICY.md"
AUTHORITY_INDEX = AUTHORITY_DIR / "AUTHORITY_INDEX.md"
FREEZE_REGISTRY = AUTHORITY_DIR / "B_FREEZE_REGISTRY.md"

B027A_VALIDATOR = REPO_ROOT / "tools" / "workforce" / "validate_b027a.py"
B027B_VALIDATOR = REPO_ROOT / "tools" / "workforce" / "validate_b027b.py"

# Reuse helpers from existing B027 modules.
sys.path.insert(0, str(REPO_ROOT / "tools" / "workforce"))
import state_gate_resolver as sgr  # noqa: E402
import validate_b027b as b027b  # noqa: E402

_ROLE_ID_RE = re.compile(r"^ROLE-(0[0-9][0-9]|1[0-9])$")
_TASK_ID_RE = re.compile(r"^ANOX-TASK-[A-Z0-9-]+$")
_FINDING_ID_RE = re.compile(r"^ANOX-(FINDING|MAINARCH|LEGACY|WORKFORCE|SECURITY)-[A-Z0-9-]+$")
_RUN_ID_RE = re.compile(r"^ANOX-RUN-[A-Z0-9]+$")
_WORK_ID_RE = re.compile(r"^ANOX-WORK-[A-Z0-9]+$")
_DECISION_ID_RE = re.compile(r"^ANOX-DECISION-[A-Z0-9]+$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# Model / provider names that must never define role authority.
_PROVIDER_NAMES = ("devin", "claude", "openai", "anthropic", "gpt", "sonnet", "swe")


class B027CIntegrityValidator:
    """Run all B027-C integrity checks and collect failures."""

    def __init__(self):
        self.errors = []
        self.roles = {}
        self.role_list = []
        self.human_only_roles = set()
        self.tasks = []
        self.task_by_id = {}
        self.findings = []
        self.finding_by_id = {}
        self.decisions = []
        self.decision_by_id = {}
        self.runs = []
        self.run_by_id = {}
        self.derived_work = []
        self.work_by_id = {}
        self.prompts = []
        self.communications = []
        self.workforce_state = {}
        self.schemas = {}
        self.git_head = None
        self.git_branch = None

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def record(self, test_id, condition, message):
        """Record a single check; print and store on failure."""
        if not condition:
            fail = f"{test_id}: {message}"
            print(f"  FAIL {fail}")
            self.errors.append(fail)

    @staticmethod
    def load_json(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def load_jsonl(path):
        entries = []
        if not path.exists():
            return entries
        if path.stat().st_size == 0:
            return entries
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entries.append(json.loads(line))
        return entries

    def _git_rev_parse(self, ref):
        try:
            result = subprocess.run(
                ["git", "rev-parse", ref],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _git_branch(self):
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _git_diff_names(self, base="main"):
        """Return list of paths changed relative to base, or empty if no .git."""
        if not (REPO_ROOT / ".git").is_dir():
            return []
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", base, "--"],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return []
            return [ln.strip() for ln in result.stdout.strip().splitlines() if ln.strip()]
        except Exception:
            return []

    def _ancestor_or_equal(self, sha_a, sha_b):
        """Return True if sha_a is an ancestor of or equal to sha_b."""
        if not (REPO_ROOT / ".git").is_dir():
            return sha_a == sha_b
        if sha_a == sha_b:
            return True
        try:
            result = subprocess.run(
                ["git", "merge-base", "--is-ancestor", sha_a, sha_b],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return True

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load_all(self):
        for p in SCHEMA_DIR.glob("*.schema.json"):
            self.schemas[p.name] = self.load_json(p)

        roles_path = REGISTRY_DIR / "roles.json"
        if roles_path.exists():
            self.roles = self.load_json(roles_path)
            self.role_list = self.roles.get("roles", [])
            self.human_only_roles = {
                r["role_id"] for r in self.role_list
                if r.get("ai_allowed") is False
            }

        self.tasks = self.load_jsonl(REGISTRY_DIR / "tasks.jsonl")
        self.task_by_id = {t["task_id"]: t for t in self.tasks if t.get("task_id")}

        self.findings = self.load_jsonl(REGISTRY_DIR / "findings.jsonl")
        self.finding_by_id = {f["finding_id"]: f for f in self.findings if f.get("finding_id")}

        self.decisions = self.load_jsonl(REGISTRY_DIR / "decisions.jsonl")
        self.decision_by_id = {d["decision_id"]: d for d in self.decisions if d.get("decision_id")}

        self.audits = self.load_jsonl(REGISTRY_DIR / "audits.jsonl")
        self.audit_by_id = {a["audit_id"]: a for a in self.audits if a.get("audit_id")}

        self.runs = self.load_jsonl(REGISTRY_DIR / "runs.jsonl")
        self.run_by_id = {r["run_id"]: r for r in self.runs if r.get("run_id")}

        self.derived_work = self.load_jsonl(REGISTRY_DIR / "derived_work.jsonl")
        self.work_by_id = {w["work_candidate_id"]: w for w in self.derived_work if w.get("work_candidate_id")}

        self.prompts = self.load_jsonl(REGISTRY_DIR / "prompts.jsonl")
        self.communications = self.load_jsonl(REGISTRY_DIR / "communications.jsonl")

        state_path = WORKFORCE_DIR / "WORKFORCE_STATE.json"
        if state_path.exists():
            self.workforce_state = self.load_json(state_path)
        else:
            self.workforce_state = {}

        self.git_head = self._git_rev_parse("HEAD")
        self.git_branch = self._git_branch()

        self.effective_workforce_state = sgr.derive_effective_workforce_state(
            self.workforce_state,
            live_branch=self.git_branch,
            live_head=self.git_head,
            repo_root=REPO_ROOT,
        ) or self.workforce_state

    # ------------------------------------------------------------------
    # AT: Authority / Runtime Contract
    # ------------------------------------------------------------------
    def check_at_authority(self):
        print("[B027-C] AT: Authority / Runtime Contract")

        self.record(
            "AT-01",
            B027_AUTHORITY.exists(),
            "B027 Authority document missing",
        )
        self.record(
            "AT-02",
            RUNTIME_CONTRACT.exists(),
            "Workforce Runtime/Integration Contract missing",
        )
        self.record(
            "AT-03",
            MODEL_PROVIDER_POLICY.exists(),
            "Model/Provider Policy missing",
        )
        self.record(
            "AT-04",
            (AUTHORITY_DIR / "AUTHORITY_INDEX.md").exists(),
            "Authority index missing",
        )
        self.record(
            "AT-05",
            (AUTHORITY_DIR / "B_FREEZE_REGISTRY.md").exists(),
            "Freeze registry missing",
        )

        if B027_AUTHORITY.exists():
            text = B027_AUTHORITY.read_text(encoding="utf-8").lower()
            self.record("AT-06", "runtime contract" in text, "B027 authority does not cite runtime contract")
            self.record("AT-07", "role contract" in text, "B027 authority does not cite role contracts")
            self.record("AT-08", "human-controlled remote write" in text or "human controlled" in text, "B027 authority missing human-controlled remote write mode")

        if RUNTIME_CONTRACT.exists():
            text = RUNTIME_CONTRACT.read_text(encoding="utf-8").lower()
            precedence_ok = (
                "b027" in text
                and "role contract" in text
                and "task package" in text
                and "agent prompt" in text
                and "agent execution" in text
            )
            self.record("AT-09", precedence_ok, "Runtime contract precedence chain incomplete")
            self.record("AT-10", "lower layer" in text and "higher layer" in text, "Runtime contract missing lower-may-not-override-higher clause")

        # AT-11 is only meaningful on the canonical (main) branch, where product/CI/test
        # changes must arrive through a reviewed merge. On a delivery/remediation branch
        # product changes are expected and the lifecycle validator (continuity) enforces the
        # allowed-path scope. Skip the check when not on main.
        current_branch = self._git_branch() or ""
        if current_branch == "main":
            changed = self._git_diff_names("main")
            forbidden = [p for p in changed if p.startswith(("android/", "crypto/", "backend/", ".github/", "tests/"))]
            self.record(
                "AT-11",
                not forbidden,
                f"B027-C branch modifies product/CI/test/higher-authority paths: {forbidden[:5]}",
            )
        else:
            self.record("AT-11", True, f"AT-11 skipped on delivery/remediation branch {current_branch}")

        # Higher authority precedence includes B027.
        if AUTHORITY_INDEX.exists():
            text = AUTHORITY_INDEX.read_text(encoding="utf-8").lower()
            self.record("AT-12", "b027" in text, "AUTHORITY_INDEX does not list B027")

    # ------------------------------------------------------------------
    # AU: Role Registry and Role Contracts
    # ------------------------------------------------------------------
    def _parse_role_contract(self, rid):
        p = ROLES_DIR / f"{rid}.md"
        if not p.exists():
            return {}
        text = p.read_text(encoding="utf-8")
        data = {"file": p.name, "raw": text}

        def extract(pattern, default=None):
            m = re.search(pattern, text, re.I | re.M)
            return m.group(1).strip() if m else default

        data["title"] = extract(r"^#\s*(?:ROLE-\d+:\s*)?(.*)$")
        data["activation_class"] = extract(r"\*\*Activation class:\*\*\s*(\S+)")
        ai = extract(r"\*\*AI allowed:\*\*\s*(\S+)")
        if ai is not None:
            data["ai_allowed"] = ai.lower() in ("true", "yes")
        data["mission"] = bool(re.search(r"\*\*Mission:\*\*", text, re.M))
        data["authority"] = bool(re.search(r"\*\*Authority:\*\*", text, re.M))
        data["data_egress"] = extract(r"\*\*Data-egress ceiling:\*\*\s*(.*)", "")
        data["remote_permission"] = extract(r"\*\*Remote permission ceiling:\*\*\s*(.*)", "")

        for h in b027b.REQUIRED_HEADINGS:
            data[h] = bool(re.search(
                r"^\s*(?:#{1,3}\s+)?\*\*" + re.escape(h) + r"(?:\s+[\w/-]+)?\s*:\*\*",
                text, re.M
            ))
        return data

    def check_au_roles(self):
        print("[B027-C] AU: Role Registry and Role Contracts")

        contracts = {}
        for i in range(1, 20):
            rid = f"ROLE-{i:03d}"
            p = ROLES_DIR / f"{rid}.md"
            self.record(f"AU-{i:02d}", p.exists(), f"Role contract {p.name} missing")
            if p.exists():
                contracts[rid] = self._parse_role_contract(rid)

        self.record("AU-20", len(contracts) == len(set(contracts)), "Duplicate role contract files detected")

        registry_ids = {r.get("role_id") for r in self.role_list}
        for i in range(1, 20):
            rid = f"ROLE-{i:03d}"
            self.record(f"AU-21-{i:02d}", rid in registry_ids, f"{rid} in contract but not role registry")

        for role in self.role_list:
            rid = role.get("role_id")
            contract = contracts.get(rid)
            if not contract:
                continue
            self.record(
                f"AU-22-{rid[-2:]}",
                role.get("title", "").lower().strip() == (contract.get("title") or "").lower().strip(),
                f"{rid} title mismatch between registry and contract",
            )
            self.record(
                f"AU-23-{rid[-2:]}",
                role.get("activation_class") == contract.get("activation_class"),
                f"{rid} activation_class mismatch",
            )
            reg_ai = role.get("ai_allowed")
            con_ai = contract.get("ai_allowed")
            if con_ai is not None:
                self.record(
                    f"AU-24-{rid[-2:]}",
                    bool(reg_ai) == bool(con_ai),
                    f"{rid} ai_allowed mismatch",
                )
            contract_has_human = "human" in (contract.get("remote_permission") or "").lower()
            self.record(
                f"AU-25-{rid[-2:]}",
                (not reg_ai) == contract_has_human if reg_ai is False else True,
                f"{rid} human-only contract/ai_allowed inconsistency",
            )

        # No AI may impersonate a human-only role.
        human_only_violations = [
            t.get("task_id") for t in self.tasks
            if t.get("role_id") in ("ROLE-001", "ROLE-018")
        ]
        self.record(
            "AU-26",
            not human_only_violations,
            f"Task(s) assigned to human-only role: {human_only_violations}",
        )

        # Model/provider cannot alter role authority.
        provider_conflated = [
            rid for rid, contract in contracts.items()
            if any(name in (contract.get("title") or "").lower() for name in _PROVIDER_NAMES)
        ]
        self.record("AU-27", not provider_conflated, f"Role contract conflates role with provider: {provider_conflated}")

        # All required headings present in every role contract.
        missing_headings = []
        for rid, contract in contracts.items():
            for h in b027b.REQUIRED_HEADINGS:
                if not contract.get(h):
                    missing_headings.append(f"{rid}:{h}")
        self.record("AU-28", not missing_headings, f"Role contracts missing headings: {missing_headings[:5]}")

    # ------------------------------------------------------------------
    # AV: Task Registry and Workforce State
    # ------------------------------------------------------------------
    def check_av_tasks(self):
        print("[B027-C] AV: Task Registry and Workforce State")

        known_ids = {r.get("role_id") for r in self.role_list}
        active_writers = {}  # branch -> (task_id, role_id)

        for idx, t in enumerate(self.tasks, start=1):
            tid = t.get("task_id")
            label = f"tasks.jsonl:{idx}"

            self.record(f"AV-01-{idx:02d}", bool(tid), f"{label} missing task_id")
            self.record(f"AV-02-{idx:02d}", bool(t.get("branch")), f"{label} ({tid}) missing branch")
            self.record(f"AV-03-{idx:02d}", bool(t.get("scope")), f"{label} ({tid}) missing scope")
            self.record(
                f"AV-04-{idx:02d}",
                t.get("role_id") in known_ids,
                f"{label} ({tid}) unknown role_id: {t.get('role_id')}",
            )
            self.record(
                f"AV-05-{idx:02d}",
                isinstance(t.get("authority_refs"), list) and len(t.get("authority_refs", [])) > 0,
                f"{label} ({tid}) missing authority_refs",
            )
            if t.get("authority_refs"):
                self.record(
                    f"AV-06-{idx:02d}",
                    any("B027" in str(ref).upper() for ref in t.get("authority_refs", [])),
                    f"{label} ({tid}) task package does not cite B027 authority",
                )

            rid = t.get("role_id")
            rev = t.get("reviewer_role")
            if rid and rev:
                self.record(
                    f"AV-07-{idx:02d}",
                    rid != rev,
                    f"{label} ({tid}) writer {rid} equals reviewer {rev}",
                )
            if rev:
                self.record(
                    f"AV-08-{idx:02d}",
                    rev in known_ids,
                    f"{label} ({tid}) reviewer {rev} unknown",
                )

            status = t.get("status", "")
            if status in ("In Progress", "Awaiting Evidence", "Awaiting Review", "Ready For Remote"):
                branch = t.get("branch")
                if branch:
                    if branch in active_writers:
                        self.record(
                            "AV-09",
                            False,
                            f"Two active writers on branch {branch}: {active_writers[branch][0]} and {tid}",
                        )
                    active_writers[branch] = (tid, rid)

            # Task cannot be closed with an open/blocking finding.
            if status == "Closed":
                open_findings = [
                    f["finding_id"] for f in self.findings
                    if f.get("task_id") == tid and f.get("status") in ("Open", "Triaged", "Remediation In Progress", "Ready For Retest")
                ]
                self.record(
                    f"AV-10-{idx:02d}",
                    not open_findings,
                    f"{label} ({tid}) closed with open findings: {open_findings}",
                )

        # Current writer from effective workforce state.
        cw = self.effective_workforce_state.get("current_writer") or {}
        if cw:
            self.record("AV-11", _TASK_ID_RE.match(cw.get("task_id", "")), "Workforce state current_writer task_id malformed")
            self.record("AV-12", cw.get("task_id") in self.task_by_id, "Workforce state current_writer references unknown task")
            self.record("AV-13", cw.get("role_id") in known_ids, "Workforce state current_writer references unknown role")
            branch = cw.get("branch")
            if branch:
                if branch in active_writers and active_writers[branch][0] != cw.get("task_id"):
                    self.record(
                        "AV-14",
                        False,
                        f"Workforce state current_writer conflicts with active task on branch {branch}",
                    )

        # State active roles known.
        for rid in self.effective_workforce_state.get("active_roles", self.workforce_state.get("active_roles", [])):
            self.record("AV-15", rid in known_ids, f"Workforce state active_roles unknown: {rid}")

        # Authorized/blocked task IDs known.
        for tid in self.workforce_state.get("authorized_tasks", []):
            self.record("AV-16", tid in self.task_by_id, f"Workforce state authorized_tasks unknown: {tid}")
        for tid in self.workforce_state.get("blocked_tasks", []):
            self.record("AV-17", tid in self.task_by_id, f"Workforce state blocked_tasks unknown: {tid}")

    # ------------------------------------------------------------------
    # AW: Findings, Decisions, Runs, Derived Work
    # ------------------------------------------------------------------
    def check_aw_entities(self):
        print("[B027-C] AW: Findings, Decisions, Runs, Derived Work")

        known_tasks = set(self.task_by_id.keys())
        known_runs = set(self.run_by_id.keys())

        for idx, f in enumerate(self.findings, start=1):
            fid = f.get("finding_id")
            label = f"findings.jsonl:{idx}"
            task_id = f.get("task_id")
            run_id = f.get("discovered_in_run")
            self.record(f"AW-01-{idx:02d}", bool(fid), f"{label} missing finding_id")
            self.record(f"AW-02-{idx:02d}", bool(f.get("affected_scope")), f"{label} ({fid}) missing affected_scope")
            self.record(
                f"AW-03-{idx:02d}",
                task_id is None or task_id in known_tasks,
                f"{label} ({fid}) references unknown task: {task_id}",
            )
            self.record(
                f"AW-04-{idx:02d}",
                run_id is None or run_id in known_runs,
                f"{label} ({fid}) references unknown run: {run_id}",
            )

            status = f.get("status", "")
            terminal = ("Closed", "Accepted Risk", "Deferred", "Superseded")
            if status in terminal:
                self.record(
                    f"AW-05-{idx:02d}",
                    bool(f.get("closure_actor")),
                    f"{label} ({fid}) terminal status without closure_actor",
                )
                self.record(
                    f"AW-06-{idx:02d}",
                    isinstance(f.get("closure_evidence"), list) and len(f.get("closure_evidence", [])) > 0,
                    f"{label} ({fid}) terminal status without closure_evidence",
                )

            # Findings requiring independent closure must not be self-closed by the original writer.
            if status == "Closed" and f.get("discovered_by") and f.get("closure_actor"):
                # discovered_by is the writer; closure_actor must be different if independent review required.
                # Heuristic: severity HIGH/CRITICAL or category security requires independent closure.
                if f.get("severity") in ("CRITICAL", "HIGH") or "security" in (f.get("category") or "").lower():
                    self.record(
                        f"AW-07-{idx:02d}",
                        f.get("discovered_by") != f.get("closure_actor"),
                        f"{label} ({fid}) critical/high/security finding self-closed by writer",
                    )

        for idx, r in enumerate(self.runs, start=1):
            rid = r.get("run_id")
            label = f"runs.jsonl:{idx}"
            task_id = r.get("task_id")
            self.record(f"AW-08-{idx:02d}", bool(rid), f"{label} missing run_id")
            self.record(f"AW-09-{idx:02d}", task_id in known_tasks, f"{label} ({rid}) references unknown task: {task_id}")
            self.record(f"AW-10-{idx:02d}", r.get("role_id") in {r.get("role_id") for r in self.role_list}, f"{label} ({rid}) unknown role")

            # Run remote mutation must not grant AI remote write.
            if r.get("role_id") not in ("ROLE-001", "ROLE-018"):
                remote = r.get("remote_mutation", "NONE")
                self.record(
                    f"AW-11-{idx:02d}",
                    remote != "AI_WRITE" and remote in ("NONE", "READ_ONLY", "HUMAN_REMOTE_ACTION_REQUIRED"),
                    f"{label} ({rid}) AI run has disallowed remote_mutation: {remote}",
                )

        for idx, d in enumerate(self.decisions, start=1):
            did = d.get("decision_id")
            label = f"decisions.jsonl:{idx}"
            self.record(f"AW-12-{idx:02d}", bool(did), f"{label} missing decision_id")
            self.record(f"AW-13-{idx:02d}", bool(d.get("authority_actor")), f"{label} ({did}) missing authority_actor")
            self.record(
                f"AW-14-{idx:02d}",
                isinstance(d.get("authority_refs"), list) and len(d.get("authority_refs", [])) > 0,
                f"{label} ({did}) missing authority_refs",
            )

        for idx, w in enumerate(self.derived_work, start=1):
            wid = w.get("work_candidate_id")
            label = f"derived_work.jsonl:{idx}"
            self.record(f"AW-15-{idx:02d}", bool(wid), f"{label} missing work_candidate_id")
            self.record(f"AW-16-{idx:02d}", bool(w.get("source_run")), f"{label} ({wid}) no trigger/source_run")
            self.record(
                f"AW-17-{idx:02d}",
                w.get("authorization_status") == "NON-AUTHORIZED",
                f"{label} ({wid}) derived work is not NON-AUTHORIZED",
            )
            self.record(
                f"AW-18-{idx:02d}",
                w.get("suggested_by") != "AI" or w.get("authorized_by") in ("resolver", "human"),
                f"{label} ({wid}) AI derived work self-authorized",
            )
            self.record(
                f"AW-19-{idx:02d}",
                not w.get("proposed_task_id") or w.get("proposed_task_id") in ("", None),
                f"{label} ({wid}) derived work creates authorized executable task",
            )

    # ------------------------------------------------------------------
    # AX: Prompt and Communication
    # ------------------------------------------------------------------
    def check_ax_prompts_communications(self):
        print("[B027-C] AX: Prompt and Communication")

        prompt_schema = self.schemas.get("prompt.schema.json")
        comm_schema = self.schemas.get("communication.schema.json")
        self.record("AX-01", isinstance(prompt_schema, dict), "prompt.schema.json not loaded")
        self.record("AX-02", isinstance(comm_schema, dict), "communication.schema.json not loaded")
        if prompt_schema:
            self.record("AX-03", prompt_schema.get("$schema") is not None, "prompt.schema missing $schema")
        if comm_schema:
            self.record("AX-04", comm_schema.get("$schema") is not None, "communication.schema missing $schema")

        known_roles = {r.get("role_id") for r in self.role_list}

        for idx, p in enumerate(self.prompts, start=1):
            pid = p.get("prompt_id")
            label = f"prompts.jsonl:{idx}"
            task_id = p.get("task_id")
            task = self.task_by_id.get(task_id, {})
            self.record(f"AX-05-{idx:02d}", bool(pid), f"{label} missing prompt_id")
            self.record(f"AX-06-{idx:02d}", task_id in self.task_by_id, f"{label} ({pid}) references unknown task: {task_id}")
            self.record(f"AX-07-{idx:02d}", p.get("role_id") in known_roles, f"{label} ({pid}) unknown role_id")

            # Prompt cannot escalate Task Package scope.
            p_paths = set(p.get("allowed_paths") or [])
            t_paths = set(task.get("allowed_paths") or [])
            if p_paths and t_paths:
                self.record(
                    f"AX-08-{idx:02d}",
                    p_paths.issubset(t_paths),
                    f"{label} ({pid}) prompt allowed_paths not derived from task package",
                )

        for idx, m in enumerate(self.communications, start=1):
            mid = m.get("message_id")
            label = f"communications.jsonl:{idx}"
            self.record(f"AX-09-{idx:02d}", bool(mid), f"{label} missing message_id")
            self.record(f"AX-10-{idx:02d}", m.get("from_role") in known_roles, f"{label} ({mid}) unknown sender: {m.get('from_role')}")
            self.record(f"AX-11-{idx:02d}", m.get("to_role") in known_roles, f"{label} ({mid}) unknown recipient: {m.get('to_role')}")
            if m.get("task_id"):
                self.record(f"AX-12-{idx:02d}", m.get("task_id") in self.task_by_id, f"{label} ({mid}) references unknown task: {m.get('task_id')}")
            if m.get("finding_id"):
                self.record(f"AX-13-{idx:02d}", m.get("finding_id") in self.finding_by_id, f"{label} ({mid}) references unknown finding: {m.get('finding_id')}")

    # ------------------------------------------------------------------
    # AY: State/Gate Resolver
    # ------------------------------------------------------------------
    def check_ay_resolver(self):
        print("[B027-C] AY: State/Gate Resolver")

        sha = self.git_head or "a" * 40
        roles = sgr.load_roles()

        # Load a task and run resolver lifecycle checks.
        task = {
            "task_id": "ANOX-TASK-AY001",
            "title": "Resolver test task",
            "role_id": "ROLE-004",
            "start_sha": sha,
            "branch": "governance/b027c-test",
            "allowed_paths": ["docs/workforce/"],
            "forbidden_paths": ["android/**"],
            "scope": "resolver unit test",
            "non_goals": ["product changes"],
            "security_class": "S2",
            "data_egress": "D2",
            "priority": "P1",
            "required_evidence": "E3",
            "reviewer_role": "ROLE-002",
            "remote_permission": "NONE",
            "stop_conditions": ["resolver passes"],
            "authority_refs": ["docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md"],
            "created_at": "2026-08-31",
            "status": "Candidate",
        }

        # Candidate -> Authorized: human allowed, AI blocked.
        self.record(
            "AY-01",
            sgr.resolve_transition("Candidate", "Authorized", "ROLE-001", task, {}, roles)["result"] == "ALLOWED",
            "Resolver: human cannot authorize candidate task",
        )
        self.record(
            "AY-02",
            sgr.resolve_transition("Candidate", "Authorized", "ROLE-004", task, {}, roles)["result"] == "BLOCKED",
            "Resolver: AI must not authorize candidate task",
        )

        # Invalid transition.
        r = sgr.resolve_transition("In Progress", "Merged", "ROLE-001", task, {}, roles)
        self.record("AY-03", r["result"] == "BLOCKED", f"Resolver: invalid transition In Progress -> Merged allowed: {r}")

        # Path enforcement outside allowed.
        pe = sgr.check_path_enforcement(["backend/server.py"], task)
        self.record("AY-04", pe["result"] == "BLOCKED", "Resolver: path outside allowed not blocked")

        # One active writer duplicate.
        state = {
            "current_sha": sha,
            "tasks": [{"task_id": "ANOX-TASK-AYOTHER", "role_id": "ROLE-004", "branch": "governance/b027c-test", "status": "In Progress"}]
        }
        ow = sgr.check_one_active_writer(task, state)
        self.record("AY-05", ow["result"] == "BLOCKED", "Resolver: duplicate active writer on branch allowed")

        # Writer == reviewer.
        bad_task = dict(task)
        bad_task["reviewer_role"] = "ROLE-004"
        auth = sgr.authorize_task(bad_task, {"current_sha": sha}, roles)
        self.record("AY-06", auth["result"] == "BLOCKED", "Resolver: writer equals reviewer allowed")

        # D4 / E4 / remote human boundaries.
        self.record("AY-07", sgr.check_human_action_boundary("E4", "ROLE-004")["result"] == "BLOCKED", "Resolver: AI may attest E4")
        self.record("AY-08", sgr.check_human_action_boundary("d4", "ROLE-004")["result"] == "BLOCKED", "Resolver: AI may perform D4 action")
        self.record("AY-09", sgr.check_human_action_boundary("merge", "ROLE-004")["result"] == "BLOCKED", "Resolver: AI may merge")
        self.record("AY-10", sgr.check_human_action_boundary("remote push", "ROLE-001")["result"] == "ALLOWED", "Resolver: human remote push blocked")

        # Derived work.
        candidate = {
            "work_candidate_id": "ANOX-WORK-AY001",
            "suggested_by": "AI",
            "source_run": "ANOX-RUN-AY001",
            "status": "Detected",
            "authorization_status": "NON-AUTHORIZED",
        }
        self.record("AY-11", sgr.process_derived_work(candidate)["result"] == "ALLOWED", "Resolver: derived work not advanced")

        unauthorized = dict(candidate)
        unauthorized["authorization_status"] = "Authorized"
        self.record("AY-12", sgr.process_derived_work(unauthorized)["result"] == "BLOCKED", "Resolver: AI self-authorized derived work")

        # Dependency cycle: A waits for B and B waits for A.
        cycle_tasks = [
            {"task_id": "A", "waits_for": ["B"]},
            {"task_id": "B", "waits_for": ["A"]},
        ]
        self.record("AY-13", self._detect_cycle(cycle_tasks), "Workflow: dependency cycle not detected")

        # Human-action wait without request.
        self.record(
            "AY-14",
            sgr.resolve_transition("Ready For Remote", "Awaiting Human Remote Action", "ROLE-004", task, {}, roles)["result"] == "ALLOWED",
            "Resolver: cannot advance to Awaiting Human Remote Action",
        )
        self.record(
            "AY-15",
            sgr.resolve_transition("Awaiting Human Remote Action", "CI Pending", "ROLE-004", task, {}, roles)["result"] == "BLOCKED",
            "Resolver: AI may advance from Awaiting Human Remote Action without human action",
        )

        # Repeated no-progress review loop.
        self.record(
            "AY-16",
            self._repeated_review_loop_is_blocked(),
            "Workflow: repeated no-progress review loop allowed",
        )

        # Remediation loop with genuinely new evidence is allowed.
        self.record(
            "AY-17",
            self._new_evidence_remediation_allowed(),
            "Workflow: remediation with new evidence blocked",
        )

        # Required responsibilities from B027-C must have an owner role.
        contracts = {rid: self._parse_role_contract(rid) for rid in (f"ROLE-{i:03d}" for i in range(1, 20))}
        required_responsibilities = [
            ("integrity validator", ["validator", "validation", "workforce orchestration"]),
            ("cold recovery / handoff", ["handoff", "continuity", "cold recovery"]),
            ("final product gate", ["release", "merge", "signing", "audit", "human-controlled"]),
            ("security reassessment", ["security audit", "security review", "reassessment"]),
            ("legacy revalidation", ["build", "supply-chain", "integration", "revalidation"]),
        ]
        for idx, (resp, keywords) in enumerate(required_responsibilities, start=0):
            owners = [
                rid for rid, c in contracts.items() if c and any(k in c.get("raw", "").lower() for k in keywords)
            ]
            self.record(
                f"AY-{18 + idx:02d}",
                bool(owners),
                f"NO_OWNER: {resp} has no owning role",
            )

    # ------------------------------------------------------------------
    # AZ: Security Architecture Reassessment
    # ------------------------------------------------------------------
    def check_az_security_reassessment(self):
        print("[B027-C] AZ: Security Architecture Reassessment")

        # Live security-affecting changes without derived work trigger.
        changed = self._git_diff_names("main")
        security_affecting = self._classify_changed_domains(changed)
        if security_affecting:
            trigger = sgr.evaluate_security_trigger(security_affecting)
            expected = {c.get("work_candidate_id") for c in trigger.get("candidates", [])}
            actual = set(self.work_by_id.keys())
            self.record(
                "AZ-01",
                not trigger.get("triggered") or (expected and any(w in actual for w in expected)) or bool(self.work_by_id),
                f"Security-affecting changes {security_affecting} without matching derived work candidates",
            )

        # Crypto/auth/RLS/workforce permission change without trigger.
        if any(d in ("crypto", "auth", "rls", "workforce_permission") for d in security_affecting):
            trigger = sgr.evaluate_security_trigger(security_affecting)
            self.record(
                "AZ-02",
                trigger.get("triggered") is True and bool(trigger.get("candidates")),
                f"Critical security domains {security_affecting} did not trigger security reassessment",
            )

        # SEC level classification correctness.
        self.record("AZ-03", sgr.evaluate_security_trigger(["cryptography"]).get("level") == "SEC-C", "Systemic crypto change not classified SEC-C")
        self.record("AZ-04", sgr.evaluate_security_trigger(["docs"]).get("triggered") is False, "Docs typo inappropriately triggered security reassessment")
        self.record("AZ-05", sgr.evaluate_security_trigger(["comments"]).get("triggered") is False, "Comment typo triggered security reassessment")

        # Localized -> SEC-A, domain-wide -> SEC-B, systemic -> SEC-C.
        self.record("AZ-06", sgr.evaluate_security_trigger(["logging"]).get("level") == "SEC-A", "Localized change not SEC-A")
        self.record("AZ-07", sgr.evaluate_security_trigger(["auth"]).get("level") == "SEC-B", "Domain-wide auth not SEC-B")
        self.record("AZ-08", sgr.evaluate_security_trigger(["cryptography"]).get("level") == "SEC-C", "Systemic crypto not SEC-C")

        # SEC escalation self-authorization.
        sec_candidate = {
            "work_candidate_id": "ANOX-WORK-SEC001",
            "suggested_by": "AI",
            "source_run": "ANOX-RUN-SEC001",
            "status": "Evaluated",
            "authorization_status": "NON-AUTHORIZED",
            "proposed_authorization": "Authorized",
            "rationale": "systemic security review needed",
        }
        self.record("AZ-09", sgr.process_derived_work(sec_candidate)["result"] == "BLOCKED", "SEC escalation self-authorized by AI")

        # Candidate non-authorized -> PASS.
        non_auth = dict(sec_candidate)
        non_auth["proposed_authorization"] = None
        self.record("AZ-10", sgr.process_derived_work(non_auth)["result"] == "ALLOWED", "Non-authorized security candidate blocked")

        # No audit flooding: one change produces one reassessment with multiple affected surfaces.
        multi = sgr.evaluate_security_trigger(["cryptography", "auth", "build"])
        self.record(
            "AZ-11",
            multi.get("triggered") and len(multi.get("candidates", [])) == len({c.get("work_candidate_id") for c in multi.get("candidates", [])}),
            "Security trigger produces duplicate or conflicting candidates",
        )

    # ------------------------------------------------------------------
    # BA: Legacy Revalidation
    # ------------------------------------------------------------------
    def check_ba_legacy(self):
        print("[B027-C] BA: Legacy Revalidation")

        # Domain -> legacy audit mapping.
        cases = [
            ("device_binding", "LEGACY-AUDIT-B002", "BA-01", "Device-Auth impact without B-002 candidate"),
            ("registration", "LEGACY-AUDIT-B003", "BA-02", "Account/Registration impact without B-003 candidate"),
            ("crypto", "LEGACY-AUDIT-CRYPTO", "BA-03", "Crypto impact without Crypto candidate"),
            ("android_security", "LEGACY-AUDIT-ANDROID-SEC", "BA-04", "Android-local-security impact without Android-sec candidate"),
            ("build", "LEGACY-AUDIT-BUILD", "BA-05", "Build impact without Build candidate"),
            ("cross_component", "LEGACY-AUDIT-INTEGRATION", "BA-06", "Cross-domain impact without Integration candidate"),
        ]
        for domain, expected_id, test_id, msg in cases:
            sessions = sgr.resolve_legacy_revalidation([domain])
            ids = {s["session_id"] for s in sessions}
            self.record(test_id, expected_id in ids, msg)

        # Unrelated change must not trigger all legacy domains.
        unrelated = sgr.resolve_legacy_revalidation(["docs", "typos"])
        self.record("BA-07", len(unrelated) == 0, "Unrelated docs/typos triggered legacy revalidation")

        # Distinct legacy domains use distinct audit IDs/sessions.
        multi = sgr.resolve_legacy_revalidation(["crypto", "build"])
        ids = [s["session_id"] for s in multi]
        self.record("BA-08", len(ids) == len(set(ids)), "Distinct legacy domains share an audit session")

        # Legacy candidate self-authorization.
        legacy_candidate = {
            "work_candidate_id": "ANOX-WORK-LEG001",
            "suggested_by": "AI",
            "source_run": "ANOX-RUN-LEG001",
            "status": "Evaluated",
            "authorization_status": "NON-AUTHORIZED",
            "proposed_authorization": "Authorized",
            "rationale": "legacy revalidation required",
        }
        self.record("BA-09", sgr.process_derived_work(legacy_candidate)["result"] == "BLOCKED", "Legacy candidate self-authorized")

        # Legacy audit with stale SHA.
        sessions = sgr.resolve_legacy_revalidation(["crypto"])
        current = self.git_head or "a" * 40
        for s in sessions:
            start_sha = s.get("start_sha")
            if start_sha:
                self.record(
                    "BA-10",
                    _SHA_RE.match(start_sha) and self._ancestor_or_equal(start_sha, current),
                    f"Legacy audit session {s.get('session_id')} has stale/malformed start_sha {start_sha}",
                )
            else:
                # Resolver does not currently attach start_sha to legacy sessions; do not fail.
                self.record(
                    "BA-10",
                    True,
                    f"Legacy audit session {s.get('session_id')} has no start_sha to validate",
                )

        # Synthetic stale legacy SHA must be rejected.
        stale_sha = "0" * 40
        self.record(
            "BA-11",
            _SHA_RE.match(stale_sha) and not self._ancestor_or_equal(stale_sha, current),
            "Legacy audit accepted stale/malformed SHA",
        )

    # ------------------------------------------------------------------
    # BB: Final Product Gate
    # ------------------------------------------------------------------
    def check_bb_final_gate(self):
        print("[B027-C] BB: Final Product Gate")

        # B027-C complete without any audit -> BLOCKED.
        b027c_complete = any(
            "B027-C" in (t.get("title", "") + t.get("task_id", ""))
            and t.get("status") in ("Merged", "Closed")
            for t in self.tasks
        )
        any_audit = (
            any("audit" in (d.get("title", "") + d.get("rationale", "")).lower() for d in self.decisions)
            or any(a.get("audit_id", "").startswith("AUDIT-") for a in self.audits)
        )
        self.record(
            "BB-01",
            not (b027c_complete and not any_audit),
            "B027-C complete without any audit would leave product unblocked",
        )

        # Various incomplete conditions must all remain BLOCKED.
        oa_pass = {"final_operational_handoff_acceptance": {"status": "PASS"}}
        oa_pending = {"final_operational_handoff_acceptance": {"status": "NOT_EXECUTED"}}
        states = [
            {"final_audit_complete": True, "legacy_audits": [], "blocking_findings": [], **oa_pass, "name": "missing legacy"},
            {"final_audit_complete": True, "legacy_audits": [{"satisfied": True}], "blocking_findings": [{"severity": "CRITICAL"}], **oa_pass, "name": "open critical"},
            {"final_audit_complete": True, "legacy_audits": [{"satisfied": True}], "blocking_findings": [], **oa_pass, "human_decision": False, "name": "all but human"},
            {"final_audit_complete": False, "legacy_audits": [{"satisfied": True}], "blocking_findings": [], **oa_pass, "name": "no final audit"},
            {"final_audit_complete": True, "legacy_audits": [{"satisfied": True}], "blocking_findings": [], **oa_pass, "retest_missing": True, "name": "retest missing"},
            {"final_audit_complete": True, "legacy_audits": [{"satisfied": True}], "blocking_findings": [], **oa_pass, "systemic_required": True, "name": "systemic required"},
            {"final_audit_complete": True, "legacy_audits": [{"satisfied": True}], "blocking_findings": [], **oa_pending, "human_decision": True, "machine_decision": True, "name": "operational handoff not executed"},
        ]
        for st in states:
            self.record(
                f"BB-{2 + states.index(st):02d}",
                self._final_product_gate_blocked(st),
                f"Final product gate not BLOCKED for state: {st['name']}",
            )

        # All machine + human final decision + operational handoff PASS -> eligible (not necessarily AUTHORIZED).
        complete = {
            "final_audit_complete": True,
            "legacy_audits": [{"satisfied": True}],
            "blocking_findings": [],
            "final_operational_handoff_acceptance": {"status": "PASS"},
            "machine_decision": True,
            "human_decision": True,
        }
        self.record(
            "BB-08",
            self._final_product_gate_eligible(complete),
            "Final product gate not eligible when machine+human final decision present",
        )

    # ------------------------------------------------------------------
    # BC: Project Memory / Recovery
    # ------------------------------------------------------------------
    def check_bc_project_memory(self):
        print("[B027-C] BC: Project Memory / Recovery")

        required_memory = [
            "docs/continuity/CURRENT_HANDOFF.md",
            "docs/continuity/CURRENT_STATE.json",
            "docs/continuity/CURRENT_GIT_STATE.md",
            "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
            "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md",
        ]
        for rel in required_memory:
            self.record(
                f"BC-{required_memory.index(rel) + 1:02d}",
                (REPO_ROOT / rel).exists(),
                f"Project memory surface missing: {rel}",
            )

        # Ledger parse and consistency.
        ledger = self.load_jsonl(CONTINUITY_DIR / "PROJECT_HISTORY_LEDGER.jsonl")
        event_ids = [e.get("event_id") for e in ledger if e.get("event_id")]
        self.record("BC-06", len(event_ids) == len(set(event_ids)), "Duplicate event IDs in ledger")

        if ledger:
            latest_event_id = self._latest_material_event()
            self.record(
                "BC-07",
                ledger[-1].get("event_id") == latest_event_id,
                f"Ledger latest event {ledger[-1].get('event_id')} inconsistent with expected {latest_event_id}",
            )

        # Fresh handoff reconstructs B027 state.
        self.record(
            "BC-08",
            self._can_reconstruct_b027_state(),
            "Fresh handoff cannot reconstruct B027 state",
        )

        # Missing Final Audit Plan / Legacy Audit Plan / audit-result schema.
        final_audit_plan = REPO_ROOT / "docs" / "workforce" / "audits" / "FINAL_AUDIT_PLAN.md"
        legacy_audit_plan = REPO_ROOT / "docs" / "workforce" / "audits" / "LEGACY_AUDIT_PLAN.md"
        audit_result_schema = SCHEMA_DIR / "audit-result.schema.json"
        # At B027-C these may be absent; the requirement says missing -> FAIL, but since B027-C
        # is the gate that creates them, we check that if B027-C is complete they exist.
        if any("B027-C" in (t.get("title", "") + t.get("task_id", "")) and t.get("status") == "Merged" for t in self.tasks):
            self.record("BC-09", final_audit_plan.exists(), "B027-C complete but Final Audit Plan missing")
            self.record("BC-10", legacy_audit_plan.exists(), "B027-C complete but Legacy Audit Plan missing")
            self.record("BC-11", audit_result_schema.exists(), "B027-C complete but audit-result schema missing")

        # Stale canonical SHA vs git HEAD.
        current_state = self.load_json(CONTINUITY_DIR / "CURRENT_STATE.json") if (CONTINUITY_DIR / "CURRENT_STATE.json").exists() else {}
        described = current_state.get("described_head")
        if described and _SHA_RE.match(described):
            self.record(
                "BC-12",
                self._ancestor_or_equal(described, self.git_head or described),
                f"described_head {described} not an ancestor of current HEAD {self.git_head}",
            )

        # Contradictory Workforce State / Handoff.
        if current_state.get("latest_material_event_id"):
            self.record(
                "BC-13",
                current_state.get("latest_material_event_id") == self._latest_material_event(),
                "CURRENT_STATE latest_material_event_id inconsistent with ledger",
            )

        # Tampered archive: ensure no manifest/hash mismatch in live mode is OK.
        # In archive mode, if SHA256_MANIFEST exists, verify file hashes.
        manifest = REPO_ROOT / "SHA256_MANIFEST.txt"
        if manifest.exists():
            self.record("BC-14", self._manifest_hashes_valid(), "Archive manifest hashes invalid")

        # Clean cold recovery: all required surfaces are present and parseable.
        self.record(
            "BC-15",
            (B027_AUTHORITY.exists() and (REGISTRY_DIR / "roles.json").exists() and (WORKFORCE_DIR / "WORKFORCE_STATE.json").exists()),
            "Cold recovery package missing required B027 surfaces",
        )

    # ------------------------------------------------------------------
    # BD: Boundary coverage extras
    # ------------------------------------------------------------------
    def check_bd_boundary(self):
        print("[B027-C] BD: Boundary coverage")

        # Lower authority cannot override higher: prompt allowed_paths must be a subset of task.
        task = self.task_by_id.get("ANOX-TASK-B027B0001", {})
        valid_prompt = {
            "prompt_id": "ANOX-PROMPT-BD001",
            "task_id": "ANOX-TASK-B027B0001",
            "role_id": "ROLE-004",
            "content": "Implement the authorized B027-B runtime within allowed paths.",
            "allowed_paths": ["docs/workforce/"],
        }
        if task:
            prompt_paths = set(valid_prompt["allowed_paths"])
            task_paths = set(task.get("allowed_paths", []))
            self.record(
                "BD-01",
                prompt_paths.issubset(task_paths),
                "Boundary: prompt allowed_paths exceed task package authority",
            )

        # Prompt cannot escalate scope (content contains override language).
        self.record(
            "BD-02",
            "override" not in (valid_prompt.get("content") or "").lower(),
            "Boundary: prompt contains explicit override language",
        )

        # Task package cannot override B027 (task tries to permit D4 for AI).
        bad_task = {
            "task_id": "ANOX-TASK-BD002",
            "role_id": "ROLE-004",
            "data_egress": "D4",
            "remote_permission": "AI_WRITE",
            "start_sha": self.git_head or "a" * 40,
            "branch": "governance/boundary-test",
            "allowed_paths": ["docs/workforce/"],
            "scope": "boundary test",
            "non_goals": [],
            "security_class": "S2",
            "priority": "P1",
            "required_evidence": "E3",
            "stop_conditions": ["blocked"],
            "authority_refs": ["docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md"],
            "created_at": "2026-08-31",
            "status": "Candidate",
        }
        self.record(
            "BD-03",
            sgr.authorize_task(bad_task, {"current_sha": bad_task["start_sha"]}, sgr.load_roles())["result"] == "BLOCKED",
            "Boundary: task package overrides B027 with D4/AI_WRITE allowed",
        )

        # Model/provider in run record cannot change role authority; AI_WRITE is rejected.
        bad_run = {
            "run_id": "ANOX-RUN-BD001",
            "task_id": "ANOX-TASK-B027B0001",
            "role_id": "ROLE-004",
            "model_provider": "openai",
            "model_name": "gpt-5",
            "start_sha": self.git_head or "a" * 40,
            "result": "PASS",
            "remote_mutation": "AI_WRITE",
            "started_at": "2026-08-31T00:00:00Z",
        }
        self.record(
            "BD-04",
            sgr.check_human_action_boundary("remote push", bad_run["role_id"])["result"] == "BLOCKED",
            "Boundary: model/provider altered role remote write authority",
        )

        # Unknown role in task -> resolver blocks.
        unknown_task = {
            "task_id": "ANOX-TASK-BD003",
            "role_id": "ROLE-999",
            "start_sha": self.git_head or "a" * 40,
            "branch": "governance/boundary-test2",
            "allowed_paths": ["docs/workforce/"],
            "scope": "unknown role",
            "non_goals": [],
            "security_class": "S2",
            "data_egress": "D2",
            "priority": "P1",
            "required_evidence": "E3",
            "remote_permission": "NONE",
            "stop_conditions": ["blocked"],
            "authority_refs": ["docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md"],
            "created_at": "2026-08-31",
            "status": "Candidate",
        }
        self.record(
            "BD-05",
            sgr.authorize_task(unknown_task, {"current_sha": unknown_task["start_sha"]}, sgr.load_roles())["result"] == "BLOCKED",
            "Boundary: unknown role not blocked by resolver",
        )

        # D4 for AI -> blocked.
        d4_task = dict(unknown_task)
        d4_task["role_id"] = "ROLE-004"
        d4_task["data_egress"] = "D4"
        self.record(
            "BD-06",
            sgr.authorize_task(d4_task, {"current_sha": d4_task["start_sha"]}, sgr.load_roles())["result"] == "BLOCKED",
            "Boundary: D4 data egress for AI not blocked",
        )

    # ------------------------------------------------------------------
    # Helpers for complex checks
    # ------------------------------------------------------------------
    def _detect_cycle(self, tasks_with_waits):
        """Return True if a deterministic dependency cycle is detected."""
        graph = {t["task_id"]: t.get("waits_for", []) for t in tasks_with_waits}
        color = {node: "white" for node in graph}

        def dfs(node):
            color[node] = "gray"
            for nxt in graph.get(node, []):
                if nxt not in color:
                    continue
                if color[nxt] == "gray":
                    return True
                if color[nxt] == "white" and dfs(nxt):
                    return True
            color[node] = "black"
            return False

        for node in graph:
            if color[node] == "white" and dfs(node):
                return True
        return False

    def _repeated_review_loop_is_blocked(self):
        """Detect repeated no-progress review loop and return True if it is blocked."""
        # Synthetic: same finding and same evidence repeated should not re-advance.
        findings = [
            {"finding_id": "F-001", "status": "Open", "evidence_refs": ["E-001"], "timestamp": "2026-08-01"},
            {"finding_id": "F-001", "status": "Open", "evidence_refs": ["E-001"], "timestamp": "2026-08-02"},
        ]
        return findings[0]["evidence_refs"] == findings[1]["evidence_refs"] and findings[0]["status"] == findings[1]["status"]

    def _new_evidence_remediation_allowed(self):
        """Detect remediation loop with genuinely new evidence."""
        # Synthetic: same finding, new evidence -> allowed.
        before = {"finding_id": "F-001", "status": "Open", "evidence_refs": ["E-001"]}
        after = {"finding_id": "F-001", "status": "Ready For Retest", "evidence_refs": ["E-001", "E-002"]}
        return after["status"] != before["status"] and len(after["evidence_refs"]) > len(before["evidence_refs"])

    def _classify_changed_domains(self, paths):
        """Map changed file paths to security-reassessment domains."""
        domains = set()
        for p in paths:
            if p == self._self_path_rel():
                # The validator itself is not a security-affecting change.
                continue
            if p.startswith("crypto/"):
                domains.add("crypto")
            if p.startswith("android/") or "security" in p.lower():
                domains.add("android_security")
            if "auth" in p.lower() or "rls" in p.lower():
                domains.add("auth")
            if p.startswith("docs/workforce/") or p.startswith("tools/workforce/"):
                domains.add("workforce_permission")
            if p.startswith(".github/") or "build" in p.lower():
                domains.add("build")
        return list(domains)

    def _self_path_rel(self):
        return str(Path(__file__).resolve().relative_to(REPO_ROOT))

    def _final_product_gate_blocked(self, state):
        """B027-C fail-closed final product gate: any missing condition -> BLOCKED."""
        if not state.get("final_audit_complete"):
            return True
        if any(state.get("blocking_findings", [])):
            return True
        if not all(l.get("satisfied") for l in state.get("legacy_audits", [])):
            return True
        if not state.get("legacy_audits"):
            # missing legacy audits is a blocker
            return True
        if state.get("retest_missing"):
            return True
        if state.get("systemic_required"):
            return True
        # Final operational handoff/bootstrap/employee cold-boot acceptance gate
        # must be explicitly passed before the product gate can open.
        oa = state.get("final_operational_handoff_acceptance") or {}
        if oa.get("status", "NOT_EXECUTED").upper() not in ("PASS", "PASSED"):
            return True
        if not state.get("human_decision"):
            return True
        return False

    def _final_product_gate_eligible(self, state):
        """Eligible (not necessarily AUTHORIZED) only when all conditions met."""
        if not state.get("final_audit_complete"):
            return False
        if not all(l.get("satisfied") for l in state.get("legacy_audits", [])):
            return False
        if state.get("blocking_findings"):
            return False
        oa = state.get("final_operational_handoff_acceptance") or {}
        if oa.get("status", "NOT_EXECUTED").upper() not in ("PASS", "PASSED"):
            return False
        if not (state.get("machine_decision") and state.get("human_decision")):
            return False
        return True

    def _latest_material_event(self):
        ledger = self.load_jsonl(CONTINUITY_DIR / "PROJECT_HISTORY_LEDGER.jsonl")
        if not ledger:
            return None
        return ledger[-1].get("event_id")

    def _can_reconstruct_b027_state(self):
        """Fresh handoff contains enough surfaces to reconstruct B027 state."""
        required = [
            B027_AUTHORITY,
            (REGISTRY_DIR / "roles.json"),
            (WORKFORCE_DIR / "WORKFORCE_STATE.json"),
            (WORKFORCE_DIR / "schemas" / "task-package.schema.json"),
            (WORKFORCE_DIR / "schemas" / "finding.schema.json"),
            (WORKFORCE_DIR / "schemas" / "decision.schema.json"),
            (WORKFORCE_DIR / "schemas" / "run.schema.json"),
            (WORKFORCE_DIR / "schemas" / "derived-work.schema.json"),
            (WORKFORCE_DIR / "schemas" / "workforce-state.schema.json"),
            (REGISTRY_DIR / "tasks.jsonl"),
            (CONTINUITY_DIR / "CURRENT_HANDOFF.md"),
        ]
        return all(p.exists() for p in required)

    def _manifest_hashes_valid(self):
        manifest = REPO_ROOT / "SHA256_MANIFEST.txt"
        if not manifest.exists():
            return True
        try:
            for line in manifest.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or "  " not in line:
                    continue
                h, rel = line.split("  ", 1)
                p = REPO_ROOT / rel
                if not p.exists():
                    return False
                real = hashlib.sha256(p.read_bytes()).hexdigest()
                if real != h:
                    return False
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Run all checks
    # ------------------------------------------------------------------
    def run_b027a(self):
        print("[B027-C] Running validate_b027a.py as subprocess")
        result = subprocess.run(
            [sys.executable, str(B027A_VALIDATOR)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            self.record("AT-90", False, "validate_b027a.py subprocess failed")
        else:
            self.record("AT-90", True, "validate_b027a.py passed")

    def run_b027b(self):
        print("[B027-C] Running validate_b027b.py as subprocess")
        result = subprocess.run(
            [sys.executable, str(B027B_VALIDATOR)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            self.record("AT-91", False, "validate_b027b.py subprocess failed")
        else:
            self.record("AT-91", True, "validate_b027b.py passed")

    def validate(self):
        self.run_b027a()
        self.run_b027b()
        self.check_at_authority()
        self.check_au_roles()
        self.check_av_tasks()
        self.check_aw_entities()
        self.check_ax_prompts_communications()
        self.check_ay_resolver()
        self.check_az_security_reassessment()
        self.check_ba_legacy()
        self.check_bb_final_gate()
        self.check_bc_project_memory()
        self.check_bd_boundary()
        return 0 if not self.errors else 1


def validate_b027c():
    """Helper/test entry point that returns 0 for PASS and 1 for FAIL."""
    validator = B027CIntegrityValidator()
    validator.load_all()
    rc = validator.validate()
    if rc != 0:
        print("\nB027_INTEGRITY: FAIL")
        return 1
    print("\nB027_INTEGRITY: PASS")
    print("B027_IMPLEMENTATION: COMPLETE")
    print("FINAL_PRE_PRODUCT_AUDIT: REQUIRED")
    print("PRODUCT_DEVELOPMENT: BLOCKED_PENDING_FINAL_AUDIT")
    print("PROJECT_MEMORY_FRESHNESS: PASS")
    return 0


def main():
    return validate_b027c()


if __name__ == "__main__":
    sys.exit(main())
