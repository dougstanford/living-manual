---
id: TICKET-0004
title: Type mapping bends onto ill-fitting labels instead of creating honest ones
type: idea
target: current
status: needs-answers
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
  semantic fit for a note type, proposes creating one named for that
  type and marks it "would be created". Reusing an existing label stays
  available as an alternative the user can pick.
- FR-2: Setup never silently accepts a poor fit. When it proposes
  reusing a label whose name differs from the note type, it says so in
  the proposal, so the user is choosing the compromise rather than
  inheriting it.
- FR-3: A label creation proposed under FR-1 happens only on the user's
  explicit confirmation, at setup time, never as a side effect of
  filing the first issue.
- FR-4: `github.labels` accepts either a string or an array of strings
  per type. An array applies every label in it to issues of that type.
- FR-5: Jira gains an equivalent per-type label set, applied alongside
  the type's `issue_types` mapping and merged with the global `labels`
  list (see Q2 for the key name).
- FR-6: `create` applies, for a given note type: the type's label or
  label set, the global extras, and any configured routing. Order and
  duplicates do not matter; the resulting issue carries each label once.
- FR-7: A config written before this change keeps working unaltered. A
  single string per type behaves exactly as it does today.
- FR-8: The existing rule for taxonomy missing at the tracker extends to
  label sets: a label in a set that no longer exists is reported at sync
  time and skipped, the issue is still filed with the rest, and nothing
  is recreated.

## Acceptance criteria

- Given a project whose labels contain no fit for `feedback`, when setup
  runs the propose step, then it offers to create a `feedback` label,
  marked as would-be-created, alongside the option of reusing an
  existing label.
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
- Given a label set naming a label deleted at the tracker since setup,
  when a note is filed, then the issue is created with the remaining
  labels, the missing one is named in the report, and it is not
  recreated.
- Given this repo after the change, when a feedback note is filed, then
  the resulting issue carries a label meaning feedback rather than
  `question`.

## Open questions

- Q1 (blocks FR-1): When nothing fits, is creating a label the default
  proposal, or one option shown level with reuse? Default: creating is
  the default proposal, with reuse offered as the alternative, because
  the bend this ticket fixes came from reuse being the path of least
  resistance. If a project forbids new labels, reuse is one keystroke
  away.
- Q2 (blocks FR-5): What is the Jira key for per-type labels, and how
  does it combine with the existing global `labels` list? Default: a
  `type_labels` map of type to list, merged with `labels`, so the global
  list keeps its meaning and the per-type list adds to it. If a project
  wants per-type to replace rather than add, that is a second key and
  not this ticket.
- Q3 (scope): Should this repo's own `feedback: question` mapping be
  corrected as part of this work? Default: yes, by creating a `feedback`
  label here and updating `.living-manual.json`, since the dogfood case
  is the clearest test of FR-1 and the mislabeling is live today.

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
