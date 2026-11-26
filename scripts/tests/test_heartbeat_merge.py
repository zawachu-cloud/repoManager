"""Tests for scripts/heartbeat_merge.py (stdlib unittest). Run: python3 -m unittest discover -s scripts/tests"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from heartbeat_merge import LINE_OK, apply_merges, render_pending, tidy_body  # noqa: E402

A = "🟡 Medium: [決策] 第一則決策,內容夠長。"
B = "🟡 Medium: [決策] 第二則決策,和第一則重複。"
C = "🔴 High: [約束] 一條不相干的硬性約束。"
D = "🟢 Low: [發現] 一則流水記錄內容。"
NEW = "🟡 Medium: [決策] 合併後的決策,保留待決事項。"


def body(*entries: tuple[str, list[str]]) -> str:
    return "\n" + "\n".join(f"Date: {d}\n\n" + "\n".join(lines) + "\n" for d, lines in entries)


def no_redact(s: str) -> str:
    return s


def redact_secret(s: str) -> str:
    return re.sub(r"sk-\w+", "[REDACTED]", s)


class LineOkTest(unittest.TestCase):
    def test_accepts_and_rejects(self):
        self.assertTrue(LINE_OK.match(A))
        self.assertFalse(LINE_OK.match("沒有格式的一行"))
        self.assertFalse(LINE_OK.match("🟡 Medium: [決策] 短"))


class TidyBodyTest(unittest.TestCase):
    def test_removes_empty_date_header_and_extra_blank_lines(self):
        text = "\nDate: 2026-01-01\n\n\nDate: 2026-01-02\n\n" + A + "\n"
        self.assertEqual(tidy_body(text), "\nDate: 2026-01-02\n\n" + A + "\n")

    def test_removes_trailing_empty_header(self):
        text = "\nDate: 2026-01-01\n\n" + A + "\n\nDate: 2026-01-02\n\n"
        out = tidy_body(text)
        self.assertNotIn("2026-01-02", out)
        self.assertIn(A, out)

    def test_untouched_when_clean(self):
        text = body(("2026-01-01", [A, B]), ("2026-01-02", [C]))
        self.assertEqual(tidy_body(text), text)


class ApplyMergesTest(unittest.TestCase):
    def setUp(self):
        self.text = body(("2026-01-01", [A, C]), ("2026-01-02", [B, D]))

    def test_merge_places_new_at_earliest_old_and_removes_rest(self):
        out, n, skipped = apply_merges(self.text, [{"old": [B, A], "new": NEW}], no_redact)
        self.assertEqual((n, skipped), (1, []))
        self.assertEqual(out, body(("2026-01-01", [NEW, C]), ("2026-01-02", [D])))

    def test_delete_when_new_empty_and_empty_header_cleaned(self):
        text = body(("2026-01-01", [A]), ("2026-01-02", [B]))
        out, n, skipped = apply_merges(text, [{"old": [A], "new": ""}], no_redact)
        self.assertEqual(n, 1)
        self.assertNotIn("2026-01-01", out)
        self.assertIn(B, out)

    def test_old_matching_is_stripped(self):
        out, n, _ = apply_merges(self.text, [{"old": ["  " + A + " "], "new": NEW}], no_redact)
        self.assertEqual(n, 1)
        self.assertIn(NEW, out)
        self.assertNotIn(A, out)

    def test_skip_empty_old(self):
        out, n, skipped = apply_merges(self.text, [{"old": [], "new": NEW}], no_redact)
        self.assertEqual((out, n, len(skipped)), (self.text, 0, 1))

    def test_skip_when_old_line_missing(self):
        out, n, skipped = apply_merges(self.text, [{"old": [A, "🟡 Medium: [決策] 不存在的一行內容"], "new": NEW}], no_redact)
        self.assertEqual((out, n, len(skipped)), (self.text, 0, 1))

    def test_skip_partial_line_match(self):
        out, n, skipped = apply_merges(self.text, [{"old": [A[:-3]], "new": NEW}], no_redact)
        self.assertEqual((out, n, len(skipped)), (self.text, 0, 1))

    def test_same_line_cannot_be_used_twice(self):
        merges = [{"old": [A, B], "new": NEW}, {"old": [A, C], "new": NEW.replace("合併後", "另一個")}]
        out, n, skipped = apply_merges(self.text, merges, no_redact)
        self.assertEqual(n, 1)
        self.assertEqual(len(skipped), 1)
        self.assertIn(C, out)  # second merge skipped entirely

    def test_invalid_new_format_skipped_others_applied(self):
        merges = [{"old": [A], "new": "格式不符的一行"}, {"old": [C], "new": NEW}]
        out, n, skipped = apply_merges(self.text, merges, no_redact)
        self.assertEqual(n, 1)
        self.assertEqual(len(skipped), 1)
        self.assertIn(A, out)
        self.assertNotIn(C, out)

    def test_new_with_redacted_skipped(self):
        new = "🟡 Medium: [決策] 使用 sk-abc123 的金鑰設定"
        out, n, skipped = apply_merges(self.text, [{"old": [A], "new": new}], redact_secret)
        self.assertEqual((out, n, len(skipped)), (self.text, 0, 1))

    def test_new_with_newline_skipped(self):
        out, n, skipped = apply_merges(self.text, [{"old": [A], "new": NEW + "\n" + NEW}], no_redact)
        self.assertEqual((out, n), (self.text, 0))

    def test_malformed_items_skipped(self):
        merges = ["字串", {"old": "不是清單", "new": NEW}, {"old": [A], "new": 5}, {"old": [1], "new": NEW}]
        out, n, skipped = apply_merges(self.text, merges, no_redact)
        self.assertEqual((out, n, len(skipped)), (self.text, 0, 4))

    def test_no_merges(self):
        self.assertEqual(apply_merges(self.text, [], no_redact), (self.text, 0, []))


class RenderPendingTest(unittest.TestCase):
    CAND = {"file": "USER.md", "section": "工作偏好", "text": "新規則一行", "reason": "常常出現", "evidence": "a.md", "impact": "AI 之後會先問再改"}

    def test_empty_returns_empty_string(self):
        self.assertEqual(render_pending("2026-01-07", [], []), "")

    def test_candidate_has_impact_line_before_reason(self):
        out = render_pending("2026-01-07", [self.CAND], [])
        lines = out.splitlines()
        self.assertIn("## 2026-01-07 週三回顧", out)
        self.assertIn("- [ ] **規則候選** → `rules/USER.md` §工作偏好:新規則一行", out)
        i = lines.index("  - 影響:AI 之後會先問再改")
        self.assertTrue(lines[i + 1].startswith("  - 理由:常常出現"))
        self.assertNotIn("記憶整理", out)

    def test_questions_only(self):
        out = render_pending("2026-01-07", [], ["line 專案的路徑是?"])
        self.assertIn("- [ ] **問題**:line 專案的路徑是?\n", out)
        self.assertNotIn("規則候選", out)


if __name__ == "__main__":
    unittest.main()
