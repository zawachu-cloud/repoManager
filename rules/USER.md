# USER.md — zawa 是誰

> L3 全域規則,每個 session 自動載入。**只寫確定的事**;互動中觀察到新偏好時提議更新(改動前先問)。
> 例外:「目前的專案」只在 `/close-session`(更新當下 repo 那一行)與每週三回顧(依對話存檔)時由 AI 直接改,平時不動。
> 依 grapeot/context-infrastructure:這份是效益最高的一份,填得越具體,AI 越不會給通用答案。

## 基本

- **稱呼**:zawa
- **語言**:一律繁體中文,包含工具呼叫之間的過程說明;不要用英文或日文敘述。程式碼識別符用英文。
- **時區**:UTC+8

## 工作環境

- 主力工具:Kiro CLI(角色 agent:`plan` / `code` / `aux` / `orchestrator`,流程用 `/pipeline`)。也有 Claude Code。
- 機器:Ubuntu;個人專案放 `~/proj/my/`。
- repo 的開與收走 repoManager 的 `/create-repo`、`/close-session`、`/check-repo`。

## 目前的專案

位於 `~/proj/my/`。每個專案一行用途,細節放該 repo 的 AGENTS.md。只寫用途與方向,不寫憑證與資料內容(姓名、薪資數字等)。

- `hr`:小型公司人事薪資、排班打卡、收支記帳系統(Supabase + Cloudflare)。近期:收支記帳改版(只選收入/支出、明細可編輯、支出發票狀態追票、LINE Pay 手續費綁定收入);每月 1、2 號 zawa 給 LINE Pay 明細,AI 對帳修正手續費。
- `hr_db`:hr 的資料庫實驗場。連 Supabase 查詢、驗證計薪假設、起草 migration 草案。select 預設 prod,其餘寫入預設 dev。
- `income_ana`:火鍋店營收與人力成本分析(不再做 hr 記帳匯入)。方向:重算 10 月損益、補齊完整 11 月營業額。
- `line`:<待補>
- `stocktake`:店員用手機盤點庫存,並預估用量與可用天數。獨立 Supabase,盤點資料保留 3 年(pg_cron 清理)。
- `innerDoc`:公司人事表單(試用期、離職、資遣、招募)的 Markdown 原始檔與 PDF 轉出,改 md 再轉檔。
- `modelRouting`:<待補>
- `repoManager`:repo 標準、開收 repo 的 skill、context 系統(規則與記憶),以及 plan/code/aux 的 model routing 與 shell 權限規則(含拋棄式測試庫用的 lab 範本)。
- `ai_session_export`:對話存檔匯出工具(fork 自 upstream),含 Kiro adapter 與遮罩,cron 每天增量匯出。
- `semantic-search-skill`:本機 Ollama 語意搜尋,查對話存檔與 OBSERVATIONS,供 /recall skill 使用。
- `private_session_data`:對話存檔的 age 加密備份 private repo。

## 工作偏好(已確認)

- commit / push 由 AI 直接做,不用問。
- 破壞性動作(`rm -rf`、`reset --hard`、force push、覆蓋既有檔)先確認。
- 機密只放 `.env`;備份敏感檔用 `age` 加密。
- 文件分層省 token:AGENTS.md 只放摘要,細節放 `docs/`,同一件事只寫一處。
- 不熟的技術(例如 embedding)希望先用白話解釋原理與代價,再做決定。
- DB schema 變更一律 additive(`add column/table if not exists`),不對線上欄位或資料做 drop、破壞性 alter 或覆蓋;被取代的欄位保留並標 DEPRECATED。
- 程式碼檔案軟上限約 300 行,到 400 行主動提拆分,硬上限 500 行(barrel、自動產生檔、測試除外),目的是省 token。新功能優先放新模組,不往大檔追加。
- 回覆 Jira 卡:送出前先給 zawa 看內容;內容精簡,只寫我們實作的內容與結論,不寫別人的待辦或與實作無關的事。
- 開單(專案待辦,非 Jira):寫在該 repo 的 `docs/issues/[YYMMDD]<slug>.md`(repo 已有其他慣例時依 repo),狀態填「待確認」,先 commit 到預設 branch;同時開 branch `issue/<slug>`(slug 與檔名相同,英文小寫、`-` 分隔)並 push。

## 溝通偏好

- 結論先講;直接、具體,不要客套。
