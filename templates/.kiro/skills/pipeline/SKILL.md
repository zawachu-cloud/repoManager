---
name: pipeline
description: orchestrator(總架構師,opus)拆解任務並跟zawa確認,視情況派 plan 規劃子項目,再派 code→test、doc 執行,各階段走各自 model。用法:先 /agent orchestrator,再 /pipeline <要做的任務>。
---

# 拆解 → 規劃 → code → test、doc pipeline

zawa要做的任務:$ARGUMENTS

你(orchestrator)是總架構師:自己拆解與跟zawa討論,子項目的細部規劃視情況派給 `plan`,實作與收尾派給 `code` / `aux`。

## 各角色

| stage | role | model 覆蓋 | 做什麼 |
|-------|------|-----------|--------|
| (自己) | `orchestrator` | — | 拆解、子項目介面與相依、跟zawa確認、整合 |
| `plan-<子項目>` | `plan` | — | 規劃一個子項目,計畫寫進 `tmp/plan-<子項目>.md` |
| `code-<子項目>` | `code` | — | 讀計畫檔,實作該子項目 |
| `test-<子項目>` | `aux` | — | 為該子項目寫單元測試並跑過 |
| `doc-<子項目>` | `aux` | `claude-sonnet-5.5` | 為該子項目補 / 更新文件 |

- 沒有覆蓋的 stage,model 由 role 對應的 agent 決定(`plan`=opus-5.5、`code`=sonnet-5.5、`aux`=haiku-5.5)。
- `doc` stage 必須在 stage 參數帶 `"model": "claude-sonnet-5.5"`。
- 都用 **subagent** 工具,`mode=blocking`。
- 只有一個子項目時,stage 名稱可省略 `-<子項目>`。

## 流程

### 第 1 步:拆解並跟zawa確認

自己讀需要的檔,把任務拆成子項目,列出:

- 每個子項目做什麼、子項目之間的介面與相依。
- 每個子項目由誰規劃:**自己**(小、或跟其他項目耦合深)或**派 plan**(邊界清楚、可獨立規劃、要讀不少程式碼或文件)。
- 需要zawa決定的事(做法 A/B、範圍、會影響外部的變更、取捨不明顯的設計):每個選項的影響與你的建議。

有需要zawa決定的事就停下來問,**等zawa回覆**(zawa直接回覆,不會再打 `/pipeline`)。沒有就直接進第 2 步。不可以自己替zawa做選擇。

### 第 2 步:規劃子項目

- **自己規劃的**:直接把計畫寫進 `tmp/plan-<子項目>.md`。
- **派 plan 的**:每個子項目一個 `plan-<子項目>` stage,互不相依的並行。prompt 要帶:子項目範圍、與其他子項目的介面、zawa已做的決定、計畫檔路徑,並要求回報只給「摘要」與「需要zawa決定」兩段(沒有就寫「無」)。

plan 回報的「需要zawa決定」有選項時,停下來問zawa,收到回覆後把決定補寫進對應計畫檔。

### 第 3 步:執行

每個子項目送 `code-<子項目>`,`test-<子項目>`、`doc-<子項目>` 都 `depends_on` 該 code stage(兩者並行)。互不相依的子項目並行,有相依的用 `depends_on` 串起來。

`code` 的 prompt 要帶計畫檔路徑與zawa的決定。所有 stage 都要求只回精簡摘要:改了哪些檔、測試結果、遇到的問題。

跑完整合各子項目結果回報zawa。任一階段失敗會 fail-fast,立刻回報錯誤與建議的處理方式。

## 跑完後zawa回覆修改意見

zawa直接回覆即可,不必重打 `/pipeline`。依修改內容**只重跑需要的部分**:

| 修改內容 | 處理 |
|---------|------|
| 改整體拆解或子項目介面 | 自己調整,回第 1 步確認 |
| 某子項目計畫小改 | 自己改 `tmp/plan-<子項目>.md`,再重跑該子項目的 code → test、doc |
| 某子項目計畫大改 | 帶zawa意見與原計畫檔重派 `plan-<子項目>`,再往下跑 |
| 改程式 | 該子項目的 code → test、doc |
| 只改測試 | test |
| 只改文件 | doc |

子 agent 跑完就結束,無法沿用前一輪的 session,重跑時要把zawa的意見和需要的上下文寫進新的 prompt。

> 需站在**有 subagent 工具**的 agent 執行,建議先 `/agent orchestrator`(已設 availableAgents / trustedAgents,spawn 不跳核可)。
> 子 agent 的 `write`/`shell` 已在 `code`/`aux` 的 `allowedTools` 放行(破壞性指令由 `deniedCommands` 擋下),pipeline **全程不跳核可,無需 `/tools trust-all`**。
