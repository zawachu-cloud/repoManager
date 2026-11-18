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
🟡 Medium: [待辦] ai_session_export 不支援 Kiro CLI,需自寫 adapter(資料在 `~/.kiro/sessions/cli/`,`<id>.json` 為 metadata、`<id>.jsonl` 為對話)。
