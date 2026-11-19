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
🟡 Medium: [完成] 第 3 階段:Ollama(user-level,127.0.0.1)+ qwen3-embedding:4b,`/recall` skill 查對話存檔與本檔。評測與換電腦步驟見 repoManager `docs/context-system.md` §4b。
🟡 Medium: [決策] embedding 模型選 qwen3-embedding:4b(14 題中文查詢 MRR 0.77,bge-m3 0.73,0.6b 0.67);0.6b 是備案。
🟢 Low: [發現] cron 環境沒有 systemd user bus,`systemctl --user` 會失敗;檢查 Ollama 改用 `curl 127.0.0.1:11434/api/version`。

Date: 2026-11-19

🔴 High: [約束] 備份加密金鑰(age)只存在這台電腦,電腦壞了備份就打不開。老闆要自己另存一份到密碼管理器等安全處,AI 不會搬動金鑰。換電腦前必須先確認這件事。
🔴 High: [決策] orchestrator 改成 opus,兼任規劃,直接跟老闆討論。plan 保留,當子項目架構師,由 orchestrator 派出去,讓大量讀碼的工作留在 subagent 的 context。plan 只回「摘要」與「需要老闆決定」,完整計畫寫進 tmp/plan-<子項目>.md。
🟡 Medium: [偏好] 老闆希望直接跟 orchestrator 討論,不想每輪都轉給 plan 再轉回來,能接受 context 變長。成本與 context 取捨由老闆自己判斷,這次他用「cowork」的角度做決定。
🟡 Medium: [決策] 老闆常需要讀大量 log。單檔約 2000 行以上或多份 log 時,orchestrator 先派 aux 篩出錯誤段落、時間線與可疑點,寫進 tmp/log-<主題>.md,只回摘要與檔名:行號。門檻是估的,待實際使用後調整。
🟡 Medium: [發現] 看 log、討論、寫 md 回覆這類工作,orchestrator 不派 subagent 是合理的。subagent 沒辦法問老闆,每輪都要重新交代脈絡。沒派 subagent 不代表設計有問題。
🟡 Medium: [決策] 子 session 改用 parent_session_id 判斷(727 個 Kiro session 中有 30 個)。session_created_reason 會把老闆的主對話也標成 subagent,照它過濾會丟掉約 92%。對帳:727 = 470 匯出 + 30 子 session + 227 空 session。
🟡 Medium: [決策] ai_session_export 在 GitHub 上 fork 無法設成 private。做法是本地 clone,upstream 指原作者,origin 指自己的 private repo。PR 回原作者屬於公開動作,要老闆另外授權。
🟢 Low: [發現] Ollama 的官方安裝腳本需要 sudo,所以改用 user-level 壓縮包,以 systemd user service 常駐並只綁 127.0.0.1。索引 rebuild 只重算 mtime 或大小有變的檔案,增量更新約 13 秒,所以 cron 每天跑成本低。
🟢 Low: [發現] semantic-search 同一個檔案會佔掉太多結果名額,查詢時候選數要放大。4B 模型有一題排第 9,屬於已知限制,已寫進文件。
🟡 Medium: [專案狀態] psapi-dotnet 發了 v1.4.22:GameHistoryInner、GameListInner、GetHostInfoInner 三支內部 endpoint 不驗 JWT,只靠 Inner IP 白名單。OfflineMiddleware 用完整路徑比對,不用 Contains。QA 和 prod 部署前,維運要先確認後台 server IP 在 Inner 白名單。
🟡 Medium: [發現] psapi-dotnet 的 GameHistoryInner 原本沒掛 Inner 白名單,只靠 JWT 擋人。拿掉 JWT 之前必須同版掛上白名單,否則會出現 IDOR。AI 動工前先查現況,才發現「規劃中」的白名單其實沒做。
🟡 Medium: [待決] psapi-dotnet 在 dev 發現:同機程式直連 container 時,docker 閘道位址是可信代理,可偽造 X-Forwarded-For 繞過 Inner 白名單。這是既有漏洞,不是 v1.4.22 造成的。AI 建議先記進文件並請維運查 stage/prod,不改程式。另外 GameHistory、V2、All、Diff 尚無白名單,要不要另開一案待老闆決定。
🟡 Medium: [偏好] 老闆在 AI 動手前,會再確認一次它對需求的理解(例如「Inner 是不是不套 JWT」)。AI 交付前先用一句話複述範圍與效果,老闆能用這句話快速確認。
🟢 Low: [驗證] 驗證 steering 規則是否生效,用「不要用任何工具,只回答 USER.md 的稱呼」這類短問題,在 /tmp 和 stocktake 各測一次即可。
🟢 Low: [專案狀態] 老闆在 WSL 設定 openssh-server,讓 Windows 端能免密碼 ssh 進來。sshd 仍允許密碼登入,AI 建議改成只允許金鑰,老闆還沒回覆。
