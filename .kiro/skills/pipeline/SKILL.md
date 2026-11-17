---
name: pipeline
description: 跑 plan→code→test→doc 四階段 subagent pipeline,各階段走各自 model(opus/sonnet/haiku)。用法:先 /agent orchestrator,再 /pipeline <要做的任務>。
---

# plan→code→test→doc pipeline

老闆要做的任務:$ARGUMENTS

請用 **subagent** 工具跑下列 pipeline(`mode=blocking`),`task` 設為上面那句任務:

| stage | role | depends_on | 做什麼 |
|-------|------|-----------|--------|
| `plan` | `plan` | — | 規劃 {task}:拆解步驟、列要改的檔與風險 |
| `code` | `code` | `plan` | 依規劃實作 {task} |
| `test` | `aux` | `code` | 為 {task} 寫單元測試並跑過 |
| `doc` | `aux` | `code` | 為 {task} 補 / 更新文件 |

- `test` 與 `doc` 只相依 `code`,讓它們並行。
- 各 stage 的 model 由 role 對應的 agent 決定(`plan`=opus-5.5、`code`=sonnet-5.5、`aux`=haiku-5.5)。
- 跑完彙整各階段結果回報老闆;任一階段失敗即 fail-fast,立刻回報錯誤。

> 需站在**有 subagent 工具**的 agent 執行,建議先 `/agent orchestrator`(已設 availableAgents / trustedAgents,spawn 不跳核可)。
> 子 agent 內部的 write/shell 若仍跳核可,想全程 hands-off 可先 `/tools trust-all`(限本 session,會被子 agent 繼承)。
