---
id: TICKET-0006
title: Staleness marker is a content hash per surface, not a base commit sha, so branches merge in any order
type: idea
target: current
status: shipped
section: The staleness guard (#guard)
created: 2026-08-12
---

## Summary

The manual stamped a single `manual-base: <sha>` comment at a fixed line
near the top of the file, and every `/manual update` rewrote that line
to its own branch's HEAD. Git's 3-way merge therefore conflicted on that
line for every merge after the first in a queue: both trunk and the
incoming branch had changed the same line away from the common ancestor
to different values. The content fingerprints added in TICKET-0002 sat
directly under the base marker and were recomputed wholesale on every
stamp, so they drifted further out of sync the deeper a branch sat in the
queue. The net effect was a guaranteed manual conflict on every parallel
merge past the first, worsening down the queue.

The fix removes the base sha entirely and promotes the per-path content
hash — already built as a rewrite-proof fallback in TICKET-0002 — to be
the sole mechanism. The manual records one `<40-hex> <path>` line per
`user_facing_paths` entry in a `manual-surfaces` comment. Staleness is a
per-surface hash comparison at HEAD: no commit sha, no commit range, no
history walk. An update rewrites only the line for a surface it actually
changed, so branches touching different surfaces edit different lines and
merge cleanly in any order; branches touching the same surface collide on
that one line, which is a reconciliation a human owes anyway.

## Motivation

The user reported that queued tickets conflicted on the manual on every
merge beyond the first, and that the drift grew down the queue. The root
cause is a per-branch, position-locked value (the base sha) that every
branch is forced to rewrite. Because merges land on GitHub's servers, a
local merge driver cannot help; the file has to merge cleanly under
git's own 3-way merge, which means no branch may rewrite a shared line
it did not semantically change.

## Functional requirements

- FR-1: The manual records staleness as a `manual-surfaces` comment, one
  git content hash per `user_facing_paths` entry, and carries no base
  commit sha. `sync-index.py` stamps it from HEAD when the payload sets
  `"surfaces": true`, rewriting only the block, so unchanged path lines
  keep their prior bytes and a 3-way merge keeps whichever side moved.
- FR-2: `stale.sh` reports `CURRENT` (exit 0) when every surface's hash
  at HEAD matches the recorded hash; otherwise exit 1 naming the moved
  surfaces. Exit 2 when it cannot run (no config, no manual, no surfaces
  block). No base sha, commit range, or history is consulted, so a
  shallow clone answers correctly.
- FR-3: `verify.py` requires a well-formed `manual-surfaces` block (one
  40-char hash and a path per line) unless the file is a static export,
  and drops the base-resolves-to-a-commit check.
- FR-4: A legacy manual carrying only a `manual-base` sha is recognized
  and reported as needing migration (stale.sh exit 2, a verify finding, a
  blocking hook message), not crashed on. One update run rewrites it to
  the new block: `sync-index.py` strips the old base and fingerprint
  comments when it first writes `manual-surfaces`.
- FR-5: `scaffold.py`, `export.py`, `install-hook.sh`, `ci-check.sh`, and
  `state.sh` all move to the surfaces model. `ci-check.sh` drops the
  shallow-clone bail; the CI workflow and its template drop
  `fetch-depth: 0`.
- FR-6: The merge-commit-only rule is relaxed. All three merge methods
  are safe because the marker is content, not a sha. The technical
  contract, CLAUDE.md, the PR template, and the manual reflect this.

## Acceptance criteria

- Given two branches from the same trunk, one editing `skills/` and one
  editing `scripts/`, when both run the update flow and merge into trunk
  in either order, then neither merge conflicts on the manual and
  `stale.sh` prints `CURRENT` on the final tree.
- Given two branches that both edit `scripts/`, when the second merges,
  then the conflict is confined to the one `scripts/` surface line.
- Given a shallow clone, when `ci-check.sh` runs, then it completes
  without asking for full history.
- Given a manual carrying only a legacy `manual-base` sha, when the
  readers run, then they report a clean migrate message and one update
  run rewrites it to `manual-surfaces` with the old comments removed.

## Decisions

- D1: Promote the existing per-path content hash to the sole mechanism
  rather than inventing a new one. TICKET-0002 already proved content
  hashes survive any history rewrite; the only change is dropping the sha
  that sat beside them and made merges conflict.
- D2: Recompute every path's hash on each stamp rather than tracking
  which changed. Unchanged paths reproduce their prior bytes, so a 3-way
  merge keeps the side that moved; the implementation stays simple and
  the merge stays clean.
- D3: Relax merge-commit-only rather than keep it as style. With nothing
  left to orphan, the rule protected nothing, and any-order parallel
  merges are the whole point. The GitHub ruleset toggle is an owner
  action recorded in `docs/WORKFLOW.md` Part III; the plugin cannot
  change server settings.

## Shipped

v0.6.0, 2026-08-12. All six requirements. Supersedes the base-sha half of
TICKET-0002; the content-fingerprint half it built lives on as the whole
mechanism.
