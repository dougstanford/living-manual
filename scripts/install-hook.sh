#!/bin/sh
# install-hook.sh [repo-root] — install the pre-push staleness guard.
# Idempotent: replaces a previous living-manual hook in place; a foreign
# pre-push is preserved as pre-push.local and chained. Worktree-safe
# (paths resolved via git rev-parse, never a hardcoded .git/).
cd "${1:-.}" || exit 1
git rev-parse --git-dir >/dev/null 2>&1 || { echo "not a git repo"; exit 1; }
HOOKS=$(git rev-parse --git-path hooks)
mkdir -p "$HOOKS"
HOOK="$HOOKS/pre-push"

if [ -f "$HOOK" ] && ! grep -q living-manual "$HOOK"; then
  mv "$HOOK" "$HOOKS/pre-push.local"
  echo "existing pre-push preserved as pre-push.local (chained)"
fi

cat > "$HOOK" <<'HOOKEOF'
#!/bin/sh
# living-manual pre-push guard: the manual must reflect what this push
# releases. Bypass once with --no-verify; the next dev inherits the gap.
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
        head = open(manual).read(4000)
    except FileNotFoundError:
        print("MISSING-MANUAL"); sys.exit(0)
    m = re.search(r"manual-base: ([0-9a-f]+)", head)
    if not m:
        print("CURRENT"); sys.exit(0)
    base = m.group(1)
    if subprocess.run("git cat-file -e %s^{commit}" % base, shell=True,
                      capture_output=True).returncode != 0:
        print("BAD-BASE " + base); sys.exit(0)
    globs = " ".join("'%s'" % g for g in cfg.get("user_facing_paths", ["src/"]))
    out = subprocess.run("git log --oneline %s..HEAD -- %s" % (base, globs),
                         shell=True, capture_output=True, text=True).stdout.strip()
    print(out if out else "CURRENT")
except Exception:
    print("CURRENT")
PYEOF
)
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
