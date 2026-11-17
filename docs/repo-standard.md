# Repo 標準(單一真實來源)

本檔定義「一個 repo 應長什麼樣子」與「收尾(close session)要檢查什麼」。
`create-repo`、`close-session`、`check-repo` 三個 skill 都以本檔為準;改規範只改這裡。

## 1. 必備結構

新建立的 repo(不論 local 新建或從 git url clone)完成後,根目錄必須有:

| 項目 | 類型 | 進版控? | 用途 |
|------|------|:------:|------|
| `AGENTS.md` | 檔案 | ✅ | 本 repo 的**精簡**資訊:總覽、技術棧、慣例、指令、指向 `docs/` 找完整資訊。給 AI/新成員開工前先讀。 |
| `docs/` | 目錄 | ✅ | **完整**資訊所在:feature / issue / 待辦 / 設計 / 決策紀錄。AGENTS.md 只摘要,細節一律放這裡。 |
| `firstTask.md` | 檔案 | ✅(暫存) | 第 1 份工作的說明。切到此 repo 開新 session 時,第一件事就是讀它。完成後可刪或歸檔到 `docs/`。 |
| `.env` | 檔案 | ❌ | 機密資訊(金鑰/密碼/連線字串)。**絕不進版控**。 |
| `.env.example` | 檔案 | ✅ | `.env` 的範本(只有 key、無真值),讓他人知道需要哪些變數。 |
| `tmp/` | 目錄 | ❌ | 暫存/草稿/實驗資料。**不進版控**。 |
| `.gitignore` | 檔案 | ✅ | 至少忽略 `.env`、`.env.*`(保留 `!.env.example`)、`tmp/`。 |
| `.git/` | 目錄 | — | git 儲存庫(`git init` 或 clone 產生)。 |

> 命名註記:本標準用 **`docs/`**(對齊 ~/proj/my/hr)。既有 repo 若用 `doc/` 亦視為合規,`check-repo` 兩者皆接受。

## 2. 建立新 repo 的流程(create-repo)

1. **決定建立方式**
   - local 新建:`mkdir -p <dir>` → `git init`(預設分支 `main`)。
   - 從 git url clone:`git clone <ssh-url> <dir>`(沿用遠端內容)。
2. **在 repo 內補齊必備結構**(上表),缺什麼補什麼;已存在的檔不覆蓋(clone 來的尤其小心)。
3. **寫入 `firstTask.md`**:把老闆口述的「我打算要做什麼任務」填進去,作為新 session 的第 1 份工作。
4. **精簡填寫 `AGENTS.md`**:專案名稱、一句話目標、已知技術棧、指向 `docs/` 與 `firstTask.md`。
5. **產出後提示**:請老闆 `cd <dir>` 後開新 session,新 session 先讀 `AGENTS.md` 與 `firstTask.md`。

## 3. 收尾規範(close session)

老闆說「close session / 收工 / 結束這個 session」時,依序:

1. **檢查未辦事項**:本 session 有無待完成的修改、未跑的測試、未回覆的問題、TODO/暫緩項。**有就先列出並處理或向老闆確認**,不略過。
2. **檢查 git 狀態是否乾淨**:`git status` 應無未預期的未追蹤/未提交變更;確認 `.env` 等機密**沒有**被 add 進去。
3. **檢查本 session 的動作與文件是否一致**:這次改了什麼,就對照 `AGENTS.md`、`docs/`、`firstTask.md` 是否同步更新;發現落差就補正或明確回報。

> **commit / push 由 AI 決定、直接執行,不用再問老闆**(老闆已授權);但**破壞性動作**(force push、`reset --hard`、drop/truncate)與**機密外洩風險**仍須先確認。push 前務必確認 `.env` 未被 add。

## 4. 合規檢查(check-repo)

對指定目錄,逐項核對:

- **結構**:§1 必備項目是否齊全(`AGENTS.md`、`docs/`、`.env.example`、`.gitignore`、`.git/`;`firstTask.md`/`tmp/` 視階段而定)。
- **.gitignore 有效性**:`.env`、`.env.*`、`tmp/` 確實被忽略;`.env.example` 未被忽略。
- **機密外洩**:`git ls-files` 不應出現 `.env`、`.env.*`(除 `.env.example`)、`tmp/` 內容。
- **文件一致**:`AGENTS.md` 有指向 `docs/`;`docs/` 非空。
- **收尾狀態**:套用 §3 的三項檢查,回報是否可安全收尾。

輸出一份清單:每項標 ✅ 合規 / ⚠️ 建議 / ❌ 缺失,並給修正動作。

## 5. Model routing(角色 agent)

依任務類型用不同 model,各角色一個 agent。Kiro CLI **沒有自動依任務切 model 的功能**;routing = 手動 `/agent <名稱>` 切換(或設 `keyboardShortcut` 一鍵切),也可用 subagent pipeline 讓各 stage 指定不同 `role`。

| agent | model | 負責 | 快捷鍵 |
|-------|-------|------|--------|
| `plan` | `claude-opus-5.5` | 規劃、拆解、架構決策(寫檔限 docs/、firstTask.md、tmp/、*.md) | `ctrl+shift+p` |
| `code` | `claude-sonnet-5.5` | 實作、改碼、重構、跑建置與測試 | `ctrl+shift+c` |
| `aux` | `claude-haiku-5.5` | 分析 log、寫單元測試、寫文件等輔助工作 | `ctrl+shift+u` |

**存放與同步**:

- **全域** `~/.kiro/agents/{plan,code,aux,orchestrator}.json`、`~/.kiro/skills/pipeline/` → **唯一維護處**。所有 repo(含 repoManager)的 session 都直接用這份,改一次全部生效。
- **備份** `templates/.kiro/` → `~/.kiro/` 不在版控,改完執行 `scripts/sync-kiro.sh` 複製回來並 commit。換機器時反向複製到 `~/.kiro/` 即可還原。
- **本地覆蓋** → 只有某 repo 需要跟全域不同(例如換 model)時,才在該 repo 放同名 `.kiro/agents/<name>.json`。本地同名檔會覆蓋全域,之後改全域不會影響它,沒必要就不要放。

**慣例**:

- 每個角色 agent 都**明確寫 `model`**。切 agent 時若新 agent 沒設 model 會沿用當下 model,寫死才可靠。
- model id 若後端不認會報 "model is not available",用 `/model` 查實際可用字串後更新本表與 agent 檔。
- 改 model routing **只改這裡 + agent 檔**;其他文件一律指回本節,勿重複清單。
- 內建 `/plan`(kiro_planner)不能綁 model,故自建 `plan` agent 取代之。

### 5a. 自動化 pipeline(orchestrator + /pipeline)

把 plan→code→test→doc 串成一條自動流程,各階段走各自 model。

- **`orchestrator` agent**:協調者,`tools` 含 `subagent`,`crew.availableAgents=[plan,code,aux]`、`trustedAgents=[plan,code,aux]`(spawn 不跳核可)。在 `~/.kiro/agents/`。
- **`pipeline` skill**:`/pipeline <任務>` → 用 subagent 跑四階段(`test`、`doc` 並行於 `code` 之後)。在 `~/.kiro/skills/pipeline/`。

**用法**:`/agent orchestrator` → `/pipeline <要做的任務>`。

**注意**:

- 必須從**有 subagent 工具**的 agent 發動(`orchestrator` 或內建 default);`plan`/`code`/`aux` 本身不含 subagent 工具,不能當發動點。
- `code`/`aux` 已把 `write`/`shell` 列入 `allowedTools`(免提示),`plan` 僅放行 `write`(限 `docs/`、`tmp/`、`*.md`);搭配 `orchestrator` 的 `trustedAgents`,pipeline **全程不跳核可,無需 `/tools trust-all`**。
- 安全網:`code`/`aux` 的 `shell.deniedCommands` 擋下破壞性指令(`rm -rf`、`git reset --hard`、force push、`git clean -f`、`sudo`、`mkfs`、`dd if=`、關機、`chmod -R 777`、寫入 `/dev/sd`、SQL `DROP/TRUNCATE`),這些仍會被拒,符合「破壞性動作先確認」。此清單為 best-effort,無法涵蓋所有危險寫法。
- 要臨時改某階段 model,可在該 stage 加 `model` 覆蓋 role 預設。
