# living-manual

A Claude Code plugin that builds and maintains a branded, interactive
user's manual for any codebase.

The manual is one self-contained HTML file:

- **Click any heading** to make a note (idea, feedback, bug). The note
  becomes a paste-ready payload for a Claude Code session, which writes
  a developer ticket with user stories, functional requirements, and
  acceptance criteria, or the open questions that would complete them.
  With the Atlassian MCP configured, tickets also land in Jira.
- **Roadmap previews** (▶ icons) show the intended future state of
  features with planned work. Items that are already changing take
  notes against the plan, not the current behavior.
- **A concept glossary** explains product-novel terms on hover, once
  per concept, and only before the manual defines them.
- **A queue check** in the note modal shows already-submitted tickets
  so duplicates become additions instead of twins.

## Install

Add this repo as a marketplace and install, or point a session at it
directly:

```bash
claude --plugin-dir /path/to/living-manual
```

## Use

First run in a repo:

```
/living-manual:manual
```

walks setup: codebase orientation, brand extraction, optional Jira
link (requires the Atlassian MCP and create-issue permission), then
writes `.living-manual.json`, installs a pre-push staleness guard,
wires CLAUDE.md, and builds the manual.

After that:

```
/living-manual:manual update      # sync the manual to the code
/living-manual:ticket             # paste a note payload from the manual
```

The pre-push hook blocks pushes whose user-facing commits postdate the
manual's base commit, so the next dev always opens a manual that
matches the release. Bypass once with `git push --no-verify`.

## Layout

```
skills/manual/    the builder and updater
skills/ticket/    note → ticket (+ Jira sync)
scripts/          state, inventory, staleness, hook install, ticket
                  numbering, tickets-index rebuild, data-block sync,
                  scaffolding, static verification
templates/        the interactive manual shell + CLAUDE.md snippet
reference/        writing style (binding) + maintenance checklist
```

Scripts do the mechanical work; the model spends tokens on content and
judgment only.

Requires git and python3. node is optional; when present, verification
also syntax-checks the manual's script.
