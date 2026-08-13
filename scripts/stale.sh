#!/bin/sh
# stale.sh [repo-root] [manual-path] — is the manual current with the code?
#
# For each user_facing_paths entry it compares the path's content hash at
# HEAD to the hash the manual records in its manual-surfaces block. Prints
# "CURRENT" when every surface matches; otherwise names the surfaces that
# moved, which is exactly the input the update flow needs. No commit sha,
# no commit range, no history walk: the answer depends only on the tree at
# HEAD, so it is the same in a shallow clone and independent of how or in
# what order branches merged.
#
# Exit contract, so an unattended caller can act on it without parsing:
#   0  the manual is current
#   1  the manual needs work: named user-facing surfaces have moved
#   2  the check could not run: no config, no manual, or no surfaces block
#      (a legacy manual carrying only a manual-base sha lands here — run
#      the update flow once to migrate it)
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

m = re.search(r"<!-- manual-surfaces.*?-->", head, re.S)
if not m:
    # A manual from before this mechanism carried only a manual-base sha.
    # It cannot be checked as-is; one update run rewrites it to surfaces.
    if re.search(r"manual-base: [0-9a-f]+", head):
        print("LEGACY-MARKER")
        print("This manual predates the manual-surfaces block and carries "
              "only a manual-base sha.")
        print("Run the update flow once to migrate it:  /living-manual:manual update")
        sys.exit(2)
    print("NO-MARKER"); sys.exit(2)

stored = dict((p, h) for h, p in
              re.findall(r"^\s*([0-9a-f]{40})\s+(\S.*?)\s*$", m.group(0), re.M))

def head_hash(path):
    r = subprocess.run(["git", "rev-parse", "--verify", "--quiet",
                        "HEAD:" + path.rstrip("/")],
                       capture_output=True, text=True)
    got = r.stdout.strip()
    # rev-parse can exit 0 echoing an unparseable arg back; only a real
    # sha counts, matching how sync-index.py decides what to stamp.
    return got if r.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", got) else None

moved = []
for path in cfg.get("user_facing_paths", ["src/", "app/"]):
    now = head_hash(path)
    was = stored.get(path.rstrip("/")) or stored.get(path)
    if now is None and was is None:
        # Not a tracked path and never recorded (an empty dir or a glob):
        # sync-index.py skips it too, so it is not a surface that moved.
        continue
    if now != was:
        moved.append(path)

if not moved:
    print("CURRENT"); sys.exit(0)
print("MOVED")
print("These user-facing surfaces changed since the manual last described them:")
for p in moved:
    print(" ", p)
sys.exit(1)
EOF
