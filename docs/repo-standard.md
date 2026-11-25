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
| `tmp/` | 目錄 | ❌ | 暫存/草稿/實驗資料。**不進版控**。一般搜尋略過,指定檔案可讀;若 repo 有 `.kiroignore`,不可列 `tmp/`。 |
| `.gitignore` | 檔案 | ✅ | 至少忽略 `.env`、`.env.*`(保留 `!.env.example`)、`tmp/`。 |
| `.git/` | 目錄 | — | git 儲存庫(`git init` 或 clone 產生)。 |

> 命名註記:本標準用 **`docs/`**(對齊 ~/proj/my/hr)。既有 repo 若用 `doc/` 亦視為合規,`check-repo` 兩者皆接受。

## 2. 建立新 repo 的流程(create-repo)

1. **決定建立方式**
   - local 新建:`mkdir -p <dir>` → `git init`(預設分支 `main`)。
   - 從 git url clone:`git clone <ssh-url> <dir>`(沿用遠端內容)。
2. **在 repo 內補齊必備結構**(上表),缺什麼補什麼;已存在的檔不覆蓋(clone 來的尤其小心)。
3. **寫入 `firstTask.md`**:把 zawa 口述的「我打算要做什麼任務」填進去,作為新 session 的第 1 份工作。
4. **精簡填寫 `AGENTS.md`**:專案名稱、一句話目標、已知技術棧、指向 `docs/` 與 `firstTask.md`。
5. **產出後提示**:請 zawa `cd <dir>` 後開新 session,新 session 先讀 `AGENTS.md` 與 `firstTask.md`。

## 3. 收尾規範(close session)

zawa 說「close session / 收工 / 結束這個 session」時,依序:

1. **檢查未辦事項**:本 session 有無待完成的修改、未跑的測試、未回覆的問題、TODO/暫緩項。**有就先列出並處理或向 zawa 確認**,不略過。
2. **檢查 git 狀態是否乾淨**:`git status` 應無未預期的未追蹤/未提交變更;確認 `.env` 等機密**沒有**被 add 進去。
3. **檢查本 session 的動作與文件是否一致**:這次改了什麼,就對照 `AGENTS.md`、`docs/`、`firstTask.md` 是否同步更新;發現落差就補正或明確回報。順便檢查 repoManager `rules/USER.md`「目前的專案」中當下 repo 那一行,需要才更新(只動那一行)。

最後執行 `~/proj/my/repoManager/scripts/session-export.sh --current` 匯出本 session 對話(見 `docs/context-system.md` §2a)。

> **commit / push 由 AI 決定、直接執行,不用再問 zawa**(zawa 已授權);但**破壞性動作**(force push、`reset --hard`、drop/truncate)與**機密外洩風險**仍須先確認。push 前務必確認 `.env` 未被 add。

## 4. 合規檢查(check-repo)

對指定目錄,逐項核對:

- **結構**:§1 必備項目是否齊全(`AGENTS.md`、`docs/`、`.env.example`、`.gitignore`、`.git/`;`firstTask.md`/`tmp/` 視階段而定)。
- **.gitignore 有效性**:`.env`、`.env.*`、`tmp/` 確實被忽略;`.env.example` 未被忽略。
- **.kiroignore(若存在)**:未列 `tmp/`(會擋指定讀取)。
- **機密外洩**:`git ls-files` 不應出現 `.env`、`.env.*`(除 `.env.example`)、`tmp/` 內容。
- **文件一致**:`AGENTS.md` 有指向 `docs/`;`docs/` 非空。
- **收尾狀態**:套用 §3 的三項檢查,回報是否可安全收尾。

輸出一份清單:每項標 ✅ 合規 / ⚠️ 建議 / ❌ 缺失,並給修正動作。

## 5. Model routing(角色 agent)

依任務類型用不同 model,各角色一個 agent。Kiro CLI **沒有自動依任務切 model 的功能**;routing = 手動 `/agent <名稱>` 切換(或設 `keyboardShortcut` 一鍵切),也可用 subagent pipeline 讓各 stage 指定不同 `role`。

| agent | model | 負責 | 快捷鍵 |
|-------|-------|------|--------|
| `plan` | `claude-opus-5.5` | 規劃、拆解、架構決策;pipeline 中當子項目架構師(寫檔限 docs/、firstTask.md、tmp/、*.md) | `ctrl+shift+p` |
| `code` | `claude-sonnet-5.5` | 實作、改碼、重構、跑建置與測試 | `ctrl+shift+c` |
| `aux` | `claude-haiku-5.5` | 分析 log、寫單元測試、寫文件等輔助工作(pipeline 的 `doc` 階段改用 sonnet,見 §5a) | `ctrl+shift+u` |

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

orchestrator 當總架構師(opus),直接跟 zawa 討論與規劃;子項目細部規劃視情況派 `plan`(子項目架構師),實作與收尾派 `code` / `aux`。目的是讓 zawa 能直接跟 orchestrator 對話,同時把吃 token 的細部規劃隔離在 subagent,控制 orchestrator 的 context。

- **`orchestrator` agent**:model `claude-opus-5.5`,`tools` 含 `subagent` 與 `write`(限 `docs/**`、`tmp/**`、`firstTask.md`、`*.md`),`crew.availableAgents=[plan,code,aux]`、`trustedAgents=[plan,code,aux]`(spawn 不跳核可)。在 `~/.kiro/agents/`。
- **分工**:orchestrator 自己做整體拆解、子項目介面與相依、跟 zawa 確認、整合;子項目邊界清楚且要讀大量程式碼 / 文件時才派 `plan`,小項目自己規劃。
- **大量 log**(單檔約 2000 行以上或多份):orchestrator 不整份讀,先派 `aux` 篩出錯誤段落、時間線、可疑點寫進 `tmp/log-<主題>.md`,只回摘要與證據位置(檔名:行號);orchestrator 依摘要跟 zawa 討論,需要時只讀特定段落。一般大小的 log 自己讀。
- **`pipeline` skill**:`/pipeline <任務>` → 拆解並確認 → 規劃子項目(自己或派 plan,可並行)→ 每個子項目跑 `code`,之後 `test`、`doc` 並行。`doc` 階段用 `aux` 角色但 model 覆蓋為 `claude-sonnet-5.5`(文件品質比 haiku 好,成本低於 opus)。在 `~/.kiro/skills/pipeline/`。

**用法**:`/agent orchestrator` → 直接討論,或 `/pipeline <要做的任務>`。

- 有需要 zawa 決定的選項時(orchestrator 拆解時,或 plan 回報時),會先停下來問;zawa**直接回覆**即可接續,不用再打 `/pipeline`。
- 跑完後回覆修改意見,也是直接回覆;orchestrator 只重跑需要的部分,子項目計畫小改自己改,大改重派 plan。
- 每個子項目的計畫寫在 `tmp/plan-<子項目>.md`(不進版控)。plan 回報只給「摘要」與「需要 zawa 決定」兩段,完整計畫留在檔案裡。

**注意**:

- 必須從**有 subagent 工具**的 agent 發動(`orchestrator` 或內建 default);`plan`/`code`/`aux` 本身不含 subagent 工具,不能當發動點。
- `code`/`aux` 已把 `write`/`shell` 列入 `allowedTools`(免提示),`plan`、`orchestrator` 僅放行 `write`(限 `docs/`、`tmp/`、`*.md`);搭配 `orchestrator` 的 `trustedAgents`,pipeline **全程不跳核可,無需 `/tools trust-all`**。
- 安全網:`code`/`aux` 的 `shell.deniedCommands` 擋下破壞性指令(`rm -rf`、`git reset --hard`、force push、`git clean -f`、`sudo`、`mkfs`、`dd if=`、關機、`chmod -R 777`、寫入 `/dev/sd`、SQL `DROP/TRUNCATE`),這些仍會被拒,符合「破壞性動作先確認」。此清單為 best-effort,無法涵蓋所有危險寫法。
- 要臨時改某階段 model,可在該 stage 加 `model` 覆蓋 role 預設。

### 5b. 拋棄式測試庫的 lab 規則

- **為什麼全域不放行 DROP**:`deniedCommands` 與 `permissions` 只做字串比對,看不出 DROP 打到哪個庫,一行指令又能串多個動作。所以全域 `code` 一律擋 `DROP/TRUNCATE`,不改。
- **何時可用**:該 repo 只碰拋棄式測試容器 / 測試庫(壞了重建即可),不碰任何正式或共用資料。
- **怎麼套用**:
  1. 複製 `templates/.kiro/agents/code-lab.json` 到該 repo 的 `.kiro/agents/code.json`(`name` 維持 `code`,repo 內同名 agent 會覆蓋全域)。
  2. 把 `__PROTECTED__` 換成受保護容器的名稱關鍵字(同一台主機上不可動的服務)。
  3. 要從 `orchestrator` 派工 DROP 時,另外複製 `~/.kiro/agents/orchestrator.json` 到該 repo 的 `.kiro/agents/orchestrator.json`,刪掉 shell deny 裡 8 條 `DROP/TRUNCATE` 規則,並刪掉 `kiroUpgrade` 欄位。原因是 subagent 執行指令時,父 agent 與子 agent 兩層的 deny 都會檢查,符合任一層就擋(擋下訊息的 `Source` 分別是 `agent-profile` 與 `subagent-profile`)。orchestrator 本身沒有 shell 工具,拿掉這些規則不會讓它自己能下指令。default agent 沒有這類 deny,從 default 派工不需要這一步。
  4. 在該 repo 的 AGENTS.md 註明:覆蓋了全域 `code`(與 `orchestrator`)、可 DROP 的測試容器 / 庫清單、受保護容器清單。
- **範本差異**:相對全域 `code`,只移除 `DROP/TRUNCATE` 的擋規則,並加上受保護容器的 `docker stop/rm/restart/kill/exec/update/rename` 與 `docker compose down` 擋規則。其餘(`rm -`、force push 等)照擋。`docker ps`、`docker inspect` 不擋,用來確認受保護容器狀態。
- **範本來源**:`code-lab.json` 的來源是 `templates/`,不在 `~/.kiro/`,不列入 `scripts/sync-kiro.sh`。
- **限制可刪的庫名**:字串比對做不到,改在資料庫帳號權限做(例如只授權 `tmp\_%` 的帳號)。
