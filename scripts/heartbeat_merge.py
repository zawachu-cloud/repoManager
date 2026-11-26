"""Pure helpers for the weekly reflector: tidy OBSERVATIONS body, apply merges.

No import of heartbeat.py (it needs the external redact module at import time).
Tests: scripts/tests/test_heartbeat_merge.py
"""

from __future__ import annotations

import re
from typing import Callable

LINE_OK = re.compile(r"^(🔴 High|🟡 Medium|🟢 Low): \[[^\]]{1,20}\] .{4,400}$")


def tidy_body(text: str) -> str:
    """Drop Date headers left with no items, then collapse runs of blank lines."""
    text = re.sub(r"(?m)^Date: \d{4}-\d{2}-\d{2}[^\n]*\n(?:[ \t]*\n)*(?=Date: |\Z)", "", text)
    return re.sub(r"\n{3,}", "\n\n", text)


def _check_merge(merge: object, line_index: dict[str, list[int]], used: set[str],
                 redact: Callable[[str], str]) -> tuple[list[str], str] | str:
    """Return (old_lines, new_line) when valid, else a skip reason."""
    if not isinstance(merge, dict):
        return "不是物件"
    old, new = merge.get("old"), merge.get("new", "")
    if not isinstance(old, list) or not old or not all(isinstance(o, str) for o in old):
        return "old 必須是非空的字串清單"
    if not isinstance(new, str):
        return "new 必須是字串"
    olds = [o.strip() for o in old]
    if any(not o for o in olds):
        return "old 含空行"
    missing = [o for o in olds if o not in line_index]
    if missing:
        return f"old 不是記錄區的完整一行:{missing[0][:40]}"
    if any(o in used for o in olds):
        return f"old 已被其他合併使用:{olds[0][:40]}"
    new = new.strip()
    if new:
        if "\n" in new:
            return "new 含換行"
        new = redact(new)
        if "[REDACTED]" in new or not LINE_OK.match(new):
            return f"new 格式不符或含機密:{new[:40]}"
    return list(dict.fromkeys(olds)), new


def apply_merges(body: str, merges: list, redact: Callable[[str], str]) -> tuple[str, int, list[str]]:
    """Apply merges to the record-region body. Invalid merges are skipped one by one.

    Returns (new_body, applied_count, skip_reasons). `new` goes where the earliest `old`
    line was; other old lines are deleted; empty `new` just deletes.
    """
    lines = body.splitlines(keepends=True)
    line_index: dict[str, list[int]] = {}
    for i, line in enumerate(lines):
        if line.strip():
            line_index.setdefault(line.strip(), []).append(i)
    used: set[str] = set()
    replace: dict[int, str] = {}  # index -> replacement line ("" = delete)
    applied, skipped = 0, []
    for merge in merges or []:
        checked = _check_merge(merge, line_index, used, redact)
        if isinstance(checked, str):
            skipped.append(checked)
            continue
        olds, new = checked
        indices = sorted(i for o in olds for i in line_index[o])
        for i in indices:
            replace[i] = ""
        if new:
            replace[indices[0]] = new + "\n"
        used.update(olds)
        applied += 1
    if not applied:
        return body, 0, skipped
    return tidy_body("".join(replace.get(i, line) for i, line in enumerate(lines))), applied, skipped


def render_pending(today: str, cands: list[dict], questions: list[str]) -> str:
    """Markdown section for pending-review.md; empty string when there is nothing to ask."""
    if not cands and not questions:
        return ""
    parts = [f"\n## {today} 週三回顧\n"]
    for c in cands:
        parts.append(f"- [ ] **規則候選** → `rules/{c.get('file', '?')}` §{c.get('section', '?')}:{c['text']}\n"
                     f"  - 影響:{c.get('impact', '')}\n"
                     f"  - 理由:{c.get('reason', '')}(依據:{c.get('evidence', '')})\n")
    for q in questions:
        parts.append(f"- [ ] **問題**:{q}\n")
    return "".join(parts)
