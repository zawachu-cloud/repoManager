# Memory Observations

三層記憶的 L1/L2 層(L3 是 `rules/`)。設計見 `docs/context-system.md`。

- 目前:**手動**記錄(收工時或發現值得記的經驗時)。
- 第 4 階段後:每日 observer 自動追加,每週 reflector 整理,提出的規則候選要老闆核准才合入 `rules/`。

## 格式

```
Date: YYYY-MM-DD

🔴 High: [方法論/約束] 描述
🟡 Medium: [專案狀態/決策] 描述
🟢 Low: [任務流水] 描述
```

- **🔴 High**:跨專案通用的經驗、硬性約束、影響架構的重大決策。永久保留,可能晉升進 `rules/`。
- **🟡 Medium**:進行中專案的關鍵進展、決策背景,未來幾週還要參考。
- **🟢 Low**:日常流水、一次性 debug。reflector 定期清掉。

**不寫機密**:不記金鑰、個資、薪資數字;機密專案只記「做了什麼決定」,不記資料內容。

## 怎麼查(不要整份讀)

```bash
grep -n "關鍵字" contexts/memory/OBSERVATIONS.md
grep -A 20 "Date: $(date -d '7 days ago' +%Y-%m-%d)" contexts/memory/OBSERVATIONS.md
```

---

<!-- 以下為記錄區,新條目追加在最後 -->

Date: 2026-11-18

🔴 High: [約束] 對話存檔要送雲端 embedding 前,必須先排除機密專案(hr、hr_db、income_ana、payroll)並遮罩金鑰/個資,再用 gitleaks 類工具掃過;遮罩在匯出時做,存檔本身就要乾淨。
🟡 Medium: [決策] context-infrastructure 架構整合進 repoManager(private repo),不另開 context repo。ai_session_export、semantic-search-skill 當外部工具安裝,不搬進來。
🟡 Medium: [決策] L3 規則透過 `scripts/link-rules.sh` symlink 到 `~/.kiro/steering/`,所有 repo 自動載入。
🟡 Medium: [待辦→2026-11-19 完成] ai_session_export 不支援 Kiro CLI,需自寫 adapter。

Date: 2026-11-19

🔴 High: [約束] 對話存檔與 embedding 全部在本地,不送雲端(取代 2026-11-18 的雲端方案與 hr 類排除清單)。所有 repo 都收,記憶只排除憑證與資料內容(姓名、身分證、薪資數字、帳號)。
🟡 Medium: [決策] 對話匯出走增量狀態檔(session id + updated_at)。`/close-session` 只匯出當下 session(`$KIRO_SESSION_ID`);cron 每天 12:30 跑全部增量補漏。
🟡 Medium: [發現] Kiro 的 `session_created_reason` 不可靠:老闆直接開的主對話也標 `subagent`,不能用它過濾子 session。
🟡 Medium: [決策] USER.md「目前的專案」不一次補齊;`/close-session` 更新當下 repo 那一行,每週三 reflector 依對話存檔回顧全部專案行。
🟡 Medium: [完成] 第 2 階段:Kiro adapter + 遮罩(fork `zawachu-cloud/ai_session_export`)、加密備份(`zawachu-cloud/private_session_data`)、cron 12:30、`/close-session` 匯出步驟。工具位置與換電腦步驟見 repoManager `docs/context-system.md` §4a。
🔴 High: [約束] 遮罩規則要拿真實存檔跑 gitleaks 調校,再回頭查誤判。第一次全量 gitleaks 抓到 12 筆漏網(GitLab runner token、Supabase key),調完再清掉誤判(「密碼是 Supabase 那組」這類中文句子、sudoers NOPASSWD)。
🟢 Low: [發現] upstream ai_session_export 的 `--source all` 遇到沒裝的工具(OpenCode)會直接報錯,所以入口腳本逐一跑 kiro、claude-code。
