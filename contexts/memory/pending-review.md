# 待zawa確認的記憶變更

> 由每週三 reflector 產生。zawa同意哪幾項,就請 AI 套用到 `rules/` 或 `OBSERVATIONS.md`,然後把該項打勾或刪除。沒處理的會一直留著。

## 2026-11-19 週三回顧(2026-11-19 zawa核准,全部已套用)
- [x] **規則候選** → `rules/USER.md` §工作偏好(已確認):DB schema 變更一律 additive(add column/table if not exists),不對線上欄位或資料做 drop、破壞性 alter 或覆蓋;被取代的欄位保留並標 DEPRECATED。
  - 理由:三個 repo 的 AGENTS.md 各自重複寫同一條,新 repo 也會需要。放全域後,每個 repo 的 AGENTS.md 可改為指向這一條。(依據:hr、hr_db、stocktake 的 AGENTS.md;20261117_盤點的資料…3年(pg_cron 清理前先確認))
- [x] **規則候選** → `rules/USER.md` §工作偏好(已確認):程式碼檔案軟上限約 300 行,達 400 行時主動提拆分建議,硬上限 500 行(barrel、自動產生檔、測試除外)。主因是省 token。新功能優先放新模組,不往大檔追加。
  - 理由:hr 與 stocktake 的 AGENTS.md 都有同一套行數規則。放全域後,新 repo 不必再複製。(依據:hr、stocktake 的 AGENTS.md;20261113_目前工讀早退可以更正工時…(hr 內拆模組慣例))
- [x] **規則候選** → `rules/SOUL.md` §自主執行:動手前先用一句話複述範圍與效果。涉及改資料或不可逆動作時,同句說明將改什麼、影響哪些列,等zawa確認。
  - 理由:zawa會在 AI 動手前再確認一次需求理解。hr_db、stocktake 的 AGENTS.md 也要求刪除或修改 prod 前先說明並確認。目前 SOUL 只寫了停下來的三種情況,沒寫這個做法。(依據:OBSERVATIONS 2026-11-19 [偏好];20261117_盤點的資料…3年(先確認基準與是否套 prod);hr_db AGENTS.md)
- [x] **規則候選** → `rules/USER.md` §基本:語言:包含工具呼叫之間的過程敘述,一律用繁體中文;不要用日文或英文敘述。
  - 理由:現有規則只寫「回覆」。hr repo 的多個 session 出現英文過程敘述,有一個 session 的回覆用了日文,zawa需要自己翻譯。(依據:20261113_銀行_推估現值(日文回覆);20261111_每日帳目_要做調整、20261113_目前工讀早退可以更正工時(英文過程敘述))
- [x] **記憶整理**:2026-11-19「🟡 [待辦→2026-11-19 完成] ai_session_export 不支援 Kiro CLI」已完成,可併入「🟡 [完成] 第 2 階段:Kiro adapter + 遮罩…」,刪掉待辦那則。
- [x] **記憶整理**:2026-11-18「🔴 對話存檔要送雲端 embedding 前必須先排除機密專案…」已被 2026-11-19「🔴 全部在本地,不送雲端」取代。建議刪除,或改成一行「已被 11-19 取代」。遮罩規則調校(gitleaks)那則 🔴 仍有效,留著。
- [x] **記憶整理**:2026-11-19「🟡 [發現] session_created_reason 不可靠」與「🟡 [決策] 子 session 改用 parent_session_id」講同一件事,可合併成一則。
- [x] **記憶整理**:2026-11-19「🟡 [完成] 第 3 階段 Ollama + qwen3-embedding」與「🟡 [決策] embedding 模型選 qwen3-embedding:4b」可合併。同一天有兩個 Date 段落,也可合成一段。
- [x] **記憶整理**:2026-11-19 的 psapi-dotnet 三則(v1.4.22 發版、GameHistoryInner 白名單發現、docker 閘道偽造 X-Forwarded-For 待決)可合併成一則專案狀態,保留「待決」那句。另外「🟢 驗證 steering 規則」屬流水帳。
