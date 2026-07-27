#!/bin/sh
# stale.sh [repo-root] [manual-path] — what changed since the manual's
# base commit. Prints "CURRENT" when nothing user-facing changed;
# otherwise prints the commit list and the changed user-facing files,
# which is exactly the input the update flow needs.
#
# Exit contract, so an unattended caller can act on it without parsing:
#   0  the manual is current
#   1  the manual needs work: user-facing commits postdate its base, or
#      the base does not resolve in this clone
#   2  the check could not run: no config, no manual, no marker
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
sys.exit(1)
EOF
