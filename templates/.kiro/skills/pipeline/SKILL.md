---
name: pipeline
description: 跑 plan→code→test→doc 四階段 subagent pipeline,各階段走各自 model(opus/sonnet/haiku)。plan 有需要老闆決定的選項會先停下來問。用法:先 /agent orchestrator,再 /pipeline <要做的任務>。
---

# plan→code→test→doc pipeline

老闆要做的任務:$ARGUMENTS

## 各階段

| stage | role | model 覆蓋 | 做什麼 |
|-------|------|-----------|--------|
| `plan` | `plan` | — | 規劃 {task}:拆解步驟、列要改的檔與風險,把計畫寫進 `tmp/pipeline-plan.md` |
| `code` | `code` | — | 讀 `tmp/pipeline-plan.md`,依計畫實作 {task} |
| `test` | `aux` | — | 為 {task} 寫單元測試並跑過 |
| `doc` | `aux` | `claude-sonnet-5.5` | 為 {task} 補 / 更新文件 |

- 沒有覆蓋的 stage,model 由 role 對應的 agent 決定(`plan`=opus-5.5、`code`=sonnet-5.5、`aux`=haiku-5.5)。
- `doc` stage 必須在 stage 參數帶 `"model": "claude-sonnet-5.5"`。
- 都用 **subagent** 工具,`mode=blocking`,`task` 設為上面那句任務。

## 流程

### 第 1 步:只跑 plan

只送一個 `plan` stage。prompt 要求 plan 在結果最後加一段「**需要老闆決定**」:

- 有需要老闆選的事(做法 A/B、範圍、會影響外部的變更、取捨不明顯的設計),列出每個選項、各自的影響,以及 plan 的建議。
- 沒有就寫「無」。

plan 不可以自己替老闆做這些選擇。

### 第 2 步:看 plan 結果決定要不要停

- **「需要老闆決定」為「無」** → 直接進第 3 步。
- **有選項** → 停下來,把計畫摘要和選項回報給老闆,**等老闆回覆**。老闆會直接回覆(例如「選 B」),不會再打 `/pipeline`。收到回覆後,把老闆的決定補寫進 `tmp/pipeline-plan.md`(透過下一階段的 prompt 一併交代),再進第 3 步。

### 第 3 步:跑 code → test、doc

送一組 stages:`code`(無相依)、`test` 與 `doc`(都 `depends_on: ["code"]`,兩者並行)。
`code` 的 prompt 要帶上:計畫檔位置 `tmp/pipeline-plan.md`、老闆的決定(若有)。

跑完彙整各階段結果回報老闆。任一階段失敗會 fail-fast,立刻回報錯誤與建議的處理方式。

## 跑完後老闆回覆修改意見

老闆直接回覆即可,不必重打 `/pipeline`。依修改內容**只重跑需要的階段**,不要整條重來:

| 修改內容 | 重跑 |
|---------|------|
| 改需求或做法 | plan(回第 1 步) |
| 改程式 | code → test、doc |
| 只改測試 | test |
| 只改文件 | doc |

重跑時在 prompt 帶上老闆的修改意見,以及前一輪結果中相關的部分。子 agent 跑完就結束,無法沿用前一輪的 session,所以需要的上下文都要寫進新的 prompt。

> 需站在**有 subagent 工具**的 agent 執行,建議先 `/agent orchestrator`(已設 availableAgents / trustedAgents,spawn 不跳核可)。
> 子 agent 的 `write`/`shell` 已在 `code`/`aux` 的 `allowedTools` 放行(破壞性指令由 `deniedCommands` 擋下),pipeline **全程不跳核可,無需 `/tools trust-all`**。
