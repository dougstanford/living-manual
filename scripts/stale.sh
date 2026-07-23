#!/bin/sh
# stale.sh [repo-root] — what changed since the manual's base commit.
# Exit 0 with "CURRENT" when nothing user-facing changed; otherwise
# prints the commit list and the changed user-facing files, which is
# exactly the input the update flow needs.
cd "${1:-.}" || exit 1
CFG=".living-manual.json"
[ -f "$CFG" ] || { echo "NO-CONFIG"; exit 2; }

python3 - <<'EOF'
import json, re, subprocess, sys

cfg = json.load(open(".living-manual.json"))
manual = cfg.get("manual_path", "docs/USER_MANUAL.html")
try:
    head = open(manual).read(4000)
except FileNotFoundError:
    print("NO-MANUAL"); sys.exit(2)
m = re.search(r"manual-base: ([0-9a-f]+)", head)
if not m:
    print("NO-MARKER"); sys.exit(2)
base = m.group(1)

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

if subprocess.run(f"git cat-file -e {base}^{{commit}}", shell=True,
                  capture_output=True).returncode != 0:
    # The marker points at a commit this clone doesn't have (rewritten
    # history, shallow clone). Unverifiable means stale, not current.
    print(f"BAD-BASE {base}"); sys.exit(1)

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
EOF
