# repoManager

管理「我怎麼開 repo、怎麼收尾 repo」的工具型 repo。存放 **repo 標準** 與 **三個可重複使用的 skill**,讓每次新開 repo / 收工都走一致流程、不用重打需求。

## 內容

- **`docs/repo-standard.md`** — repo 必備結構 + close session 規範(**單一真實來源**)。
- **`.kiro/skills/`** — 三個 slash 指令:
  - `/create-repo <目錄> <local 或 git url> <第 1 份工作>` — 建立新 repo 並補齊必備結構。
  - `/close-session` — 收尾檢查:未辦事項 → git 乾淨 → 動作與文件一致。
  - `/check-repo <目錄>` — 檢查指定目錄是否符合 repo 標準。
- **`templates/`** — 新 repo 範本(AGENTS.md、firstTask.md、gitignore、env.example、docs/README),以及 `templates/.kiro/`:全域 `~/.kiro/` 角色 agent 與 pipeline skill 的版控備份。
- **`scripts/sync-kiro.sh`** — 把 `~/.kiro/` 的 agent 與 pipeline skill 同步回 `templates/.kiro/`。
- **`rules/`、`contexts/memory/`** — context 系統(參考 grapeot/context-infrastructure):全域規則與觀察紀錄。`scripts/link-rules.sh` 把 `rules/*.md` 掛到 `~/.kiro/steering/`,所有 repo 自動載入。見 `docs/context-system.md`。

## 換機器

```
git clone git@github.com:zawachu-cloud/repoManager.git ~/proj/my/repoManager
cp -r templates/.kiro/agents templates/.kiro/skills ~/.kiro/   # 還原角色 agent 與 pipeline
scripts/link-rules.sh                                          # 掛上全域規則
```

## Model routing 與 pipeline

依任務用不同 model:`plan`=opus-5.5、`code`=sonnet-5.5、`aux`=haiku-5.5(log、測試、文件)。設定只維護全域 `~/.kiro/`,所有 repo 共用。

```
/agent plan | code | aux                    # 手動切換角色
/agent orchestrator                         # 總架構師:直接討論,或 /pipeline 拆解並分派
/pipeline 為報表頁加 CSV 匯出功能
```

細節見 `docs/repo-standard.md` §5 / §5a。

## 怎麼用

在這個 repo(或任何載入這些 skill 的 session)輸入 slash 指令即可,例如:

```
/create-repo 在 ~/proj/my/foo 建立一個 local repo,我打算要做一個報表匯出工具
/check-repo ~/proj/my/hr
/close-session
```

細節與慣例見 `AGENTS.md`;規範見 `docs/repo-standard.md`。
