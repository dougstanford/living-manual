# Tracker gateway

The ticket skill syncs local tickets to at most one external issue
tracker. This file is the contract: the operations the skills rely on,
the setup discipline every provider follows, and one section per
provider mapping both onto concrete mechanisms. Skills reference the
operations; only this file knows provider specifics. Adding a provider
means adding a section here and a sub-block to the config schema. The
skills do not change.

## Config

The `tracker` block in `.living-manual.json`. `provider` is `"jira"`,
`"github"`, or `"none"`; only the selected provider's sub-block is
required. Fields marked optional are recorded only when the user chose
them during setup.

```json
"tracker": {
  "provider": "github",
  "jira": {
    "project_key": "ABC",
    "issue_types": { "bug": "Bug", "idea": "Story", "feedback": "Task" },
    "type_labels": { "bug": ["needs-triage"] },
    "component": "optional: route new issues to one component",
    "labels": ["optional: labels applied to every issue"]
  },
  "github": {
    "repo": "owner/name",
    "labels": { "bug": ["bug", "needs-triage"], "idea": "enhancement",
                "feedback": "feedback" },
    "extra_labels": ["optional: applied to every issue"],
    "milestone": "optional: title of the milestone new issues join"
  }
}
```

`github.labels` maps a note type to either one label or a list of them.
A list applies every label in it, so issues the plugin files can carry
the routing labels a project expects on that kind of work and look like
issues the team files by hand. A plain string behaves exactly as it
always has; configs written before lists existed need no change.

`jira.type_labels` is the same idea for Jira, kept separate from
`issue_types` because Jira's issue type and its labels are different
fields. Its labels **merge** with the global `labels` list rather than
replacing it: the global list keeps the meaning it already has, and
per-type adds to it. A label named in both is applied once.

When a provider was considered and rejected (tools missing, no write
permission, user declined), record `"provider": "none"` with a
`"reason"` in the user's terms, so a later setup run can say what to
fix. A legacy config with a top-level `"jira"` block reads as
`tracker.provider: "jira"` with the same fields.

## Operations

| Operation | Meaning |
|---|---|
| detect | Is the provider usable from this session? |
| inspect | Enumerate the project's existing taxonomy before configuring. |
| create | One new issue from a ticket file. |
| update | Edit the issue the plugin created, in place. |
| comment | Append to an issue without touching its body. |
| list | Open issues, for reconciling the queue against the tracker. |
| ref | The string stored in ticket frontmatter (`issue:`). |

`list` is the only operation a script performs unattended
(`tickets-index.py`, to fold issues with no ticket file into the queue,
and to answer `--check`), so a provider whose access needs a model
session supports it only during one. The rest run inside the ticket
skill.

A provider that cannot answer `list` from a script is not a failure
state: `--check` reports that it could not compare and exits zero. A
tracker nobody can reach is never drift.

## Setup discipline: inspect, propose, commit

Projects accumulate their own labels, milestones, issue types, and
components. Setup adapts to what exists; it never assumes the defaults
above fit.

1. **Inspect.** Enumerate the project's existing taxonomy with the
   provider's inspect commands. Read before write, always.
2. **Propose.** Print what was found, then a mapping built from it:
   each ticket type (`bug`, `idea`, `feedback`) mapped to an existing
   type or label **wherever one genuinely fits**. Offer optional
   routing (a component, a milestone, extra labels) from the existing
   list only.

   A fit means the label means what the note type means. It is not
   "the closest of what happens to exist". When nothing fits, **lead
   with creating a label named for the type**, marked plainly as
   "would be created", and offer reuse of an existing label as the
   alternative to it — not as an equal option beside it. Reuse being
   the path of least resistance is exactly how a type ends up filed
   under a label that means something else, so levelling the two would
   preserve the failure. A project that forbids new labels is one
   keystroke from reuse.

   Never let a poor fit pass silently. When the proposal reuses a label
   whose name differs from the note type, say so in the proposal, in
   the form "feedback would be filed as `question`, which on GitHub
   means someone is asking for information". The user should be
   choosing the compromise, not inheriting it.
3. **Commit.** Write the config only after the user confirms the
   mapping. Create missing taxonomy only on that explicit
   confirmation, never as a side effect of the first synced ticket. A
   proposed label the user does not confirm is never created, then or
   later.

This repo is the worked example of getting it wrong. Nothing here meant
feedback, so setup reached for `question` — which on GitHub means
someone is asking a question, not reporting how a shipped feature
behaves. Every feedback note would have been mislabeled. The fix was to
create a `feedback` label, which is what step 2 now leads with.

## Jira (Atlassian MCP)

- detect: ToolSearch for "atlassian jira". Tools absent: provider
  unavailable; the fix is installing the Atlassian MCP and re-running
  setup.
- inspect: list visible projects (key and name). After the user picks
  one: fetch its issue types, components, and the user's create-issue
  permission. Never create a test issue to probe.
- create: the MCP create-issue tool. Summary = ticket title.
  Description = ticket body converted to the format the tool accepts.
  Issue type from `issue_types`; component from config when set. Labels
  are the union of `type_labels[<type>]` and the global `labels`, each
  applied once.
- update: the MCP edit tool, same issue key.
- comment: the MCP comment tool.
- list: the MCP search tool, open issues in `project_key`. MCP tools
  need a model session, so `tickets-index.py` cannot run this; it
  reports that Jira reconciliation belongs to the ticket skill and
  indexes the local files alone.
- ref: the issue key, `ABC-123`.

## GitHub Issues (gh CLI)

- detect: `gh auth status` succeeds and the repo resolves
  (`gh repo view`). No MCP involved.
- inspect: `gh label list --limit 200`,
  `gh api repos/{owner}/{repo}/milestones --jq '.[].title'`, and any
  issue templates under `.github/`. Write permission:
  `gh api repos/{owner}/{repo} --jq .permissions.push`.
- create: `gh issue create --repo <repo> --title <title>
  --body-file <file>` with `--milestone` when configured, and the
  union of the type's label or label list and `extra_labels`, each
  passed once.
- update: `gh issue edit`.
- comment: `gh issue comment`.
- list: `gh issue list --state open --json
  number,title,body,labels,url`. Scriptable, so `tickets-index.py`
  runs it directly; any failure degrades to the local files with a
  warning.
- ref: `owner/name#42`.

## Shared rules

- A tracker write failure never blocks the local ticket. The ticket
  file is the record; report the failure and the retry path.
- Config taxonomy the tracker no longer has is reported and skipped,
  never recreated. This holds per label, not per issue: when a type
  maps to several labels and one has been deleted since setup, the
  issue is still filed with the rest, and the missing one is named in
  the report. Losing a routing label is not a reason to lose the
  issue, and silently recreating it would undo a deliberate deletion.
- Additions and status changes update the issue the plugin created:
  comment with the new submission, edit the description. Never a twin
  issue.
- Never modify issues the plugin didn't create, except to comment.
- The `issue:` frontmatter field is the only link between a ticket
  file and its tracker issue.
