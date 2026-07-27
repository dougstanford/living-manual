#!/bin/sh
# install-hook.sh [repo-root] — install the pre-push staleness guard.
# Idempotent: replaces a previous living-manual hook in place; a foreign
# pre-push is preserved as pre-push.local and chained. Worktree-safe
# (paths resolved via git rev-parse, never a hardcoded .git/).
# Where this plugin lives, resolved before the cd so it survives one.
# The hook needs it to call tickets-index.py --check, which it cannot
# inline: that check must be the same command CI runs, not a second
# implementation that can disagree with it.
LM_SCRIPTS=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
cd "${1:-.}" || exit 1
git rev-parse --git-dir >/dev/null 2>&1 || { echo "not a git repo"; exit 1; }
HOOKS=$(git rev-parse --git-path hooks)
mkdir -p "$HOOKS"
HOOK="$HOOKS/pre-push"

if [ -f "$HOOK" ] && ! grep -q living-manual "$HOOK"; then
  mv "$HOOK" "$HOOKS/pre-push.local"
  echo "existing pre-push preserved as pre-push.local (chained)"
fi

printf '#!/bin/sh\nLM_SCRIPTS=%s\n' "'$LM_SCRIPTS'" > "$HOOK"
cat >> "$HOOK" <<'HOOKEOF'
# living-manual pre-push guard: the manual must reflect what this push
# releases. Bypass once with --no-verify; the next dev inherits the gap.
#
# Two checks, two different powers. Staleness blocks: it is computed
# locally, and a broken base marker disables the guard for everyone.
# Queue drift only warns: proving it needs the tracker, which can be
# down for reasons the pusher did not cause, and a stale queue leaves
# the mechanism working. See reference/maintenance.md.
LOCAL="$(git rev-parse --git-path hooks)/pre-push.local"
[ -x "$LOCAL" ] && { "$LOCAL" "$@" || exit 1; }
cd "$(git rev-parse --show-toplevel)" || exit 0
[ -f .living-manual.json ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
OUT=$(python3 - <<'PYEOF'
import json, re, subprocess, sys
try:
    cfg = json.load(open(".living-manual.json"))
    manual = cfg.get("manual_path", "docs/USER_MANUAL.html")
    try:
        head = open(manual).read(8000)
    except FileNotFoundError:
        print("MISSING-MANUAL"); sys.exit(0)
    m = re.search(r"manual-base: ([0-9a-f]+)", head)
    if not m:
        print("CURRENT"); sys.exit(0)
    base = m.group(1)
    if subprocess.run("git cat-file -e %s^{commit}" % base, shell=True,
                      capture_output=True).returncode != 0:
        # History was rewritten after stamping, so there is no commit
        # range. The content fingerprints outlive the commit and can
        # still say whether anything user-facing actually moved.
        fp = re.search(r"<!-- manual-fingerprint.*?-->", head, re.S)
        fps = re.findall(r"^\s*([0-9a-f]{40})\s+(\S.*?)\s*$", fp.group(0), re.M) if fp else []
        if not fps:
            print("BAD-BASE " + base); sys.exit(0)
        moved = []
        for want, path in fps:
            got = subprocess.run(["git", "rev-parse", "HEAD:" + path.rstrip("/")],
                                 capture_output=True, text=True)
            if got.returncode != 0 or got.stdout.strip() != want:
                moved.append(path)
        if not moved:
            print("RESTAMP " + base); sys.exit(0)
        print("MOVED")
        for p in moved:
            print("  " + p)
        sys.exit(0)
    globs = " ".join("'%s'" % g for g in cfg.get("user_facing_paths", ["src/"]))
    out = subprocess.run("git log --oneline %s..HEAD -- %s" % (base, globs),
                         shell=True, capture_output=True, text=True).stdout.strip()
    print(out if out else "CURRENT")
except Exception:
    print("CURRENT")
PYEOF
)

# Advisory half: has the published queue drifted from the tracker? This
# calls the same command CI calls, so the two can never disagree about
# what drift is. It can never change the exit code, and it goes quiet
# when the plugin has moved since install or the tracker cannot be
# reached. The one network call is bounded by the fetch timeout a normal
# reconciliation already uses.
if [ -n "$LM_SCRIPTS" ] && [ -f "$LM_SCRIPTS/tickets-index.py" ]; then
  PATHS=$(python3 - <<'PYEOF' 2>/dev/null
import json
try:
    c = json.load(open(".living-manual.json"))
    print(c.get("tickets_dir", "docs/tickets"))
    print(c.get("manual_path", "docs/USER_MANUAL.html"))
except Exception:
    pass
PYEOF
)
  TDIR=$(printf '%s\n' "$PATHS" | sed -n 1p)
  MPATH=$(printf '%s\n' "$PATHS" | sed -n 2p)
  if [ -n "$TDIR" ] && [ -d "$TDIR" ] && [ -f "$MPATH" ]; then
    if DRIFT=$(python3 "$LM_SCRIPTS/tickets-index.py" "$TDIR" "$MPATH" --check 2>/dev/null); then
      :
    else
      echo "living-manual: the manual's queue has drifted from the tracker."
      printf '%s\n\n' "$DRIFT"
    fi
  fi
fi

case "$OUT" in
  CURRENT|"") exit 0 ;;
  MISSING-MANUAL)
    echo "living-manual: .living-manual.json names a manual that does not exist."
    echo "Rebuild it:   claude -p \"/living-manual:manual\""
    echo "Bypass once:  git push --no-verify"
    exit 1 ;;
  BAD-BASE*)
    echo "living-manual: the manual's base commit (${OUT#BAD-BASE }) is not in this clone."
    echo "Re-stamp it:  claude -p \"/living-manual:manual update\""
    echo "Bypass once:  git push --no-verify"
    exit 1 ;;
  RESTAMP*)
    echo "living-manual: the manual's base commit (${OUT#RESTAMP }) is gone, but every"
    echo "user-facing path still hashes the same. The manual's content is current."
    echo ""
    echo "Re-stamping the marker is the whole fix. Nothing needs rewriting:"
    echo "Re-stamp it:  claude -p \"/living-manual:manual update\""
    echo "Bypass once:  git push --no-verify"
    exit 1 ;;
  MOVED*)
    echo "living-manual: the manual's base commit is gone, so there is no commit"
    echo "range to read. These user-facing paths changed since it was stamped:"
    echo "$OUT" | tail -n +2
    echo ""
    echo "Update it before pushing:  claude -p \"/living-manual:manual update\""
    echo "Or bypass once:            git push --no-verify"
    exit 1 ;;
  *)
    echo "living-manual: the manual predates these user-facing commits:"
    echo "$OUT" | head -10
    echo ""
    echo "Update it before pushing:  claude -p \"/living-manual:manual update\""
    echo "Or bypass once:            git push --no-verify"
    exit 1 ;;
esac
HOOKEOF
chmod +x "$HOOK"
echo "pre-push guard installed at $HOOK"
