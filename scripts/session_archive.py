#!/usr/bin/env python3
"""Encrypted backup / restore of the session archive (~/.local/share/ai-session-export).

backup : encrypt each archive file with age into <repo>/blobs/<hash>.age, write an
         encrypted manifest, commit and push. Only changed files are re-encrypted
         (age output is non-deterministic, so unchanged files must not be touched).
         File names are hashed because archive names contain session titles.
restore: decrypt the manifest and every blob back into the archive directory.
         Refuses to overwrite existing files unless --force.

Design notes: repoManager docs/context-system.md §4a.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ARCHIVE = Path.home() / ".local" / "share" / "ai-session-export"
REPO = Path.home() / "proj" / "my" / "private_session_data"
IDENTITY = Path(os.environ.get("SESSION_ARCHIVE_IDENTITY", Path.home() / "proj" / "my" / "age.txt"))
LOCAL_INDEX = ARCHIVE / ".backup_index.json"  # local only: rel path -> plaintext sha256
SKIP_NAMES = {".backup_index.json"}
SKIP_DIRS = {"logs"}


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kwargs)


def recipient(identity: Path) -> str:
    for line in identity.read_text(encoding="utf-8").splitlines():
        if line.startswith("# public key:"):
            return line.split(":", 1)[1].strip()
    out = run(["age-keygen", "-y", str(identity)], capture_output=True, text=True)
    return out.stdout.strip()


def archive_files(archive: Path) -> dict[str, Path]:
    files = {}
    for path in sorted(archive.rglob("*")):
        rel = path.relative_to(archive)
        if not path.is_file() or path.name in SKIP_NAMES or rel.parts[0] in SKIP_DIRS or path.name.endswith(".tmp"):
            continue
        files[rel.as_posix()] = path
    return files


def blob_name(rel: str) -> str:
    return hashlib.sha256(rel.encode("utf-8")).hexdigest()[:24] + ".age"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encrypt(src: Path | None, dst: Path, rcpt: str, data: bytes | None = None) -> None:
    tmp = dst.with_name(dst.name + ".tmp")
    if src is not None:
        run(["age", "-r", rcpt, "-o", str(tmp), str(src)])
    else:
        run(["age", "-r", rcpt, "-o", str(tmp)], input=data)
    tmp.replace(dst)


def decrypt(src: Path, identity: Path) -> bytes:
    return run(["age", "-d", "-i", str(identity), str(src)], capture_output=True).stdout


def git(repo: Path, *args: str, capture: bool = False) -> str:
    out = run(["git", "-C", str(repo), *args], capture_output=capture, text=True)
    return out.stdout if capture else ""


def backup(archive: Path, repo: Path, identity: Path, push: bool) -> int:
    rcpt = recipient(identity)
    blobs = repo / "blobs"
    blobs.mkdir(parents=True, exist_ok=True)
    index = json.loads(LOCAL_INDEX.read_text()) if LOCAL_INDEX.is_file() else {}
    files = archive_files(archive)
    changed = 0
    manifest = {}
    for rel, path in files.items():
        name = blob_name(rel)
        digest = sha256(path)
        manifest[rel] = name
        if index.get(rel) == digest and (blobs / name).is_file():
            continue
        encrypt(path, blobs / name, rcpt)
        index[rel] = digest
        changed += 1
    wanted = set(manifest.values())
    removed = 0
    for blob in blobs.glob("*.age"):
        if blob.name not in wanted:
            blob.unlink()
            removed += 1
    index = {rel: digest for rel, digest in index.items() if rel in manifest}
    if changed or removed or not (repo / "manifest.json.age").is_file():
        encrypt(None, repo / "manifest.json.age", rcpt, json.dumps(manifest, ensure_ascii=False, indent=1).encode())
    tmp = LOCAL_INDEX.with_name(LOCAL_INDEX.name + ".tmp")
    tmp.write_text(json.dumps(index, indent=1))
    tmp.replace(LOCAL_INDEX)

    git(repo, "add", "-A")
    if not git(repo, "status", "--porcelain", capture=True).strip():
        print(f"[backup] no changes ({len(files)} files)")
        return 0
    git(repo, "commit", "-q", "-m", f"backup: {changed} updated, {removed} removed, {len(files)} total")
    if push:
        git(repo, "push", "-q", "origin", "HEAD")
    print(f"[backup] {changed} updated, {removed} removed, {len(files)} total, pushed={push}")
    return 0


def restore(archive: Path, repo: Path, identity: Path, force: bool) -> int:
    manifest = json.loads(decrypt(repo / "manifest.json.age", identity))
    conflicts = [rel for rel in manifest if (archive / rel).exists()]
    if conflicts and not force:
        print(f"[restore] {len(conflicts)} files already exist in {archive}; use --force to overwrite", file=sys.stderr)
        return 1
    old_umask = os.umask(0o077)
    try:
        for rel, name in manifest.items():
            dst = archive / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(decrypt(repo / "blobs" / name, identity))
    finally:
        os.umask(old_umask)
    print(f"[restore] {len(manifest)} files -> {archive}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["backup", "restore"])
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--identity", type=Path, default=IDENTITY, help="age identity file (secret key)")
    parser.add_argument("--no-push", action="store_true")
    parser.add_argument("--force", action="store_true", help="restore: overwrite existing files")
    args = parser.parse_args()
    global LOCAL_INDEX
    LOCAL_INDEX = args.archive / ".backup_index.json"
    if args.command == "backup":
        return backup(args.archive, args.repo, args.identity, push=not args.no_push)
    return restore(args.archive, args.repo, args.identity, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
