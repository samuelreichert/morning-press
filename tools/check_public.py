#!/usr/bin/env python3
"""Check indexed and optionally historical Git blobs before public release."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

PATTERNS = {
    "absolute home path": re.compile(r"(?:/Users/|/home/)[A-Za-z0-9_.-]+|[A-Za-z]:\\Users\\[A-Za-z0-9_.-]+"),
    "email address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "credential-like token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{24,}|AKIA[A-Z0-9]{16})\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "private calendar feed": re.compile(r"webcal" r"://|https://[^\s\"<>]*(?:private-[A-Za-z0-9]+|/calendar/ical/[^\s\"<>]+/private)"),
}


def findings(text):
    # Deliberately return labels, not potentially sensitive matching values.
    return [name for name, pattern in PATTERNS.items() if pattern.search(text)]


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def scan(root, history=False):
    root = Path(root)
    indexed = git(root,"ls-files","--stage","-z").decode().split("\0")
    manifest = json.loads(git(root,"show",":public-files.json"))
    if not isinstance(manifest,list) or len(manifest) != len(set(manifest)) or any(not isinstance(p,str) or PurePosixPath(p).is_absolute() or ".." in PurePosixPath(p).parts for p in manifest):
        raise ValueError("public-files.json must be a unique list of relative public paths")
    allowed = set(manifest)
    problems, checked, current = [], set(), set()

    def blob(sha, path):
        if path not in allowed:
            problems.append(f"Unapproved public path: {path}")
        if sha in checked:
            return
        checked.add(sha)
        data = git(root,"cat-file","blob",sha)
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"Binary file requires separate publication review: {path}")
            return
        for kind in findings(text):
            problems.append(f"{path}: {kind}")

    for entry in filter(None,indexed):
        info, path = entry.split("\t",1)
        mode, sha, stage = info.split()
        current.add(path)
        if mode != "100644" and mode != "100755":
            problems.append(f"Only regular files are allowed: {path}")
        if stage != "0":
            problems.append(f"Unmerged index entry: {path}")
        if mode in ("100644","100755"):
            blob(sha,path)
    for missing in sorted(allowed-current):
        problems.append(f"Manifest path is not indexed: {missing}")
    if history:
        for entry in git(root,"rev-list","--objects","--all").decode().splitlines():
            sha, _, path = entry.partition(" ")
            if path and git(root,"cat-file","-t",sha).strip() == b"blob":
                blob(sha,path)
    if problems:
        raise ValueError("\n".join(sorted(set(problems))))
    return len(checked)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history",action="store_true",help="Also inspect all reachable historical blobs")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        count = scan(root,args.history)
    except (ValueError,subprocess.CalledProcessError) as exc:
        parser.exit(1,f"Public-file check failed:\n{exc}\n")
    print(f"Public-file check passed: {count} blobs. Review prose manually before publication.")


if __name__ == "__main__":
    main()
