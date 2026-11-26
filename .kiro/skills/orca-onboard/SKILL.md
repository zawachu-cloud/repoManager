---
name: orca-onboard
description: 把既有 repo 的本機機密(.env 等不進版控的檔)接上 orca 的 workspace 機制:在 ~/.config/<repo>/ 建單一來源、放通用 orca-setup.sh,讓每次開 workspace 自動 symlink 進去。當 zawa 說「把某 repo 接進 orca / 讓某 repo 在 orca 開 workspace 時自動帶 .env / orca onboard 某專案」時使用。不建立新 repo(那是 create-repo),只處理既有 repo 的本機機密與 orca hook。
---

# orca-onboard:既有 repo 接上 orca 本機機密機制

zawa 的指示(來源 repo 路徑,可含 repo 名):$ARGUMENTS

> 背景:orca 開 workspace 用的是 git worktree,`.env` 這類不進版控的本機機密不會跟著進來。
> 做法:把機密集中到 `~/.config/<repo>/`(單一來源),放一支通用 `orca-setup.sh`,再讓 orca 在開/收 workspace 時跑它,把機密 symlink 進該 worktree。hr、ansible、psapi-dotnet 都是這套。

## 1. 解析指示,缺的先問

| 項目 | 說明 | 預設/推法 |
|------|------|-----------|
| **來源 repo 路徑** | 目前握有 `.env` 等本機機密的那份(如 `~/proj/my/<repo>` 或 `~/orca/projects/<repo>`) | 必填,不清楚就問 |
| **repo 名** | 決定 `~/.config/<repo>/` | 取來源路徑 basename;有疑義就問 |
| **orca 專案目錄** | `~/orca/projects/<repo>`,用來對現有 worktree 首次 link | 可選;有就一併處理 |

任一不清楚先問 zawa,不要亂猜。

## 2. 安全檢查(動手前)

- 來源路徑要是 git 工作樹(`git -C <src> rev-parse --is-inside-work-tree`),否則停下來問。
- `~/.config/<repo>/` 已存在且已有機密檔 → 不覆蓋,先列出差異問 zawa。
- 全程不用 `rm -rf`、不強制覆蓋。步驟 4 會把來源原檔換成 symlink(動原檔),動手前一定先列清單給 zawa 確認。

## 3. 建 ~/.config/<repo>/ 並放 orca-setup.sh

```bash
mkdir -p ~/.config/<repo> && chmod 700 ~/.config/<repo>
TPL=<repoManager 路徑>/templates
cp "$TPL/orca-setup.sh" ~/.config/<repo>/orca-setup.sh
chmod 700 ~/.config/<repo>/orca-setup.sh
```
> `orca-setup.sh` 是通用範本,逐 repo 不用改:它會把 `~/.config/<repo>/` 內「被該 worktree gitignore 的頂層檔」symlink 進 worktree,已有實體檔則不覆蓋。

## 4. 複製機密來源檔 → 換來源原檔為 symlink(單一來源)

**偵測**:來源 repo 頂層、被 gitignore 的一般檔(等同 `orca-setup.sh` 會 link 的集合)。
```bash
cd <src>
for f in $(git ls-files --others --ignored --exclude-standard --directory | grep -vE '/$'); do
  case "$f" in */*) continue;; esac          # 只要頂層檔
  git check-ignore -q -- "$f" && echo "$f"
done
```
- **要收**:`.env`、`.env.local`、`.env.prod` 這類機密來源檔。
- **不收**:衍生/產生檔(如 `frontend/lib/config.js`,由腳本從 `.env` 產生)、目錄(`tmp/`、`node_modules/`)、`.DS_Store`/`*.log` 等雜訊。
- 偵測到 `.env*` 以外的檔,先列出問 zawa 要不要收,別自動搬。

對每個要收的檔(先把清單印給 zawa 確認再執行):
```bash
# a. 複製進單一來源(不覆蓋既有)
cp -n "<src>/$f" ~/.config/<repo>/"$f" && chmod 600 ~/.config/<repo>/"$f"
# b. 驗證內容一致(來源已有同名檔時)
diff -q "<src>/$f" ~/.config/<repo>/"$f"
# c. 來源原檔換成 symlink(動原檔→先確認過才做);先備份再換
cp -a "<src>/$f" "<src>/$f.bak.$(date +%Y%m%d%H%M%S)"
ln -sfn ~/.config/<repo>/"$f" "<src>/$f"
```
> 換 symlink 後,來源 repo 與所有 orca worktree 都指向 `~/.config/<repo>/` 同一份,改一處即生效。確認無誤後可刪 `.bak`(刪前再問一次)。

## 5. 對現有 worktree 首次 link

```bash
# 當前目錄或指定 worktree
bash ~/.config/<repo>/orca-setup.sh "<worktree 路徑>"
# 有 orca 專案目錄時,對其所有 workspace 跑一遍
for w in ~/orca/workspaces/<repo>/*/; do bash ~/.config/<repo>/orca-setup.sh "$w"; done
```

## 6. 設 orca hook(zawa 手動,CLI 不支援)

orca CLI **沒有**設 setup/hook 腳本的命令(`orca repo set` 只管 worktree 可見性與 browser profile);那段 `hookSettings.scripts` 存在 orca 背景程式用的 `profile-state.db`,**不要直接改**(有被覆蓋/改壞風險)。請 zawa 到 orca UI 的該專案設定,把下面這行填進 **setup**:

```
setup: bash ~/.config/<repo>/orca-setup.sh "$ORCA_WORKTREE_PATH"
```
> 只設 setup 即可。archive 不用設:`orca-setup.sh` 只建 symlink、不刪東西,worktree 被收時 symlink(指向 `~/.config/<repo>/`,非實體機密)自然消失,所以 archive 跑這支是 no-op。
> 設好後,之後每次開該專案的 workspace 都會自動帶機密,不用再手動跑步驟 5。

## 7. 收尾提示

- 列出實際做了什麼:`~/.config/<repo>/` 內容、來源哪些檔變成 symlink、對哪些 worktree link 了。
- 把步驟 6 的 setup 那行再貼一次,提醒 zawa 去 orca UI 設(這是唯一還要手動的一步;archive 不用設)。
- 驗證:在一個 worktree `ls -la .env` 應指向 `~/.config/<repo>/.env`,且 `git status` 乾淨(機密被 ignore)。
