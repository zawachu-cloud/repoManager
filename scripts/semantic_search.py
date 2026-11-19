#!/usr/bin/env python3
"""Local semantic search over the AI session archive and OBSERVATIONS.md.

Wraps the semantic-search CLI (~/proj/my/semantic-search-skill) with the private
defaults: local Ollama endpoint, model, cache location, and source file list.
Nothing leaves the machine: Ollama listens on 127.0.0.1 only.

  semantic_search.py index                      # incremental: embed new/changed files only
  semantic_search.py query "問題" [-k 8] [--json] [--project hr] [--since 2026-10-01]

Design and model choice: repoManager docs/context-system.md §4b.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
CLI = HOME / "proj/my/semantic-search-skill/.venv/bin/semantic-search"
ARCHIVE = HOME / ".local/share/ai-session-export"
SOURCES = [ARCHIVE / "kiro", ARCHIVE / "claude_code"]
EXTRA_FILES = [Path(__file__).resolve().parent.parent / "contexts/memory/OBSERVATIONS.md"]
CACHE = HOME / ".local/share/semantic-search/sessions"
MODEL = os.environ.get("SEMANTIC_SEARCH_EMBEDDING_MODEL", "qwen3-embedding:4b")
ENV = {
    **os.environ,
    "OPENAI_API_KEY": "ollama-local",  # Ollama ignores it; the OpenAI SDK requires a value
    "SEMANTIC_SEARCH_BASE_URL": os.environ.get("SEMANTIC_SEARCH_BASE_URL", "http://127.0.0.1:11434/v1"),
}
BASE = [str(CLI), "--model", MODEL, "--provider", "ollama"]


def file_list() -> Path:
    files = sorted(str(p) for root in SOURCES if root.is_dir() for p in root.glob("*.md"))
    files += [str(p) for p in EXTRA_FILES if p.is_file()]
    handle = tempfile.NamedTemporaryFile("w", prefix="ss-files-", suffix=".txt", delete=False)
    handle.write("\n".join(files) + "\n")
    handle.close()
    return Path(handle.name)


def run(args: list[str]) -> str:
    if not CLI.exists():
        sys.exit(f"找不到 {CLI}。在 semantic-search-skill 建 venv:python3 -m venv .venv && .venv/bin/pip install -e .")
    proc = subprocess.run(args, capture_output=True, text=True, env=ENV)
    if proc.returncode != 0:
        sys.exit(f"semantic-search 失敗(Ollama 有在跑嗎?systemctl --user status ollama):\n{proc.stderr.strip()[-800:]}")
    return proc.stdout


FRONT = re.compile(r"^(title|date|project_directory|session_id):\s*\"?(.*?)\"?\s*$", re.M)


def meta(path: str, cache: dict[str, dict]) -> dict:
    if path not in cache:
        try:
            head = Path(path).read_text(encoding="utf-8", errors="replace")[:4000]
        except OSError:
            head = ""
        cache[path] = dict(FRONT.findall(head.split("\n---", 1)[0])) if head.startswith("---") else {}
    return cache[path]


def cmd_index(_: argparse.Namespace) -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    files = file_list()
    try:
        out = json.loads(run(BASE + ["rebuild", "--file-list", str(files), "--cache-dir", str(CACHE),
                                     "--workers", "4", "--batch-size", "32"]))
    finally:
        files.unlink(missing_ok=True)
    print(f"[index] files={out.get('files_scanned')} updated={out.get('files_updated')} "
          f"chunks_added={out.get('chunks_added')} model={MODEL}")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    files = file_list()
    want = max(40, args.k * 8)  # over-fetch: results are capped at 2 chunks per file, then filtered
    cmd = BASE + ["query", "--file-list", str(files), "--cache-dir", str(CACHE), "--query", args.text,
                  "--top-k", str(want)]
    if args.no_refresh:
        cmd.append("--no-refresh")
    try:
        results = json.loads(run(cmd))
    finally:
        files.unlink(missing_ok=True)

    metas: dict[str, dict] = {}
    rows, seen = [], {}
    for item in results:
        chunk = item["chunk"]
        path = chunk["source_file"]
        m = meta(path, metas)
        project = m.get("project_directory", "")
        if args.project and args.project not in project:
            continue
        if args.since and m.get("date", "9999") < args.since:
            continue
        if seen.get(path, 0) >= 2:  # at most 2 chunks per file
            continue
        seen[path] = seen.get(path, 0) + 1
        rows.append({
            "score": round(item["score"], 3),
            "file": path,
            "lines": chunk.get("position"),
            "title": m.get("title", Path(path).name),
            "date": m.get("date", ""),
            "project": project.replace(str(HOME), "~"),
            "session_id": m.get("session_id", ""),
            "text": chunk["text"],
        })
        if len(rows) >= args.k:
            break

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    if not rows:
        print("沒有結果")
    for i, r in enumerate(rows, 1):
        snippet = re.sub(r"\s+", " ", r["text"])[: args.chars]
        lines = f":{r['lines'][0]}-{r['lines'][1]}" if r["lines"] else ""
        print(f"{i}. [{r['score']}] {r['date']} {r['project']} | {r['title'][:60]}")
        print(f"   {r['file']}{lines}")
        print(f"   {snippet}\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index", help="incremental index of archive + OBSERVATIONS").set_defaults(func=cmd_index)
    q = sub.add_parser("query", help="search")
    q.add_argument("text")
    q.add_argument("-k", type=int, default=8, help="number of results (default 8)")
    q.add_argument("--project", help="substring of project_directory, e.g. hr or psapi-dotnet")
    q.add_argument("--since", help="only sessions on/after YYYY-MM-DD")
    q.add_argument("--chars", type=int, default=300, help="snippet length")
    q.add_argument("--json", action="store_true")
    q.add_argument("--no-refresh", action="store_true", help="skip indexing changed files first")
    q.set_defaults(func=cmd_query)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
