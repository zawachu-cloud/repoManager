#!/usr/bin/env bash
# 匯出 AI 對話存檔(ai_session_export),通過 gitleaks 後加密備份到 private_session_data。
#
# 用法:
#   scripts/session-export.sh            # cron 用:kiro + claude-code 全部增量 → gitleaks → 加密備份並 push → 語意索引增量 → observer
#   scripts/session-export.sh --current  # /close-session 用:只匯出 $KIRO_SESSION_ID 這一個 session,不備份
#
# 設計見 docs/context-system.md §2a、§4a。log 在 ~/.local/share/ai-session-export/logs/。
set -euo pipefail
umask 077
export PATH="${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPORTER="${AI_SESSION_EXPORT_DIR:-${HOME}/proj/my/ai_session_export}"
PY="${EXPORTER}/.venv/bin/python"
ARCHIVE="${HOME}/.local/share/ai-session-export"
LOG_DIR="${ARCHIVE}/logs"
HEARTBEAT_DIR="${HOME}/.local/share/ai-heartbeat"   # observer/reflector 的 Kiro session,不匯出
mkdir -p "${LOG_DIR}"

if [[ ! -x "${PY}" ]]; then
  echo "找不到 ${PY}。先在 ${EXPORTER} 建 venv:python3 -m venv .venv && .venv/bin/pip install -e ." >&2
  exit 1
fi

if [[ "${1:-}" == "--current" ]]; then
  if [[ -z "${KIRO_SESSION_ID:-}" ]]; then
    echo "KIRO_SESSION_ID 未設定(要在 Kiro session 內執行)" >&2
    exit 1
  fi
  "${PY}" "${EXPORTER}/export_sessions.py" --source kiro --session-id "${KIRO_SESSION_ID}"
  exit 0
fi

# 同時只跑一份(cron 與手動重疊時)
exec 9>"${LOG_DIR}/.lock"
flock -n 9 || { echo "另一個匯出正在執行,略過"; exit 0; }

echo "=== $(date '+%F %T') session-export"
"${PY}" "${EXPORTER}/export_sessions.py" --source kiro --kiro-exclude-cwd "${HEARTBEAT_DIR}"
if [[ -d "${HOME}/.claude/projects" ]]; then
  "${PY}" "${EXPORTER}/export_sessions.py" --source claude-code
fi

if ! gitleaks dir "${ARCHIVE}" --config "${EXPORTER}/.gitleaks.toml" --no-banner --redact \
     --report-path "${LOG_DIR}/gitleaks-last.json" >/dev/null 2>&1; then
  echo "gitleaks 有命中,本次不備份。看 ${LOG_DIR}/gitleaks-last.json(已遮蔽原值),補遮罩規則後重跑 --full。" >&2
  exit 2
fi
echo "gitleaks: no leaks"

python3 "${REPO_ROOT}/scripts/session_archive.py" backup

# 語意搜尋索引:只重算有變動的檔(本地 Ollama)。失敗不影響已完成的備份。
if systemctl --user is-active --quiet ollama 2>/dev/null || curl -sf http://127.0.0.1:11434/api/version >/dev/null; then
  python3 "${REPO_ROOT}/scripts/semantic_search.py" index || echo "語意索引更新失敗,下次再試" >&2
else
  echo "Ollama 沒在跑,略過語意索引" >&2
fi

# L1 每日觀察:新對話 → OBSERVATIONS.md(見 docs/context-system.md §4c)。失敗不影響備份,下次會重試同一段。
python3 "${REPO_ROOT}/scripts/heartbeat.py" observe || echo "observer 失敗,見 ${HEARTBEAT_DIR}/last-obs.log" >&2
