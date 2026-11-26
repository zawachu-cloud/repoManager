#!/usr/bin/env python3
"""Memory heartbeat: daily observer + weekly reflector (context system phase 4).

  heartbeat.py observe [--dry-run]          # L1: new/changed sessions since last run -> OBSERVATIONS.md
  heartbeat.py reflect [--force] [--dry-run]  # L2: GC old 🟢, merge notes, update USER.md project lines, write candidates

Files: this file = observe + CLI; heartbeat_reflect.py = weekly reflector; heartbeat_common.py = paths,
state, kiro runner, gitleaks, commit; heartbeat_merge.py = pure merge/tidy helpers.

The LLM (Kiro agent `heartbeat`: read/grep/glob only) never writes files. It prints its
result between markers; this script validates, redacts, gitleaks-checks, writes, and
commits only the touched files in repoManager. Kiro sessions it creates run with cwd
~/.local/share/ai-heartbeat, which session-export.sh excludes from the archive.

Design: repoManager docs/context-system.md §4c.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from heartbeat_common import (
    HOME, OBS, all_sessions, clean_lines, commit, gitleaks_clean, load_state, log, meta, run_kiro, save_state,
)
from heartbeat_reflect import cmd_reflect


OBSERVE_PROMPT = """任務:L1 每日觀察。基準日期 {today}。

下面是自上次觀察後新增或更新的 AI 對話存檔(Markdown;zawa 和 AI 的對話,機密已遮成 [REDACTED])。
請自己用 read / grep 讀內容。檔案可能很長,先看開頭與 `## User` 段落,再挑重點讀,不必逐字讀完。

{files}

已有的記憶在 {obs}。動筆前先 grep 它,**已經記過的事不要重記**。

寫出值得跨 session 記住的觀察,每行一則,格式嚴格如下(不要日期標題,不要其他文字):
🔴 High: [分類] 描述   ← 跨專案通用的經驗、硬性約束、重大架構決策
🟡 Medium: [分類] 描述 ← 專案的關鍵進展、決策與理由,未來幾週還要參考
🟢 Low: [分類] 描述    ← 值得留一下的流水

規則:
- [分類] 用 2~6 個字,例如 [決策]、[約束]、[發現]、[專案狀態]、[偏好]。
- 描述要具體,提到專案時寫 repo 名(例如 hr、psapi-dotnet),一行 200 字以內。
- 記「做了什麼決定、為什麼、學到什麼、zawa 的偏好」,不記操作細節。
- zawa 表現出的新偏好或不喜歡的做法,用 🔴 或 🟡 + [偏好] 記下。
- 絕不寫金鑰、密碼、token、IP、個資(員工姓名、身分證、薪資數字、帳號)。
- 總共最多 15 行;沒有值得記的就只輸出 NONE。

最後把結果放在標記之間輸出:
<<<OBS
(觀察行,或 NONE)
OBS>>>
"""


def cmd_observe(args: argparse.Namespace) -> int:
    """Change = file size differs from the last observed size (identical re-exports, e.g. --full, do not count).
    First run: everything older than yesterday is marked seen; history stays reachable through /recall."""
    state = load_state()
    seen: dict[str, int] = state.setdefault("seen_sizes", {})
    if not seen:
        cutoff = (date.today() - timedelta(days=1)).isoformat()
        for p in all_sessions():
            if meta(p).get("date", "") < cutoff:
                seen[str(p)] = p.stat().st_size
    files = [p for p in all_sessions() if seen.get(str(p)) != p.stat().st_size]
    if not files:
        log("沒有新的對話,略過")
        save_state(state)
        return 0
    files = files[-40:]  # cap one run; the rest stays unseen and is picked up next run
    listing = []
    for p in files:
        m = meta(p)
        listing.append(f"- {p}  ({m.get('date', '')}, {m.get('project_directory', '').replace(str(HOME), '~')}, "
                       f"{m.get('message_count', '?')} 則, {p.stat().st_size // 1024} KB) {m.get('title', '')[:60]}")
    today = date.today().isoformat()
    log(f"觀察 {len(files)} 個 session")
    raw = run_kiro(OBSERVE_PROMPT.format(today=today, files="\n".join(listing), obs=OBS), "OBS")
    if raw is None:
        return 1  # state not advanced: next run retries the same window
    lines = [] if raw.strip().upper() == "NONE" else clean_lines(raw)
    if raw.strip().upper() != "NONE" and not lines:
        log("輸出格式不符,未寫入;見 last-obs.log")
        return 1
    if lines:
        block = f"\nDate: {today}\n\n" + "\n".join(lines) + "\n"
        if not gitleaks_clean(block):
            log("gitleaks 在觀察結果裡有命中,未寫入")
            return 2
        if args.dry_run:
            print(block)
        else:
            with OBS.open("a", encoding="utf-8") as handle:
                handle.write(block)
            commit([OBS], f"memory: observer {today} ({len(lines)} items)", args.dry_run)
    log(f"寫入 {len(lines)} 則")
    if not args.dry_run:
        for p in files:
            seen[str(p)] = p.stat().st_size
        save_state(state)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    o = sub.add_parser("observe")
    o.add_argument("--dry-run", action="store_true")
    o.set_defaults(func=cmd_observe)
    r = sub.add_parser("reflect")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--force", action="store_true", help="run even if today is not Wednesday")
    r.set_defaults(func=cmd_reflect)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
