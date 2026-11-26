"""Tests for apply_projects multi-root handling in scripts/heartbeat_reflect.py.
Needs ~/proj/my/ai_session_export/src (redact module). Run: python3 -m unittest discover -s scripts/tests"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from heartbeat_reflect import PROJECTS_ROOTS, apply_projects  # noqa: E402

USER_TEXT = (
    "# USER\n\n## 目前的專案\n\n說明。\n\n"
    "- `hr`:舊的 hr 說明\n"
    "- `old`:舊專案\n\n"
    "## 工作偏好\n"
)


class ApplyProjectsRoots(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.new_root = base / "orca/projects"
        self.old_root = base / "proj/my"
        self.missing_root = base / "nope"
        for d in (self.new_root / "alpha", self.old_root / "beta", self.old_root / "hr"):
            d.mkdir(parents=True)
        self.roots = [self.new_root, self.old_root]

    def test_default_roots_are_orca_then_proj(self):
        self.assertEqual([str(r).split("/", 3)[-1] for r in PROJECTS_ROOTS], ["orca/projects", "proj/my"])

    def test_accepts_repo_in_first_root(self):
        _, changed = apply_projects(USER_TEXT, {"alpha": "新根專案"}, self.roots)
        self.assertEqual(changed, ["alpha"])

    def test_accepts_repo_in_second_root(self):
        new_text, changed = apply_projects(USER_TEXT, {"beta": "舊根專案"}, self.roots)
        self.assertEqual(changed, ["beta"])
        self.assertIn("- `beta`:舊根專案\n", new_text)

    def test_updates_existing_line(self):
        new_text, changed = apply_projects(USER_TEXT, {"hr": "新說明"}, self.roots)
        self.assertEqual(changed, ["hr"])
        self.assertIn("- `hr`:新說明\n", new_text)
        self.assertNotIn("舊的 hr 說明", new_text)

    def test_rejects_repo_in_no_root(self):
        new_text, changed = apply_projects(USER_TEXT, {"ghost": "不存在"}, self.roots)
        self.assertEqual(changed, [])
        self.assertEqual(new_text, USER_TEXT)

    def test_tolerates_missing_root(self):
        _, changed = apply_projects(USER_TEXT, {"beta": "x專案說明"}, [self.missing_root, self.old_root])
        self.assertEqual(changed, ["beta"])

    def test_all_roots_missing(self):
        _, changed = apply_projects(USER_TEXT, {"beta": "x"}, [self.missing_root])
        self.assertEqual(changed, [])

    def test_rejects_path_traversal_name(self):
        _, changed = apply_projects(USER_TEXT, {"../my/beta": "x專案說明"}, self.roots)
        self.assertEqual(changed, [])

    def test_file_not_dir_rejected(self):
        (self.new_root / "afile").write_text("x")
        _, changed = apply_projects(USER_TEXT, {"afile": "x專案說明"}, self.roots)
        self.assertEqual(changed, [])


if __name__ == "__main__":
    unittest.main()
