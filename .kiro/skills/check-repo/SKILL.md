---
name: check-repo
description: 檢查指定目錄是否符合 repo 標準(必備結構 + .gitignore 有效性 + 機密未外洩 + 文件一致 + 收尾狀態)。當 zawa 說「檢查某目錄是否合規 / 這個 repo 有沒有照規範」時使用。
---

# 檢查 repo 是否合規(check-repo)

要檢查的目錄(未指定則用目前目錄):$ARGUMENTS

> 規範來源:repoManager `docs/repo-standard.md`(§1 必備結構、§4 檢查項)。
> 本 skill 只**檢查與回報**,不自動修改;要補齊請走 `/create-repo` 或經 zawa 同意後動手。

## 檢查項目

針對目標目錄 `<dir>`,逐項核對並標記 ✅ 合規 / ⚠️ 建議 / ❌ 缺失。

### A. 必備結構(§1)
```bash
cd <dir>
for p in AGENTS.md .gitignore .env.example .git; do
  [ -e "$p" ] && echo "✅ $p" || echo "❌ 缺 $p"
done
{ [ -d doc ] || [ -d docs ]; } && echo "✅ docs/(或 doc/)" || echo "❌ 缺 docs/"
{ [ -f docs/glossary.md ] || [ -f doc/glossary.md ]; } && echo "✅ docs/glossary.md" || echo "❌ 缺 docs/glossary.md"
[ -d tmp ]        && echo "✅ tmp/"        || echo "⚠️ 無 tmp/(視階段)"
[ -f firstTask.md ] && echo "✅ firstTask.md" || echo "⚠️ 無 firstTask.md(可能已完成歸檔)"
```

### B. .gitignore 有效性
```bash
grep -qE '(^|/)\.env($|\*)' .gitignore && echo "✅ .env 已忽略" || echo "❌ .gitignore 未忽略 .env"
grep -q '!.env.example' .gitignore && echo "✅ 保留 .env.example" || echo "⚠️ 建議加 !.env.example"
grep -qE '(^|/)tmp/' .gitignore && echo "✅ tmp/ 已忽略" || echo "❌ .gitignore 未忽略 tmp/"
[ -f .kiroignore ] && grep -qE '^\s*/?tmp(/|/\*)?\s*$' .kiroignore && echo "❌ .kiroignore 列了 tmp/(會擋指定讀取)" || echo "✅ .kiroignore 未擋 tmp/"
```

### C. 機密未外洩(git 已追蹤清單)
```bash
git ls-files | grep -E '(^|/)\.env($|\.)' | grep -v '\.env\.example$' \
  && echo "❌ 有 .env 類機密被追蹤!" || echo "✅ 無 .env 機密被追蹤"
git ls-files | grep -E '(^|/)tmp/' && echo "⚠️ tmp/ 內容被追蹤" || echo "✅ tmp/ 未被追蹤"
```

### D. 文件一致
- `AGENTS.md` 內有指向 `docs/`(或 `doc/`)嗎?`grep -q 'doc' AGENTS.md`。
- `docs/`(或 `doc/`)是否非空?空的 → ⚠️ 提醒補文件。

### E. 收尾狀態(套用 §3)
- `git status --short` 是否乾淨?
- 有無明顯未辦事項(firstTask 未完成的勾、TODO)。

## 輸出

一份表格清單:每項 ✅/⚠️/❌ + 一句修正動作。結尾給總評:**合規** / **可用但有建議** / **不合規(列出必補項)**,並提示可用 `/create-repo` 補齊缺少的結構。
