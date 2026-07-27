#!/bin/sh
# stale.sh [repo-root] [manual-path] — what changed since the manual's
# base commit. Prints "CURRENT" when nothing user-facing changed;
# otherwise prints the commit list and the changed user-facing files,
# which is exactly the input the update flow needs.
#
# Exit contract, so an unattended caller can act on it without parsing:
#   0  the manual is current
#   1  the manual needs work: user-facing commits postdate its base, or
#      the base does not resolve and its content has moved with it
#   2  the check could not run: no config, no manual, no marker
#   3  the base does not resolve but nothing user-facing moved: the
#      content is current and only the marker needs re-stamping
#
# manual-path overrides manual_path in the config, for a repo that moved
# its manual. Omit it and the config decides, as it always has.
cd "${1:-.}" || exit 1
CFG=".living-manual.json"
[ -f "$CFG" ] || { echo "NO-CONFIG"; exit 2; }
LM_MANUAL="${2:-$LM_MANUAL}"; export LM_MANUAL

python3 - <<'EOF'
import json, os, re, subprocess, sys

cfg = json.load(open(".living-manual.json"))
manual = os.environ.get("LM_MANUAL") or cfg.get("manual_path", "docs/USER_MANUAL.html")
try:
    head = open(manual).read(8000)
except FileNotFoundError:
    print("NO-MANUAL"); sys.exit(2)
m = re.search(r"manual-base: ([0-9a-f]+)", head)
if not m:
    print("NO-MARKER"); sys.exit(2)
base = m.group(1)

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

def fingerprints(text):
    """[(hash, path)] from the manual's fingerprint comment, if it has one."""
    m = re.search(r"<!-- manual-fingerprint.*?-->", text, re.S)
    if not m:
        return []
    return re.findall(r"^\s*([0-9a-f]{40})\s+(\S.*?)\s*$", m.group(0), re.M)

if subprocess.run(f"git cat-file -e {base}^{{commit}}", shell=True,
                  capture_output=True).returncode != 0:
    # The marker points at a commit this clone doesn't have: history was
    # rewritten after stamping. There is no commit range left, so fall
    # back to comparing content hashes, which survive the rewrite.
    fps = fingerprints(head)
    if not fps:
        # A manual stamped before fingerprints existed. Unverifiable
        # means stale, not current, exactly as it always did.
        print(f"BAD-BASE {base}"); sys.exit(1)
    moved = []
    for want, path in fps:
        got = subprocess.run(["git", "rev-parse", "HEAD:" + path.rstrip("/")],
                             capture_output=True, text=True)
        if got.returncode != 0 or got.stdout.strip() != want:
            moved.append(path)
    if not moved:
        print(f"RESTAMP {base}")
        print("The base commit is gone, but every user-facing path still "
              "hashes the same.")
        print("The manual's content is current; only the marker needs "
              "re-stamping.")
        sys.exit(3)
    print(f"MOVED {base}")
    print("The base commit is gone, so there is no commit range. These "
          "user-facing paths")
    print("changed since the manual was stamped:")
    for p in moved:
        print(" ", p)
    sys.exit(1)

globs = cfg.get("user_facing_paths", ["src/", "app/"])
paths = " ".join(f"'{g}'" for g in globs)
commits = sh(f"git log --oneline {base}..HEAD -- {paths}").strip()
if not commits:
    print("CURRENT"); sys.exit(0)
files = sh(f"git diff --name-only {base}..HEAD -- {paths}").strip()
print(f"BASE {base}")
print("== commits touching user-facing paths ==")
print(commits)
print("== files ==")
print(files)
sys.exit(1)
EOF
