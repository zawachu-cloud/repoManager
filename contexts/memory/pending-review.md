# 待 zawa 確認的記憶變更

> 由每週三 reflector 產生。zawa 同意哪幾項,就請 AI 套用到 `rules/` 或 `OBSERVATIONS.md`,然後把該項打勾或刪除。沒處理的會一直留著。

## 2026-11-19 週三回顧(2026-11-19 zawa 核准,全部已套用)
- [x] **規則候選** → `rules/USER.md` §工作偏好(已確認):DB schema 變更一律 additive(add column/table if not exists),不對線上欄位或資料做 drop、破壞性 alter 或覆蓋;被取代的欄位保留並標 DEPRECATED。
  - 理由:三個 repo 的 AGENTS.md 各自重複寫同一條,新 repo 也會需要。放全域後,每個 repo 的 AGENTS.md 可改為指向這一條。(依據:hr、hr_db、stocktake 的 AGENTS.md;20261117_盤點的資料…3年(pg_cron 清理前先確認))
- [x] **規則候選** → `rules/USER.md` §工作偏好(已確認):程式碼檔案軟上限約 300 行,達 400 行時主動提拆分建議,硬上限 500 行(barrel、自動產生檔、測試除外)。主因是省 token。新功能優先放新模組,不往大檔追加。
  - 理由:hr 與 stocktake 的 AGENTS.md 都有同一套行數規則。放全域後,新 repo 不必再複製。(依據:hr、stocktake 的 AGENTS.md;20261113_目前工讀早退可以更正工時…(hr 內拆模組慣例))
- [x] **規則候選** → `rules/SOUL.md` §自主執行:動手前先用一句話複述範圍與效果。涉及改資料或不可逆動作時,同句說明將改什麼、影響哪些列,等 zawa 確認。
  - 理由:zawa 會在 AI 動手前再確認一次需求理解。hr_db、stocktake 的 AGENTS.md 也要求刪除或修改 prod 前先說明並確認。目前 SOUL 只寫了停下來的三種情況,沒寫這個做法。(依據:OBSERVATIONS 2026-11-19 [偏好];20261117_盤點的資料…3年(先確認基準與是否套 prod);hr_db AGENTS.md)
- [x] **規則候選** → `rules/USER.md` §基本:語言:包含工具呼叫之間的過程敘述,一律用繁體中文;不要用日文或英文敘述。
  - 理由:現有規則只寫「回覆」。hr repo 的多個 session 出現英文過程敘述,有一個 session 的回覆用了日文,zawa 需要自己翻譯。(依據:20261113_銀行_推估現值(日文回覆);20261111_每日帳目_要做調整、20261113_目前工讀早退可以更正工時(英文過程敘述))
- [x] **記憶整理**:2026-11-19「🟡 [待辦→2026-11-19 完成] ai_session_export 不支援 Kiro CLI」已完成,可併入「🟡 [完成] 第 2 階段:Kiro adapter + 遮罩…」,刪掉待辦那則。
- [x] **記憶整理**:2026-11-18「🔴 對話存檔要送雲端 embedding 前必須先排除機密專案…」已被 2026-11-19「🔴 全部在本地,不送雲端」取代。建議刪除,或改成一行「已被 11-19 取代」。遮罩規則調校(gitleaks)那則 🔴 仍有效,留著。
- [x] **記憶整理**:2026-11-19「🟡 [發現] session_created_reason 不可靠」與「🟡 [決策] 子 session 改用 parent_session_id」講同一件事,可合併成一則。
- [x] **記憶整理**:2026-11-19「🟡 [完成] 第 3 階段 Ollama + qwen3-embedding」與「🟡 [決策] embedding 模型選 qwen3-embedding:4b」可合併。同一天有兩個 Date 段落,也可合成一段。
- [x] **記憶整理**:2026-11-19 的 psapi-dotnet 三則(v1.4.22 發版、GameHistoryInner 白名單發現、docker 閘道偽造 X-Forwarded-For 待決)可合併成一則專案狀態,保留「待決」那句。另外「🟢 驗證 steering 規則」屬流水帳。

## 2026-11-25 週三回顧
- [ ] **規則候選** → `rules/USER.md` §工作偏好(已確認):維運轉貼的問題或反饋(貼原文、沒有其他指示):先查程式碼取證,結論先講並附檔案:行號,整理成可直接轉貼給維運的回覆;反饋指向的文件不在本 repo 時,先回報可能位置,不猜、不改別處。
  - 理由:zawa 每次只貼維運原文,沒有多說指示,AI 的做法每次相同(查證、給可轉貼的結論)。寫下來可以讓這個流程固定,也避免誤改方向相反的文件。(依據:20261112_維運問了以下問題、20260821_維運反饋如下_2、20260730_維運回報、20260713_維運反應_v1_1_14、20260914_前幾次的commit_有改到_proxy_psx1)
- [ ] **記憶整理**:2026-11-19 的 🔴 orchestrator 改成 opus 兼任規劃、🟡 zawa 想直接跟 orchestrator 討論、🟡 看 log 與討論不派 subagent 合理,三則講同一個設計,可合併成一則 🔴 [決策] orchestrator 分工。
- [ ] **記憶整理**:2026-11-19 的 🔴 shell deny 規則只比對字串、🟡 Kiro 3.x 把 deniedCommands 轉成 glob 丟掉邊界、🟡 被擋時不改寫繞過,都屬於 shell 權限規則,建議合併成一則 🔴,細節指向 docs/repo-standard.md §5b。
- [ ] **記憶整理**:2026-11-19 的 🟡 第 2、3、4 階段 [完成] 已是完成紀錄,細節在 docs/context-system.md。建議壓成一則「context 系統 1 到 4 階段已完成」,只留 repo 與文件指向。
- [ ] **記憶整理**:2026-11-19 的 🟡 USER.md 專案行由 /close-session 與週三 reflector 更新,和 2026-11-23 的 🟡 空欄位已刪除是同一份檔的演進,可合併成一則。
- [ ] **記憶整理**:2026-11-24 的 🟡 zawa 改用 orca 與兩則 🟢 killifish、手動建 git 目錄(Claude Code 未登入、結構怪怪的)屬同一件事。待確認結果後合併成一則 🟡,並更新 psapi-dotnet v1.4.22 那則的工作路徑。
