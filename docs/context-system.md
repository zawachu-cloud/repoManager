# Context 系統(記憶與規則)

讓 AI 在每個 repo 都知道「老闆是誰、怎麼工作、以前決定過什麼」。架構參考 [grapeot/context-infrastructure](https://github.com/grapeot/context-infrastructure)(參考版本 `3c25337`,2026-11-12),整合進 repoManager,不另開 repo。

## 1. 三層記憶

| 層 | 位置 | 內容 | 載入方式 |
|----|------|------|----------|
| **L3 全域規則** | `rules/SOUL.md`、`USER.md`、`COMMUNICATION.md` | AI 行為基調、老闆背景與偏好、溝通風格 | symlink 到 `~/.kiro/steering/`,**每個 session 自動載入**(每行都佔 token,保持精簡) |
| **L1/L2 觀察** | `contexts/memory/OBSERVATIONS.md` | 依日期追加的經驗與決策,標 🔴🟡🟢 | **按需** grep,不整份讀 |
| **原始對話** | `~/.local/share/ai-session-export/`(不在 repo) | 匯出並去除機密的對話 Markdown | 語意搜尋(第 3 階段) |

### L3 怎麼生效

`scripts/link-rules.sh` 把 `rules/*.md` symlink 到 `~/.kiro/steering/`。Kiro 的 `kiro_default` 會載入 `~/.kiro/steering/**/*.md`,自建 agent(`plan`/`code`/`aux`/`orchestrator`)預設也會繼承。
已驗證(2026-11-18):從 `/tmp` 用 default agent、從 `~/proj/my/stocktake` 用 `code` agent,都讀得到 `USER.md`。

- 改規則:直接改 `rules/*.md`,symlink 讓下一個 session 立刻生效,不需要 sync。
- 換機器:clone repoManager 後執行 `scripts/link-rules.sh`(冪等,不覆蓋非 symlink 的同名檔)。
- 若設定 `chat.disableInheritingDefaultResources=true`,自建 agent 就不會載入,需在 agent 的 `resources` 加 `file://~/.kiro/steering/**/*.md`。

## 2. 資料流(完整版)

```
~/.kiro/sessions/cli/ + ~/.claude/projects/
  │  ai_session_export(+ 自寫 Kiro adapter)
  │  ├─ 排除機密專案的 session(依 cwd)
  │  ├─ 遮罩金鑰 / 個資
  │  └─ 只留使用者與 assistant 文字,丟掉 thinking、tool result、subagent session
  ▼
~/.local/share/ai-session-export/   (私有;age 加密後備份)
  │  gitleaks 類掃描通過才往下
  ▼
semantic-search-skill 建索引(雲端 embedding;快取在本機,可重建,不備份)
  │
  ▼
observer(每日)→ OBSERVATIONS.md 追加 L1
reflector(每週)→ 整理 L1/L2,提出 rules/ 候選 → 老闆核准才合入
```

## 3. 決策紀錄

| 日期 | 決策 | 理由 / 替代方案 |
|------|------|------|
| 2026-11-18 | 整合進 repoManager,不另開 `~/proj/my/context` | repoManager 是 private;內容都是「AI 怎麼跟老闆工作」,和既有標準、`~/.kiro/` 備份同類;只需維護、備份一個 repo。代價:記憶會隨 repo 走,**repoManager 不可轉 public**。 |
| 2026-11-18 | ai_session_export、semantic-search-skill 當外部工具安裝 | 它們是獨立 repo,有自己的測試與更新;Kiro adapter 寫在 ai_session_export 的 fork。 |
| 2026-11-18 | 不搬 upstream 的 `rules/axioms/`(44 份)、`rules/skills/`(42 份)、`WORKSPACE.md` | upstream 說明那些是原作者的累積,只能參考;我們的 skill 已在 `.kiro/skills/`。 |
| 2026-11-18 | L3 用 `~/.kiro/steering/` symlink 載入 | default 與自建 agent 都吃得到,不必改每個 agent 的 `resources`。 |
| 2026-11-18 | embedding 可用雲端,但送出前不得含機密 | 老闆接受雲端;遮罩在匯出時做,存檔本身就乾淨。被排除的專案日後要查,可另用本地模型建索引。 |

## 4. 機密處理(第 2、3 階段的硬性要求)

1. **排除**:`cwd` 在下列目錄的 session 不匯出:`~/proj/my/hr`、`~/proj/my/hr_db`、`~/proj/my/income_ana`;內容提到 payroll 檔案的 session 一併排除。`line`、`stocktake`、`innerDoc` 待老闆確認。
2. **遮罩**:金鑰格式(`sk-…`、`AKIA…`、JWT、`service_role`)、密碼、身分證字號、銀行帳號、email、電話 → `[REDACTED]`。
3. **掃描**:建索引前用 gitleaks 類工具掃匯出結果,有命中就停止,不送出。
4. OBSERVATIONS 與 `rules/` 也不寫機密數值。

## 5. 分階段計畫

| 階段 | 內容 | 狀態 |
|------|------|------|
| 1 | `rules/` 三份檔、`OBSERVATIONS.md`、steering symlink、本文件 | ✅ 2026-11-18(`USER.md` 仍有 `<待補>`) |
| 2 | fork ai_session_export,寫 Kiro adapter + 排除 / 遮罩;匯出 Kiro 與 Claude Code;age 加密備份 | 待做 |
| 3 | 安裝 semantic-search-skill,選雲端 embedding 供應商,建索引;寫查詢 skill | 待做 |
| 4 | observer / reflector 改用 `kiro-cli chat --no-interactive`(已確認此參數存在)取代 upstream 的 OpenCode;接 cron 與 `/close-session` | 待做 |

## 6. 未決事項

- `line`、`stocktake`、`innerDoc` 是否列入排除清單。
- `USER.md` 的 `<待補>` 欄位(背景、各專案用途、討厭什麼)。
- embedding 供應商與模型(第 3 階段決定)。
- 換電腦前要先跑一次匯出,確認最後幾天的對話進了存檔(`~/.kiro/sessions/` 不會跟著走)。
