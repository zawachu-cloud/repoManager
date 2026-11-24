#!/usr/bin/env python3
"""Memory heartbeat: daily observer + weekly reflector (context system phase 4).

  heartbeat.py observe [--dry-run]          # L1: new/changed sessions since last run -> OBSERVATIONS.md
  heartbeat.py reflect [--dry-run]          # L2: GC old 🟢, update USER.md project lines, write candidates

The LLM (Kiro agent `heartbeat`: read/grep/glob only) never writes files. It prints its
result between markers; this script validates, redacts, gitleaks-checks, writes, and
commits only the touched files in repoManager. Kiro sessions it creates run with cwd
~/.local/share/ai-heartbeat, which session-export.sh excludes from the archive.

Design: repoManager docs/context-system.md §4c.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

HOME = Path.home()
os.environ["PATH"] = f"{HOME}/.local/bin:" + os.environ.get("PATH", "/usr/bin:/bin")  # cron: kiro-cli, gitleaks
REPO = Path(__file__).resolve().parent.parent
OBS = REPO / "contexts/memory/OBSERVATIONS.md"
USER = REPO / "rules/USER.md"
PENDING = REPO / "contexts/memory/pending-review.md"
ARCHIVE = HOME / ".local/share/ai-session-export"
SOURCES = [ARCHIVE / "kiro", ARCHIVE / "claude_code"]
WORKDIR = HOME / ".local/share/ai-heartbeat"
STATE = WORKDIR / "state.json"
PROJECTS_ROOT = HOME / "proj/my"
FORK_SRC = HOME / "proj/my/ai_session_export/src"
GITLEAKS_CONFIG = HOME / "proj/my/ai_session_export/.gitleaks.toml"
RECORD_MARK = "<!-- 以下為記錄區,新條目追加在最後 -->"
LINE_OK = re.compile(r"^(🔴 High|🟡 Medium|🟢 Low): \[[^\]]{1,20}\] .{4,400}$")
GC_DAYS = 30
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

sys.path.insert(0, str(FORK_SRC))
try:
    from ai_session_export.redact import redact  # noqa: E402
except ImportError:  # pragma: no cover
    sys.exit(f"找不到遮罩模組 {FORK_SRC}/ai_session_export/redact.py")


# ---------- helpers ----------

def log(msg: str) -> None:
    print(f"[heartbeat {datetime.now():%F %T}] {msg}", flush=True)


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.is_file() else {}


def save_state(state: dict) -> None:
    WORKDIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1))
    tmp.replace(STATE)


FRONT = re.compile(r"^(title|date|project_directory|message_count):\s*\"?(.*?)\"?\s*$", re.M)


def meta(path: Path) -> dict:
    head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    return dict(FRONT.findall(head.split("\n---", 1)[0])) if head.startswith("---") else {}


def run_kiro(prompt: str, marker: str, timeout: int = 1800, attempts: int = 2) -> str | None:
    """Run the heartbeat agent; retry once (the service sometimes fails mid-stream)."""
    for attempt in range(1, attempts + 1):
        result = _run_kiro_once(prompt, marker, timeout)
        if result is not None:
            return result
        if attempt < attempts:
            log(f"第 {attempt} 次失敗,60 秒後重試")
            time.sleep(60)
    return None


def _run_kiro_once(prompt: str, marker: str, timeout: int) -> str | None:
    WORKDIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["kiro-cli", "chat", "--no-interactive", "--agent", "heartbeat", prompt],
        cwd=WORKDIR, capture_output=True, text=True, timeout=timeout,
    )
    out = ANSI.sub("", proc.stdout)
    (WORKDIR / f"last-{marker.lower()}.log").write_text(out[-20000:] + "\n--- stderr ---\n" + proc.stderr[-4000:])
    match = re.search(rf"<<<{marker}\s*\n?(.*?)\n?\s*{marker}>>>", out, re.S)
    if proc.returncode != 0 or not match:
        log(f"kiro 執行失敗或沒有 {marker} 標記(rc={proc.returncode}),見 {WORKDIR}/last-{marker.lower()}.log")
        return None
    return match.group(1).strip()


def gitleaks_clean(text: str) -> bool:
    proc = subprocess.run(["gitleaks", "stdin", "--no-banner", "--redact", "--config", str(GITLEAKS_CONFIG)],
                          input=text, capture_output=True, text=True)
    return proc.returncode == 0


def commit(paths: list[Path], message: str, dry_run: bool) -> None:
    if dry_run:
        return
    rel = [str(p.relative_to(REPO)) for p in paths]
    subprocess.run(["git", "-C", str(REPO), "add", "--", *rel], check=True)  # only these files
    if not subprocess.run(["git", "-C", str(REPO), "status", "--porcelain", "--", *rel],
                          capture_output=True, text=True).stdout.strip():
        return
    subprocess.run(["git", "-C", str(REPO), "commit", "-q", "-m", message, "--", *rel], check=True)
    push = subprocess.run(["git", "-C", str(REPO), "push", "-q"], capture_output=True, text=True)
    log("pushed" if push.returncode == 0 else f"push 失敗(下次 commit 會一起推):{push.stderr.strip()[-200:]}")


def clean_lines(raw: str) -> list[str]:
    lines = []
    for line in raw.splitlines():
        line = redact(line.strip().lstrip("-* ").strip())
        if LINE_OK.match(line):
            lines.append(line)
    return lines


# ---------- observe ----------

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


def changed_sessions(since_ts: float) -> list[Path]:  # used by reflect (last 7 days)
    files = [p for root in SOURCES if root.is_dir() for p in root.glob("*.md") if p.stat().st_mtime > since_ts]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def all_sessions() -> list[Path]:
    return sorted((p for root in SOURCES if root.is_dir() for p in root.glob("*.md")), key=lambda p: p.stat().st_mtime)


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


# ---------- reflect ----------

REFLECT_PROMPT = """任務:L2 每週回顧。基準日期 {today}。

請讀:
1. 記憶檔 {obs}(L1/L2 觀察,依 Date 分段)。
2. zawa 的使用者檔 {user}(每個 session 都會載入)。
3. 過去 7 天的對話存檔(需要時用 read / grep 看內容):
{files}
4. 各專案的 AGENTS.md:{projects_root}/<repo>/AGENTS.md(需要時讀)。

產出一個 JSON 物件,放在標記之間:
<<<REFLECT
{{
  "projects": {{"<repo 目錄名>": "<一行用途與目前方向,60 字以內>"}},
  "rule_candidates": [
    {{"file": "USER.md|SOUL.md|COMMUNICATION.md", "section": "<要放的段落標題>", "text": "<建議新增或修改的那一行>", "reason": "<為什麼>", "evidence": "<依據:Date 或存檔檔名>"}}
  ],
  "merge_suggestions": ["<哪幾則 🟡 可以合併或已過時,以及建議怎麼改>"]
}}
REFLECT>>>

規則:
- projects:只放 {projects_root} 下真的存在、而且你從存檔或 AGENTS.md 有依據的 repo。沒依據就不要放,不要猜。
  寫用途與方向,不寫憑證、IP、資料內容(姓名、薪資數字等)。目前的寫法:{current_projects}
- rule_candidates:反覆出現(至少兩次)的偏好或做法,而且 USER/SOUL/COMMUNICATION 還沒寫到的才提。最多 5 則。沒有就給空陣列。
- merge_suggestions:最多 5 則;沒有就空陣列。
- 只輸出標記之間的 JSON,不要 markdown 程式碼框。
"""


def record_region(text: str) -> tuple[str, str]:
    if RECORD_MARK not in text:
        return text, ""
    head, body = text.split(RECORD_MARK, 1)
    return head + RECORD_MARK, body


def gc_low(body: str, today: date) -> tuple[str, int]:
    """Drop 🟢 lines from entries older than GC_DAYS. Headers and other lines are kept."""
    out, removed, entry_date = [], 0, None
    for line in body.splitlines(keepends=True):
        match = re.match(r"^Date: (\d{4}-\d{2}-\d{2})", line)
        if match:
            entry_date = date.fromisoformat(match.group(1))
        elif line.startswith("🟢") and entry_date and (today - entry_date).days > GC_DAYS:
            removed += 1
            continue
        out.append(line)
    # drop Date headers left with no items
    cleaned = re.sub(r"\nDate: \d{4}-\d{2}-\d{2}\n\n(?=\nDate: |\Z)", "\n", "".join(out))
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned, removed


PROJECT_SECTION = re.compile(r"(## 目前的專案\n(?:.*\n)*?\n)((?:- `[^`]+`:[^\n]*\n)+)")


def current_projects(user_text: str) -> dict[str, str]:
    match = PROJECT_SECTION.search(user_text)
    if not match:
        return {}
    return dict(re.findall(r"^- `([^`]+)`:(.*)$", match.group(2), re.M))


def apply_projects(user_text: str, proposed: dict) -> tuple[str, list[str]]:
    match = PROJECT_SECTION.search(user_text)
    if not match:
        return user_text, []
    lines = current_projects(user_text)
    changed = []
    for repo, desc in (proposed or {}).items():
        repo = str(repo).strip()
        desc = redact(re.sub(r"\s+", " ", str(desc)).strip())
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", repo) or not (PROJECTS_ROOT / repo).is_dir():
            continue
        if not desc or len(desc) > 120 or "[REDACTED]" in desc or lines.get(repo) == desc:
            continue
        lines[repo] = desc
        changed.append(repo)
    if not changed:
        return user_text, []
    block = "".join(f"- `{repo}`:{desc}\n" for repo, desc in lines.items())  # keep order; new repos at the end
    return user_text[: match.start(2)] + block + user_text[match.end(2):], changed


def cmd_reflect(args: argparse.Namespace) -> int:
    today = date.today()
    if today.weekday() != 2 and not args.force:
        log("今天不是週三,略過(--force 強制)")
        return 0
    week_ago = time.time() - 7 * 86400
    files = changed_sessions(week_ago)[-80:]
    listing = "\n".join(f"   - {p} ({meta(p).get('project_directory', '').replace(str(HOME), '~')}) {meta(p).get('title', '')[:50]}"
                        for p in files) or "   (無)"
    user_text = USER.read_text(encoding="utf-8")
    prompt = REFLECT_PROMPT.format(today=today, obs=OBS, user=USER, files=listing, projects_root=PROJECTS_ROOT,
                                   current_projects=json.dumps(current_projects(user_text), ensure_ascii=False))
    raw = run_kiro(prompt, "REFLECT")
    if raw is None:
        return 1
    try:
        result = json.loads(re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M))
    except json.JSONDecodeError as exc:
        log(f"JSON 解析失敗:{exc};見 last-reflect.log")
        return 1

    touched: list[Path] = []
    # 1. USER.md project lines (direct, docs/context-system.md §2b)
    new_user, changed = apply_projects(user_text, result.get("projects"))
    if changed and gitleaks_clean(new_user):
        if not args.dry_run:
            USER.write_text(new_user, encoding="utf-8")
        touched.append(USER)
    log(f"USER.md 專案行更新:{changed or '無'}")

    # 2. GC old 🟢 (deterministic)
    obs_text = OBS.read_text(encoding="utf-8")
    head, body = record_region(obs_text)
    new_body, removed = gc_low(body, today)
    if removed:
        if not args.dry_run:
            OBS.write_text(head + new_body, encoding="utf-8")
        touched.append(OBS)
    log(f"清掉 {removed} 則超過 {GC_DAYS} 天的 🟢")

    # 3. candidates for the boss to approve
    cands = [c for c in result.get("rule_candidates") or [] if isinstance(c, dict) and c.get("text")][:5]
    merges = [str(m) for m in result.get("merge_suggestions") or []][:5]
    if cands or merges:
        parts = [f"\n## {today.isoformat()} 週三回顧\n"]
        for c in cands:
            parts.append(f"- [ ] **規則候選** → `rules/{c.get('file', '?')}` §{c.get('section', '?')}:{c['text']}\n"
                         f"  - 理由:{c.get('reason', '')}(依據:{c.get('evidence', '')})\n")
        for m in merges:
            parts.append(f"- [ ] **記憶整理**:{m}\n")
        section = redact("".join(parts))
        if gitleaks_clean(section):
            if not args.dry_run:
                if not PENDING.exists():
                    PENDING.write_text("# 待 zawa 確認的記憶變更\n\n> 由每週三 reflector 產生。zawa 同意哪幾項,就請 AI 套用到 `rules/` 或 `OBSERVATIONS.md`,"
                                       "然後把該項打勾或刪除。沒處理的會一直留著。\n", encoding="utf-8")
                with PENDING.open("a", encoding="utf-8") as handle:
                    handle.write(section)
            touched.append(PENDING)
        if args.dry_run:
            print(section)
    log(f"候選:規則 {len(cands)} 則、記憶整理 {len(merges)} 則")

    commit(touched, f"memory: reflector {today.isoformat()}", args.dry_run)
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
