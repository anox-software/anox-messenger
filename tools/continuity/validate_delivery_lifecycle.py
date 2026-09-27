import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import validate_continuity as continuity

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workforce"))
from state_gate_resolver import check_path_enforcement

STATE_PATH = "docs/continuity/CURRENT_STATE.json"
WORKFORCE_PATH = "docs/workforce/WORKFORCE_STATE.json"
TASKS_PATH = "docs/workforce/registries/tasks.jsonl"
BOOTSTRAP_PATHS = (
    "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md",
    "docs/authority/AUTHORITY_INDEX.md",
    "docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md",
    "docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md",
)
RULE_ANCHORS = ("merge-safe-delivery-finalization-invariant", "on-demand-handoff-generation")


class Blocked(Exception):
    pass


def run(root, args, env=None):
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    clean_env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1")
    clean_env.update(env or {})
    result = subprocess.run(args, cwd=root, env=clean_env, capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise Blocked(f'{args[0]} {args[1]} failed: {result.stdout}\n{result.stderr}')
    return result.stdout.strip()


def git(root, *args, env=None):
    return run(root, ["git", *args], env=env)


def fingerprint(root):
    return tuple(git(root, *args) for args in (
        ("rev-parse", "HEAD"), ("symbolic-ref", "HEAD"), ("show-ref",),
        ("status", "--porcelain=v1", "--untracked-files=all"), ("ls-files", "--stage"),
        ("worktree", "list", "--porcelain"), ("remote", "-v"),
    ))


def bootstrap_errors(root):
    try:
        bootstrap, index, policy, b026 = [(root / p).read_text() for p in BOOTSTRAP_PATHS]
    except OSError as exc:
        return [str(exc)]
    errors = []
    if BOOTSTRAP_PATHS[1] not in bootstrap or "DEVELOPMENT_SECURITY_WORKFLOW_V1.md" not in index:
        errors.append("bootstrap must resolve development governance through AUTHORITY_INDEX")
    for anchor in RULE_ANCHORS:
        link = f"../authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md#{anchor}"
        if link not in bootstrap:
            errors.append(f"missing bootstrap policy link: {anchor}")
        if f"DEVELOPMENT_SECURITY_WORKFLOW_V1.md#{anchor}" not in b026:
            errors.append(f"missing B026 canonical policy reference: {anchor}")
        headings = re.findall(r"^## (.+)$", policy, re.MULTILINE)
        if anchor not in {heading.lower().replace(" ", "-") for heading in headings}:
            errors.append(f"missing canonical policy section: {anchor}")
    if bootstrap.find(BOOTSTRAP_PATHS[1]) > bootstrap.find(RULE_ANCHORS[0]):
        errors.append("policy discovery must follow AUTHORITY_INDEX")
    return errors


def changed_paths(root, start, tip):
    paths = set(git(root, "diff", "--no-renames", "--name-only", "-z", start, tip).split("\0"))
    for commit in git(root, "rev-list", f"{start}..{tip}").splitlines():
        parents = git(root, "rev-list", "--parents", "-n", "1", commit).split()[1:]
        for parent in parents:
            paths.update(git(root, "diff", "--no-renames", "--name-only", "-z", parent, commit).split("\0"))
    return sorted(paths - {""})


def require(condition, reason):
    if not condition:
        raise Blocked(reason)


def check_metadata(state, workforce, task):
    for key in ("canonical_branch", "delivery_branch", "described_head"):
        require(state.get(key) == workforce.get(key), f"continuity/workforce {key} mismatch")
    for prefix in ("pre", "post"):
        block = workforce.get(f"{prefix}_merge_state", {})
        require(block.get("described_head") == state["described_head"], f"{prefix} transaction anchor mismatch")
        require(block.get("current_gate") == state.get(f"{prefix}_merge_gate"), f"{prefix} effective gate mismatch")
    require(workforce.get("current_gate") == state.get("pre_merge_gate"), "top-level workforce gate is stale")
    writer = workforce.get("current_writer")
    require(isinstance(writer, dict) and writer.get("task_id") == task["task_id"]
            and writer.get("branch") == task["branch"], "current writer does not match delivery task")
    post = workforce["post_merge_state"]
    require(post.get("current_writer") is None and post.get("active_task") is None,
            "post-merge state retains active writer/task")


def continuity_check(root, env):
    return run(root, [sys.executable, "tools/continuity/validate_continuity.py", "--mode", "live"], env)


def validate(root, task_id, finalize=False):
    root = Path(root).resolve()
    result = {key: "FAIL" for key in (
        "DELIVERY_BRANCH_VALIDATION", "SYNTHETIC_POST_MERGE_VALIDATION",
        "MERGE_SAFE_METADATA_STATE", "AUTHORIZED_SCOPE_ONLY",
    )}
    result.update(PUSH_READINESS="BLOCKED", WORKING_TREE="UNKNOWN", correction="NOT_EXECUTED")
    before = None
    correction = None
    original = None
    try:
        require(continuity.git_is_worktree(cwd=root), "source is not a Git worktree root")
        status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
        result["WORKING_TREE"] = "DIRTY" if status else "CLEAN"
        require(not status, "working tree must be clean; commit authorized changes and revalidate")
        before = fingerprint(root)
        branch = git(root, "branch", "--show-current")
        tip = git(root, "rev-parse", "HEAD")
        original = (root / STATE_PATH).read_bytes()
        state = json.loads(original)
        canonical = state["canonical_branch"]
        require(canonical != branch and state["delivery_branch"] == branch, "wrong delivery branch")
        for name in (canonical, branch):
            git(root, "check-ref-format", "--branch", name)
        base = git(root, "rev-parse", "--verify", f"refs/remotes/origin/{canonical}^{{commit}}")
        result.update(canonical_base=base, delivery_tip=tip, delivery_branch=branch)
        tasks = [json.loads(line) for line in (root / TASKS_PATH).read_text().splitlines() if line.strip()]
        matches = [t for t in tasks if t.get("task_id") == task_id]
        require(len(matches) == 1, "missing/ambiguous authorized task package")
        task = matches[0]
        require(task.get("branch") == branch, "task package declares wrong delivery branch")
        require(task.get("status") in {"Authorized", "In Progress", "Awaiting Evidence", "Awaiting Review",
                                      "Ready For Remote", "Awaiting Human Remote Action", "CI Pending", "Ready To Merge"},
                "task is not an authorized delivery")
        start = task.get("start_sha", "")
        require(continuity.is_valid_sha(start), "task start SHA is unbound")
        git(root, "merge-base", "--is-ancestor", start, tip)
        git(root, "merge-base", "--is-ancestor", start, base)
        paths = changed_paths(root, start, tip)
        enforcement = check_path_enforcement(paths, task)
        require(enforcement["result"] == "ALLOWED", f"STOP — unauthorized path / scope expansion: {enforcement}")
        result["AUTHORIZED_SCOPE_ONLY"] = "PASS"
        described = state.get("described_head")
        require(continuity.is_valid_sha(described), "invalid described_head")
        git(root, "merge-base", "--is-ancestor", described, tip)
        require(not continuity.git_is_ancestor(described, base, cwd=root),
                "described_head already belongs to canonical base; seal the current delivery checkpoint")
        workforce = json.loads((root / WORKFORCE_PATH).read_text())
        check_metadata(state, workforce, task)
        if state.get("current_gate") != "__EFFECTIVE_GATE__":
            require(finalize and state.get("current_gate") in {state.get("pre_merge_gate"), state.get("post_merge_gate")},
                    "current_gate needs deterministic placeholder finalization")
            require(check_path_enforcement([STATE_PATH], task)["result"] == "ALLOWED",
                    "STOP — correction outside authorized metadata scope")
            state["current_gate"] = "__EFFECTIVE_GATE__"
            correction = (json.dumps(state, indent=1, ensure_ascii=False) + "\n").encode()
        with tempfile.TemporaryDirectory(prefix="anox_delivery_sim_") as tmp:
            workspace = Path(tmp)
            simulation = workspace / "repository"
            simulation.mkdir()
            template = workspace / "empty-template"
            template.mkdir()
            env = {
                "HOME": tmp, "XDG_CONFIG_HOME": tmp, "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "anoX Synthetic Validation",
                "GIT_AUTHOR_EMAIL": "synthetic@example.invalid", "GIT_COMMITTER_NAME": "anoX Synthetic Validation",
                "GIT_COMMITTER_EMAIL": "synthetic@example.invalid",
            }
            git(simulation, "init", f"--template={template}", f"--initial-branch={canonical}", env=env)
            git(simulation, "fetch", "--no-tags", "--no-write-fetch-head", str(root), base, tip, env=env)
            git(simulation, "update-ref", f"refs/heads/{canonical}", base, env=env)
            git(simulation, "update-ref", f"refs/remotes/origin/{canonical}", base, env=env)
            git(simulation, "checkout", "-b", branch, tip, env=env)
            simulated_tip = tip
            if correction is not None:
                (simulation / STATE_PATH).write_bytes(correction)
                git(simulation, "add", "--", STATE_PATH, env=env)
                git(simulation, "commit", "-m", "synthetic deterministic metadata correction", env=env)
                simulated_tip = git(simulation, "rev-parse", "HEAD", env=env)
            result["delivery_validation_output"] = continuity_check(simulation, env)
            result["DELIVERY_BRANCH_VALIDATION"] = "PASS"
            git(simulation, "checkout", canonical, env=env)
            git(simulation, "merge", "--no-ff", "--no-edit", "-m", "synthetic normal delivery merge", branch, env=env)
            parents = git(simulation, "rev-list", "--parents", "-n", "1", "HEAD", env=env).split()[1:]
            require(parents == [base, simulated_tip], "synthetic merge has unexpected topology")
            result["synthetic_parents"] = parents
            result["post_merge_validation_output"] = continuity_check(simulation, env)
            result["SYNTHETIC_POST_MERGE_VALIDATION"] = "PASS"
        require(fingerprint(root) == before, "source repository changed during simulation; result invalid")
        if correction is not None:
            require((root / STATE_PATH).read_bytes() == original, "metadata changed concurrently")
            (root / STATE_PATH).write_bytes(correction)
            result.update(correction="APPLIED_COMMIT_AND_REVALIDATE", WORKING_TREE="DIRTY")
            result["reason"] = "metadata correction passed both simulated contexts; commit it and rerun; current delivery is not push-ready"
        else:
            result.update(MERGE_SAFE_METADATA_STATE="PASS", PUSH_READINESS="READY")
    except (Blocked, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        result["reason"] = str(exc)
    finally:
        if before is not None and correction is None:
            try:
                require(fingerprint(root) == before, "source repository changed during validation")
            except (Blocked, OSError, subprocess.TimeoutExpired) as exc:
                result.update(PUSH_READINESS="BLOCKED", MERGE_SAFE_METADATA_STATE="FAIL", reason=str(exc))
    return result


def main():
    parser = argparse.ArgumentParser(description="Offline delivery preflight; never pushes or merges real main.")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--finalize-metadata", action="store_true")
    args = parser.parse_args()
    result = validate(Path(__file__).resolve().parents[2], args.task_id, args.finalize_metadata)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["PUSH_READINESS"] == "READY" else 1


if __name__ == "__main__":
    sys.exit(main())
