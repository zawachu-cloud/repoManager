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
🟡 Medium: [決策] USER.md 只寫確定的事。背景等空欄位 zawa 決定不填,已刪除,AI 不再提醒補填。「目前的專案」不一次補齊:`/close-session` 更新當下 repo 那一行,每週三 reflector 依對話存檔回顧全部專案行。
🟡 Medium: [完成] context 系統第 1 到 4 階段已完成:第 2 階段 ai_session_export 匯出與加密備份,第 3 階段 Ollama 語意搜尋與 /recall,第 4 階段 heartbeat observer/reflector。細節見 docs/context-system.md §4a 到 §4c。
🔴 High: [約束] 遮罩規則要拿真實存檔跑 gitleaks 調校,再回頭查誤判。第一次全量 gitleaks 抓到 12 筆漏網(GitLab runner token、Supabase key),調完再清掉誤判(「密碼是 Supabase 那組」這類中文句子、sudoers NOPASSWD)。
🟢 Low: [發現] upstream ai_session_export 的 `--source all` 遇到沒裝的工具(OpenCode)會直接報錯,所以入口腳本逐一跑 kiro、claude-code。
🟢 Low: [發現] cron 環境沒有 systemd user bus,`systemctl --user` 會失敗;檢查 Ollama 改用 `curl 127.0.0.1:11434/api/version`。
🔴 High: [約束] 備份加密金鑰(age)只存在這台電腦,電腦壞了備份就打不開。zawa 要自己另存一份到密碼管理器等安全處,AI 不會搬動金鑰。換電腦前必須先確認這件事。
🔴 High: [決策] orchestrator 改用 opus,兼任規劃並直接跟 zawa 討論,zawa 能接受 context 變長。plan 當子項目架構師,由 orchestrator 派出,大量讀碼留在 subagent 的 context;plan 只回摘要與需 zawa 決定的事,完整計畫寫進 tmp/plan-<子項目>.md。看 log、討論、寫 md 這類工作,orchestrator 不派 subagent 是合理的,因為 subagent 無法問 zawa。
🟡 Medium: [決策] zawa 常需要讀大量 log。單檔約 2000 行以上或多份 log 時,orchestrator 先派 aux 篩出錯誤段落、時間線與可疑點,寫進 tmp/log-<主題>.md,只回摘要與檔名:行號。門檻是估的,待實際使用後調整。
🟡 Medium: [決策] 子 session 改用 parent_session_id 判斷(727 個 Kiro session 中有 30 個)。Kiro 的 session_created_reason 不可靠,zawa 直接開的主對話也標成 subagent,照它過濾會丟掉約 92%。對帳:727 = 470 匯出 + 30 子 session + 227 空 session。
🟡 Medium: [決策] ai_session_export 在 GitHub 上 fork 無法設成 private。做法是本地 clone,upstream 指原作者,origin 指自己的 private repo。PR 回原作者屬於公開動作,要 zawa 另外授權。
🟢 Low: [發現] Ollama 的官方安裝腳本需要 sudo,所以改用 user-level 壓縮包,以 systemd user service 常駐並只綁 127.0.0.1。索引 rebuild 只重算 mtime 或大小有變的檔案,增量更新約 13 秒,所以 cron 每天跑成本低。
🟢 Low: [發現] semantic-search 同一個檔案會佔掉太多結果名額,查詢時候選數要放大。4B 模型有一題排第 9,屬於已知限制,已寫進文件。
🟡 Medium: [專案狀態] psapi-dotnet v1.4.22:GameHistoryInner、GameListInner、GetHostInfoInner 三支內部 endpoint 不驗 JWT,改掛 Inner IP 白名單(GameHistoryInner 原本只靠 JWT,拿掉前必須同版掛白名單,否則 IDOR);OfflineMiddleware 用完整路徑比對。QA/prod 部署前維運要確認後台 server IP 在白名單。**待決**:dev 發現 docker 閘道位址是可信代理,同機程式可偽造 X-Forwarded-For 繞過白名單(既有漏洞),建議先記文件並請維運查 stage/prod;GameHistory、V2、All、Diff 尚無白名單,是否另開一案待 zawa 決定。
🟡 Medium: [偏好] zawa 在 AI 動手前,會再確認一次它對需求的理解(例如「Inner 是不是不套 JWT」)。AI 交付前先用一句話複述範圍與效果,zawa 能用這句話快速確認。
🟡 Medium: [發現] observer 挑「新增對話」改用檔案大小判斷,不用 mtime。`--full` 重匯出會讓所有檔案 mtime 變新,dry-run 一次抓了 40 個舊 session。
🔴 High: [經驗] 腳本要先拿真實資料離線驗證確定性部分(GC、USER.md 專案行替換)再接 cron。這次抓到兩個 bug:專案段落的 regex 會越過清單吃掉後面的段落,以及專案行被重新排序。
🟡 Medium: [約束] cron 的 PATH 不含 `~/.local/bin`(kiro-cli、gitleaks 都在那),腳本要自己補 PATH,並用乾淨環境實跑一次才算驗證過。
🟢 Low: [發現] `kiro-cli chat --no-interactive` 偶爾遇到服務端暫時性錯誤(dispatch failure),`run_kiro` 加一次自動重試。新檔案要先 `git add` 再 commit,否則 commit 會失敗。
🟢 Low: [專案狀態] Kiro CLI 從 2.27.0 升到 3.5.0(2026-11-19)。
🟡 Medium: [偏好] zawa 收工時說「都先不處理」,代表待決事項只記進文件,AI 不要再追問或擅自動手。psapi-dotnet 有 3 個 `[261104]` 簽章文件是 untracked,不屬於該次任務,AI 不 commit。
🔴 High: [約束] shell deny 規則只比對指令字串,看不出 DROP 打到哪個庫,所以全域 code 保留 DROP/TRUNCATE 攔截,只有拋棄式測試庫的 repo 才用 code-lab 範本(見 docs/repo-standard.md §5b)。Kiro 3.x 把 deniedCommands 轉成 glob 時丟掉單字邊界,已改成帶空白的 glob(commit 87e99a4),手改 permissions 後要留意 kiroUpgrade 會不會蓋回。AI 被擋時不改寫指令繞過,停下來回報;派 subagent 時要求附上被擋的指令與擋下訊息。
🟡 Medium: [專案狀態] dbUpgrade(`~/proj/db/dbUpgrade`)已套用 lab 規則:可對 lab_mysql57_test / lab_mysql80_test 的庫 DROP,gameapi 容器的變更類 docker 指令擋。repo 內 code agent 是否覆蓋 orchestrator 派出的 subagent 尚未實測。dbUpgrade 沒設 remote,只有本地 commit。

Date: 2026-11-23

🟡 Medium: [決策] hr、hr_db、stocktake 的 AGENTS.md 與全域 USER.md 重複的 DB additive 規則和行數上限,改成指向全域規則,只留 repo 自己的細節。同一條規則只寫一處。
🟡 Medium: [決策] sync 時發現 `~/.kiro/agents/` 被 Orca 工具加了 hooks,內含這台電腦專用路徑,不放進 templates 備份。只 commit 自己改的檔。
🟢 Low: [發現] 備份到 private_session_data 的檔案以雜湊命名,對照表加密另存,GitHub 上看不到對話標題。gitleaks 會把本機備份索引(sha256)誤判成金鑰,要在 `.gitleaks.toml` 排除,否則 cron 備份被擋。
🟢 Low: [決策] 要從存檔移除某個 session 得做三件事:刪 Markdown 並移出索引、加進匯出排除清單(否則 cron 會重匯)、加密備份的 git 歷史仍留舊版。zawa 要求刪記憶時,只刪 OBSERVATIONS 等記憶,對話存檔預設保留。
🟡 Medium: [決策] .kiroignore 會擋指定讀取,.gitignore 只讓搜尋略過;tmp/ 只放 .gitignore。起因:hr 的 .kiroignore 擋 tmp/,pipeline 讀不回計畫檔與 zawa 放的資料。

Date: 2026-11-24

🟡 Medium: [專案狀態] zawa 改用 orca(SSH 連進 WSL)開發,psapi-dotnet 現在在 ~/orca/projects/psapi-dotnet(原在 ~/proj/api/psapi-dotnet)。orca 的工作目錄是 ~/orca/workspaces/<專案>/<worktree>,與 zawa 原本預期不同;.env 管理方式也不同,教 orca 流程時要特別說明。

Date: 2026-11-25

🟡 Medium: [決策] /pipeline 改成 v2,吸收 mattpocock/skills 的 spec → TDD → review 作法:保留 orchestrator 分派、model routing、tmp/ 計畫檔,不搬 issue tracker、worktree、整合 branch、PR。測試改由 code 先寫(TDD),移除 aux 的 test 階段;中型以上任務新增 plan(opus)審查階段,只讀不改;測試的驗證入口由 orchestrator / plan 自己決定,有疑慮才用白話問 zawa。計畫模板與 TDD 規則放 `~/.kiro/skills/pipeline/`(plan-template.md、tdd.md),NOTICE.md 附 MIT 授權。sync-kiro.sh 改成同步整個 skill 目錄。

🟡 Medium: [決策] 採用 improve-codebase-architecture 改寫版(來源 mattpocock/skills,MIT),放全域 `~/.kiro/skills/improve-codebase-architecture/`:orchestrator 派 planner 掃描並寫 Markdown 報告到 repo 的 `tmp/`,zawa 挑一項後追問、必要時 design it twice,決策清楚再交給 /pipeline 實作,本身不改程式碼。不建 GLOSSARY.md 與 docs/adr/,用語與否決理由記進該 repo 的 docs/。同批評估過 diagnosing-bugs,暫不做,先驗證新 pipeline。

🟡 Medium: [決策] 每個 repo 必備 `docs/glossary.md`(名詞表),取代先前「不建 GLOSSARY.md」的做法。格式比 mattpocock 多「程式名稱」欄,內容可先放空。寫入規則:zawa 講明或確認的直接寫,AI 從程式推出的標「(待確認)」,用語衝突時當場問 zawa 並記進「曾經混用」。範本在 `templates/docs/glossary.md`,pipeline、improve-codebase-architecture、create-repo、check-repo、close-session 都依它運作。

🟡 Medium: [決策] close session 新增第 4 步「清理暫存」(`docs/repo-standard.md` §3):本 session 由 AI 建立、工作已完成的 `tmp/` 檔(plan-*、review-*、arch-*、log-*、下載的參考原文、.bak、下載暫存)直接刪;zawa 放的資料、舊 session 留下或來源不明、工作未完成的檔先問。只刪 `tmp/` 內的檔,逐檔刪,不用 `rm -rf`,空目錄用 `rmdir`,`tmp/` 本身保留。理由:zawa 已授權這類刪除,範圍以外仍依「破壞性動作先確認」。

🟡 Medium: [專案狀態] Kiro 新版 session(從 orca/ACP 開的)存在 `~/.kiro/sessions/<sha256(工作目錄路徑) 前 16 碼>/sess_<UUID>/`,檔案為 `session.json` + `messages.jsonl`,與舊格式 `~/.kiro/sessions/cli/<id>.json` + `.jsonl` 並存。舊的匯出只掃 cli/,因此 `/close-session` 找不到新格式 session,回報 `session metadata not found`;每日 cron 也漏匯新格式(約 40 個 11/19 起的 session)。

🟡 Medium: [決策] 修正:ai_session_export commit d0387ba 新增 `sources/kiro_workspace.py` 與 `--kiro-workspace-root`(預設 ~/.kiro/sessions),兩種格式都掃、輸出到同一個 kiro/ 資料夾;新格式只匯出 user 與 assistant 文字,子代理不匯出。新格式的 project_directory 是 orca 工作目錄,zawa 同意照實記錄。文件已更新於 docs/context-system.md §2a。

Date: 2026-11-26

🟡 Medium: [決策] /pipeline 中型以上任務完成後,doc 階段把計畫的「問題」「解法」「實作決定」「不做的範圍」四段存進該 repo 的 `docs/issues/[YYMMDD]<slug>.md`(狀態「已完成」,不開 branch);「實作提示」不存,小型任務不存。close session 刪 `plan-*` 前要確認已存檔。理由:tmp/ 的計畫檔會被清掉,決策與取捨需要留在版控。

🟢 Low: [決策] mattpocock to-spec 的完整情境清單與 prior art 欄位評估過,zawa 決定先不加進 plan-template.md,之後有需要再議。

🟡 Medium: [待辦] 專案搬到 ~/orca/projects 延後:zawa 要先用 orca 2~3 週再決定,期間不動作。現況 repoManager 有兩份 clone(~/proj/my/repoManager 是 cron 使用,~/orca/projects/repoManager 是 orca 使用),都推同一個 main;文件與腳本仍有多處寫死 ~/proj/my。

🟡 Medium: [偏好] 提議拆檔時要明說原因是檔案太大(目前行數與超過的門檻),否則 zawa 不知道為什麼要拆。已寫進 rules/USER.md。

Date: 2026-11-26

🔴 High: [發現] Kiro 派 subagent 時,父 agent(如 orchestrator)與子 agent 兩層的 shell deny 規則同時檢查,任一層命中就擋,來源分別標 agent-profile 與 subagent-profile。lab repo 要放行 DROP,得另放本地 orchestrator.json 拿掉 DROP/TRUNCATE(dbUpgrade 已實測有效,見 docs/repo-standard.md §5b)。
🟡 Medium: [決策] orchestrator.json 補一條 shell allow 並搬入 code/aux 的 deny 清單,解決每次派 subagent 都跳批准提示。選 (f) 只對當前 session 有效。deny 優先於 allow,orchestrator 自己沒有 shell 工具,不受影響。
🟡 Medium: [決策] orca 本機機密檔:每個 repo 一份 ~/.config/<repo>/ 當單一來源,放通用 orca-setup.sh,在 orca UI 的 setup/archive hook 填命令。orca CLI 無法設 hook。hr、stocktake、ansible、psapi-dotnet 都已套用。新增 /orca-onboard skill,舊 repo 的原檔換成 symlink。專案要用「開啟既有 repo」或 clone 加入,不要用「建立新專案」。
🟡 Medium: [決策] hr 與 stocktake 是各自獨立的 Supabase 專案,同名 .env key 的值不同,不合併。只有同一帳號共用的憑證(如 Jira)才抽成 ~/.config/<名稱>/ 共用,避免連錯庫。
🟡 Medium: [決策] psapi-dotnet 的 token-in-log 單:zawa 決定不遮 access_token,因為線上排查要拿營運商給的 token 比對 log。只有 password 類不得以原值入 log。已寫進該 repo AGENTS.md 的「Log 去敏政策」,等安全部門提出再處理。
🟡 Medium: [專案狀態] psapi-dotnet 錯誤碼寫死數字已改成 3 個 enum(HostApiErrorCode、HostErrorLogAction、HostErrorLogCode),新增掃描測試防再寫死,數值與行為不變。v1.4.23 之後累積 6 個未發版 commit,下次發版要整理 release note。
🟡 Medium: [發現] ansible 的 DB migration 有共通缺陷:版本號在套件或 SQL 檢查前就寫入,SQL 缺檔時版本表仍記已套用。jp 與 gameapi server 已改成檢查通過後才寫版本;backstage、gameapi 的 migration 仍有同寫法,待修。jp 的 DB 密碼檔放 ~/.config/ansible,不進版控。
🟡 Medium: [發現] gameapi 的 systemd 範本把 ASPNETCORE_ENVIRONMENT 寫死 Development,三個環境共用,所以 prod 也開 swagger 並回傳例外細節。決定全面移除 swagger。部署健康檢查要先改打 /Version,且 ansible 要比新 tag 先上。prod LB 與監控是否打 /swagger 要先問維運。
🟡 Medium: [專案狀態] hr v1.27.1 上線(repo 第一個 tag),是 /improve-codebase-architecture 首次實跑:掃出 9 項,先做薪資前處理共用。排班預估改與實際產薪走同一段,含到職折算與請假扣款,不含離職結清、季獎金、12 月國定假日加倍。其餘 7 項待排,最大的是資料存取層無測試。
🟡 Medium: [專案狀態] hr 記帳:LINE Pay 入帳日依結算單比對,規則是交易日後第 2 個銀行營業日(不是日曆 +2),併入自動扣手續費勾選框。v1.25.4 把類別欄改成選收入/支出,新增後保留方向、管道、日期,方便連續記帳。
🟡 Medium: [偏好] zawa 看不懂用日期、編號指稱筆記的整理項目。需要他決定的事要寫成白話問題;合併重複筆記這類 AI 能自己決定的維護,直接做,不列合併清單。
🟢 Low: [專案狀態] repoManager 的 heartbeat.py 超過 400 行,已拆成三個檔(各約 120~200 行),28 項測試通過。週三回顧現在同時讀 ~/orca/projects 與 ~/proj/my。
🟢 Low: [發現] psapi-dotnet 的 GetHostGameInfo 快取 key 含 access_token,命中率低,且回應含玩家注單號卻允許中間層快取 60 秒。RD01-7178 的建議是拆兩段快取並改 private,待 zawa 確認。
🟢 Low: [發現] psapi-dotnet 簽章規劃發現兩個實作風險:BaseRequest.ToString() 不做 URL 編碼,HostApi 的 HttpClient 開著自動轉址。開 sign_enable 的 host 要處理這兩點。

Date: 2026-11-26

🔴 High: [方法論/約束] Kiro 的 subagent 名稱 `plan` 與內建名稱衝突,orchestrator 的派工工具清單不會出現它。規劃用的 subagent 改名 `planner`(內容與 plan 相同),orchestrator 與 pipeline、improve-codebase-architecture skill 都改派 planner;plan.json 已刪除,規劃角色只有 planner(互動與派工共用)。

Date: 2026-11-27

🟡 Medium: [經驗] psapi-dotnet v1.4.28 為了先上 dev 驗證,把 tag 打在 feature branch,之後合併 master 時撞到別的 session 已寫進 master 的 v1.4.28 release note,只好補打 v1.4.29。tag 一律在預設 branch 打,已寫進 USER.md。
🟡 Medium: [偏好] psapi-dotnet 是 zawa 單人專案:feature branch 做完、測試全綠、無衝突就直接合 master,不開 MR。只加 log 或只改文件這類 QA 不用測的變更不單獨打 tag,先寫 release note,下次發版併入;需要上 dev 驗證的才打 tag。已寫進 AGENTS.md。
🟡 Medium: [偏好] psapi-dotnet 的 QA 由 QA 自己部署、自己驗,AI 只做到 dev 驗證,回報時不再把部署 QA 或 QA 驗證列成待辦。有特例時 zawa 自己處理。
🟡 Medium: [決策] /pipeline 新增批次模式(`/pipeline 批次做 A、B、C`):開頭把所有待決事項合成一輪問完,之後不再互動;新待決事項就先擱著做下一項;大型高風險項單獨開 session;約 5 個中型任務換 session。起因:hr 一批任務被切成多個 session。
🟡 Medium: [專案狀態] hr 照 /improve-codebase-architecture 報告上線 v1.27.2 到 v1.27.9:台灣時間換算收進 lib/taipei-time.js、HTML 跳脫與金額格式收進 lib/format.js、LINE Pay 兩筆寫入失敗時補償還原、core.js 與 4 個大檔拆子目錄。候選 7(工資上限規則兩份)先觀望。
🟡 Medium: [決策] hr 資料存取層重構採方案 A:mock 模式改用記憶體裡的假 Supabase(lib/fake-supabase/),資料函式只留雲端寫法,測試才跑得到雲端那段。真 RLS 測試之後另開題目。共 8 批,v1.27.10 完成試點(stores、punches),第 2 批計畫已寫好待實作。遷移時發現的線上既有落差一律列單,不順手修。
🟡 Medium: [專案狀態] stocktake v1.3.0 到 v1.3.2:店長逐項設半單位與安全量,店員盤點時看不到安全量。只有店長與老闆有「採購」鍵,按下後依廠商彙整低於安全量的品項,經 Edge Function 與 Brevo 寄給多位收件者。不做 10 天自動換算,防重複寄送暫不做。
🟢 Low: [決策] Supabase 存取權杖屬於帳號層級,同帳號的 hr 與 stocktake 可共用。zawa 自己把它複製進 stocktake 的 .env,AI 不自行讀別的 repo 的憑證,等 zawa 授權。Brevo 金鑰則每個專案各產一把,只由 zawa 貼進 Supabase Secrets。
🟡 Medium: [決策] food_delivery 的 Uber 建議價目標是兩平台每單實收相同:Uber 價 = foodpanda 上架價 × 0.794(foodpanda 抽成 35%、Uber 33.5%,不含提袋費)。鍋底另加價,使最低價為 160,全部鍋底平移,保留價差。參數放 Google 試算表,抽成變動時改參數格即可。
🟡 Medium: [決策] psapi-dotnet v1.4.28:GetHostGameInfo 的快取拆兩段。商戶與遊戲設定的 key 拿掉 access_token 後共用 60 秒,history_sn 每次即時查,每次回傳快取的副本。ResponseCache 由 public 改 private,避免 CDN 存含注單號的回應。history_sn 有值的情況 dev 沒測到。
🟢 Low: [專案狀態] psapi-dotnet v1.4.29 起,每個 instance 啟動時寫一筆 `[Startup] GameAPI started version=...`,與 /Version 同一個版號來源。驗證 prod log 時先 grep 它。RD01-7181 對 v1.4.23 的 log 驗證通過,已在 Jira 回覆。
🟡 Medium: [發現] psapi-dotnet 的 UpsDeposit:URL 的 rate 是儲值加成倍率,入帳 = amount × rate;出金門檻倍率是 DB 的 ups_game_setting.threshold_rate,門檻 = 入帳 × threshold_rate。要「入帳 1 萬、門檻 2 萬」得用 rate=1 加上 threshold_rate=2。
🟡 Medium: [偏好] devDB 要建與 mis 同級的帳號時,AI 先指出它與權限集中化方向相反並提出較小權限方案。zawa 說明這是 dev 庫、不用那麼小心,要求比照 zawa_chiu,AI 照辦並在 history 記軌跡。dev 庫的權限決定可以較寬鬆,prod 不適用。
🟢 Low: [決策] /orca-onboard 只需在 orca UI 設 setup hook,archive 不用設:orca-setup.sh 只建 symlink,worktree 收掉時 symlink 自然消失。go-accounting-etl 已套用。orca CLI 沒有設 hook 的命令,這步由 zawa 手動做。
🟢 Low: [發現] hr 寄信流程:前端呼叫 Supabase Edge Function(send-payslip、send-schedule),函式驗身分與 MFA 後從資料庫取收件人,再打 Brevo API。stocktake 的採購信沿用同一套做法。
