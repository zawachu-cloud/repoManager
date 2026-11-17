#!/usr/bin/env bash
# 把全域 ~/.kiro/ 的 model routing 設定複製回 templates/.kiro/(版控備份)。
# 用法:改完 ~/.kiro/ 後執行 scripts/sync-kiro.sh,確認 git diff 後 commit。
# 只同步下列清單,不會碰 ~/.kiro/ 的其他檔。
set -euo pipefail

SRC="${HOME}/.kiro"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DST="${REPO_ROOT}/templates/.kiro"

AGENTS=(plan code aux orchestrator)
SKILLS=(pipeline)

mkdir -p "${DST}/agents" "${DST}/skills"

for name in "${AGENTS[@]}"; do
  src="${SRC}/agents/${name}.json"
  if [[ ! -f "${src}" ]]; then
    echo "缺少 ${src},略過" >&2
    continue
  fi
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" "${src}" \
    || { echo "JSON 格式錯誤:${src},中止" >&2; exit 1; }
  cp "${src}" "${DST}/agents/${name}.json"
  echo "agent  ${name}"
done

for name in "${SKILLS[@]}"; do
  src="${SRC}/skills/${name}/SKILL.md"
  if [[ ! -f "${src}" ]]; then
    echo "缺少 ${src},略過" >&2
    continue
  fi
  mkdir -p "${DST}/skills/${name}"
  cp "${src}" "${DST}/skills/${name}/SKILL.md"
  echo "skill  ${name}"
done

echo "--- git 變更 ---"
git -C "${REPO_ROOT}" status --short -- templates/.kiro
