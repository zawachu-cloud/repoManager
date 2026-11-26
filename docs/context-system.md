# Context 系統(記憶與規則)

讓 AI 在每個 repo 都知道「zawa 是誰、怎麼工作、以前決定過什麼」。架構參考 [grapeot/context-infrastructure](https://github.com/grapeot/context-infrastructure)(參考版本 `3c25337`,2026-11-12),整合進 repoManager,不另開 repo。

## 1. 三層記憶

| 層 | 位置 | 內容 | 載入方式 |
|----|------|------|----------|
| **L3 全域規則** | `rules/SOUL.md`、`USER.md`、`COMMUNICATION.md` | AI 行為基調、zawa 背景與偏好、溝通風格 | symlink 到 `~/.kiro/steering/`,**每個 session 自動載入**(每行都佔 token,保持精簡) |
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
~/.kiro/sessions/(cli/ 與 <hash>/ 兩種格式並存,見 §2a)+ ~/.claude/projects/
  │  ai_session_export(+ 自寫 Kiro adapter)
  │  ├─ 增量:只匯出新的或有更新的 session(見 §2a)
  │  ├─ 遮罩金鑰 / 個資
  │  └─ 只留使用者與 assistant 文字,丟掉 thinking、tool result、subagent session
  ▼
~/.local/share/ai-session-export/   (私有;age 加密後備份)
  │  gitleaks 類掃描通過才備份
  ▼
semantic-search-skill 建索引(本地 Ollama qwen3-embedding:4b;快取在本機,可重建,不備份)→ /recall
  │
  ▼
observer(每日)→ OBSERVATIONS.md 追加 L1
reflector(每週)→ 直接合併 L1/L2 重複筆記,提出 rules/ 候選 → zawa 核准才合入
```

### 2b. USER.md「目前的專案」的更新時機

| 時機 | 範圍 | 依據 | 要不要問 zawa |
|------|------|------|------|
| `/close-session` | 只動當下 repo 那一行 | 本 session 做的事 + 該 repo 的 AGENTS.md | 不用,直接改並 commit |
| 每週三 13:00 回顧(reflector) | 所有專案行 | 本週匯出的對話 Markdown | 專案行直接改;其他段落(偏好、溝通方式)只提候選,zawa 核准才改 |

平時 session 不動這段,避免根據片段對話寫錯。

### 2a. 怎麼知道哪些 session 已匯出

**Kiro session 有兩種格式,兩種都掃**(`sources/kiro_workspace.py` 處理新格式,`--kiro-workspace-root` 指定根目錄,預設 `~/.kiro/sessions`):

| 格式 | 位置 | 檔案 | 來源 |
|------|------|------|------|
| 舊 | `~/.kiro/sessions/cli/` | `<id>.json` + `<id>.jsonl` | Kiro CLI 舊版 |
| 新 | `~/.kiro/sessions/<hash>/sess_<UUID>/` | `session.json` + `messages.jsonl` | orca / ACP 開的 session |

- 新格式的 `<hash>` 是工作目錄路徑 sha256 的前 16 碼。`project_directory` 會是 orca 工作目錄(例如 `~/orca/workspaces/repoManager/matt`),照實記錄,不改寫成 repo 路徑。
- 新格式只匯出 user 與 assistant(Say)文字,白名單制。子代理在 `sub-executions/`,不匯出。
- 兩種格式輸出到同一個 `kiro/` 資料夾。`--session-id` 帶不帶 `sess_` 前綴都可以。
- 新格式支援由 ai_session_export commit d0387ba 加入。

ai_session_export 用**狀態檔**(預設在 `~/.local/share/ai-session-export/`)做增量匯出。Kiro adapter 照同一機制:

| 情況 | 判斷 | 動作 |
|------|------|------|
| session id 不在狀態檔 | 新 session | 匯出,記下 id 與 `updated_at` |
| 在狀態檔,但 `<id>.json` 的 `updated_at` 變了 | 匯出後又繼續聊 | 重寫同一份 Markdown |
| 在狀態檔,`updated_at` 沒變 | 已是最新 | 略過 |

- 每份 Markdown 的 frontmatter 有 `session_id`,可反查。
- **兩個觸發點,分工不同**:
  - `/close-session`:**只匯出當下這個 session**。Kiro 會把目前 session id 放在環境變數 `KIRO_SESSION_ID`,兩種格式的位置見上方表格(2026-11-19 舊格式已驗證)。
  - cron **每天 12:30**(系統時區 Asia/Taipei):跑全部增量,補上沒下 `/close-session` 的 session,以及收工後又繼續聊的 session。crontab:`30 12 * * *`。
- WSL 注意:cron 只在 WSL 開著時才跑(目前 cron 有在跑,開機自動啟用)。12:30 電腦沒開就略過那天,下次執行會補上,不會掉資料。
- **子 session 用 `parent_session_id` 判斷**(只有 30 個有,父 session 都存在)。`session_created_reason` 不可靠:zawa 直接開的主對話也標 `subagent`。
- 對帳(2026-11-19 首次全量):727 個 `.json` = 470 匯出 + 30 子 session + 227 空對話,無遺漏。Claude Code 8 個 transcript 中 3 個有對話,全數匯出。
- 增量判斷實際用舊格式 `.json` 與 `.jsonl`、新格式 `session.json` 與 `messages.jsonl` 的 mtime + 大小(對話先寫進 `.jsonl`/`messages.jsonl`,`updated_at` 較晚才更新)。
- 要全部重來用 `--full`。

## 3. 決策紀錄

| 日期 | 決策 | 理由 / 替代方案 |
|------|------|------|
| 2026-11-18 | 整合進 repoManager,不另開 `~/proj/my/context` | repoManager 是 private;內容都是「AI 怎麼跟 zawa 工作」,和既有標準、`~/.kiro/` 備份同類;只需維護、備份一個 repo。代價:記憶會隨 repo 走,**repoManager 不可轉 public**。 |
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
| 匯出工具 | `~/proj/my/ai_session_export`(private fork;`origin`=zawachu-cloud,`upstream`=grapeot) | 新增 `--source kiro`、`--session-id`、`--kiro-workspace-root`(Kiro 新舊格式,見 §2a);`redact.py` 對所有來源遮罩。venv 在 `.venv/`。 |
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

### 4b. 語意搜尋(第 3 階段實作)

| 元件 | 位置 / 設定 |
|------|------|
| embedding 服務 | Ollama 0.40.16,`~/.local/opt/ollama`(免 sudo 安裝),systemd user service `ollama.service`,**只聽 127.0.0.1:11434**,開了 linger(沒登入也會跑)。用 GPU(RTX 3050)。 |
| 模型 | `qwen3-embedding:4b`(2.5GB,索引 185MB)。換模型要重建索引。 |
| 搜尋工具 | `~/proj/my/semantic-search-skill`(upstream clone,未修改,venv 在 `.venv/`)。用 OpenAI 相容端點接 Ollama。 |
| 入口 | `scripts/semantic_search.py index` / `query "<問題>" [-k] [--project] [--since] [--json]`。來源:`kiro/`、`claude_code/` 存檔 + `OBSERVATIONS.md`。 |
| 索引 | `~/.local/share/semantic-search/sessions/`(700)。可重建,不備份。 |
| 更新 | cron 12:30 的 `session-export.sh` 備份完後跑 `index`,只重算有變動的檔(約 10 秒)。`query` 預設也會先補索引。 |
| skill | 全域 `~/.kiro/skills/recall/`(備份在 `templates/.kiro/skills/recall/`)。`/recall <要找的事>`,AI 也會自動使用。 |

**模型評測**(2026-11-19,真實存檔 474 檔 / 15187 塊,14 題換句話說的中文查詢,看正確 session 排第幾):

| 模型 | 第 1 名 | 前 5 名 | MRR | 全量建索引 | 查詢 |
|------|:--:|:--:|:--:|:--:|:--:|
| qwen3-embedding:0.6b | 7 | 14 | 0.67 | 6 分 | 1.1 秒 |
| bge-m3 | 9 | 11 | 0.73 | 7 分 | 1.2 秒 |
| **qwen3-embedding:4b** | 9 | 13 | **0.77** | 24 分 | 1.3 秒 |

選 4b:準確度最好,建索引慢只影響第一次(之後每天增量)。0.6b 沒有大失誤,是換低階電腦時的備案。已知弱點:用很不同的說法描述技術事件(例如把「ETL 追補」說成「補跑歷史資料的批次」)會掉到 10 名左右,換個說法再查。

**換電腦**:裝 Ollama(下載官方 `ollama-linux-amd64.tar.zst` 解壓到 `~/.local/opt/ollama`,複製 `~/.config/systemd/user/ollama.service`,`loginctl enable-linger`)→ `ollama pull qwen3-embedding:4b` → clone semantic-search-skill 並建 venv → `scripts/semantic_search.py index`(約 25 分鐘)。

### 4c. 自動記憶(第 4 階段實作)

| 元件 | 內容 |
|------|------|
| `scripts/heartbeat.py observe` | 每天 12:30(接在 `session-export.sh` 最後)。挑出大小有變的存檔(新 session 或續聊),一次最多 40 個,交給 Kiro 寫 🔴🟡🟢,追加到 `OBSERVATIONS.md` 並 commit。失敗不推進狀態,下次重試同一批。 |
| `scripts/heartbeat.py reflect` | 每週三 13:00(cron `0 13 * * 3`)。① 依過去 7 天存檔與各 repo AGENTS.md(repo 位於 `~/orca/projects/` 與 `~/proj/my/` 兩處)**直接**更新 `USER.md`「目前的專案」(只改這段,repo 要真的存在)② 刪掉超過 30 天的 🟢(程式判斷,不靠 AI)③ 產出規則候選與問題寫進 `contexts/memory/pending-review.md`,並直接合併重複筆記(細節見下方)。 |
| Kiro agent `heartbeat` | `~/.kiro/agents/heartbeat.json`(sonnet-5.5),只有 read/grep/glob,**不能寫檔或執行指令**(已實測)。結果印在標記之間,由腳本驗證格式 → 遮罩 → gitleaks → 寫檔 → 只 commit 碰到的檔。 |
| 程式檔案 | `heartbeat.py`(入口與 observe)、`heartbeat_reflect.py`(reflect)、`heartbeat_common.py`(路徑、狀態、kiro 執行、gitleaks、commit)、`heartbeat_merge.py`(純函式:整理與合併重複筆記)。 |
| 不回灌 | heartbeat 的 Kiro session 在 `~/.local/share/ai-heartbeat/` 執行,匯出時用 `--kiro-exclude-cwd` 排除,不會變成下一輪的觀察來源。 |
| 狀態 / log | `~/.local/share/ai-heartbeat/state.json`(各存檔上次觀察時的大小)、`last-obs.log`、`last-reflect.log`、`cron.log`。 |

- reflect 的輸出分三類,各自的處理方式不同:
  - **規則候選**:寫進 `pending-review.md`,每則附一行白話「影響」(套用後 AI 的哪個行為會改變),**zawa 核准才套用**到 `rules/`。
  - **重複筆記合併**:不列在 `pending-review.md`。agent 在 `merges` 欄位輸出「要取代的原行」與「合併後的一行」,腳本驗證後直接改寫 `OBSERVATIONS.md`,合併後的行放在被合併條目中最早那則的位置,其餘刪除。驗證:原行必須逐字存在;新行符合觀察格式(`🔴/🟡/🟢 High|Medium|Low: [標籤] 描述`);遮罩後不含 `[REDACTED]`;通過 gitleaks。任一項不符就略過那則。
  - **問題**:需要 zawa 提供的事實,用白話問句寫進 `pending-review.md`。zawa 回覆後,AI 處理並打勾或刪除。
- 判斷變動用檔案大小,不用 mtime:`--full` 重匯會讓所有檔 mtime 變新,但內容一樣。第一次執行時,昨天以前的存檔一律當作已看過(歷史用 `/recall` 查)。
- Kiro 服務偶爾在回應中途失敗(`dispatch failure`),`run_kiro` 會等 60 秒重試一次。
- 首次執行(2026-11-19):observer 寫入 15 則;reflector 補了 9 個專案行,提出 4 則規則候選、5 則記憶整理(當時列在 pending-review,現改為直接合併)。

## 5. 分階段計畫

| 階段 | 內容 | 狀態 |
|------|------|------|
| 1 | `rules/` 三份檔、`OBSERVATIONS.md`、steering symlink、本文件 | ✅ 2026-11-18(`USER.md` 仍有 `<待補>`) |
| 2 | fork ai_session_export,寫 Kiro adapter + 遮罩;匯出 Kiro 與 Claude Code;age 加密備份;cron 與 `/close-session` 串接 | ✅ 2026-11-19(見 §4a) |
| 3 | 安裝 Ollama + 本地 embedding 模型,semantic-search-skill 指向本地端點,建索引;寫查詢 skill | ✅ 2026-11-19(見 §4b) |
| 4 | observer(每日)/ reflector(**每週三**,含 §2b 的 USER.md 回顧)改用 `kiro-cli chat --no-interactive` 取代 upstream 的 OpenCode;接 cron 與 `/close-session` | ✅ 2026-11-19(見 §4c) |

## 6. 未決事項

- `USER.md`「目前的專案」的 `line`、`modelRouting` 依 §2b 由 AI 逐步補(zawa 決定不填背景等其他欄位)。
- `age.txt` 的異地保存方式(zawa 決定)。
- 換電腦前要先跑一次匯出,確認最後幾天的對話進了存檔(`~/.kiro/sessions/` 不會跟著走)。
