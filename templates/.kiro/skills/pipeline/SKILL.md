---
name: pipeline
description: orchestrator(總架構師,opus)釐清需求並拆解,自己寫或派 plan 產出計畫,code 以 TDD 實作(先寫測試),中型以上任務派 plan 審查,aux 補文件,各階段走各自 model。用法:先 /agent orchestrator,再 /pipeline <要做的任務>;多個任務用 /pipeline 批次做 <任務 A、B、C>(一輪問完後不再互動)。
---

# 釐清 → 規劃 → code(TDD)→ 審查 → 文件 pipeline

zawa 要做的任務:$ARGUMENTS

你(orchestrator)是總架構師:自己釐清需求、拆解、跟 zawa 討論。子項目的細部規劃視情況派給 `plan`,實作派 `code`,審查派 `plan`,文件派 `aux`。

部分作法改寫自 mattpocock/skills,授權見同目錄 `NOTICE.md`。

## 各角色

| stage | role | model 覆蓋 | 做什麼 |
|-------|------|-----------|--------|
| (自己) | `orchestrator` | — | 釐清需求、拆解、介面與相依、跟 zawa 確認、整合 |
| `plan-<子項目>` | `plan` | — | 依 `plan-template.md` 寫 `tmp/plan-<子項目>.md` |
| `code-<子項目>` | `code` | — | 讀計畫與 `tdd.md`,一次一條小功能,先寫測試再實作 |
| `review-<子項目>` | `plan` | — | 中型以上才跑。只讀不改程式,寫 `tmp/review-<子項目>.md` |
| `doc-<子項目>` | `aux` | `claude-sonnet-5.5` | 補 / 更新文件 |

- 沒有覆蓋的 stage,model 由 role 對應的 agent 決定(`plan`=opus-5.5、`code`=sonnet-5.5、`aux`=haiku-5.5)。
- `doc` stage 必須在 stage 參數帶 `"model": "claude-sonnet-5.5"`。
- 都用 **subagent** 工具,`mode=blocking`。
- 只有一個子項目時,stage 名稱可省略 `-<子項目>`。
- 環境沒有 `plan` subagent 時:規劃自己做;審查改派 `code` 唯讀執行(只准寫 `tmp/review-<子項目>.md`,不改程式、不 commit)。
- 模板與規則在本 skill 同目錄:`plan-template.md`(計畫檔格式)、`tdd.md`(code 的測試規則)。派 subagent 時一律寫絕對路徑 `~/.kiro/skills/pipeline/plan-template.md`、`~/.kiro/skills/pipeline/tdd.md`(若 repo 有本地覆蓋的 `.kiro/skills/pipeline/`,改用該路徑)。

## 流程

### 第 1 步:釐清需求並拆解

**釐清需求**:追問到需求清楚。

- 能從程式碼、文件、記憶查到的事自己查,不問 zawa。
- 先讀該 repo 的 `docs/glossary.md`。需求用語跟表不一致時,列入問題。repo 沒有這個檔,從 `~/proj/my/repoManager/templates/docs/glossary.md` 建一份(替換 repo 名稱)。
- 要問的事每輪集中編號列出,最多約 5 題。每題附你的建議答案,並把問題寫成「回答 yes 就採用建議」。
- 一題的答案取決於另一題時,放到下一輪問。

**拆子項目**:

- 優先垂直切。每個子項目做完,都能從頭到尾跑起來驗證。避免按資料庫層、API 層、畫面層水平切。
- 列出每個子項目做什麼、子項目之間的介面與相依。
- 每個子項目由誰規劃:**自己**(小、或跟其他項目耦合深)或**派 plan**(邊界清楚、可獨立規劃、要讀不少程式碼或文件)。

**檢查測試環境**:看該 repo 有沒有測試框架與型別檢查指令。沒有的話,列入「需要 zawa 決定」(要不要新增、用哪個)。code 不得自行新增依賴。

**判斷規模**:

- 小型:單一子項目、預估改動約 3 個檔以內、沒有 schema 或對外介面變更。
- 中型以上:其餘情況。這類要跑 review。

**驗證入口**(測試從哪裡驗證行為):自己決定。只有疑慮時才問 zawa,並用白話說明,例如「我們會從某個函式的輸入輸出確認對不對」。

需要 zawa 決定的事(做法 A/B、範圍、會影響外部的變更、取捨不明顯的設計)列出每個選項的影響與你的建議。有就停下來問,**等 zawa 回覆**(zawa 直接回覆,不會再打 `/pipeline`)。沒有就直接進第 2 步。不可以自己替 zawa 做選擇。

### 第 2 步:規劃子項目

計畫檔一律照 `plan-template.md`。

- **自己規劃的**:直接寫進 `tmp/plan-<子項目>.md`。
- **派 plan 的**:每個子項目一個 `plan-<子項目>` stage,互不相依的並行。prompt 要帶子項目範圍、與其他子項目的介面、zawa 已做的決定、計畫檔路徑、`plan-template.md` 路徑,並要求回報只給「摘要」與「需要 zawa 決定」兩段(沒有就寫「無」)。

plan 回報的「需要 zawa 決定」有選項時,停下來問 zawa,收到回覆後把決定補寫進對應計畫檔。

### 第 3 步:實作(code)

每個子項目送 `code-<子項目>`。互不相依的子項目並行,有相依的用 `depends_on` 串起來。

prompt 要帶計畫檔路徑、`tdd.md` 路徑、zawa 的決定。規則摘要(細節在 `tdd.md`):

- 依計畫的小功能切片順序,一次一條:寫一個會失敗的測試,再寫最小實作讓它通過,然後下一條。不預做未來需求。
- 只在計畫列的驗證入口寫測試。mock 只用在外部系統邊界(資料庫、第三方 API),不 mock 自己的模組。
- 期望值用獨立來源(寫死的值、計畫的例子),不照程式的算法重算。
- 重構不在這個迴圈內,留給 review。
- 完成標準:每條驗收條件都有對應測試、全部測試通過、型別檢查與 lint(repo 有的話)通過、遵守檔案行數上限。

回報只給精簡摘要:改了哪些檔、每條切片對應的測試、測試與型別檢查結果、偏離計畫之處、遇到的問題。

### 第 4 步:審查(中型以上,plan)

`review-<子項目>` `depends_on` 該 code stage。審查者只讀不改程式,對照計畫檢查:

- 驗收條件是否都達成且有測試。
- 測試是否綁實作或同義反覆(期望值照程式算法重算)。
- mock 是否只在外部邊界。
- 命名是否跟 `docs/glossary.md` 一致。
- 檔案行數、機密與輸入驗證。
- 可重構的地方。

結果寫進 `tmp/review-<子項目>.md`,回報分「必修」與「建議」兩段。

有必修時,你帶 review 檔路徑重派 `code-<子項目>-fix`。修完不必再審,除非改動很大。建議項目整合進最後的回報給 zawa。小型任務跳過本步。

### 第 5 步:文件(aux,sonnet)

這次出現的新詞,依 `docs/glossary.md` 開頭規則補進去(定義由 zawa 講明或確認的直接寫,其餘標「(待確認)」)。

小型任務的 `doc-<子項目>` `depends_on` code。中型以上 `depends_on` review(有 fix 時再加 fix)。

**計畫存檔(中型以上才做)**:doc 的 prompt 另外要求:讀 `tmp/plan-<子項目>.md`,把「問題」「解法」「實作決定」「不做的範圍」四段(標題照 `plan-template.md`)存成該 repo 的 `docs/issues/[YYMMDD]<slug>.md`。「實作提示」不存。
- slug 英文小寫、`-` 分隔。檔案開頭寫「狀態:已完成」、日期、一行「由 /pipeline 計畫存檔」。
- 不另開 branch(這是完成紀錄,不是待辦開單)。repo 已有其他 issue 慣例時依 repo。
- 同一任務的多個子項目合併成一份。檔案已存在不覆蓋,改用新 slug。小型任務不存。

所有 stage 都要求只回精簡摘要。跑完整合各子項目結果回報 zawa。任一階段失敗會 fail-fast,立刻回報錯誤與建議的處理方式。

## 批次模式

zawa 一次給多個任務時使用(例如「`/pipeline 批次做 A、B、C`」),目的是一輪問完,之後不用再互動。每個任務仍照第 1~5 步走,只改下面幾點:

1. **開頭一次問完**:先讀完所有任務,把各任務第 1 步的待決事項合成一輪問題(題數可超過 5,依任務分組編號)。zawa 回覆後全程不再停。
2. **分流**(在同一輪問題中列出,讓 zawa 一起確認):
   - 可直接跑:沒有待決,或待決已在本輪問完。
   - 不適合批次:大型、高風險(碰 RLS / 權限、大量資料模組、改部署方式)→ 建議單獨開 session,不納入本批。
3. **順序與並行**:會改到同一檔或同一模組的任務依序做,其餘可並行。每個任務各自完成測試、上線與版號(repo 有例行部署授權時),出問題才能分辨是哪一項。
4. **中途出現新待決**:該任務停在當下的步驟並記下狀態,繼續做下一個,不讓整批停下。任一任務失敗也照此處理,不 fail-fast 整批。
5. **context 上限**:約做完 5 個中型任務,或 context 明顯變長時,停在任務之間,回報進度並附下個 session 可直接貼的 prompt(含已完成項目、擱置項目與狀態)。
6. **最後回報**:每個任務一列(版本 / 測試結果 / 狀態),接著是擱置項目,最後是需要 zawa 決定的事(編號列出)。

## 跑完後 zawa 回覆修改意見

zawa 直接回覆即可,不必重打 `/pipeline`。依修改內容**只重跑需要的部分**:

| 修改內容 | 處理 |
|---------|------|
| 改整體拆解或子項目介面 | 自己調整,回第 1 步確認 |
| 某子項目計畫小改 | 自己改 `tmp/plan-<子項目>.md`,再重跑該子項目的 code、review(中型以上)、doc |
| 某子項目計畫大改 | 帶 zawa 意見與原計畫檔重派 `plan-<子項目>`,再往下跑 |
| 改程式 | 該子項目的 code、review(中型以上)、doc |
| 只改測試 | code(測試由 code 負責) |
| 審查意見 | 必修與 zawa 點名的建議項目,帶 review 檔路徑重派 code |
| 只改文件 | doc |

計畫改動時,同步更新已存的 `docs/issues/` 檔。

子 agent 跑完就結束,無法沿用前一輪的 session,重跑時要把 zawa 的意見和需要的上下文寫進新的 prompt。

> 需站在**有 subagent 工具**的 agent 執行,建議先 `/agent orchestrator`(已設 availableAgents / trustedAgents,spawn 不跳核可)。
> 子 agent 的 `write`/`shell` 已在 `code`/`aux` 的 `allowedTools` 放行(破壞性指令由 `deniedCommands` 擋下),pipeline **全程不跳核可,無需 `/tools trust-all`**。
