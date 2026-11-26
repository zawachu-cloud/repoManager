#!/usr/bin/env bash
# Orca 建立工作樹時執行：把本資料夾內的本機設定檔（不進 git）symlink 到工作樹根目錄。
# 放置規則：~/.config/<repo>/orca-setup.sh，與該 repo 的本機設定檔放在同一資料夾。
# 用法：bash ~/.config/<repo>/orca-setup.sh [工作樹路徑，預設目前目錄]
# 由 repoManager /orca-onboard skill 複製到 ~/.config/<repo>/；本檔為通用範本，不需逐 repo 改。
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SELF="$(basename "${BASH_SOURCE[0]}")"
DST="$(cd "${1:-$PWD}" && pwd)"
echo "orca-setup: SRC=$SRC DST=$DST"

if ! git -C "$DST" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "orca-setup: $DST 不是 git 工作樹，停止"; exit 1
fi

shopt -s dotglob nullglob
for path in "$SRC"/*; do
  f="$(basename "$path")"
  [ "$f" = "$SELF" ] && continue
  [ -f "$path" ] || continue
  if ! git -C "$DST" check-ignore -q -- "$f"; then
    echo "skip $f（不在 .gitignore，避免出現在 git status）"; continue
  fi
  if [ -e "$DST/$f" ] && [ ! -L "$DST/$f" ]; then
    echo "skip $f（已有實體檔，不覆蓋）"; continue
  fi
  ln -sfn "$path" "$DST/$f"
  echo "linked $f"
done
