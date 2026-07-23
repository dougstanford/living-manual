---
name: ticket
description: Turn a note from the living manual (idea, feedback, or bug in a <submission> block, or a free-form report) into an actionable developer ticket with user stories, functional requirements, and acceptance criteria, plus open questions when completeness can't be verified. Syncs the manual's queue index and, when a tracker is configured, creates or updates the matching issue (Jira via the Atlassian MCP, or GitHub Issues via the gh CLI).
---

# Note → ticket

Input: a `<submission>` block pasted from the manual's "Make a note"
modal (source, section, target, type, summary, details, and optionally
relates-to / roadmap fields), or a free-form report. One ticket per
submission unless it clearly contains independent requests.

Config: `.living-manual.json` at repo root supplies `tickets_dir`,
`manual_path`, and `tracker`. Prose follows the plugin's
`reference/writing-style.md`. `$LM` below is the plugin root; this
file lives at `$LM/skills/ticket/SKILL.md`.

## Targets

- `target: current behavior` → a ticket against the shipped app.
- `target: roadmapped work` → a plan-revision ticket. Ground in the
  named roadmap source and planned-state text, write stories,
  requirements, and criteria as deltas to the plan, and surface any
  conflict with the plan's intent as an open question. Never write it
  as a change to today's implementation.

Enforce the routing for free-form reports too: a complaint about
behavior that a planned item already replaces becomes a plan-revision
ticket against that item, stated in the summary.

## Procedure

1. Ground first. Read the named manual section, the code behind it,
   and the project's planning docs. Every claim about current behavior
   must be verifiable in code or docs.
2. Classify honestly. Designed-but-frustrating behavior is feedback
   naming the governing decision, not a bug. Reclassify a mislabeled
   submission and say so in the ticket.
3. Check for collisions: existing tickets in `tickets_dir`, planned
   items, roadmap docs. Duplicate of a queued ticket → treat as an
   addition (below) and tell the user. Covered by planned work → scope
   the ticket to the delta only.
4. Number it: `sh $LM/scripts/next-ticket.sh <tickets_dir>`.
5. Write `<tickets_dir>/TICKET-NNNN-<slug>.md`:

   ```markdown
   ---
   id: TICKET-NNNN
   title: <one line>
   type: idea | feedback | bug
   target: current | roadmap:<item-id>
   status: ready | needs-answers   (later: shipped | declined)
   section: <manual section + anchor>
   created: <YYYY-MM-DD>
   issue: <tracker ref, when synced: ABC-123 or owner/name#42>
   ---
   ## Summary
   ## Origin            (submission verbatim, fenced)
   ## Current behavior  (or "Planned behavior" for roadmap tickets; with file refs)
   ## User stories      (As a / I want / so that; every FR traces to one)
   ## Functional requirements  (FR-1...; each testable and unambiguous)
   ## Acceptance criteria      (Given/When/Then; together they cover every FR)
   ## Open questions    (required when status is needs-answers)
   ## References
   ```

6. The completeness gate. `ready` only when every FR is unambiguous
   and testable, criteria cover every FR, and nothing rests on a guess.
   Otherwise `needs-answers`, and Open Questions must be sufficient:
   each question names the FR it blocks, proposes a default, and says
   what changes if the default is wrong. Answering all of them must
   flip the ticket to ready. Do not pad a thin submission into false
   precision; ask.
7. Sync the manual's queue index in one command:
   `python3 $LM/scripts/tickets-index.py <tickets_dir> <manual_path>`.
   It rebuilds the TICKETS block from the ticket files' frontmatter and
   Summary sections, so the index can't drift. Run it after every write
   or status change. A resolved ticket gets `status: shipped` or
   `status: declined`; the file stays as the record and the index drops
   it automatically.
8. Tracker sync, when `tracker.provider` is not `none` (a legacy
   top-level `jira` block with `enabled: true` reads as provider
   `jira`):
   - Read `$LM/reference/trackers.md` for the provider's operations.
   - Run its detect step first. Unavailable: note it, skip, local
     ticket stands.
   - Create the issue per the provider section: title from the ticket
     title, body from the ticket (stories, FRs, criteria, open
     questions) in the format the provider accepts, type or label
     mapping and any routing (component, milestone, extra labels) from
     config. Config taxonomy missing at the tracker (a label deleted
     since setup, say): create nothing; sync without it and report the
     mismatch.
   - Write the returned ref into the ticket frontmatter (`issue:`) and
     mention it in your report.
   - Additions and status changes update the same issue (comment with
     the new submission, edit the description) rather than creating a
     twin.
   - A tracker write failure never blocks the local ticket. Report the
     failure and the retry path.
9. Report: ticket path, status, tracker ref if any, and open questions
   inline so the user can answer immediately. Answers update the same
   ticket in place: fold into FRs and criteria, clear resolved
   questions, flip status, re-sync index and Jira.

## Additions (`relates-to: TICKET-NNNN`)

The user reviewed the queue and identified their note as an addition.
Do not create a new ticket. Update the named one in place: append the
submission to Origin, fold the new information through every section,
re-verify completeness, re-sync the index, and update the tracker
issue if linked. A note that contradicts the ticket it claims to extend gets
surfaced for a decision, not silently forked.

## Rules

- User-facing vocabulary in stories and criteria; the manual's glossary
  is the reference for terms.
- This skill writes tickets. It never changes app code.
- Never modify tracker issues the plugin didn't create, except to
  comment.
