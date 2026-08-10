import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_skill_content.py"


def ignore_copy(directory, names):
    ignored = {".git", "tmp", "__pycache__"}
    return [name for name in names if name in ignored]


class RepositoryGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        shutil.copytree(ROOT, self.root, ignore=ignore_copy)

    def tearDown(self):
        self.temp.cleanup()

    def validate(self):
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--root", str(self.root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
            check=False,
        )

    def mutate(self, relative_path, transform):
        path = self.root / relative_path
        original = path.read_text(encoding="utf-8")
        path.write_text(transform(original), encoding="utf-8", newline="\n")

    def assert_rejected(self, expected_message):
        result = self.validate()
        self.assertNotEqual(0, result.returncode, result.stdout)
        self.assertIn(expected_message, result.stdout + result.stderr)

    def test_clean_repository_passes(self):
        result = self.validate()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_single_generated_entry_edit_is_rejected(self):
        self.mutate("SKILL.md", lambda value: value + "\nmanual drift\n")
        self.assert_rejected("generated Skill entry is stale: SKILL.md")

    def test_missing_r4_is_rejected(self):
        self.mutate(
            "references/validation-scenarios.md",
            lambda value: value.replace("### R4：", "### RX：", 1),
        )
        self.assert_rejected("validation scenarios lack R4")

    def test_current_release_marked_beta_is_rejected(self):
        self.mutate(
            "validation/1.4.0.md",
            lambda value: value + "\n版本仍标记为 beta。\n",
        )
        self.assert_rejected("incorrectly marks the current release as beta")

    def test_broken_link_is_rejected(self):
        self.mutate("README.md", lambda value: value + "\n[broken](missing-file.md)\n")
        self.assert_rejected("broken local link in README.md")

    def test_missing_evidence_layer_is_rejected(self):
        self.mutate(
            "validation/1.4.0.md",
            lambda value: value.replace("## 4. 探针实板基线", "## 4. 其他记录", 1),
        )
        self.assert_rejected("release validation lacks evidence layer")


if __name__ == "__main__":
    unittest.main()
