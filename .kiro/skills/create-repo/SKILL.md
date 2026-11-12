---
name: create-repo
description: 建立一個新 repo:在指定目錄 local 新建(git init)或從 git ssh url clone,並補齊必備結構(AGENTS.md、docs/、firstTask.md、.env、.env.example、tmp/、.gitignore),把老闆口述的第 1 份工作寫進 firstTask.md。當老闆說「在某目錄建立一個 [local] repo,我打算要做某任務」或「clone 某 git url 開新 repo」時使用。
---

# 建立新 repo

老闆的指示(目標目錄 + local/clone + 要做的任務):$ARGUMENTS

> 規範來源:repoManager `docs/repo-standard.md`(§1 必備結構、§2 建立流程)。範本在 repoManager `templates/`。
> 典型講法:「在 `<目錄>` 建立一個 local repo,我打算要做 <任務>」或「clone `<git ssh url>` 到 `<目錄>`,我打算要做 <任務>」。

## 1. 先解析指示,缺的先問

從 $ARGUMENTS 解析出三項;**任一不清楚就先問老闆**,不要亂猜:

| 項目 | 說明 |
|------|------|
| **目標目錄** | 新 repo 要放哪裡(絕對或相對路徑)。 |
| **建立方式** | `local`(新建空 repo)**或** 一個 **git ssh url**(要 clone)。 |
| **第 1 份工作** | 「我打算要做什麼任務」—— 會寫進 `firstTask.md`。 |

## 2. 安全檢查(動手前)

- 目標目錄**已存在且非空** → 先停下來向老闆確認,**不覆蓋**既有內容。
- clone 的 url 看起來不是老闆的 repo → 先確認。
- 全程**不使用** `rm -rf`、強制覆蓋;遇到要覆蓋既有檔一律先問。

## 3. 建立 repo

**方式 A:local 新建**
```bash
mkdir -p <目錄>
cd <目錄>
git init -b main        # 舊版 git 不支援 -b 時:git init && git symbolic-ref HEAD refs/heads/main
```

**方式 B:從 git ssh url clone**
```bash
git clone <ssh-url> <目錄>
cd <目錄>
```

## 4. 補齊必備結構(缺什麼補什麼,已存在不覆蓋)

以 repoManager `templates/` 為範本,在新 repo 根目錄備妥:

- `AGENTS.md` ← 複製 `templates/AGENTS.md` 後,填入專案名稱 / 一句話目標 / 已知技術棧。
- `docs/` ← 建目錄,放入 `templates/docs/README.md`(完整資訊之後往這裡擺)。
- `firstTask.md` ← 複製 `templates/firstTask.md`,把老闆口述的任務填進「任務」段(見步驟 5)。
- `.gitignore` ← 複製 `templates/gitignore` 為 `.gitignore`(至少要忽略 `.env`、`.env.*`、`tmp/`,保留 `!.env.example`)。
- `.env.example` ← 複製 `templates/env.example` 為 `.env.example`。
- `.env` ← 建立空的本機機密檔(**不進版控**;若有已知金鑰可請老闆填,勿寫死在版控)。
- `tmp/` ← 建目錄(放 `.gitkeep` 以保留空目錄;內容不進版控)。

範本路徑請用 repoManager 的絕對路徑(本 skill 所在 repo),例如:
```bash
TPL=<repoManager 路徑>/templates
cp "$TPL/AGENTS.md"       <目錄>/AGENTS.md
cp "$TPL/gitignore"       <目錄>/.gitignore
cp "$TPL/env.example"     <目錄>/.env.example
cp "$TPL/firstTask.md"    <目錄>/firstTask.md
mkdir -p <目錄>/docs <目錄>/tmp
cp "$TPL/docs/README.md"  <目錄>/docs/README.md
touch <目錄>/.env <目錄>/tmp/.gitkeep
```
> clone 來的 repo 若已有同名檔,**保留原檔**,只補缺少的。

## 5. 寫入第 1 份工作

把老闆口述的任務填進 `<目錄>/firstTask.md` 的「任務」段落(連同已知背景與完成定義),讓之後切進來的新 session 一讀就懂。

## 6. 收尾提示

- 列出實際建立/補齊了哪些檔。
- 跑一次 `/check-repo <目錄>` 自我驗證結構合規(或直接套用 `docs/repo-standard.md` §4 清單)。
- 告訴老闆:**`cd <目錄>` 後開新 session**,新 session 先讀 `AGENTS.md` 與 `firstTask.md` 再開工。
- **首次 commit 由 AI 直接做、不用問**(老闆已授權):確認 `.env` 未被 add 後 `git add -A && git commit`;若是 clone 來且有 remote,push 亦可直接進行。破壞性動作(force push 等)才需先確認。
