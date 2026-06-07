import os
import pathlib
import py_compile
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
HARNESS_DIR = REPO_ROOT / "harness" / "scripts"
DOCS_DIR = REPO_ROOT / "docs"


class TestRepositoryValidation(unittest.TestCase):
    def test_skill_scripts_compile(self):
        files = [
            HARNESS_DIR / "skill_state.py",
            HARNESS_DIR / "skill_plan.py",
            HARNESS_DIR / "skill_docker.py",
            HARNESS_DIR / "skill_commit_push.py",
        ]
        for source in files:
            with self.subTest(source=source):
                py_compile.compile(str(source), doraise=True)

    def test_docs_use_new_skill_script_paths(self):
        paths = [
            "python3 harness/scripts/skill_state.py",
            "python3 harness/scripts/skill_plan.py",
            "bash harness/scripts/skill_memory.sh",
            "python3 harness/scripts/skill_docker.py",
            "python3 harness/scripts/skill_commit_push.py",
        ]
        old_paths = [
            "harness/skill_state.py",
            "harness/skill_plan.py",
            "harness/skill_memory.sh",
            "harness/skill_docker.py",
            "harness/skill_commit_push.py",
        ]
        files = [
            DOCS_DIR / "copilot-instructions.md",
            HARNESS_DIR.parent / "README.md",
            HARNESS_DIR.parent / "docs" / "COPILOT_SKILL.md",
        ]
        for file_path in files:
            text = file_path.read_text(encoding="utf-8")
            for path in paths:
                with self.subTest(file=file_path, expected_path=path):
                    self.assertIn(path, text)
            for old_path in old_paths:
                with self.subTest(file=file_path, old_path=old_path):
                    self.assertNotIn(old_path, text)

    def test_docs_references_current_docs_location(self):
        text = (DOCS_DIR / "copilot-instructions.md").read_text(encoding="utf-8")
        self.assertIn("docs/HERMES_TELEGRAM_INSTALL_PLAN.md", text)
        self.assertNotIn("`HERMES_TELEGRAM_INSTALL_PLAN.md`", text)
        n8n_text = (DOCS_DIR / "N8N.md").read_text(encoding="utf-8")
        self.assertIn("docs/N8N.md", n8n_text)

    def test_required_docs_exist(self):
        required = [
            REPO_ROOT / "README.md",
            REPO_ROOT / "CONTRIBUTING.md",
            DOCS_DIR / "README.md",
            DOCS_DIR / "copilot-instructions.md",
            DOCS_DIR / "HERMES_TELEGRAM_INSTALL_PLAN.md",
            DOCS_DIR / "N8N.md",
            HARNESS_DIR.parent / "README.md",
            HARNESS_DIR.parent / "docs" / "COPILOT_SKILL.md",
        ]
        for file_path in required:
            with self.subTest(file=file_path):
                self.assertTrue(file_path.exists(), f"Required file missing: {file_path}")


if __name__ == "__main__":
    unittest.main()
