# Memory Observations

三層記憶的 L1/L2 層(L3 是 `rules/`)。設計見 `docs/context-system.md`。

- 每天 12:30 observer 自動追加;每週三 reflector 清掉 30 天以上的 🟢,規則候選寫到 `pending-review.md`,zawa 核准才合入 `rules/`。
- 手動追加也可以(收工時或發現值得記的經驗時)。

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

🟡 Medium: [決策] context-infrastructure 架構整合進 repoManager(private repo),不另開 context repo。ai_session_export、semantic-search-skill 當外部工具安裝,不搬進來。
🟡 Medium: [決策] L3 規則透過 `scripts/link-rules.sh` symlink 到 `~/.kiro/steering/`,所有 repo 自動載入。

Date: 2026-11-19

🔴 High: [約束] 對話存檔與 embedding 全部在本地,不送雲端(取代 2026-11-18 的雲端方案與 hr 類排除清單)。所有 repo 都收,記憶只排除憑證與資料內容(姓名、身分證、薪資數字、帳號)。
🟡 Medium: [決策] 對話匯出走增量狀態檔(session id + updated_at)。`/close-session` 只匯出當下 session(`$KIRO_SESSION_ID`);cron 每天 12:30 跑全部增量補漏。
🟡 Medium: [決策] USER.md「目前的專案」不一次補齊;`/close-session` 更新當下 repo 那一行,每週三 reflector 依對話存檔回顧全部專案行。
🟡 Medium: [完成] 第 2 階段(補上 ai_session_export 原本不支援的 Kiro CLI):Kiro adapter + 遮罩(fork `zawachu-cloud/ai_session_export`)、加密備份(`zawachu-cloud/private_session_data`)、cron 12:30、`/close-session` 匯出步驟。工具位置與換電腦步驟見 repoManager `docs/context-system.md` §4a。
🔴 High: [約束] 遮罩規則要拿真實存檔跑 gitleaks 調校,再回頭查誤判。第一次全量 gitleaks 抓到 12 筆漏網(GitLab runner token、Supabase key),調完再清掉誤判(「密碼是 Supabase 那組」這類中文句子、sudoers NOPASSWD)。
🟢 Low: [發現] upstream ai_session_export 的 `--source all` 遇到沒裝的工具(OpenCode)會直接報錯,所以入口腳本逐一跑 kiro、claude-code。
🟡 Medium: [完成] 第 3 階段:Ollama(user-level,127.0.0.1)+ qwen3-embedding:4b,`/recall` skill;模型評測 MRR 4b 0.77 / bge-m3 0.73 / 0.6b 0.67,0.6b 是備案; 查對話存檔與本檔。評測與換電腦步驟見 repoManager `docs/context-system.md` §4b。
🟢 Low: [發現] cron 環境沒有 systemd user bus,`systemctl --user` 會失敗;檢查 Ollama 改用 `curl 127.0.0.1:11434/api/version`。
🔴 High: [約束] 備份加密金鑰(age)只存在這台電腦,電腦壞了備份就打不開。zawa 要自己另存一份到密碼管理器等安全處,AI 不會搬動金鑰。換電腦前必須先確認這件事。
🔴 High: [決策] orchestrator 改成 opus,兼任規劃,直接跟 zawa 討論。plan 保留,當子項目架構師,由 orchestrator 派出去,讓大量讀碼的工作留在 subagent 的 context。plan 只回「摘要」與「需要 zawa 決定」,完整計畫寫進 tmp/plan-<子項目>.md。
🟡 Medium: [偏好] zawa 希望直接跟 orchestrator 討論,不想每輪都轉給 plan 再轉回來,能接受 context 變長。成本與 context 取捨由 zawa 自己判斷,這次他用「cowork」的角度做決定。
🟡 Medium: [決策] zawa 常需要讀大量 log。單檔約 2000 行以上或多份 log 時,orchestrator 先派 aux 篩出錯誤段落、時間線與可疑點,寫進 tmp/log-<主題>.md,只回摘要與檔名:行號。門檻是估的,待實際使用後調整。
🟡 Medium: [發現] 看 log、討論、寫 md 回覆這類工作,orchestrator 不派 subagent 是合理的。subagent 沒辦法問 zawa,每輪都要重新交代脈絡。沒派 subagent 不代表設計有問題。
🟡 Medium: [決策] 子 session 改用 parent_session_id 判斷(727 個 Kiro session 中有 30 個)。Kiro 的 session_created_reason 不可靠,zawa 直接開的主對話也標成 subagent,照它過濾會丟掉約 92%。對帳:727 = 470 匯出 + 30 子 session + 227 空 session。
🟡 Medium: [決策] ai_session_export 在 GitHub 上 fork 無法設成 private。做法是本地 clone,upstream 指原作者,origin 指自己的 private repo。PR 回原作者屬於公開動作,要 zawa 另外授權。
🟢 Low: [發現] Ollama 的官方安裝腳本需要 sudo,所以改用 user-level 壓縮包,以 systemd user service 常駐並只綁 127.0.0.1。索引 rebuild 只重算 mtime 或大小有變的檔案,增量更新約 13 秒,所以 cron 每天跑成本低。
🟢 Low: [發現] semantic-search 同一個檔案會佔掉太多結果名額,查詢時候選數要放大。4B 模型有一題排第 9,屬於已知限制,已寫進文件。
🟡 Medium: [專案狀態] psapi-dotnet v1.4.22:GameHistoryInner、GameListInner、GetHostInfoInner 三支內部 endpoint 不驗 JWT,改掛 Inner IP 白名單(GameHistoryInner 原本只靠 JWT,拿掉前必須同版掛白名單,否則 IDOR);OfflineMiddleware 用完整路徑比對。QA/prod 部署前維運要確認後台 server IP 在白名單。**待決**:dev 發現 docker 閘道位址是可信代理,同機程式可偽造 X-Forwarded-For 繞過白名單(既有漏洞),建議先記文件並請維運查 stage/prod;GameHistory、V2、All、Diff 尚無白名單,是否另開一案待 zawa 決定。
🟡 Medium: [偏好] zawa 在 AI 動手前,會再確認一次它對需求的理解(例如「Inner 是不是不套 JWT」)。AI 交付前先用一句話複述範圍與效果,zawa 能用這句話快速確認。
🟡 Medium: [完成] 第 4 階段(repoManager):唯讀 `heartbeat` agent(無 write/shell,結果由腳本寫入)跑 observer(每天 12:30,匯出與索引之後)與 reflector(每週三)。heartbeat 自己的 session 不匯出,避免觀察自己。設計見 `docs/context-system.md`。
🟡 Medium: [發現] observer 挑「新增對話」改用檔案大小判斷,不用 mtime。`--full` 重匯出會讓所有檔案 mtime 變新,dry-run 一次抓了 40 個舊 session。
🔴 High: [經驗] 腳本要先拿真實資料離線驗證確定性部分(GC、USER.md 專案行替換)再接 cron。這次抓到兩個 bug:專案段落的 regex 會越過清單吃掉後面的段落,以及專案行被重新排序。
🟡 Medium: [約束] cron 的 PATH 不含 `~/.local/bin`(kiro-cli、gitleaks 都在那),腳本要自己補 PATH,並用乾淨環境實跑一次才算驗證過。
🟢 Low: [發現] `kiro-cli chat --no-interactive` 偶爾遇到服務端暫時性錯誤(dispatch failure),`run_kiro` 加一次自動重試。新檔案要先 `git add` 再 commit,否則 commit 會失敗。
🟢 Low: [專案狀態] Kiro CLI 從 2.27.0 升到 3.5.0(2026-11-19)。
🟡 Medium: [偏好] zawa 收工時說「都先不處理」,代表待決事項只記進文件,AI 不要再追問或擅自動手。psapi-dotnet 有 3 個 `[261104]` 簽章文件是 untracked,不屬於該次任務,AI 不 commit。
🔴 High: [約束] shell deny 規則只比對指令字串,判斷不出 DROP 實際打到哪個庫(一行可串多個指令,連線目標在 env)。全域 code/aux 保留 DROP/TRUNCATE 攔截;只碰拋棄式測試庫的 repo 才放 repo 內 `.kiro/agents/code.json`(範本 `templates/.kiro/agents/code-lab.json`,規範 `docs/repo-standard.md` §5b)。要限制可刪的庫名,改在 DB 帳號權限做。
🟡 Medium: [發現] Kiro CLI 3.x 升級把 agent 的 regex `deniedCommands` 自動轉成 `permissions.rules` glob,轉換時丟掉單字邊界與空白(例如 `\brm\s+-` 變 `*rm*-*`),information_schema 加 `-` 參數也會被擋。已改成帶空白的 glob(commit 87e99a4)。手改 permissions 後要留意 kiroUpgrade 會不會蓋回。
🟡 Medium: [決策] AI 被指令規則擋時,不改寫指令(包成腳本檔、藏進 SQL 檔)繞過,停下來回報,由 zawa 決定是否改規則。派 subagent 時要求被擋就附指令原文與擋下訊息原文,不只給摘要。
🟡 Medium: [專案狀態] dbUpgrade(`~/proj/db/dbUpgrade`)已套用 lab 規則:可對 lab_mysql57_test / lab_mysql80_test 的庫 DROP,gameapi 容器的變更類 docker 指令擋。repo 內 code agent 是否覆蓋 orchestrator 派出的 subagent 尚未實測。dbUpgrade 沒設 remote,只有本地 commit。

Date: 2026-11-23

🟡 Medium: [偏好] zawa 認為 USER.md 的背景、擅長領域、會讓你煩的事等空欄位沒有意義,決定不填,已刪除這些欄位。AI 不要再提醒補填。
🟡 Medium: [決策] hr、hr_db、stocktake 的 AGENTS.md 與全域 USER.md 重複的 DB additive 規則和行數上限,改成指向全域規則,只留 repo 自己的細節。同一條規則只寫一處。
🟡 Medium: [決策] sync 時發現 `~/.kiro/agents/` 被 Orca 工具加了 hooks,內含這台電腦專用路徑,不放進 templates 備份。只 commit 自己改的檔。
🟢 Low: [發現] 備份到 private_session_data 的檔案以雜湊命名,對照表加密另存,GitHub 上看不到對話標題。gitleaks 會把本機備份索引(sha256)誤判成金鑰,要在 `.gitleaks.toml` 排除,否則 cron 備份被擋。
🟢 Low: [決策] 要從存檔移除某個 session 得做三件事:刪 Markdown 並移出索引、加進匯出排除清單(否則 cron 會重匯)、加密備份的 git 歷史仍留舊版。zawa 要求刪記憶時,只刪 OBSERVATIONS 等記憶,對話存檔預設保留。
🟡 Medium: [決策] .kiroignore 會擋指定讀取,.gitignore 只讓搜尋略過;tmp/ 只放 .gitignore。起因:hr 的 .kiroignore 擋 tmp/,pipeline 讀不回計畫檔與 zawa 放的資料。

Date: 2026-11-24

🟡 Medium: [專案狀態] zawa 從 2026-11-24 開始學用 orca(透過 SSH 連進 WSL),原本 psapi-dotnet 的 API 開發都在 ~/proj/api/psapi-dotnet 的 main 上直接做,現在改在 ~/orca/workspaces/<repo>/<worktree> 底下工作,例如 apiServer/killifish。
🟡 Medium: [發現] orca 的 workspace 目錄是 workspaces/<專案>/<worktree 名>,和 zawa 原本預期的 workspaces/<專案> 不同。zawa 也發現 orca 的 .env 管理方式和他以往不同,之後教他 orca 的流程時要特別說明這兩點。
🟢 Low: [發現] orca 會自動呼叫 Claude Code 產生 git branch 名稱。在 killifish 這幾個 session 中 Claude Code 未登入(Not logged in),所以 AI 沒有回答,只留下 prompt 存檔。要用這項功能得先在 WSL 裡 /login。
🟢 Low: [專案狀態] zawa 在 orca 下手動建了 psapi-dotnet 的 git 目錄(~/orca/workspaces/api/git-gitlab.com-bu00-rd-api-psapi-dotnet.git),覺得結果怪怪的,請 AI 檢查。這可能是 orca 對 repo 的 clone 或 bare 結構,內容待後續確認。

Date: 2026-11-25

🟡 Medium: [決策] /pipeline 改成 v2,吸收 mattpocock/skills 的 spec → TDD → review 作法:保留 orchestrator 分派、model routing、tmp/ 計畫檔,不搬 issue tracker、worktree、整合 branch、PR。測試改由 code 先寫(TDD),移除 aux 的 test 階段;中型以上任務新增 plan(opus)審查階段,只讀不改;測試的驗證入口由 orchestrator / plan 自己決定,有疑慮才用白話問 zawa。計畫模板與 TDD 規則放 `~/.kiro/skills/pipeline/`(plan-template.md、tdd.md),NOTICE.md 附 MIT 授權。sync-kiro.sh 改成同步整個 skill 目錄。

🟡 Medium: [決策] 採用 improve-codebase-architecture 改寫版(來源 mattpocock/skills,MIT),放全域 `~/.kiro/skills/improve-codebase-architecture/`:orchestrator 派 plan 掃描並寫 Markdown 報告到 repo 的 `tmp/`,zawa 挑一項後追問、必要時 design it twice,決策清楚再交給 /pipeline 實作,本身不改程式碼。不建 GLOSSARY.md 與 docs/adr/,用語與否決理由記進該 repo 的 docs/。同批評估過 diagnosing-bugs,暫不做,先驗證新 pipeline。

🟡 Medium: [決策] 每個 repo 必備 `docs/glossary.md`(名詞表),取代先前「不建 GLOSSARY.md」的做法。格式比 mattpocock 多「程式名稱」欄,內容可先放空。寫入規則:zawa 講明或確認的直接寫,AI 從程式推出的標「(待確認)」,用語衝突時當場問 zawa 並記進「曾經混用」。範本在 `templates/docs/glossary.md`,pipeline、improve-codebase-architecture、create-repo、check-repo、close-session 都依它運作。

🟡 Medium: [決策] close session 新增第 4 步「清理暫存」(`docs/repo-standard.md` §3):本 session 由 AI 建立、工作已完成的 `tmp/` 檔(plan-*、review-*、arch-*、log-*、下載的參考原文、.bak、下載暫存)直接刪;zawa 放的資料、舊 session 留下或來源不明、工作未完成的檔先問。只刪 `tmp/` 內的檔,逐檔刪,不用 `rm -rf`,空目錄用 `rmdir`,`tmp/` 本身保留。理由:zawa 已授權這類刪除,範圍以外仍依「破壞性動作先確認」。
