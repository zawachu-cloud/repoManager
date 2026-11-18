# USER.md — 老闆是誰

> L3 全域規則,每個 session 自動載入。**只寫確定的事**;標 `<待補>` 的請老闆填,互動中觀察到新偏好時提議更新(改動前先問)。
> 依 grapeot/context-infrastructure:這份是效益最高的一份,填得越具體,AI 越不會給通用答案。

## 基本

- **稱呼**:老闆
- **語言**:一律繁體中文回覆;程式碼識別符用英文。
- **時區**:UTC+8
- **背景 / 職務**:<待補>
- **擅長領域**:<待補>

## 工作環境

- 主力工具:Kiro CLI(角色 agent:`plan` / `code` / `aux` / `orchestrator`,流程用 `/pipeline`)。也有 Claude Code。
- 機器:Ubuntu;個人專案放 `~/proj/my/`。
- repo 的開與收走 repoManager 的 `/create-repo`、`/close-session`、`/check-repo`。

## 目前的專案

位於 `~/proj/my/`:`hr`、`hr_db`、`income_ana`、`line`、`stocktake`、`innerDoc`、`modelRouting`、`repoManager`。

- 各專案的用途:<待補>
- `hr`、`hr_db`、`income_ana` 與 payroll 相關資料視為**機密**,不送雲端、不寫進記憶細節。

## 工作偏好(已確認)

- commit / push 由 AI 直接做,不用問。
- 破壞性動作(`rm -rf`、`reset --hard`、force push、覆蓋既有檔)先確認。
- 機密只放 `.env`;備份敏感檔用 `age` 加密。
- 文件分層省 token:AGENTS.md 只放摘要,細節放 `docs/`,同一件事只寫一處。
- 不熟的技術(例如 embedding)希望先用白話解釋原理與代價,再做決定。

## 會讓老闆煩的

- <待補>

## 溝通偏好

- 結論先講;直接、具體,不要客套。
- <待補>
