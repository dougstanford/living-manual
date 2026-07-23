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
    "component": "optional: route new issues to one component",
    "labels": ["optional: labels applied to every issue"]
  },
  "github": {
    "repo": "owner/name",
    "labels": { "bug": "bug", "idea": "enhancement", "feedback": "feedback" },
    "extra_labels": ["optional: applied to every issue"],
    "milestone": "optional: title of the milestone new issues join"
  }
}
```

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
| ref | The string stored in ticket frontmatter (`issue:`). |

## Setup discipline: inspect, propose, commit

Projects accumulate their own labels, milestones, issue types, and
components. Setup adapts to what exists; it never assumes the defaults
above fit.

1. **Inspect.** Enumerate the project's existing taxonomy with the
   provider's inspect commands. Read before write, always.
2. **Propose.** Print what was found, then a mapping built from it:
   each ticket type (`bug`, `idea`, `feedback`) mapped to an existing
   type or label wherever one fits. Offer optional routing (a
   component, a milestone, extra labels) from the existing list only.
   Suggest creating something new only when nothing existing fits, and
   mark it plainly as "would be created".
3. **Commit.** Write the config only after the user confirms the
   mapping. Create missing taxonomy only on that explicit
   confirmation, never as a side effect of the first synced ticket.

## Jira (Atlassian MCP)

- detect: ToolSearch for "atlassian jira". Tools absent: provider
  unavailable; the fix is installing the Atlassian MCP and re-running
  setup.
- inspect: list visible projects (key and name). After the user picks
  one: fetch its issue types, components, and the user's create-issue
  permission. Never create a test issue to probe.
- create: the MCP create-issue tool. Summary = ticket title.
  Description = ticket body converted to the format the tool accepts.
  Issue type from `issue_types`; component and labels from config when
  set.
- update: the MCP edit tool, same issue key.
- comment: the MCP comment tool.
- ref: the issue key, `ABC-123`.

## GitHub Issues (gh CLI)

- detect: `gh auth status` succeeds and the repo resolves
  (`gh repo view`). No MCP involved.
- inspect: `gh label list --limit 200`,
  `gh api repos/{owner}/{repo}/milestones --jq '.[].title'`, and any
  issue templates under `.github/`. Write permission:
  `gh api repos/{owner}/{repo} --jq .permissions.push`.
- create: `gh issue create --repo <repo> --title <title>
  --body-file <file>` with the mapped label, `extra_labels`, and
  `--milestone` when configured.
- update: `gh issue edit`.
- comment: `gh issue comment`.
- ref: `owner/name#42`.

## Shared rules

- A tracker write failure never blocks the local ticket. The ticket
  file is the record; report the failure and the retry path.
- Additions and status changes update the issue the plugin created:
  comment with the new submission, edit the description. Never a twin
  issue.
- Never modify issues the plugin didn't create, except to comment.
- The `issue:` frontmatter field is the only link between a ticket
  file and its tracker issue.
