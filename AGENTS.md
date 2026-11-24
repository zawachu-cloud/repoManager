# AGENTS.md

本檔提供給 AI 代理(以及新成員)理解 **repoManager** 的用途與慣例。開工前先讀本檔;規範細節在 `docs/`。

## 專案總覽

**repoManager** — 管理「我怎麼開 repo、怎麼收尾 repo」的工具型 repo。
它本身不是應用程式,而是存放**標準**與**可重複使用的 skill**,讓每次新開 repo / 收工都走一致流程、不用重打需求。

核心產出:
- **repo 標準**(`docs/repo-standard.md`):一個 repo 該有的結構 + close session 要檢查什麼,是**單一真實來源**。
- **repo 生命週期 skill**(`.kiro/skills/*/SKILL.md`):
  | 指令 | 用途 |
  |------|------|
  | `/create-repo` | 建立一個新 repo(local 新建或從 git ssh url clone),並補齊必備結構、寫入第 1 份工作。 |
  | `/close-session` | 收尾檢查:未辦事項 → git 是否乾淨 → 本 session 動作與文件是否一致。 |
  | `/check-repo` | 檢查指定目錄是否符合 repo 標準(結構 + 收尾規範)。 |
  | `/recall` | 語意搜尋過去的對話存檔與 OBSERVATIONS(本地 Ollama)。(全域 skill,在 `~/.kiro/skills/`) |
| `/pipeline` | orchestrator(總架構師)拆解任務,視情況派 plan 規劃子項目,再派 code→test、doc,各階段走各自 model。先 `/agent orchestrator` 再用。(全域 skill,在 `~/.kiro/skills/`) |
- **templates/**:新 repo 用的範本檔(AGENTS.md、firstTask.md、.gitignore、.env.example、docs/README、`.kiro/agents/`、`.kiro/skills/{pipeline,recall}/`)。
- **context 系統**(`rules/`、`contexts/memory/`):讓 AI 在每個 repo 都知道zawa是誰、以前決定過什麼。`rules/` 是全域規則(symlink 到 `~/.kiro/steering/`,每個 session 自動載入);`contexts/memory/OBSERVATIONS.md` 是按需 grep 的觀察紀錄。設計、機密處理與分階段計畫見 **`docs/context-system.md`**。

## 目錄結構

```
repoManager/
├── AGENTS.md                      # 本檔:精簡規範,指向 docs/
├── README.md                      # 入口說明
├── docs/
│   ├── repo-standard.md           # repo 必備結構 + close session 規範(單一真實來源)
│   └── context-system.md          # context 系統:三層記憶、資料流、機密處理、分階段計畫
├── rules/                         # L3 全域規則(symlink 到 ~/.kiro/steering/,每個 session 自動載入)
│   ├── SOUL.md                    # AI 行為基調
│   ├── USER.md                    # zawa背景與偏好
│   └── COMMUNICATION.md           # 溝通風格
├── contexts/memory/
│   ├── OBSERVATIONS.md            # L1/L2 觀察紀錄(按需 grep,不整份讀)
│   └── pending-review.md          # reflector 提出、待zawa核准的規則候選
├── templates/                     # 新 repo 範本(由 create-repo 複製 / 參考)
│   ├── AGENTS.md
│   ├── firstTask.md
│   ├── gitignore                  # 複製到新 repo 時改名為 .gitignore
│   ├── env.example                # 複製到新 repo 時改名為 .env.example
│   ├── docs/README.md
│   ├── .kiro/agents/              # agent 備份(plan/code/aux/orchestrator/heartbeat),來源是 ~/.kiro/;另含 code-lab.json(拋棄式測試庫用範本,來源是 templates,見 docs §5b)
│   └── .kiro/skills/{pipeline,recall}/  # 全域 skill 備份,來源是 ~/.kiro/
├── scripts/
│   ├── sync-kiro.sh               # 把 ~/.kiro/ 的 agent 與 pipeline skill 同步回 templates/.kiro/
│   ├── session-export.sh          # 對話匯出:cron 每天 12:30 全部增量+加密備份;--current 給 /close-session
│   ├── session_archive.py         # 存檔 age 加密備份 / 還原(→ private_session_data)
│   ├── semantic_search.py         # 本地語意搜尋(Ollama):index / query,給 /recall 用
│   ├── heartbeat.py               # 自動記憶:observe(每日)/ reflect(週三),用唯讀 heartbeat agent
│   └── link-rules.sh              # 把 rules/*.md symlink 到 ~/.kiro/steering/(換機器跑一次)
├── .kiro/skills/
│   ├── create-repo/SKILL.md
│   ├── close-session/SKILL.md
│   └── check-repo/SKILL.md
├── .gitignore
├── .env.example
└── tmp/                           # 暫存(不進版控)
```

## repo 標準(摘要)

一個 repo 完成後根目錄應有:`AGENTS.md`(精簡資訊)、`docs/`(完整資訊)、`firstTask.md`(第 1 份工作,暫存)、`.env`(機密,不進版控)、`.env.example`、`tmp/`(暫存,不進版控)、`.gitignore`、`.git/`。
**完整定義與理由見 `docs/repo-standard.md`**,勿在此處重複細節(省 token、避免兩處不同步)。

## 慣例(對齊 ~/proj/my/hr)

- **中文回覆**:一律用**繁體中文**回覆zawa。
- **語言**:文件與對話用繁體中文;程式碼識別符用英文。
- **機密**:真實金鑰只放 `.env`(已 gitignore),版控只放 `.env.example`(無真值)。`service_role` 類高權限金鑰嚴禁進版控。
- **暫存**:草稿/實驗/zawa給 AI 看的資料放 `tmp/`,不進版控;一般搜尋會略過(靠 .gitignore),指定檔案時可讀。`.kiroignore` 不可列 `tmp/`(會連指定讀取一起擋)。
- **文件分層省 token**:AGENTS.md 只放最關鍵摘要,細節放 `docs/` 或 skill;避免兩處重複。
- **skill 格式**:每個 skill 是 `.kiro/skills/<name>/SKILL.md`,以 YAML frontmatter(`name` + `description`)開頭,用 `$ARGUMENTS` 接參數。
- **commit / push 由 AI 決定**:完成變更後**直接** `git add / commit / push`,不用再問zawa(zawa已授權)。
- **破壞性動作先確認**:`rm -rf`、`git reset --hard`、force push、覆蓋既有檔(尤其 clone 來的)等,動手前先向zawa確認。
- **不擅自大重構**:規範只在 `docs/repo-standard.md` 改一處。
- **model routing**:依任務用不同 model(`plan`=opus-5.5 / `code`=sonnet-5.5 / `aux`=haiku-5.5)。角色 agent 與 `orchestrator`、`pipeline` skill **只維護全域 `~/.kiro/`**;改完跑 `scripts/sync-kiro.sh` 同步回 `templates/.kiro/` 並 commit(版控備份)。自動化流程 `/agent orchestrator` → `/pipeline <任務>`。定義與用法是 `docs/repo-standard.md` §5 / §5a(單一真實來源),勿在他處重複清單。

## 給 AI 代理的工作準則

- 要「開新 repo」時走 `/create-repo`;「收工」時走 `/close-session`;「檢查某 repo 合不合規」時走 `/check-repo`。
- 三個 skill 的判斷基準一律回到 `docs/repo-standard.md`,不要各自硬編規則。
- 建立新 repo 時以 `templates/` 為範本;新 repo 已存在的檔**不覆蓋**,缺的才補。
- 收尾(close session)依 `docs/repo-standard.md` §3 三步驟進行。
- **context 系統**:改全域規則就改 `rules/*.md`(symlink 立即生效,不用 sync);值得跨 session 記住的經驗或決策,追加到 `contexts/memory/OBSERVATIONS.md`(格式見該檔,**不寫機密**)。repoManager 因此含個人記憶,**不可轉 public**。
