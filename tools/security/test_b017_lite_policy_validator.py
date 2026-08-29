#!/usr/bin/env python3
"""Unit tests for the B-017-Lite policy validator.

Covers the original 18 independent-review bypass cases, the additional bypass
cases discovered in the R3 retest, and a real-workflow-style integration test.
"""

import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

try:
    import b017_lite_policy_validator as pv
except ImportError:
    from tools.security import b017_lite_policy_validator as pv

GOOD_SHA = "a" * 40
DOCKER_DIGEST = (
    "docker://alpine@sha256:"
    "a8451eeda314d0568b5340498b36edf147a8f0d692c5ff58082d477abe9146e4"
)


def _workflow(style="B", extra=""):
    """Return a minimal workflow using either the real step style (B) or the
    list-dash compact style (A).
    """
    if style == "A":
        steps = (
            "    steps:\n"
            f"      - uses: actions/checkout@{GOOD_SHA} # v4\n" + extra
        )
    else:
        steps = (
            "    steps:\n"
            "      - name: Checkout\n"
            f"        uses: actions/checkout@{GOOD_SHA} # v4\n" + extra
        )
    return (
        "on:\n"
        "  push:\n"
        "    branches: [main]\n"
        "\n"
        "permissions:\n"
        "  contents: read\n"
        "\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n" + steps
    )


class B017LitePolicyValidatorTests(unittest.TestCase):
    def setUp(self):
        self.original_repo_root = pv.REPO_ROOT
        self.td = Path(tempfile.mkdtemp(prefix="b017_lite_test_"))
        pv.REPO_ROOT = self.td

    def tearDown(self):
        pv.REPO_ROOT = self.original_repo_root
        shutil.rmtree(self.td, ignore_errors=True)

    def _write_good_files(self, wf=None):
        wf = wf or _workflow("B")
        (self.td / ".github" / "workflows").mkdir(parents=True)
        (self.td / ".github" / "workflows" / "ci.yml").write_text(wf, encoding="utf-8")

        (self.td / "gradle" / "wrapper").mkdir(parents=True)
        (self.td / "gradle" / "wrapper" / "gradle-wrapper.properties").write_text(
            "distributionUrl=https\\://services.gradle.org/distributions/gradle-9.3.1-bin.zip\n"
            "distributionSha256Sum=b266d5ff6b90eada6dc3b20cb090e3731302e553a27c5d3e4df1f0d76beaff06\n"
            "validateDistributionUrl=true\n",
            encoding="utf-8",
        )

        (self.td / "build.gradle.kts").write_text(
            "plugins { id(\"com.android.application\") version \"8.13.2\" }\n"
            "dependencies { implementation(\"androidx.core:core-ktx:1.12.0\") }\n",
            encoding="utf-8",
        )

        (self.td / "settings.gradle.kts").write_text(
            "dependencyResolutionManagement {\n"
            "  repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)\n"
            "  repositories {\n"
            "    google()\n"
            "    mavenCentral()\n"
            "    gradlePluginPortal()\n"
            "  }\n"
            "}\n",
            encoding="utf-8",
        )

        (self.td / "crypto" / "rust").mkdir(parents=True)
        (self.td / "crypto" / "rust" / "Cargo.toml").write_text(
            "[package]\nname = \"anox_crypto\"\nversion = \"0.1.0\"\n\n"
            "[dependencies]\n"
            "vodozemac = \"0.10.0\"\n"
            "serde = { version = \"1.0\", features = [\"derive\"] }\n",
            encoding="utf-8",
        )
        (self.td / "crypto" / "rust" / "Cargo.lock").write_text(
            "version = 4\n", encoding="utf-8"
        )
        (self.td / ".gitignore").write_text("/local.properties\n", encoding="utf-8")

    def _run(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = pv.main()
        return rc, buf.getvalue()

    # ---- POSITIVE / SANITY ----

    def test_all_good_passes_style_b(self):
        self._write_good_files()
        self.assertEqual(self._run()[0], 0)

    def test_all_good_passes_style_a(self):
        self._write_good_files(_workflow("A"))
        self.assertEqual(self._run()[0], 0)

    def test_docker_sha_digest_passes(self):
        self._write_good_files(
            _workflow("B").replace(
                f"actions/checkout@{GOOD_SHA} # v4",
                DOCKER_DIGEST,
                1,
            )
        )
        self.assertEqual(self._run()[0], 0)

    def test_local_action_passes(self):
        self._write_good_files(
            _workflow("B").replace(
                f"actions/checkout@{GOOD_SHA} # v4",
                "./.github/actions/local",
                1,
            )
        )
        self.assertEqual(self._run()[0], 0)

    # ---- ORIGINAL 18 ----

    def test_001_workflow_permissions_write_all(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace("permissions:\n  contents: read", "permissions: write-all"),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_002_job_permissions_write_all(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace(
                "    runs-on: ubuntu-latest",
                "    runs-on: ubuntu-latest\n    permissions: write-all",
            ),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_003_pull_requests_write(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace("  contents: read", "  contents: read\n  pull-requests: write"),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_004_id_token_write(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace("  contents: read", "  contents: read\n  id-token: write"),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_005_actions_write(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace("  contents: read", "  contents: read\n  actions: write"),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_006_pull_request_target_inline(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace(
                "on:\n  push:\n    branches: [main]",
                "on:\n  pull_request_target: {branches: [main]}",
            ),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_007_pull_request_target_list(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace(
                "on:\n  push:\n    branches: [main]",
                "on: [pull_request_target]",
            ),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_008_workflow_run_inline(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace(
                "on:\n  push:\n    branches: [main]",
                "on:\n  workflow_run: {workflows: [CI], types: [completed]}",
            ),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_009_unpinned_action_in_yaml(self):
        self._write_good_files()
        (self.td / ".github" / "workflows" / "evil.yaml").write_text(
            _workflow("B").replace(
                f"actions/checkout@{GOOD_SHA} # v4", "actions/checkout@v4"
            ),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_010_mutable_docker_image_tag(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace(f"actions/checkout@{GOOD_SHA} # v4", "docker://alpine:latest"),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_011_gradle_dynamic_version_1_dot_plus(self):
        self._write_good_files()
        build = self.td / "build.gradle.kts"
        text = build.read_text(encoding="utf-8")
        build.write_text(text.replace(":1.12.0\"", ":1.+\""), encoding="utf-8")
        self.assertEqual(self._run()[0], 1)

    def test_012_gradle_version_range(self):
        self._write_good_files()
        build = self.td / "build.gradle.kts"
        text = build.read_text(encoding="utf-8")
        build.write_text(text.replace(":1.12.0\"", ":[1.12,2.0)\""), encoding="utf-8")
        self.assertEqual(self._run()[0], 1)

    def test_013_groovy_http_repository(self):
        self._write_good_files()
        settings = self.td / "settings.gradle.kts"
        text = settings.read_text(encoding="utf-8")
        settings.write_text(
            text.replace("google()", 'maven { url "http://evil.example/m2" }\n    google()'),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_014_gradle_seturl_http(self):
        self._write_good_files()
        settings = self.td / "settings.gradle.kts"
        text = settings.read_text(encoding="utf-8")
        settings.write_text(
            text.replace("google()", 'maven { setUrl("http://evil.example/m2") }\n    google()'),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_015_unauthorized_https_maven_repo(self):
        self._write_good_files()
        settings = self.td / "settings.gradle.kts"
        text = settings.read_text(encoding="utf-8")
        settings.write_text(
            text.replace("google()", 'maven { url = uri("https://evil.example/m2") }\n    google()'),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_016_cargo_bare_git_dep(self):
        self._write_good_files()
        cargo = self.td / "crypto" / "rust" / "Cargo.toml"
        text = cargo.read_text(encoding="utf-8")
        cargo.write_text(
            text.replace('vodozemac = "0.10.0"', 'vodozemac = { git = "https://evil.example/v.git" }'),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_017_cargo_git_dep_reordered_keys(self):
        self._write_good_files()
        cargo = self.td / "crypto" / "rust" / "Cargo.toml"
        text = cargo.read_text(encoding="utf-8")
        cargo.write_text(
            text.replace(
                'vodozemac = "0.10.0"',
                'vodozemac = { branch = "main", git = "https://evil.example/v.git" }',
            ),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_018_cargo_wildcard_1_dot_star(self):
        self._write_good_files()
        cargo = self.td / "crypto" / "rust" / "Cargo.toml"
        text = cargo.read_text(encoding="utf-8")
        cargo.write_text(text.replace('vodozemac = "0.10.0"', 'vodozemac = "1.*"'), encoding="utf-8")
        self.assertEqual(self._run()[0], 1)

    # ---- R3 ADDITIONAL BYPASSES ----

    def test_019_mutable_tag_v4_in_production_style(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace(f"actions/checkout@{GOOD_SHA} # v4", "actions/checkout@v4"),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_020_branch_ref_main_in_production_style(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace(f"actions/checkout@{GOOD_SHA} # v4", "evil/action@main"),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_021_short_malformed_sha_production_style(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace(f"actions/checkout@{GOOD_SHA} # v4", "actions/checkout@11d5960"),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_022_unpinned_action_no_at(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace(f"actions/checkout@{GOOD_SHA} # v4", "evil/action"),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_023_uppercase_hex_sha(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace(GOOD_SHA, "A" * 40),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_024_inline_mapping_permissions(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace("permissions:\n  contents: read", "permissions: {contents: write}"),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_025_quoted_permission_key(self):
        self._write_good_files()
        wf = (self.td / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        (self.td / ".github" / "workflows" / "ci.yml").write_text(
            wf.replace("  contents: read", '  "contents": write'),
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    def test_026_gradle_3part_dynamic_1_2_plus(self):
        self._write_good_files()
        build = self.td / "build.gradle.kts"
        text = build.read_text(encoding="utf-8")
        build.write_text(text.replace(":1.12.0\"", ":1.2.+\""), encoding="utf-8")
        self.assertEqual(self._run()[0], 1)

    def test_027_gradle_3component_range(self):
        self._write_good_files()
        build = self.td / "build.gradle.kts"
        text = build.read_text(encoding="utf-8")
        build.write_text(text.replace(":1.12.0\"", ":[1.0.0,2.0.0)\""), encoding="utf-8")
        self.assertEqual(self._run()[0], 1)

    def test_028_cargo_subtable_bare_git(self):
        self._write_good_files()
        cargo = self.td / "crypto" / "rust" / "Cargo.toml"
        text = cargo.read_text(encoding="utf-8")
        cargo.write_text(
            text + '\n[dependencies.evil]\ngit = "https://example.invalid/repo.git"\n',
            encoding="utf-8",
        )
        self.assertEqual(self._run()[0], 1)

    # ---- REAL WORKFLOW INTEGRATION ----

    def test_real_repo_workflow_is_inspected(self):
        real = (pv.original_repo_root if hasattr(pv, 'original_repo_root') else self.original_repo_root)
        real_wf = (real / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self._write_good_files()
        # overwrite test fixture with the real workflow
        (self.td / ".github" / "workflows" / "ci.yml").write_text(real_wf, encoding="utf-8")
        rc, out = self._run()
        self.assertEqual(rc, 0)
        self.assertIn("inspected:", out)
        self.assertRegex(out, r"inspected: \d+ total, \d+ external")

    def test_real_repo_workflow_mutation_fails(self):
        real = (pv.original_repo_root if hasattr(pv, 'original_repo_root') else self.original_repo_root)
        real_wf = (real / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        bad_wf = real_wf.replace(
            "actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4",
            "actions/checkout@v4",
            1,
        )
        self._write_good_files()
        (self.td / ".github" / "workflows" / "ci.yml").write_text(bad_wf, encoding="utf-8")
        self.assertEqual(self._run()[0], 1)

    def test_cargo_lock_ignored_fails(self):
        self._write_good_files()
        (self.td / ".gitignore").write_text("/crypto/rust/Cargo.lock\n", encoding="utf-8")
        self.assertEqual(self._run()[0], 1)


if __name__ == "__main__":
    unittest.main()
