---
id: TICKET-0002
title: Base marker survives history rewrites by stamping content fingerprints alongside the sha
type: idea
target: current
status: needs-answers
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
  the stamped commit).
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
- FR-6: The pre-push hook distinguishes the FR-3 case (allow the push or
  auto-message "re-stamp only") from the FR-4 case (block).

## Acceptance criteria

- Given a manual stamped with sha and fingerprints, when history is
  rewritten without changing user-facing content, then stale.sh reports
  the re-stamp-only state and the update flow needs only a sync-index.py
  call.
- Given the same manual, when history is rewritten and a user-facing
  path's content changed, then stale.sh exits nonzero naming that path.
- Given a manual carrying only a sha, when any script runs, then output
  is identical to today's.
- Given a resolvable base sha, when stale.sh runs, then fingerprints are
  not consulted.

## Open questions

- Q1 (blocks FR-1): One combined hash or one per path? Default: per
  path, so FR-4 can name where the change is. If the marker comment gets
  unwieldy for repos with many entries, fall back to one combined hash
  and lose the naming.
- Q2 (blocks FR-6): In the re-stamp-only state, should the hook block
  the push? Default: block with a message that the fix is a re-stamp,
  since letting it through publishes a manual whose marker is broken for
  every future clone. If that proves too noisy, downgrade to a warning.
- Q3 (blocks FR-1): `user_facing_paths` entries are path prefixes today
  (directories). Tree hashes require each entry to resolve as a tracked
  path. Default: resolve each entry with `git rev-parse HEAD:<path>` and
  skip, with a warning, entries that do not resolve (a glob or an
  as-yet-empty directory).

## References

- `scripts/sync-index.py:77,79` (single-sha stamping, two locations)
- `scripts/stale.sh:31` (BAD-BASE path)
- `scripts/verify.py` (orphaned-marker finding, shipped in PR #1)
- `scripts/install-hook.sh:57` (hook's BAD-BASE block)
- Manual section: The staleness guard (#guard)
- Related: TICKET-0001 / issue #2 (CI detection of the same failure)
