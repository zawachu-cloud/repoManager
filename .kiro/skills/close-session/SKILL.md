---
name: close-session
description: 收尾檢查一個工作 session。依序做三件事:(1) 檢查本 session 未辦事項,(2) 檢查 git 狀態是否乾淨,(3) 檢查本 session 動作與文件是否一致。當老闆說「close session / 收工 / 結束這個 session」時使用。
---

# 收尾檢查(close session)

額外指示(可選,如指定對哪個目錄收尾):$ARGUMENTS

> 規範來源:repoManager `docs/repo-standard.md` §3。預設對「目前所在的 repo」收尾。
> 目的:先結清手邊工作,再確保 git 乾淨、文件與動作一致,讓下次接手不踩坑。

## 步驟 1:檢查未辦事項(先做,沒清完不往下)

盤點本 session:
- 待完成的修改、尚未跑或沒過的測試、未回覆老闆的問題、留著的 TODO / 暫緩項。
- `firstTask.md`(若存在)的「完成定義」是否都打勾?未完成就列出來。

**有未辦事項 → 先列出並處理,或向老闆確認要不要留到下次**;確認前不進入步驟 2。

## 步驟 2:檢查 git 狀態是否乾淨

```bash
git status
git status --short
git ls-files --error-unmatch .env 2>/dev/null && echo "⚠️ .env 被追蹤了!" || echo "OK: .env 未被追蹤"
```
- 有未預期的未追蹤/未提交變更 → 列出並整理。
- **確認機密沒被 add**:`.env`、`.env.*`(除 `.env.example`)、`tmp/` 內容都不該出現在 `git ls-files`。

## 步驟 3:檢查本 session 動作與文件是否一致

- 這次改了什麼(程式/設定/流程),就對照 `AGENTS.md`、`docs/`、`firstTask.md` 是否同步更新。
- 文件描述與現狀不符 → 補正或明確回報落差。
- 文件結構若明顯可更省 token(重複、該下放到 `docs/`),**提建議讓老闆決定,不擅自大改**。

## 步驟 3b:更新 USER.md 的「目前的專案」(只動當下 repo 那一行)

檔案:`~/proj/my/repoManager/rules/USER.md`(全域規則,`~/.kiro/steering/USER.md` 是它的 symlink)。

- 依本 session 做的事與該 repo 的 `AGENTS.md`,判斷當下 repo 那一行是否缺、是 `<待補>`、或用途已改變。需要才改,**一行為限**,不動其他 repo 的行與其他段落。
- 新 repo 不在清單 → 加一行。
- 只寫用途與方向,不寫憑證與資料內容(姓名、身分證、薪資數字、帳號)。
- 有改就在 repoManager 另外 commit / push(訊息如 `USER.md: update <repo> project line`)。當下 repo 就是 repoManager 時,併入步驟 4 一起提交。

## 步驟 4:直接 commit / push(AI 決定,不用問)

確認機密未外洩後,**直接** `git add -A && git commit && git push`(老闆已授權,不用再問);commit 訊息用祈使句描述本次變更。
**破壞性動作**(force push、`reset --hard`、drop/truncate)仍須先向老闆確認。
若該 repo 自己的 `AGENTS.md` 另有部署/push 規範(如先 DB 後前端),以該 repo 規範為準。

## 步驟 5:匯出本 session 對話(最後做,才包含上面的收尾內容)

```bash
~/proj/my/repoManager/scripts/session-export.sh --current
```
- 只匯出 `$KIRO_SESSION_ID` 這一個 session 到 `~/.local/share/ai-session-export/kiro/`(已遮罩金鑰),不掃其他 session、不備份。加密備份由每天 12:30 的 cron 做。
- 失敗(例如 `KIRO_SESSION_ID` 未設定、venv 不存在)只回報,不擋收尾;cron 會補上。
- 設計見 repoManager `docs/context-system.md` §2a。

## 輸出

給一份收尾報告:
1. 未辦事項:無 / 已處理 / 待老闆決定(列清單)。
2. git 狀態:乾淨 / 有變更(列清單)+ 機密未外洩確認。
3. 文件一致性:一致 / 已補正 / 建議事項;USER.md 專案行:未變 / 已更新(寫出新內容)。
4. commit / push:已提交的 commit 訊息與是否已 push。
5. 對話匯出:已匯出(檔名)/ 失敗(原因,cron 會補)。
最後一句明確說:**已收尾完成** 或 **還有 N 項待處理**。
