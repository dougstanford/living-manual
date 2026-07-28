# Manual maintenance (per release)

The update flow in skills/manual/SKILL.md is the procedure. This is the
checklist form, for review before reporting done.

1. `stale.sh` output consumed: every listed commit's user-facing effect
   is either reflected in a section or explicitly irrelevant.
2. Sections revised where behavior changed. No planned work described
   as shipped.
3. One "What's new" release block appended, newest first, dated,
   user-facing language, no internal jargon.
4. Previews synced: shipped items removed (content folded into sections
   and "What's new"), newly planned items added with icons placed where
   they apply.
5. Glossary synced: new concepts entered with defining context; renamed
   terms renamed in both GLOSSARY and DEFINED_IN.
6. Tickets index rebuilt (`python3 $LM/scripts/tickets-index.py
   <tickets_dir> <manual_path>`); tickets shipped by this release set
   to `status: shipped` and noted in "What's new" when user visible.
   Never pass `--no-tracker` here. The queue in a released manual is
   the one readers file notes against, and it should be true as of the
   release, not as of whenever the tracker was last consulted. The flag
   exists for offline work, not for a release.
7. `asof` and `base` stamped via sync-index.py.
8. `python3 $LM/scripts/verify.py <manual_path>` prints OK. Browser
   check when machinery or slots changed: headings clickable, one
   glossary alert max per concept and none after its definition,
   previews open, note payload copies.
9. Prose passes reference/writing-style.md. Em-dash count in new prose:
   zero.
10. If a static copy goes out with this release, regenerate it:
    `python3 $LM/scripts/export.py <manual_path>`. Never edit an export;
    it is a build artifact, and the maintained manual is the only
    document anyone keeps current. Regenerate after step 7, so the copy
    carries the release's stamps rather than the previous one's.

## Enforcement principle

When a check finds something wrong at push time, it either blocks the
push or warns and lets it through. One rule decides which, and every
guard the plugin installs follows it:

**Block when the guard itself is disabled and the tool can prove it
locally. Warn when the output is merely imperfect, or when proving it
requires an external service.**

Two halves, both load-bearing:

- *The guard itself is disabled.* A broken base marker means every later
  staleness check returns a meaningless answer, for every clone, until
  someone re-stamps. The mechanism is down, not the content. Content
  that is merely out of date is what the manual already tolerates
  between updates, and it self-corrects on the next run.
- *Provable locally.* A check that must reach a third party can fail for
  reasons the pusher did not cause and cannot fix. Blocking on it trades
  a real outage for a theoretical correctness gain, and it teaches
  people to reach for `--no-verify`, which costs more than the check was
  worth.

Do not decide by who caused the problem. The tool cannot tell: a marker
is as often orphaned by someone else's squash merge as by your own
rebase, and a stale queue is as often your own doing as a colleague's.
Blame is unmeasurable, so it makes a poor rule.

Applied: an orphaned or re-stamp-only base marker blocks
(TICKET-0002 D2). Queue drift against the tracker warns
(TICKET-0003 D1). Both follow from the one rule above.

Warning well is the other half of this. A warning nobody can act on is
noise, and noise is what teaches people to stop reading. So the drift
warning names the issues that drifted and the command that fixes them,
and it stays silent when the tracker could not be reached at all —
an outage is not drift, and saying so every push would train the
warning out of usefulness.
