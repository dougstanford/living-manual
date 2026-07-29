# living-manual

A Claude Code plugin that builds and maintains a branded, interactive
user's manual for any codebase.

The manual is one self-contained HTML file:

- **Click any heading** to make a note (idea, feedback, bug). The note
  becomes a paste-ready payload for a Claude Code session, which writes
  a developer ticket with user stories, functional requirements, and
  acceptance criteria, or the open questions that would complete them.
  With a tracker configured, tickets also land in Jira or GitHub
  Issues.
- **Roadmap previews** (▶ icons) show the intended future state of
  features with planned work. Items that are already changing take
  notes against the plan, not the current behavior.
- **A concept glossary** explains product-novel terms on hover, once
  per concept, and only before the manual defines them.
- **A queue check** in the note modal shows already-submitted tickets
  so duplicates become additions instead of twins.
- **Drag the contents to reorder**: each TOC entry has a handle in its
  left margin; drag it (subsections riding along) and the manual slides
  into the new order on release. The browser remembers the arrangement
  on every open; an optional payload makes it the committed order for
  everyone.
- **Edit the copy where you read it**: click into any paragraph,
  heading, or the title to correct it. Press Enter to save your edit,
  Shift+Enter to start a new line, Escape to discard your changes.
  Renaming a heading renames its contents entry with it. Edits persist
  in the browser and change no file until a payload commits them.
- **A menu on small screens**: when a frame is too short or too narrow
  to show the contents whole, they collapse to a menu button that opens
  them centred over a frozen page.

**See it demonstrate itself:** [dougstanford.com/living-manual/]([docs/USER_MANUAL.html](https://dougstanford.com/living-manual/))
is this plugin's own manual, built and maintained by the plugin. Open it
in a browser: the clickable headings, roadmap previews, glossary, and
queue check are all live, and its What's new tracks this repo's releases.

## Install

Add this repo as a marketplace, then install the plugin:

```
/plugin marketplace add dougstanford/living-manual
/plugin install living-manual@living-manual
```

Or point a session at a local checkout directly:

```bash
claude --plugin-dir /path/to/living-manual
```

## Use

First run in a repo:

```
/living-manual:manual
```

walks setup: codebase orientation, brand extraction, optional issue
tracker link (Jira via the Atlassian MCP, or GitHub Issues via the gh
CLI; setup inspects the project's existing labels, milestones, and
issue types and proposes a mapping before writing anything), then
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

## Handing the manual out

The manual is built for the people who maintain the code. To distribute
a release more widely, export a static copy:

```bash
python3 scripts/export.py docs/USER_MANUAL.html
```

That writes `docs/USER_MANUAL_prod.html` with the note-filing path gone,
along with the affordances that advertise it, and the roadmap previews,
which describe work that has not shipped. Editing and reordering go too:
both end at a payload for a session with the repo checked out, which an
outside reader does not have. The glossary, all prose, and the
responsive layout stay, so a distributed copy still reads on whatever it
is opened on.

The queue matters most here. `TICKETS` and `QUEUE_SYNC` live *inside*
the file, so a distributed manual that kept them would publish your
backlog and name your issue tracker to anyone who views source. The
export carries neither, and verification fails if one survives.

Add a second argument to write the copy somewhere else. Inside the repo
it picks up a git rule when the repo has none; outside the repo
`.gitignore` is left alone, because git never sees a file outside the
working tree.

Exports are build artifacts: `.gitignore`d and regenerated at release,
so there is only ever one document to keep current.

## The same guard in CI

The hook lives in a clone, so it never sees a merge performed on
GitHub: a squash or an "Update branch" click rewrites history on the
server and can land a stale manual. Setup offers a workflow that runs
the same checks where merges actually happen. It is one step, because
the plugin publishes itself as a composite action:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0        # the manual's base commit is usually far back
- uses: dougstanford/living-manual@v0.5.0
```

The action reads `.living-manual.json` for the paths it needs; pass
`manual-path` or `tickets-dir` only if this workflow guards a repo
whose manual moved. A failing check names the offending commits and
the command that fixes them. It stays advisory until an admin adds it
to the branch's required checks. The plugin supplies the signal; the
repo owner decides its force.

## Layout

```
action.yml        composite action: the guard, runnable in CI
skills/manual/    the builder and updater
skills/ticket/    note → ticket (+ tracker sync)
scripts/          state, inventory, staleness, hook install, ticket
                  numbering, tickets-index rebuild, data-block sync,
                  scaffolding, static verification, the CI entry point,
                  static export, section reorder, prose write-back
templates/        the interactive manual shell, CLAUDE.md snippet, and
                  the CI workflow setup installs
reference/        writing style and documentation voice (binding) +
                  maintenance checklist + tracker gateway contract
```

Scripts do the mechanical work; the model spends tokens on content and
judgment only.

Requires git and python3. node is optional; when present, verification
also syntax-checks the manual's script.

## Acknowledgements

`reference/writing-style.md` is the binding style guide for every word
this plugin generates. Its catalogue of words and patterns to cut is
adapted from the `no-ai-slop` skill by Peter Yang, reused and modified
under the MIT License, Copyright (c) 2026 Peter Yang. The full notice
travels with the adapted text, at the end of that file.

The rest of the guide, covering who reads a manual and what they need
from it, is this project's own.

## Contributing

`main` is protected: every change lands through a pull request that
passes the **Manual reflects the code** check. See
[docs/WORKFLOW.md](docs/WORKFLOW.md) for the full contract and
[CLAUDE.md](CLAUDE.md) for what an agent session is expected to do.

The short version: branch from `origin/main`, keep one concern per
branch, run `/living-manual:manual update` before pushing so the manual
matches what you changed, and open the PR against `main`.

## License

MIT. See [LICENSE](LICENSE).

The catalogue of words and patterns to cut in
`reference/writing-style.md` is adapted from the `no-ai-slop` skill by
Peter Yang, reused under the MIT License. Its notice travels with the
adapted text.

---

Built by [Doug Stanford](https://dougstanford.com) ·
[LinkedIn](https://www.linkedin.com/in/dougstanford/)
