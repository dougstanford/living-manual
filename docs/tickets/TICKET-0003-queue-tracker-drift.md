---
id: TICKET-0003
title: The queue index goes stale against the tracker with no signal
type: idea
target: current
status: needs-answers
section: Notes become tickets › The queue check (#queue-check)
created: 2026-07-26
issue: dougstanford/living-manual#4
---

## Summary

The manual's queue is a snapshot. `tickets-index.py` folds open tracker
issues into the TICKETS block, but the block is static JSON baked into
the HTML, and the only things that rebuild it are a ticket-skill run and
a manual update run. Neither is triggered by the tracker changing. An
issue closed after the last rebuild keeps appearing as queued; an issue
filed since does not appear at all. Nothing detects the drift and nothing
tells the reader how old the queue is.

This is the reconciliation feature's own blind spot: v0.2.5 closed the
gap between the queue and the tracker at write time, and left it open
over time.

## Origin

```
Free-form report (raised in session, 2026-07-26):

The manual's TICKETS queue block is a point-in-time snapshot of tracker
reconciliation. tickets-index.py folds open tracker issues into the
block, but nothing forces a rerun when tracker state changes (issues
opened, closed, retitled). stale.sh only watches user_facing_paths and
knows nothing about tracker state, so the published manual can show
closed issues as queued or miss newly filed ones.

Section: Notes become tickets > The queue check (#queue-check).
```

Corrected during grounding: the report says "nothing forces a rerun".
Two things do, just never in response to the tracker. See below.

## Current behavior

- `scripts/tickets-index.py` builds the TICKETS block from the ticket
  files, then `from_tracker()` folds in open tracker issues no file
  references, and writes the result into the manual through
  `sync-index.replace_block`.
- The block is static JSON inside `docs/USER_MANUAL.html`. The manual is
  self-contained by design and makes no network call when opened, so the
  queue a reader sees is whatever was written at the last rebuild.
- Rebuilds happen on exactly two triggers, both hand-initiated and both
  keyed to repo activity, not tracker activity:
  - `skills/ticket/SKILL.md` step 7, after a ticket write or status
    change.
  - `reference/maintenance.md` step 6, during a manual update run.
- `scripts/stale.sh` derives staleness from git commits touching
  `user_facing_paths`. It never consults the tracker, so tracker drift
  produces no staleness signal and the pre-push guard does not fire on
  it.
- Net effect between rebuilds: the queue can list issues that have since
  closed, omit issues filed since, and show titles or summaries that
  have been edited at the tracker.

## User stories

- As a reader filing a note, I want the queue to reflect the tracker as
  it is now, so I do not file an addition to an issue that shipped last
  week or a duplicate of one filed yesterday.
- As a reader deciding whether to trust the queue, I want to see how
  recently it was reconciled, so a stale queue misleads me less than a
  queue whose age is visible.
- As a maintainer, I want drift between the published queue and the
  tracker to announce itself, so keeping the manual honest is not
  something I have to remember to do.

## Functional requirements

- FR-1: `tickets-index.py --check` fetches tracker state and compares it
  against the TICKETS block already in the manual, without writing.
  Exits zero when they agree, nonzero when they differ, listing each
  difference as added, removed, or changed with the issue ref.
- FR-2: `tickets-index.py` records the reconciliation moment in the
  manual when it writes: the timestamp, and the provider it reached (or
  that it reached none).
- FR-3: The note modal's queue section shows that reconciliation
  timestamp, so a reader sees the queue's age without leaving the
  modal.
- FR-4: The pre-push guard runs the FR-1 check and surfaces drift, with
  the fix named in its message (see Q1 for whether it blocks).
- FR-5: The manual update flow reconciles against the tracker
  unconditionally, never with `--no-tracker`, so a released manual's
  queue is current as of its release.
- FR-6: When the tracker is unreachable, FR-1 and FR-4 report that they
  could not check and exit zero. An unreachable tracker never blocks a
  push and never counts as drift.

## Acceptance criteria

- Given a manual whose TICKETS block matches open tracker issues, when
  `tickets-index.py --check` runs, then it exits zero and writes nothing
  to the manual.
- Given an issue closed at the tracker since the last rebuild, when
  `--check` runs, then it exits nonzero and names that issue as removed.
- Given an issue filed since the last rebuild, when `--check` runs, then
  it exits nonzero and names that issue as added.
- Given a rebuild against a reachable tracker, when the manual is
  written, then it carries the reconciliation timestamp and provider,
  and the note modal displays that timestamp.
- Given a rebuild attempted with no reachable tracker, when the manual is
  written, then it records that no tracker was reached, and a subsequent
  `--check` exits zero rather than reporting drift.
- Given drift and a push, when the pre-push guard runs, then its output
  names the drifted issues and the command that fixes them.
- Given a manual update run, when it completes, then the queue reflects
  tracker state as of that run.

## Open questions

- Q1 (blocks FR-4): Should tracker drift block a push, the way a stale
  manual does? Default: no, warn only. A stale manual is caused by the
  pusher's own commits and is theirs to fix; tracker drift is caused by
  anyone touching the tracker and can appear between a clone and a push,
  so blocking would punish the wrong person. If drift proves to be
  routinely ignored, promote it to a block.
- Q2 (blocks FR-1, FR-4): Should the check run on every push, adding a
  network call to the hook? Default: yes, with the short timeout
  `tickets-index.py` already uses and a silent skip when the tracker is
  unreachable, since a push already tolerates that latency. If it proves
  slow, gate it behind a config flag.
- Q3 (blocks FR-3): Where does the timestamp appear? Default: in the
  queue section of the note modal only, next to the queue label, since
  that is where the reader decides whether to trust the list. Putting it
  in the hero would imply the whole manual was refreshed, which it was
  not.
- Q4 (scope): Issue #2 proposes a CI check running `verify.py` and
  `stale.sh`. Should the FR-1 check join that workflow instead of, or in
  addition to, the pre-push hook? Default: in addition. CI catches drift
  on the server where merges happen; the hook catches it before a push.
  If #2 lands first, this ticket adds one step to its workflow.

## References

- `scripts/tickets-index.py` (`from_tracker`, `main`)
- `scripts/stale.sh` (staleness from `user_facing_paths` only)
- `scripts/install-hook.sh` (pre-push guard)
- `reference/trackers.md` (the `list` operation)
- `reference/maintenance.md` step 6 (index rebuilt during an update run)
- `skills/ticket/SKILL.md` step 7 (index rebuilt after a ticket write)
- Manual section: Notes become tickets › The queue check (#queue-check)
- Related: issue #2 (CI check), which shares the enforcement surface
