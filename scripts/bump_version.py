#!/usr/bin/env python3
"""Utility to bump the application version in version.py and optionally create a git tag.

Usage:
  python scripts/bump_version.py patch
  python scripts/bump_version.py minor
  python scripts/bump_version.py major
  python scripts/bump_version.py set 2.1.0

Options:
  --tag    Create a git commit & tag after bump.

The script enforces simple SemVer formatting (X.Y.Z).
"""
from __future__ import annotations
import re
import sys
import subprocess
from pathlib import Path

VERSION_FILE = Path(__file__).resolve().parent.parent / "version.py"
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

def read_version() -> str:
    text = VERSION_FILE.read_text(encoding="utf-8")
    # Look for __version__ = "x.y.z"
    for line in text.splitlines():
        if "__version__" in line and "=" in line:
            val = line.split("=")[-1].strip().strip("'\"")
            if SEMVER_RE.match(val):
                return val
    raise SystemExit("Could not locate current version in version.py")

def write_version(new_version: str):
    text = VERSION_FILE.read_text(encoding="utf-8")
    new_text = re.sub(r"__version__\s*=\s*['\"](.*?)['\"]", f"__version__ = \"{new_version}\"", text, count=1)
    VERSION_FILE.write_text(new_text + ("" if new_text.endswith("\n") else "\n"), encoding="utf-8")

def bump(part: str, current: str) -> str:
    m = SEMVER_RE.match(current)
    if not m:
        raise SystemExit(f"Current version '{current}' is not valid semver")
    major, minor, patch = map(int, m.groups())
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise SystemExit("Unknown bump part; expected major|minor|patch")

def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()

def main(argv: list[str]):
    if len(argv) < 2:
        print(__doc__)
        return 1
    action = argv[1]
    tag = "--tag" in argv
    if action == "set":
        if len(argv) < 3:
            raise SystemExit("Provide version to set")
        new_version = argv[2]
        if not SEMVER_RE.match(new_version):
            raise SystemExit("Version must match X.Y.Z")
        current = read_version()
    else:
        current = read_version()
        new_version = bump(action, current)

    if new_version == current:
        print(f"Version unchanged: {current}")
        return 0

    write_version(new_version)
    print(f"Version updated: {current} -> {new_version}")

    if tag:
        try:
            git("add", str(VERSION_FILE.relative_to(Path.cwd())))
            git("commit", "-m", f"chore: bump version to {new_version}")
            git("tag", f"v{new_version}")
            print(f"Created git tag v{new_version}")
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
