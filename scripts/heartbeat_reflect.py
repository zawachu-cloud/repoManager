"""Weekly reflector (L2): GC old 🟢, merge duplicate observations, update USER.md project lines,
write rule candidates / questions to pending-review.md. Called by `heartbeat.py reflect`.

Design: repoManager docs/context-system.md §4c.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import date
from pathlib import Path

from heartbeat_common import (
    GC_DAYS, HOME, OBS, PENDING, PROJECTS_ROOTS, RECORD_MARK, USER,
    changed_sessions, commit, gitleaks_clean, log, meta, redact, run_kiro,
)
from heartbeat_merge import apply_merges, render_pending, tidy_body  # noqa: E402


REFLECT_PROMPT = """任務:L2 每週回顧。基準日期 {today}。

請讀:
1. 記憶檔 {obs}(L1/L2 觀察,依 Date 分段)。
2. zawa 的使用者檔 {user}(每個 session 都會載入)。
3. 過去 7 天的對話存檔(需要時用 read / grep 看內容):
{files}
4. 各專案的 AGENTS.md:<根目錄>/<repo>/AGENTS.md(需要時讀)。專案根目錄有兩個:
{projects_roots}

產出一個 JSON 物件,放在標記之間:
<<<REFLECT
{{
  "projects": {{"<repo 目錄名>": "<一行用途與目前方向,60 字以內>"}},
  "rule_candidates": [
    {{"file": "USER.md|SOUL.md|COMMUNICATION.md", "section": "<要放的段落標題>", "text": "<建議新增或修改的那一行>", "impact": "<白話:這條規則在實際工作中會有什麼不同>", "reason": "<為什麼>", "evidence": "<依據:Date 或存檔檔名>"}}
  ],
  "merges": [
    {{"old": ["<OBSERVATIONS 記錄區的完整原行,逐字複製>", "..."], "new": "<合併後的一行,符合觀察行格式>"}}
  ],
  "questions": ["<需要 zawa 提供的事實,白話,一句話能回答>"]
}}
REFLECT>>>

規則:
- projects:只放上述任一根目錄下真的存在(repo 目錄名只寫名稱,不含路徑)、而且你從存檔或 AGENTS.md 有依據的 repo。沒依據就不要放,不要猜。
  寫用途與方向,不寫憑證、IP、資料內容(姓名、薪資數字等)。目前的寫法:{current_projects}
- rule_candidates:反覆出現(至少兩次)的偏好或做法,而且 USER/SOUL/COMMUNICATION 還沒寫到的才提。最多 5 則。沒有就給空陣列。
  impact 用白話寫,讓沒讀過 {obs} 的 zawa 也看得懂;不要用日期或 emoji 指稱筆記。
- merges:腳本會直接套用到 {obs},最多 5 則;沒有就空陣列。
  只合併講同一件事的重複條目,或已被取代的條目。
  old 是 {obs} 記錄區的完整原行,必須逐字複製(含 emoji 與 [分類]);整行要存在才會套用。
  new 是合併後的一行,格式同觀察行(🔴 High / 🟡 Medium / 🟢 Low: [分類] 描述,200 字以內);要保留仍有效的資訊,尤其是待決事項。
  條目只是過時要刪除時,new 給空字串。
- questions:需要 zawa 提供、你從存檔查不到的事實(例如某專案的路徑)。白話,一句話能回答;最多 3 則,沒有就空陣列。
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
    return tidy_body("".join(out)), removed


PROJECT_SECTION = re.compile(r"(## 目前的專案\n(?:.*\n)*?\n)((?:- `[^`]+`:[^\n]*\n)+)")


def current_projects(user_text: str) -> dict[str, str]:
    match = PROJECT_SECTION.search(user_text)
    if not match:
        return {}
    return dict(re.findall(r"^- `([^`]+)`:(.*)$", match.group(2), re.M))


def repo_exists(repo: str, roots: list[Path]) -> bool:
    return any((root / repo).is_dir() for root in roots)  # a missing root just yields False


def apply_projects(user_text: str, proposed: dict, roots: list[Path] | None = None) -> tuple[str, list[str]]:
    roots = PROJECTS_ROOTS if roots is None else roots
    match = PROJECT_SECTION.search(user_text)
    if not match:
        return user_text, []
    lines = current_projects(user_text)
    changed = []
    for repo, desc in (proposed or {}).items():
        repo = str(repo).strip()
        desc = redact(re.sub(r"\s+", " ", str(desc)).strip())
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", repo) or not repo_exists(repo, roots):
            continue
        if not desc or len(desc) > 120 or "[REDACTED]" in desc or lines.get(repo) == desc:
            continue
        lines[repo] = desc
        changed.append(repo)
    if not changed:
        return user_text, []
    block = "".join(f"- `{repo}`:{desc}\n" for repo, desc in lines.items())  # keep order; new repos at the end
    return user_text[: match.start(2)] + block + user_text[match.end(2):], changed


PENDING_HEADER = ("# 待 zawa 確認的記憶變更\n\n"
                  "> 由每週三 reflector 產生,只放需要 zawa 決定的事:規則候選(會改變 AI 行為)與問題(需要 zawa 提供的事實)。"
                  "重複筆記的合併由 reflector 直接做,不列在這裡。zawa 回覆後,AI 套用並打勾或刪除;沒處理的會一直留著。\n")


def _changed_lines(old: str, new: str) -> list[str]:
    """Lines present in new but not in old (what a merge introduced), for the gitleaks check."""
    before = set(old.splitlines())
    return [line for line in new.splitlines() if line.strip() and line not in before]


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
    roots = "\n".join(f"   - {r}" for r in PROJECTS_ROOTS)
    prompt = REFLECT_PROMPT.format(today=today, obs=OBS, user=USER, files=listing, projects_roots=roots,
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

    # 2. OBSERVATIONS.md: GC old 🟢, then apply merges (one write)
    obs_text = OBS.read_text(encoding="utf-8")
    head, body = record_region(obs_text)
    gc_body, removed = gc_low(body, today)
    log(f"清掉 {removed} 則超過 {GC_DAYS} 天的 🟢")
    merges = result.get("merges") or []
    if not isinstance(merges, list):
        merges = []
    new_body, applied, skipped = apply_merges(gc_body, merges[:5], redact)
    for reason in skipped:
        log(f"略過一則合併:{reason}")
    if applied and not gitleaks_clean("\n".join(_changed_lines(gc_body, new_body))):
        log("gitleaks 在合併結果裡有命中,整批合併不套用")
        new_body, applied = gc_body, 0
    log(f"{'會套用' if args.dry_run else '套用'}合併 {applied} 則(略過 {len(skipped)} 則)")
    if removed or applied:
        if not args.dry_run:
            OBS.write_text(head + new_body, encoding="utf-8")
        touched.append(OBS)

    # 3. pending-review: rule candidates and questions for zawa
    cands = [c for c in result.get("rule_candidates") or [] if isinstance(c, dict) and c.get("text")][:5]
    questions = [str(q).strip() for q in result.get("questions") or [] if str(q).strip()][:3]
    section = redact(render_pending(today.isoformat(), cands, questions))
    if section:
        if gitleaks_clean(section):
            if not args.dry_run:
                if not PENDING.exists():
                    PENDING.write_text(PENDING_HEADER, encoding="utf-8")
                with PENDING.open("a", encoding="utf-8") as handle:
                    handle.write(section)
            touched.append(PENDING)
        if args.dry_run:
            print(section)
    log(f"待確認:規則候選 {len(cands)} 則、問題 {len(questions)} 則")

    commit(touched, f"memory: reflector {today.isoformat()}", args.dry_run)
    return 0
