---
id: TICKET-0005
title: Export a static copy of the manual for distribution outside the team
type: idea
target: current
status: ready
section: One file that stays true (#the-manual)
created: 2026-07-27
issue: dougstanford/living-manual#10
---

## Summary

The manual is built for the people who maintain the code: every heading
files a note, the modal shows the internal queue, and the payload is
addressed to a Claude Code session. Shipping that same file to customers
or to a wider audience hands them affordances they cannot use and
information meant for the team. An export step should produce a static
copy of the same document with the note-filing path removed, so a
release can be distributed without the machinery that only makes sense
inside the repo.

The removal is not only about hiding buttons. The queue data travels
inside the file. `TICKETS` carries every queued ticket's id, title,
status, and summary, and `QUEUE_SYNC` names the tracker the project
reconciles against. A distributed manual that still contains those
blocks publishes the team's backlog and the location of its issue
tracker, whether or not anything on screen displays them.

## Origin

```
Free-form report (raised in session, 2026-07-27):

I want one last feature to add tonight before release tomorrow - I want
the user to be able to "export" their manual:

1. The user must be able to remove the interactive components of the
system so that it can be a static, distributed production version for
release that will not generate tickets or allow users to update the
manual themselves
```

Recorded verbatim. The submission says "remove the interactive
components" and then names the property that matters: no ticket
generation, no reader-side updating. Those are not the same set, because
some interactive parts generate nothing. Which parts survive was the
decision this ticket rested on; it is settled in D1.

## Current behavior

State as of 2026-07-27 (v0.2.9).

- `templates/manual-shell.html` carries all machinery inline; the built
  manual is that shell with slots filled. There is no second output
  form and no export path anywhere in `scripts/`.
- The note-filing path is: a click handler on `main h2, main h3`
  (`manual-shell.html:698`), the `#rev-overlay` modal
  (`manual-shell.html:255-285`), the type chips, summary and details
  inputs, the queue rendered by `renderQueue`, and a clipboard write of
  the payload (`manual-shell.html:631`).
- The affordance advertising it is CSS, not markup: `main h2::after`
  sets `content: "✎ make a note"` and reveals it on hover
  (`manual-shell.html:112-119`). Removing the handler without removing
  this rule would leave every heading still offering a note and doing
  nothing when clicked.
- Roadmap previews are a second overlay (`#prev-overlay`) opened by
  `.preview-btn` icons placed inline in prose. Read-only, except that
  `#prev-revise` hands off to the note modal, which is a ticket path.
- Glossary tooltips annotate prose on hover from the `GLOSSARY` and
  `DEFINED_IN` blocks. They generate nothing.
- Five data blocks live in the script: `QUEUESYNC`, `TICKETS`,
  `PREVIEWS`, `GLOSSARY`, `DEFINED`. `TICKETS` holds ticket ids,
  titles, statuses, and summaries; `QUEUESYNC` holds the reconciliation
  timestamp and the provider name.
- `verify.py` requires all of the data markers, checks every
  `data-preview` names a `PREVIEWS` entry, and requires a `<script>`
  block. An export that strips machinery would fail it as written.
- The base marker and content fingerprints sit near the top of the file
  and are read by `stale.sh`, `verify.py`, and the pre-push hook.

## User stories

- As a maintainer shipping a release, I want to hand out a copy of the
  manual that has no note-filing path in it, so readers outside the team
  are not offered an affordance that only works inside the repo.
- As a maintainer, I want the distributed copy to carry none of the
  ticket queue, so publishing the manual does not publish the backlog
  or name the issue tracker.
- As a maintainer, I want the distributed copy to carry none of the
  roadmap previews, so work that has not shipped is not published to
  people outside the team.
- As a reader of a distributed manual, I want no controls that appear
  clickable and do nothing, so I am not left wondering what I did wrong.
- As a reader of a distributed manual, I want the glossary to keep
  working, so the document is no harder to read than the one the team
  has.
- As a maintainer, I want the export regenerated from the maintained
  manual rather than hand-edited, so the two cannot drift and the
  distributed copy is never the one I have to keep current.

## Functional requirements

- FR-1: A script produces a static copy from the maintained manual. The
  maintained manual is not modified by the export.
- FR-2: The exported copy contains no note-filing path: no heading click
  handler, no note modal markup, no type chips, no summary or details
  inputs, no clipboard write, and no queue rendering.
- FR-3: The affordances advertising that path are removed with it,
  including the `main h2::after` / `main h3::after` rule and the pointer
  cursor on headings. No control in the export appears actionable and
  does nothing.
- FR-4: The exported copy carries neither the `TICKETS` block nor the
  `QUEUESYNC` block, in any form, so no ticket id, title, status,
  summary, tracker provider, or reconciliation timestamp travels with a
  distributed file.
- FR-5: Roadmap previews are removed entirely: the `PREVIEWS` block, the
  `#prev-overlay` markup, its CSS, its script, and every `.preview-btn`
  element and `data-preview` attribute placed inline in prose. No
  orphaned icon remains in the text.
- FR-6: The glossary survives and is fully functional: `GLOSSARY` and
  `DEFINED_IN` are retained, `.term` spans still carry their tooltips,
  and the one-alert-per-concept rule behaves as it does in the
  maintained manual.
- FR-7: The exported copy is self-contained and opens with no console
  errors and no unresolved references to removed handlers, elements, or
  data.
- FR-8: The export is written beside the maintained manual, at its path
  with the `.html` extension replaced by `_prod.html`
  (`docs/USER_MANUAL.html` produces `docs/USER_MANUAL_prod.html`). A
  destination may be supplied explicitly; the maintained manual's own
  path is never a valid destination and is refused.
- FR-9: The export is a build artifact, not a stored file: the export
  step ensures the destination is covered by `.gitignore`, and the
  documented release routine regenerates it rather than committing it.
- FR-10: The exported copy carries a single `manual-export` comment near
  the top naming the plugin version and the commit it was built from. It
  carries neither the `manual-base` marker nor the fingerprint block.
- FR-11: That same comment is what identifies the file as an export to
  both a reader and to `verify.py`, so the file declares its own kind
  rather than relying on a caller remembering a flag.
- FR-12: The export states in the document that it is a static copy and
  that notes cannot be filed from it. It offers no contact or feedback
  route.
- FR-13: Regenerating the export from an unchanged manual produces an
  identical file.
- FR-14: The staleness guard, the CI check, and the queue drift check
  continue to act on the maintained manual only. The export is never the
  file they read, and its presence changes none of their output.
- FR-15: `verify.py`, on a file carrying the `manual-export` comment,
  does not report the absence of `TICKETS`, `QUEUESYNC`, `PREVIEWS`, the
  base marker, or the fingerprints as findings, and does not require a
  `data-preview` to resolve. It still checks `GLOSSARY`, `DEFINED_IN`,
  duplicate element ids, and that the remaining script parses.

## Acceptance criteria

- Given a maintained manual, when the export runs, then a static copy is
  written and the maintained manual is byte-identical to before.
- Given an exported copy opened in a browser, when a heading is hovered
  and clicked, then no note affordance appears and nothing happens.
- Given an exported copy, when its source is searched, then no ticket
  id, title, status, or summary from the queue appears anywhere in the
  file, and neither does the tracker provider name.
- Given a maintained manual containing roadmap previews, when the export
  runs, then the exported copy contains no `PREVIEWS` data, no preview
  overlay, and no preview icon anywhere in its prose.
- Given an exported copy, when a term with a glossary entry is hovered,
  then its tooltip appears, once, and only before the concept's
  defining passage.
- Given an exported copy opened in a browser, when the console is
  inspected after exercising every remaining control, then it is empty.
- Given `docs/USER_MANUAL.html` as the source, when the export runs with
  no destination given, then it writes `docs/USER_MANUAL_prod.html`.
- Given the maintained manual's own path supplied as the destination,
  when the export runs, then it refuses and writes nothing.
- Given a repo whose `.gitignore` does not cover the export, when the
  export runs, then the destination is thereafter ignored by git.
- Given an exported copy, when a reader opens it, then it states that it
  is a static copy and that notes cannot be filed from it, and offers no
  contact route.
- Given an exported copy, when its head is read, then it carries one
  `manual-export` comment naming the version and source commit, and no
  `manual-base` marker or fingerprint block.
- Given an unchanged manual, when the export is run twice, then the two
  outputs are identical.
- Given a repo containing an exported copy, when `stale.sh`,
  `ci-check.sh`, and the drift check run, then their output is identical
  to a repo without one.
- Given an exported copy, when `verify.py` runs on it, then it prints OK
  and reports none of the deliberately removed blocks as findings.
- Given an exported copy whose remaining script has been corrupted or
  whose glossary block has been damaged, when `verify.py` runs on it,
  then it reports that.
- Given the maintained manual, when `verify.py` runs on it, then its
  behavior is exactly as it is today.

## Decisions

Settled 2026-07-27, all four as proposed, with Q2's destination named
`_prod.html` rather than the proposed `.static.html`.

- D1 (FR-5, FR-6): The glossary survives; roadmap previews do not. The
  glossary generates nothing and is purely a reading aid, so removing it
  would make the distributed copy worse to read for no gain. Previews
  are different in kind: they describe work that has not shipped, which
  is the last thing wanted in a copy handed outside the team, and
  `#prev-revise` is a route into the note modal that FR-2 removes
  anyway. "Interactive" was never the real criterion; publishing
  unreleased plans and generating tickets are.
- D2 (FR-8, FR-9): The export lives beside the manual as
  `<name>_prod.html`, gitignored, regenerated at release. Treating it as
  a build artifact keeps one source of truth and makes FR-14 trivial:
  the guard reads `manual_path` and the export is never at that path.
  Committing it would create a second staleness problem needing a second
  guard, which is the cost this design avoids.
- D3 (FR-12): The export says it is static and offers no contact route.
  This leaves a real gap, and it is a knowing one: a reader with a
  correction has nowhere to put it. Filling it properly means a config
  key for an address or URL and a decision about what the manual
  promises when someone writes to it. That is a separate feature, and
  guessing a route here would ship a promise nobody agreed to.
- D4 (FR-10, FR-11): The export carries a provenance comment and not the
  guard's marker. Leaving `manual-base` and the fingerprints in a file
  the guard does not maintain would invite a later reader to trust a
  staleness answer nobody is keeping true. The provenance comment then
  does double duty as the export's identifier: FR-12 needs the file to
  declare itself to a reader, and FR-15 needs `verify.py` to know which
  ruleset applies, and both are the same fact. A file that declares its
  own kind beats a flag a caller has to remember, because the file
  outlives the command that made it.

## Notes on sequencing

FR-15 is work on a shipped script, not just a new one. `verify.py`
currently requires every data marker and a `<script>` block, so an
export fails it as written. That is the piece most likely to be
underestimated if this is built quickly.

FR-7 is the other one. A stripped handler that leaves a dangling
reference produces a silent console error in a file that has already
been distributed, and no existing check would catch it. The browser
pass with the console open is not optional for this ticket.

## References

- `templates/manual-shell.html:112-119` (the note affordance and the
  heading pointer cursor, both in CSS)
- `templates/manual-shell.html:255-285` (`#rev-overlay`, the note modal)
- `templates/manual-shell.html:287` (`#prev-overlay`, roadmap previews)
- `templates/manual-shell.html:318-333` (the five data blocks)
- `templates/manual-shell.html:631` (clipboard write of the payload)
- `templates/manual-shell.html:698` (heading click handler)
- `scripts/verify.py` (requires the data markers and a script block)
- `scripts/scaffold.py` (the only script that currently writes a manual)
- Manual section: One file that stays true (#the-manual)
