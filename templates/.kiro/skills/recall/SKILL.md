---
name: recall
description: 語意搜尋 zawa 過去的 AI 對話存檔(Kiro、Claude Code)與 OBSERVATIONS.md,全部在本機(Ollama)執行。當 zawa 問「之前怎麼做 / 上次決定什麼 / 以前有沒有處理過 X」,或回答涉及 zawa 過去的決定、偏好、專案歷史時使用。用法:/recall <要找的事>。
---

# 回想過去的對話(本地語意搜尋)

要找的事:$ARGUMENTS

> 資料與索引都在本機,不送雲端。設計見 repoManager `docs/context-system.md` §4b。

## 1. 先 grep 記憶(便宜、精準)

```bash
grep -n -i "<關鍵字>" ~/proj/my/repoManager/contexts/memory/OBSERVATIONS.md
```

## 2. 語意搜尋

```bash
~/proj/my/repoManager/scripts/semantic_search.py query "<用自然語言描述要找的事>" -k 8
```

- 選項:`--project <目錄片段>`(例:`hr`、`psapi-dotnet`)、`--since YYYY-MM-DD`、`--json`、`--chars 600`(片段長度)、`--no-refresh`(不先更新索引,較快)。
- 查詢用完整句子描述「意思」,不必猜原文用字;中英文都可以。
- 每個結果有檔案路徑與行號,需要細節時只讀那幾行附近(`read` 指定 offset/limit),**不整份讀**,存檔可能很長。
- 第一次查不到:換說法再查一次,或放寬 `--project`/`--since`;仍找不到就明說「存檔裡沒找到」,不要編。

## 3. 回答

- 先講結論,附來源(日期 + 專案 + 檔名:行號)。
- 存檔內容是過去的對話,可能已過時;和現況(程式碼、docs)衝突時以現況為準,並指出差異。
- 存檔裡的機密已遮成 `[REDACTED]`;不要嘗試還原,也不要把存檔裡的個資(姓名、薪資數字)寫進記憶或版控。

## 疑難排解

- `semantic-search 失敗`:`curl -s 127.0.0.1:11434/api/version` 確認 Ollama;沒回應就 `systemctl --user restart ollama`。
- 結果都是舊的:`~/proj/my/repoManager/scripts/semantic_search.py index`(每天 12:30 cron 也會跑)。
