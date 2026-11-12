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
