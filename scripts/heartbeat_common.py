"""Shared helpers for heartbeat.py (observe) and heartbeat_reflect.py (reflect).

Paths, state, session listing, kiro runner, gitleaks check, scoped git commit, redact import.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HOME = Path.home()
os.environ["PATH"] = f"{HOME}/.local/bin:" + os.environ.get("PATH", "/usr/bin:/bin")  # cron: kiro-cli, gitleaks
REPO = Path(__file__).resolve().parent.parent
OBS = REPO / "contexts/memory/OBSERVATIONS.md"
USER = REPO / "rules/USER.md"
PENDING = REPO / "contexts/memory/pending-review.md"
ARCHIVE = HOME / ".local/share/ai-session-export"
SOURCES = [ARCHIVE / "kiro", ARCHIVE / "claude_code"]
WORKDIR = HOME / ".local/share/ai-heartbeat"
STATE = WORKDIR / "state.json"
PROJECTS_ROOTS = [HOME / "orca/projects", HOME / "proj/my"]  # new projects go to the first; old ones remain in the second
FORK_SRC = HOME / "proj/my/ai_session_export/src"
GITLEAKS_CONFIG = HOME / "proj/my/ai_session_export/.gitleaks.toml"
RECORD_MARK = "<!-- 以下為記錄區,新條目追加在最後 -->"
GC_DAYS = 30
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

sys.path.insert(0, str(FORK_SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from heartbeat_merge import LINE_OK  # noqa: E402
try:
    from ai_session_export.redact import redact  # noqa: E402
except ImportError:  # pragma: no cover
    sys.exit(f"找不到遮罩模組 {FORK_SRC}/ai_session_export/redact.py")


# ---------- helpers ----------

def log(msg: str) -> None:
    print(f"[heartbeat {datetime.now():%F %T}] {msg}", flush=True)


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.is_file() else {}


def save_state(state: dict) -> None:
    WORKDIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1))
    tmp.replace(STATE)


FRONT = re.compile(r"^(title|date|project_directory|message_count):\s*\"?(.*?)\"?\s*$", re.M)


def meta(path: Path) -> dict:
    head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    return dict(FRONT.findall(head.split("\n---", 1)[0])) if head.startswith("---") else {}


def run_kiro(prompt: str, marker: str, timeout: int = 1800, attempts: int = 2) -> str | None:
    """Run the heartbeat agent; retry once (the service sometimes fails mid-stream)."""
    for attempt in range(1, attempts + 1):
        result = _run_kiro_once(prompt, marker, timeout)
        if result is not None:
            return result
        if attempt < attempts:
            log(f"第 {attempt} 次失敗,60 秒後重試")
            time.sleep(60)
    return None


def _run_kiro_once(prompt: str, marker: str, timeout: int) -> str | None:
    WORKDIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["kiro-cli", "chat", "--no-interactive", "--agent", "heartbeat", prompt],
        cwd=WORKDIR, capture_output=True, text=True, timeout=timeout,
    )
    out = ANSI.sub("", proc.stdout)
    (WORKDIR / f"last-{marker.lower()}.log").write_text(out[-20000:] + "\n--- stderr ---\n" + proc.stderr[-4000:])
    match = re.search(rf"<<<{marker}\s*\n?(.*?)\n?\s*{marker}>>>", out, re.S)
    if proc.returncode != 0 or not match:
        log(f"kiro 執行失敗或沒有 {marker} 標記(rc={proc.returncode}),見 {WORKDIR}/last-{marker.lower()}.log")
        return None
    return match.group(1).strip()


def gitleaks_clean(text: str) -> bool:
    proc = subprocess.run(["gitleaks", "stdin", "--no-banner", "--redact", "--config", str(GITLEAKS_CONFIG)],
                          input=text, capture_output=True, text=True)
    return proc.returncode == 0


def commit(paths: list[Path], message: str, dry_run: bool) -> None:
    if dry_run:
        return
    rel = [str(p.relative_to(REPO)) for p in paths]
    subprocess.run(["git", "-C", str(REPO), "add", "--", *rel], check=True)  # only these files
    if not subprocess.run(["git", "-C", str(REPO), "status", "--porcelain", "--", *rel],
                          capture_output=True, text=True).stdout.strip():
        return
    subprocess.run(["git", "-C", str(REPO), "commit", "-q", "-m", message, "--", *rel], check=True)
    push = subprocess.run(["git", "-C", str(REPO), "push", "-q"], capture_output=True, text=True)
    log("pushed" if push.returncode == 0 else f"push 失敗(下次 commit 會一起推):{push.stderr.strip()[-200:]}")


def clean_lines(raw: str) -> list[str]:
    lines = []
    for line in raw.splitlines():
        line = redact(line.strip().lstrip("-* ").strip())
        if LINE_OK.match(line):
            lines.append(line)
    return lines


def changed_sessions(since_ts: float) -> list[Path]:  # used by reflect (last 7 days)
    files = [p for root in SOURCES if root.is_dir() for p in root.glob("*.md") if p.stat().st_mtime > since_ts]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def all_sessions() -> list[Path]:
    return sorted((p for root in SOURCES if root.is_dir() for p in root.glob("*.md")), key=lambda p: p.stat().st_mtime)
