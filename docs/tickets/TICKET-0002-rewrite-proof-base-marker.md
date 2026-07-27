---
id: TICKET-0002
title: Base marker survives history rewrites by stamping content fingerprints alongside the sha
type: idea
target: current
status: ready
section: The staleness guard (#guard)
created: 2026-07-23
issue: dougstanford/living-manual#3
---

## Summary

The base marker is a commit sha frozen inside the manual, so any history
rewrite after stamping (amend, rebase, squash merge) orphans it.
Detection now exists (`BAD-BASE` from stale.sh, a verify.py finding),
but recovery loses information: with the sha gone there is no commit
range, so the update flow cannot list what changed. Stamping a content
fingerprint of the user-facing paths alongside the sha would make
staleness answerable even after a rewrite: identical fingerprint means
the manual is still current and only needs a re-stamp; a differing
fingerprint names which surfaces changed.

Motivating defect: this repo's manual carried base `2a646e9`, orphaned
by a rewrite before the history was ever published; the update flow had
to reconstruct the true base by hand from the clone point. A squash
merge of any PR would recreate the situation on upstream main.

## Origin

Reconstructed 2026-07-26 from tracker issue
`dougstanford/living-manual#3`, filed 2026-07-23 by @manbradcalf.

The issue states this file "lands with PR #1". It did not: the ticket
files were never committed on any branch, so the issue was the only
record until now. The queue check surfaced the gap by showing the issue
as open at the tracker with no ticket file behind it.

Content below is the issue's, with Current behavior added and the
References corrected where PR #1 has since shipped. No requirement was
altered.

## Current behavior

State as of 2026-07-26 (v0.2.5), which differs from when the issue was
written:

- `scripts/sync-index.py` stamps the base on the `base` payload key and
  writes it to two places: the `manual-base:` HTML comment (line 77) and
  the `MANUAL_BASE` script variable (line 79, added in v0.2.3 so a
  note's ticket names the commit the manual reflected). Both carry the
  same single sha. No content fingerprint is recorded anywhere.
- `scripts/stale.sh:31` prints `BAD-BASE <sha>` and exits 1 when the sha
  does not resolve, with the comment that unverifiable means stale
  rather than current. It has no way to distinguish a rewrite that
  changed user-facing content from one that changed none.
- `scripts/verify.py` flags an orphaned marker as a finding. That
  shipped with PR #1, which is merged, so the issue's reference to it as
  pending is out of date. FR-5's sha-resolution half is therefore
  already done; the fingerprint half is not.
- `scripts/install-hook.sh:57` has a `BAD-BASE*` branch that blocks the
  push and prints the bypass. It is a single outcome; there is no
  re-stamp-only state for it to distinguish.
- Net: after a rewrite the operator learns only that the marker is
  broken, never whether anything user-facing actually moved.

## User stories

- As a dev running the update flow after someone squash-merged, I want
  stale.sh to tell me whether the manual is still current and, if not,
  which user-facing paths changed, so I am not reconstructing the base
  from reflogs and clone dates.
- As a maintainer, I want a rewrite that changed nothing user-facing (a
  commit-message reword, a squash of already-stamped work) to resolve to
  "current, re-stamp only" instead of a manual rebuild.

## Functional requirements

- FR-1: `sync-index.py` stamps, alongside the base sha, one git tree
  hash per entry in `user_facing_paths` (the hash of that path's tree at
  the stamped commit). One hash per path, not one combined hash, so FR-4
  can name the surface that moved.
- FR-1a: An entry that does not resolve as a tracked tree path
  (`git rev-parse HEAD:<path>` fails, as with a glob or an empty
  directory) is skipped with a warning. The remaining entries are still
  fingerprinted and the stamp still succeeds.
- FR-2: When the base sha resolves, behavior is unchanged: commit list
  from `git log base..HEAD`.
- FR-3: When the base sha does not resolve and every stamped tree hash
  equals the corresponding hash at HEAD, `stale.sh` reports the manual
  current but needing a re-stamp, distinctly from plain `CURRENT`.
- FR-4: When the base sha does not resolve and any tree hash differs,
  `stale.sh` reports stale and lists the user-facing paths whose hashes
  differ, so the update flow knows where to look without a commit range.
- FR-5: `verify.py` accepts a manual with fingerprints and continues to
  verify sha resolution; a manual stamped before this change (sha only)
  keeps today's behavior everywhere.
- FR-6: The pre-push hook distinguishes the FR-3 case from the FR-4
  case. Both block the push. FR-3's message says the manual's content is
  current and names the re-stamp command as the whole fix; FR-4's
  message names the changed paths and points at the update flow.

## Acceptance criteria

- Given a manual stamped with sha and fingerprints, when history is
  rewritten without changing user-facing content, then stale.sh reports
  the re-stamp-only state and the update flow needs only a sync-index.py
  call.
- Given the same manual, when history is rewritten and a user-facing
  path's content changed, then stale.sh exits nonzero naming that path.
- Given a manual carrying only a sha, when any script runs, then output
  is identical to today's.
- Given a manual carrying fingerprints, when `verify.py` runs, then it
  accepts the marker format without a finding, and still reports an
  unresolvable base sha as one.
- Given a resolvable base sha, when stale.sh runs, then fingerprints are
  not consulted.
- Given a `user_facing_paths` entry that does not resolve as a tracked
  tree path, when the manual is stamped, then that entry is skipped with
  a warning naming it, and the other entries are still fingerprinted.
- Given the re-stamp-only state, when a push is attempted, then the hook
  blocks it and its message names the re-stamp command as the whole fix.

## Decisions

Settled 2026-07-26, all three as proposed.

- D1 (FR-1): One tree hash per `user_facing_paths` entry, not one
  combined hash. Per path is what lets FR-4 name the surface that moved,
  which is the recovery the ticket exists to provide. This repo has four
  entries, so the marker stays small; revisit only if a repo with many
  entries makes the comment unwieldy.
- D2 (FR-6): The re-stamp-only state blocks the push, like the
  fully-stale state, but with a different message. The manual's content
  is correct, yet its marker is broken for every future clone, and the
  fix is a single `sync-index.py` call by the person already pushing.
  This cuts against TICKET-0003's D1, where drift only warns, and the
  distinction is deliberate: there the fix belonged to whoever touched
  the tracker, here it belongs to the pusher and costs one command.
- D3 (FR-1a): An entry that does not resolve as a tracked tree path is
  skipped with a warning rather than failing the stamp. A config naming
  an as-yet-empty directory or a glob keeps working. All four entries in
  this repo resolve today, so this path is for other repos.

## References

- `scripts/sync-index.py:77,79` (single-sha stamping, two locations)
- `scripts/stale.sh:31` (BAD-BASE path)
- `scripts/verify.py` (orphaned-marker finding, shipped in PR #1)
- `scripts/install-hook.sh:57` (hook's BAD-BASE block)
- Manual section: The staleness guard (#guard)
- Related: TICKET-0001 / issue #2 (CI detection of the same failure)
