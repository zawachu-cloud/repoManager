# Context 系統(記憶與規則)

讓 AI 在每個 repo 都知道「老闆是誰、怎麼工作、以前決定過什麼」。架構參考 [grapeot/context-infrastructure](https://github.com/grapeot/context-infrastructure)(參考版本 `3c25337`,2026-11-12),整合進 repoManager,不另開 repo。

## 1. 三層記憶

| 層 | 位置 | 內容 | 載入方式 |
|----|------|------|----------|
| **L3 全域規則** | `rules/SOUL.md`、`USER.md`、`COMMUNICATION.md` | AI 行為基調、老闆背景與偏好、溝通風格 | symlink 到 `~/.kiro/steering/`,**每個 session 自動載入**(每行都佔 token,保持精簡) |
| **L1/L2 觀察** | `contexts/memory/OBSERVATIONS.md` | 依日期追加的經驗與決策,標 🔴🟡🟢 | **按需** grep,不整份讀 |
| **原始對話** | `~/.local/share/ai-session-export/`(不在 repo) | 匯出並去除機密的對話 Markdown | 語意搜尋(第 3 階段) |

### L3 怎麼生效

`scripts/link-rules.sh` 把 `rules/*.md` symlink 到 `~/.kiro/steering/`。Kiro 的 `kiro_default` 會載入 `~/.kiro/steering/**/*.md`,自建 agent(`plan`/`code`/`aux`/`orchestrator`)預設也會繼承。
已驗證(2026-11-18):從 `/tmp` 用 default agent、從 `~/proj/my/stocktake` 用 `code` agent,都讀得到 `USER.md`。

- 改規則:直接改 `rules/*.md`,symlink 讓下一個 session 立刻生效,不需要 sync。
- 換機器:clone repoManager 後執行 `scripts/link-rules.sh`(冪等,不覆蓋非 symlink 的同名檔)。
- 若設定 `chat.disableInheritingDefaultResources=true`,自建 agent 就不會載入,需在 agent 的 `resources` 加 `file://~/.kiro/steering/**/*.md`。

## 2. 資料流(完整版)

```
~/.kiro/sessions/cli/ + ~/.claude/projects/
  │  ai_session_export(+ 自寫 Kiro adapter)
  │  ├─ 增量:只匯出新的或有更新的 session(見 §2a)
  │  ├─ 遮罩金鑰 / 個資
  │  └─ 只留使用者與 assistant 文字,丟掉 thinking、tool result、subagent session
  ▼
~/.local/share/ai-session-export/   (私有;age 加密後備份)
  │  gitleaks 類掃描通過才備份
  ▼
semantic-search-skill 建索引(本地 embedding,經 Ollama;快取在本機,可重建,不備份)
  │
  ▼
observer(每日)→ OBSERVATIONS.md 追加 L1
reflector(每週)→ 整理 L1/L2,提出 rules/ 候選 → 老闆核准才合入
```

### 2b. USER.md「目前的專案」的更新時機

| 時機 | 範圍 | 依據 | 要不要問老闆 |
|------|------|------|------|
| `/close-session` | 只動當下 repo 那一行 | 本 session 做的事 + 該 repo 的 AGENTS.md | 不用,直接改並 commit |
| 每週三回顧(reflector,第 4 階段) | 所有專案行 | 本週匯出的對話 Markdown | 專案行直接改;其他段落(偏好、溝通方式)只提候選,老闆核准才改 |

平時 session 不動這段,避免根據片段對話寫錯。

### 2a. 怎麼知道哪些 session 已匯出

ai_session_export 用**狀態檔**(預設在 `~/.local/share/ai-session-export/`)做增量匯出。Kiro adapter 照同一機制:

| 情況 | 判斷 | 動作 |
|------|------|------|
| session id 不在狀態檔 | 新 session | 匯出,記下 id 與 `updated_at` |
| 在狀態檔,但 `<id>.json` 的 `updated_at` 變了 | 匯出後又繼續聊 | 重寫同一份 Markdown |
| 在狀態檔,`updated_at` 沒變 | 已是最新 | 略過 |

- 每份 Markdown 的 frontmatter 有 `session_id`,可反查。
- **兩個觸發點,分工不同**:
  - `/close-session`:**只匯出當下這個 session**。Kiro 會把目前 session id 放在環境變數 `KIRO_SESSION_ID`,對應 `~/.kiro/sessions/cli/$KIRO_SESSION_ID.json`(2026-11-19 已驗證)。
  - cron **每天 12:30**(系統時區 Asia/Taipei):跑全部增量,補上沒下 `/close-session` 的 session,以及收工後又繼續聊的 session。crontab:`30 12 * * *`。
- WSL 注意:cron 只在 WSL 開著時才跑(目前 cron 有在跑,開機自動啟用)。12:30 電腦沒開就略過那天,下次執行會補上,不會掉資料。
- **子 session 用 `parent_session_id` 判斷**(只有 30 個有,父 session 都存在)。`session_created_reason` 不可靠:老闆直接開的主對話也標 `subagent`。
- 對帳(2026-11-19 首次全量):727 個 `.json` = 470 匯出 + 30 子 session + 227 空對話,無遺漏。Claude Code 8 個 transcript 中 3 個有對話,全數匯出。
- 增量判斷實際用 `.json` 與 `.jsonl` 的 mtime + 大小(對話先寫進 `.jsonl`,`updated_at` 較晚才更新)。
- 要全部重來用 `--full`。

## 3. 決策紀錄

| 日期 | 決策 | 理由 / 替代方案 |
|------|------|------|
| 2026-11-18 | 整合進 repoManager,不另開 `~/proj/my/context` | repoManager 是 private;內容都是「AI 怎麼跟老闆工作」,和既有標準、`~/.kiro/` 備份同類;只需維護、備份一個 repo。代價:記憶會隨 repo 走,**repoManager 不可轉 public**。 |
| 2026-11-18 | ai_session_export、semantic-search-skill 當外部工具安裝 | 它們是獨立 repo,有自己的測試與更新;Kiro adapter 寫在 ai_session_export 的 fork。 |
| 2026-11-18 | 不搬 upstream 的 `rules/axioms/`(44 份)、`rules/skills/`(42 份)、`WORKSPACE.md` | upstream 說明那些是原作者的累積,只能參考;我們的 skill 已在 `.kiro/skills/`。 |
| 2026-11-18 | L3 用 `~/.kiro/steering/` symlink 載入 | default 與自建 agent 都吃得到,不必改每個 agent 的 `resources`。 |
| 2026-11-18 | ~~embedding 可用雲端,但送出前不得含機密~~ | 已由 2026-11-19 決策取代。 |
| 2026-11-19 | **embedding 全部在本地,不送雲端**;所有 repo 的對話都收(含 hr 類),只是不記憑證與資料內容 | 遮罩抓不準人名、薪資數字,全本地就不必賭遮罩。機器有 RTX 3050 8GB、16 核、15GB RAM,跑小型 embedding 模型(如 Qwen3-Embedding-0.6B、bge-m3)夠用。代價:要裝 Ollama 等本地服務,建索引花運算時間但不花錢。 |
| 2026-11-19 | USER.md「目前的專案」只在 `/close-session`(當下 repo)與每週三回顧時由 AI 更新 | 依實際工作內容寫比一次讀 AGENTS.md 猜準。見 §2b。 |
| 2026-11-19 | 匯出是**增量**的;`/close-session` 只匯出當下 session,cron 每天 12:30 跑全部增量補漏 | 收工要快,不必每次掃 700 多個 session;cron 負責補漏。見 §2a。 |

## 4. 機密處理(第 2、3 階段的硬性要求)

所有資料都留在本機(2026-11-19 決策),所以不排除任何 repo 的對話。仍要做:

1. **遮罩**:金鑰格式(`sk-…`、`AKIA…`、JWT、`glrt-`、`sb_secret_` 等)、`secret` 類變數的值、連線字串密碼、「密碼是 …」、身分證字號(檢查碼正確才遮)、銀行帳號 → `[REDACTED]`。完整規則見 fork 的 README「Redaction」。首次全量共遮 194 處。
2. **掃描**:備份前用 gitleaks 類工具掃匯出結果,有命中就先處理再備份。
3. **記憶不寫兩類**:憑證(密碼、key、token)與資料內容(員工姓名、身分證、薪資數字、銀行帳號)。可以寫專案用途與決策。

### 4a. 工具與備份(第 2 階段實作)

| 元件 | 位置 | 說明 |
|------|------|------|
| 匯出工具 | `~/proj/my/ai_session_export`(private fork;`origin`=zawachu-cloud,`upstream`=grapeot) | 新增 `--source kiro`、`--session-id`;`redact.py` 對所有來源遮罩。venv 在 `.venv/`。 |
| 入口腳本 | `scripts/session-export.sh` | 無參數(cron):kiro + claude-code 增量 → gitleaks → 加密備份並 push。`--current`(close-session):只匯出 `$KIRO_SESSION_ID`。 |
| 加密備份 | `scripts/session_archive.py backup / restore` | 每個檔各自 age 加密成 `blobs/<hash>.age`,檔名用雜湊(原檔名含標題),對照表 `manifest.json.age` 也加密。只重新加密有變動的檔(本機 `.backup_index.json` 記 sha256)。 |
| 備份 repo | `~/proj/my/private_session_data` → `zawachu-cloud/private_session_data`(private) | 只有加密檔。 |
| 金鑰 | `~/proj/my/age.txt`(600,不在任何 repo) | **金鑰遺失 = 備份無法還原**。要另外安全保存(例如密碼管理器)。 |
| 存檔 | `~/.local/share/ai-session-export/{kiro,claude_code}/`、`logs/cron.log` | 權限 700/600。 |
| cron | `30 12 * * *` | 已安裝;另一筆 `kiro-cli update` 未動。 |

gitleaks 有命中時,cron **不備份**並以 exit 2 結束,看 `logs/gitleaks-last.json`(原值已遮蔽),到 `redact.py` 補規則後 `--full` 重匯。

**換電腦**:

```bash
git clone git@github.com:zawachu-cloud/repoManager.git ~/proj/my/repoManager
git clone git@github.com:zawachu-cloud/ai_session_export.git ~/proj/my/ai_session_export
git clone git@github.com:zawachu-cloud/private_session_data.git ~/proj/my/private_session_data
# 放回 ~/proj/my/age.txt(chmod 600)
cd ~/proj/my/ai_session_export && python3 -m venv .venv && .venv/bin/pip install -e .
python3 ~/proj/my/repoManager/scripts/session_archive.py restore
~/proj/my/repoManager/scripts/link-rules.sh
# 重裝 crontab 那一行(見上表)
```

舊電腦處理掉前,先跑一次 `scripts/session-export.sh`,確認最後的對話已備份。

## 5. 分階段計畫

| 階段 | 內容 | 狀態 |
|------|------|------|
| 1 | `rules/` 三份檔、`OBSERVATIONS.md`、steering symlink、本文件 | ✅ 2026-11-18(`USER.md` 仍有 `<待補>`) |
| 2 | fork ai_session_export,寫 Kiro adapter + 遮罩;匯出 Kiro 與 Claude Code;age 加密備份;cron 與 `/close-session` 串接 | ✅ 2026-11-19(見 §4a) |
| 3 | 安裝 Ollama + 本地 embedding 模型,semantic-search-skill 指向本地端點,建索引;寫查詢 skill | 待做 |
| 4 | observer(每日)/ reflector(**每週三**,含 §2b 的 USER.md 回顧)改用 `kiro-cli chat --no-interactive`(已確認此參數存在)取代 upstream 的 OpenCode;接 cron 與 `/close-session` | 待做 |

## 6. 未決事項

- `USER.md` 的 `<待補>` 欄位(背景、討厭什麼);「目前的專案」依 §2b 由 AI 逐步補。
- 本地 embedding 模型選哪個(第 3 階段實測中文檢索品質後決定)。
- `age.txt` 的異地保存方式(老闆決定)。
- 換電腦前要先跑一次匯出,確認最後幾天的對話進了存檔(`~/.kiro/sessions/` 不會跟著走)。
