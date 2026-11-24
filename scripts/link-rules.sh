#!/usr/bin/env bash
# 把 repoManager/rules/*.md 以 symlink 掛到 ~/.kiro/steering/,讓所有 repo 的 Kiro session 自動載入 L3 規則。
# kiro_default 會載入 ~/.kiro/steering/**/*.md;自建 agent 預設也會繼承(除非 chat.disableInheritingDefaultResources=true)。
# 冪等:已是指向正確位置的 symlink 就略過;同名但不是 symlink 的檔不覆蓋,報錯讓 zawa 處理。
# 換機器時:clone repoManager 後執行一次即可。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${REPO_ROOT}/rules"
DST="${HOME}/.kiro/steering"
FILES=(SOUL.md USER.md COMMUNICATION.md)

mkdir -p "${DST}"
rc=0
for f in "${FILES[@]}"; do
  target="${SRC}/${f}"
  link="${DST}/${f}"
  if [[ ! -f "${target}" ]]; then
    echo "缺少 ${target},略過" >&2; rc=1; continue
  fi
  if [[ -L "${link}" ]]; then
    if [[ "$(readlink "${link}")" == "${target}" ]]; then
      echo "ok     ${link}"; continue
    fi
    echo "${link} 是指向別處的 symlink($(readlink "${link}")),未變更" >&2; rc=1; continue
  fi
  if [[ -e "${link}" ]]; then
    echo "${link} 已存在且不是 symlink,未覆蓋" >&2; rc=1; continue
  fi
  ln -s "${target}" "${link}"
  echo "linked ${link} -> ${target}"
done
exit "${rc}"
