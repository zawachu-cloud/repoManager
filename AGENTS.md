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
  | `/pipeline` | 跑 plan→code→test→doc 四階段 subagent pipeline,各階段走各自 model。先 `/agent orchestrator` 再用。 |
- **templates/**:新 repo 用的範本檔(AGENTS.md、firstTask.md、.gitignore、.env.example、docs/README、`.kiro/agents/`、`.kiro/skills/pipeline/`)。

## 目錄結構

```
repoManager/
├── AGENTS.md                      # 本檔:精簡規範,指向 docs/
├── README.md                      # 入口說明
├── docs/
│   └── repo-standard.md           # repo 必備結構 + close session 規範(單一真實來源)
├── templates/                     # 新 repo 範本(由 create-repo 複製 / 參考)
│   ├── AGENTS.md
│   ├── firstTask.md
│   ├── gitignore                  # 複製到新 repo 時改名為 .gitignore
│   ├── env.example                # 複製到新 repo 時改名為 .env.example
│   ├── docs/README.md
│   ├── .kiro/agents/              # 角色 agent 範本(plan/code/aux/orchestrator)
│   └── .kiro/skills/pipeline/     # pipeline skill 範本
├── .kiro/
│   ├── agents/
│   │   └── orchestrator.json      # pipeline 協調者(本地覆蓋全域)
│   └── skills/
│       ├── create-repo/SKILL.md
│       ├── close-session/SKILL.md
│       ├── check-repo/SKILL.md
│       └── pipeline/SKILL.md      # plan→code→test→doc pipeline
├── .gitignore
├── .env.example
└── tmp/                           # 暫存(不進版控)
```

## repo 標準(摘要)

一個 repo 完成後根目錄應有:`AGENTS.md`(精簡資訊)、`docs/`(完整資訊)、`firstTask.md`(第 1 份工作,暫存)、`.env`(機密,不進版控)、`.env.example`、`tmp/`(暫存,不進版控)、`.gitignore`、`.git/`。
**完整定義與理由見 `docs/repo-standard.md`**,勿在此處重複細節(省 token、避免兩處不同步)。

## 慣例(對齊 ~/proj/my/hr)

- **中文回覆**:一律用**繁體中文**回覆老闆。
- **語言**:文件與對話用繁體中文;程式碼識別符用英文。
- **機密**:真實金鑰只放 `.env`(已 gitignore),版控只放 `.env.example`(無真值)。`service_role` 類高權限金鑰嚴禁進版控。
- **暫存**:草稿/實驗放 `tmp/`,不進版控、也不需讀入 context。
- **文件分層省 token**:AGENTS.md 只放最關鍵摘要,細節放 `docs/` 或 skill;避免兩處重複。
- **skill 格式**:每個 skill 是 `.kiro/skills/<name>/SKILL.md`,以 YAML frontmatter(`name` + `description`)開頭,用 `$ARGUMENTS` 接參數。
- **commit / push 由 AI 決定**:完成變更後**直接** `git add / commit / push`,不用再問老闆(老闆已授權)。
- **破壞性動作先確認**:`rm -rf`、`git reset --hard`、force push、覆蓋既有檔(尤其 clone 來的)等,動手前先向老闆確認。
- **不擅自大重構**:規範只在 `docs/repo-standard.md` 改一處。
- **model routing**:依任務用不同 model(`plan`=opus-5.5 / `code`=sonnet-5.5 / `aux`=haiku-5.5)。角色 agent 與 `orchestrator`、`pipeline` skill 放全域 `~/.kiro/`,範本在 `templates/.kiro/`。自動化流程 `/agent orchestrator` → `/pipeline <任務>`。定義與用法是 `docs/repo-standard.md` §5 / §5a(單一真實來源),勿在他處重複清單。

## 給 AI 代理的工作準則

- 要「開新 repo」時走 `/create-repo`;「收工」時走 `/close-session`;「檢查某 repo 合不合規」時走 `/check-repo`。
- 三個 skill 的判斷基準一律回到 `docs/repo-standard.md`,不要各自硬編規則。
- 建立新 repo 時以 `templates/` 為範本;新 repo 已存在的檔**不覆蓋**,缺的才補。
- 收尾(close session)依 `docs/repo-standard.md` §3 三步驟進行。
