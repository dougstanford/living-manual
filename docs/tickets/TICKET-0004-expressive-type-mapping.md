---
id: TICKET-0004
title: Type mapping bends onto ill-fitting labels instead of creating honest ones
type: idea
target: current
status: shipped
section: The ticket skill › The issue tracker (#tracker-sync)
created: 2026-07-26
issue: dougstanford/living-manual#5
---

## Summary

Setup maps each note type onto exactly one existing label or issue type.
When a project has nothing that fits a type, the mapping bends: the type
gets filed under a label that means something else. Two changes remove
the bend. Let setup propose creating a label named for the type when
nothing existing fits, and let a type carry a set of labels rather than
one, so issues can also pick up the routing labels a project expects.

This repo is the live example. Nothing here fits `feedback`, so setup
mapped it to `question`, which on GitHub means someone is asking for
information. Feedback filed from the manual is not a question, so every
feedback note this repo receives will be mislabeled.

## Origin

```
Free-form report (raised in session, 2026-07-26):

Considering whether the manual's note taxonomy should adopt the
tracker's own taxonomy at install time, to avoid the complication of
remapping issues, "to avoid pushing our square peg into each provider's
round hole".

Resolved in discussion: keep idea/feedback/bug as the reader's
vocabulary, because it is a user-facing classification that drives the
modal's per-type elicitation prompts and the ticket skill's
classification rules, and because provider: none must still work.
Improve the mapping's expressiveness instead.
```

Reclassified from the original framing. The submission proposed
replacing the taxonomy; the accepted change keeps the taxonomy and fixes
the mapping. The diagnosis (a real impedance mismatch) stands and is
what this ticket addresses.

## Current behavior

- `reference/trackers.md` config schema maps one type to one value:
  `github.labels` is `{ "bug": "bug", "idea": "enhancement",
  "feedback": "feedback" }`, and `jira.issue_types` is
  `{ "bug": "Bug", "idea": "Story", "feedback": "Task" }`. Both are
  type to single string.
- Optional routing exists but is global, not per type:
  `github.extra_labels` and `jira.labels` apply to every issue, and
  `github.milestone` / `jira.component` route everything the same way.
- The setup discipline's propose step says to map "each ticket type to
  an existing type or label wherever one fits" and to "suggest creating
  something new only when nothing existing fits, and mark it plainly as
  'would be created'". The permission to create is already written down.
  It is not what setup reached for here.
- `create` passes the single mapped label plus the global extras:
  `gh issue create ... ` with the mapped label, `extra_labels`, and
  `--milestone` when configured.
- Result in this repo: `.living-manual.json` carries
  `"feedback": "question"`, and the nine labels available contain no
  honest home for feedback.

## User stories

- As a maintainer running setup, I want a type with no fitting label to
  offer me a new label named for that type, so I am not asked to choose
  between three labels that all mean something else.
- As a maintainer, I want a note type to apply the several labels my
  project expects on that kind of work, so issues the plugin files look
  like issues my team files.
- As someone triaging the tracker, I want a feedback note to carry a
  label that means feedback, so filtering by label returns what it
  claims to.

## Functional requirements

- FR-1: Setup's propose step, when no existing label or issue type is a
  semantic fit for a note type, leads with creating one named for that
  type, marked "would be created". Reuse of an existing label is offered
  as the alternative, not as the leading proposal.
- FR-2: Setup never silently accepts a poor fit. When it proposes
  reusing a label whose name differs from the note type, it says so in
  the proposal, so the user is choosing the compromise rather than
  inheriting it.
- FR-3: A label creation proposed under FR-1 happens only on the user's
  explicit confirmation, at setup time, never as a side effect of
  filing the first issue.
- FR-4: `github.labels` accepts either a string or an array of strings
  per type. An array applies every label in it to issues of that type.
- FR-5: Jira gains `type_labels`, a map of note type to list of labels,
  applied alongside the type's `issue_types` mapping. Its labels merge
  with (do not replace) the global `labels` list, so an issue carries
  both sets.
- FR-6: `create` applies, for a given note type: the type's label or
  label set, the global extras, and any configured routing. Order and
  duplicates do not matter; the resulting issue carries each label once.
- FR-7: A config written before this change keeps working unaltered. A
  single string per type behaves exactly as it does today.
- FR-8: The existing rule for taxonomy missing at the tracker extends to
  label sets: a label in a set that no longer exists is reported at sync
  time and skipped, the issue is still filed with the rest, and nothing
  is recreated.
- FR-9: This repo's own mapping is corrected as part of the work: a
  `feedback` label is created at `dougstanford/living-manual`, and
  `.living-manual.json` maps `feedback` to it instead of `question`.
  This is the FR-1 path walked end to end on a live repo.
  **Landed 2026-07-26, ahead of the rest.** The label exists (amber,
  described "How a shipped feature behaves, and what better would look
  like") and the config points at it. No issue needed relabelling: none
  had been filed as feedback. FR-1 through FR-8 remain to build.

## Acceptance criteria

- Given a project whose labels contain no fit for `feedback`, when setup
  runs the propose step, then creating a `feedback` label is the leading
  proposal, marked as would-be-created, and reuse of an existing label
  is presented as the alternative to it.
- Given the user picks reuse of a differently-named label, when setup
  prints the proposal, then the proposal states the mismatch before the
  user confirms.
- Given a proposed label creation, when the user does not confirm, then
  no label is created at the tracker, then or at first sync.
- Given `"bug": ["bug", "needs-triage"]`, when a bug note is filed, then
  the issue carries both labels plus any global extras.
- Given `"bug": "bug"` in a config written before this change, when a
  bug note is filed, then the issue carries exactly the labels it
  carries today.
- Given a Jira config with `type_labels` for `bug` and a global `labels`
  list, when a bug note is filed, then the issue carries the union of
  both, and its issue type still comes from `issue_types`.
- Given a type label set and a global extras list that name the same
  label, when a note is filed, then the issue carries that label once.
- Given a label set naming a label deleted at the tracker since setup,
  when a note is filed, then the issue is created with the remaining
  labels, the missing one is named in the report, and it is not
  recreated.
- Given this repo after the change, when a feedback note is filed, then
  the resulting issue carries a label meaning feedback rather than
  `question`.

## Decisions

Settled 2026-07-26, all three as proposed. Recorded because each one
constrains an FR, and a later reader should find the reasoning rather
than re-litigate it.

- D1 (FR-1): When nothing fits, creating a label leads and reuse is the
  alternative, rather than the two being offered level. The bend this
  ticket fixes came from reuse being the path of least resistance, so
  levelling the options would preserve the failure. A project that
  forbids new labels is one keystroke from reuse.
- D2 (FR-5): Jira's per-type labels live under `type_labels`, a map of
  type to list, and merge with the global `labels` list rather than
  replacing it. The global list keeps the meaning it already has, and
  per-type adds to it. Replacement semantics, if ever wanted, are a
  second key and a different ticket.
- D3 (FR-9, scope): This repo's `feedback: question` is corrected as
  part of this work rather than separately. It is the clearest test of
  FR-1, it exercises the create path on a live repo, and the
  mislabeling is active until it lands.

## Shipped

v0.2.9, 2026-07-27. FR-1 through FR-8; FR-9 had landed 2026-07-26.

Most of this ticket is discipline, not machinery. FR-1, FR-2, FR-3,
FR-6, and FR-8 govern what setup and the ticket skill do, so they landed
in `reference/trackers.md` and the two skills, with the reasoning
attached rather than the rule alone. The propose step now defines a fit
("the label means what the type means, not the closest of what happens
to exist"), leads with creation when nothing fits, and requires a
proposal that reuses a differently-named label to state what that label
already means. This repo's `feedback` to `question` bend is written into
trackers.md as the worked example of getting it wrong.

FR-4, FR-5, FR-7 are the config schema: `github.labels` takes a string
or a list, `jira.type_labels` maps a type to a list and merges with the
global `labels` rather than replacing it.

One code path actually read the mapping, and it would have broken:
`type_from_labels` matched only values that were strings, so a list
would have silently classified every folded-in issue as `idea` — the
new config shape failing quietly rather than loudly. Any one of a
type's labels now identifies it, which is the right rule anyway: an
issue routed as `bug` + `needs-triage` is still a bug after someone
drops the routing label. First match wins when a label is named under
two types.

Verified: ten mapping cases including old string configs unchanged,
lists matching on any member, mixed string-and-list configs,
case-insensitivity, and empty or null values tolerated. Then end to end
against this repo's live issues with a list mapping configured.

## Out of scope

An optional second axis in the note modal, offering the project's own
labels as a refinement after the type is chosen (area: auth, billing,
docs). It was discussed alongside this change and is a separate feature:
new modal UI, a payload field, and a setup step to choose which labels
form the axis. File it separately if the axis proves wanted.

## References

- `reference/trackers.md` (config schema; setup discipline; create per
  provider; the missing-taxonomy rule)
- `skills/manual/SKILL.md` (setup's tracker step)
- `skills/ticket/SKILL.md` step 8 (tracker sync at create time)
- `.living-manual.json` (this repo's `feedback: question` mapping)
- Manual section: The ticket skill › The issue tracker (#tracker-sync)
