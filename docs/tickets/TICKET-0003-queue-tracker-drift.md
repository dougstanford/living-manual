---
id: TICKET-0003
title: The queue index goes stale against the tracker with no signal
type: idea
target: current
status: ready
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
  timestamp beside the queue label, so a reader sees the queue's age at
  the moment of deciding whether to trust it. It appears nowhere else in
  the manual; the hero's "as of" date continues to describe the code the
  manual reflects, not the queue.
- FR-4: The pre-push guard runs the FR-1 check on every push. Drift
  produces a warning naming the drifted issues and the command that
  fixes them, and the push proceeds. A nonzero check never fails a push.
- FR-5: The manual update flow reconciles against the tracker
  unconditionally, never with `--no-tracker`, so a released manual's
  queue is current as of its release.
- FR-6: When the tracker is unreachable, FR-1 reports that it could not
  check and exits zero, and FR-4's hook step passes silently. An
  unreachable tracker never counts as drift, never warns, and never
  blocks a push.
- FR-7: The check is one command with a documented exit contract (zero
  clean or unreachable, nonzero drift), callable unchanged by the
  pre-push guard and by a CI workflow. The hook's network call uses the
  same fetch timeout a normal reconciliation run uses, so a push is never
  delayed beyond it.

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
  and the note modal shows that timestamp beside the queue label.
- Given a manual carrying a reconciliation timestamp, when a reader opens
  the manual, then the hero's "as of" date is unchanged by
  reconciliation and no timestamp appears outside the modal.
- Given a rebuild attempted with no reachable tracker, when the manual is
  written, then it records that no tracker was reached, and a subsequent
  `--check` exits zero rather than reporting drift.
- Given drift and a push, when the pre-push guard runs, then it prints a
  warning naming the drifted issues and the fix command, and the push
  completes successfully.
- Given an unreachable tracker and a push, when the pre-push guard runs,
  then it emits no drift warning, adds no delay beyond the fetch
  timeout, and the push completes successfully.
- Given the same check invoked from a CI workflow rather than the hook,
  when it runs, then its exit code and output are identical to the hook's
  invocation for the same repository state.
- Given a manual update run, when it completes, then the queue reflects
  tracker state as of that run.

## Decisions

Settled 2026-07-26, all four as proposed. Recorded because each one
constrains an FR, and a later reader should find the reasoning rather
than re-litigate it.

- D1 (FR-4): Tracker drift warns, it does not block. This follows the
  enforcement principle in `reference/maintenance.md`: a stale queue
  leaves the guard working and only makes one section of the manual
  imperfect, which self-corrects on the next rebuild, and proving the
  drift needs a call to the tracker rather than a local computation.
  Neither half of the rule is met, so it warns. TICKET-0002's orphaned
  marker blocks under the same rule, because that failure disables the
  guard and is locally provable. An earlier draft justified the split by
  who caused the problem; that was wrong, since drift is as often the
  pusher's own doing as a colleague's. Revisit if drift warnings turn
  out to be routinely ignored.
- D2 (FR-1, FR-4, FR-7): The check runs on every push, accepting one
  network call in the hook, bounded by the fetch timeout a normal
  reconciliation already uses. Revisit with a config flag if the added
  latency is felt.
- D3 (FR-3): The timestamp appears beside the queue label in the note
  modal and nowhere else. The hero's date describes the code the manual
  reflects; reusing it for queue freshness would claim the whole manual
  had been refreshed when only the queue was.
- D4 (FR-7, scope): The check runs in both the pre-push guard and, once
  issue #2's workflow exists, in CI. The hook catches drift before a
  push; CI catches it on the server where merges land. FR-7 keeps the
  check a single command so #2 adds one step rather than a second
  implementation.

## References

- `scripts/tickets-index.py` (`from_tracker`, `main`)
- `scripts/stale.sh` (staleness from `user_facing_paths` only)
- `scripts/install-hook.sh` (pre-push guard)
- `reference/trackers.md` (the `list` operation)
- `reference/maintenance.md` step 6 (index rebuilt during an update run)
- `skills/ticket/SKILL.md` step 7 (index rebuilt after a ticket write)
- Manual section: Notes become tickets › The queue check (#queue-check)
- Related: issue #2 (CI check), which shares the enforcement surface
