#!/bin/sh
# ci-check.sh [repo-root] — the staleness guard, run server-side.
#
# The pre-push hook only guards a developer's clone. A squash merge or an
# "Update branch" click in the GitHub web UI rewrites history on the
# server, passes through no hook, and can land a manual whose base marker
# is orphaned or whose content is stale. This runs the same checks
# unattended, so CI catches what the hook never sees.
#
# LM_MANUAL and LM_TICKETS override the paths .living-manual.json names,
# for a repo that moved either.
#
# Exit 0 when every check passes, 1 otherwise. Every check runs even
# after one fails: a stale manual and a broken data block are one fix
# each, and reporting only the first would cost a second round trip.
SELF=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
cd "${1:-.}" || exit 1

FIX='claude -p "/living-manual:manual update"'

if [ ! -f .living-manual.json ]; then
  echo "living-manual: no .living-manual.json in $(pwd)."
  echo "This repo has no manual to guard. Either remove this check, or"
  echo "set one up:  claude -p \"/living-manual:manual\""
  exit 1
fi

# The config is the default for both paths; an explicit input wins, so a
# repo that moved its manual still works without editing the workflow.
MANUAL="$LM_MANUAL"
TICKETS="$LM_TICKETS"
[ -n "$MANUAL" ] || MANUAL=$(python3 -c 'import json; print(json.load(open(".living-manual.json")).get("manual_path", "docs/USER_MANUAL.html"))') || exit 1
[ -n "$TICKETS" ] || TICKETS=$(python3 -c 'import json; print(json.load(open(".living-manual.json")).get("tickets_dir", "docs/tickets"))') || exit 1

echo "living-manual: checking $MANUAL (tickets in $TICKETS)"
echo ""

if [ ! -f "$MANUAL" ]; then
  echo "FAIL: the configured manual does not exist at $MANUAL."
  echo ""
  echo "Build it:  claude -p \"/living-manual:manual\""
  exit 1
fi

# Staleness is answered from the tree at HEAD alone — no commit range, no
# history walk — so a shallow clone is fine and needs no fetch-depth: 0.

FAILED=0

echo "== integrity =="
python3 "$SELF/verify.py" "$MANUAL" || FAILED=1

echo ""
echo "== staleness =="
sh "$SELF/stale.sh" . "$MANUAL" || FAILED=1

# Advisory, exactly as in the pre-push hook, and the same command: drift
# is reported and never fails the check. A stale queue leaves the guard
# working, and proving drift needs the tracker, which can be down for
# reasons this branch did not cause.
echo ""
echo "== queue drift (advisory) =="
if [ -d "$TICKETS" ]; then
  python3 "$SELF/tickets-index.py" "$TICKETS" "$MANUAL" --check || true
else
  echo "no ticket directory at $TICKETS: skipping"
fi

if [ "$FAILED" -ne 0 ]; then
  echo ""
  echo "The manual does not match what this branch would release."
  echo "Fix it in a Claude Code session, then push the result:"
  echo "  $FIX"
  echo ""
  echo "These checks are plain python3 and sh, so CI can find the problem."
  echo "Writing the manual still needs a session."
  exit 1
fi

echo ""
echo "living-manual: manual is current and verifies."
