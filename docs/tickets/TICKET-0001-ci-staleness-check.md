---
id: TICKET-0001
title: CI check runs verify.py and stale.sh so GitHub-side merges can't ship a broken manual
type: idea
target: current
status: ready
section: The staleness guard (#guard)
created: 2026-07-23
issue: dougstanford/living-manual#2
---

## Summary

The staleness guard only runs in a developer's clone: the pre-push hook
fires on `git push`, and nothing else. A squash merge or "Update branch"
click in the GitHub web UI rewrites history on the server, passes through
no hook, and can land a manual whose base marker is orphaned or whose
content is stale. A GitHub Actions workflow running `verify.py` and
`stale.sh` on pull requests and on the default branch would surface the
break where it happens. Both scripts are plain python3/sh with no model
dependency, so CI can detect the problem; the fix still needs a Claude
Code session.

Motivating defect: this repo's own manual shipped with base marker
`2a646e9`, a commit absent from published history (rewritten after
stamping). Nothing server-side could have caught it.

## Origin

Reconstructed 2026-07-26 from tracker issue
`dougstanford/living-manual#2`, filed 2026-07-23 by @manbradcalf.

The issue states this file "lands with PR #1". It did not: the ticket
files were never committed on any branch, so the issue was the only
record until now. The queue check surfaced the gap by showing the issue
as open at the tracker with no ticket file behind it.

Content below is the issue's, with Current behavior added and the
References corrected where PR #1 has since shipped. No requirement was
altered.

## Current behavior

State as of 2026-07-26 (v0.2.5), which differs from when the issue was
written:

- `scripts/install-hook.sh` installs a pre-push hook and nothing else.
  Enforcement is local to each clone. A push that never happens (a
  web-UI merge, a squash, an "Update branch" click) passes through no
  check at all.
- The repo has no `.github/workflows` directory. Nothing runs
  server-side.
- `scripts/stale.sh:31` prints `BAD-BASE <sha>` and exits 1 when the
  marker does not resolve. The hook translates that into a blocked push
  with a message.
- `scripts/verify.py` now flags an orphaned base marker directly. That
  finding shipped with PR #1, which is merged, so the issue's reference
  to it as pending is out of date. The check exists; only the
  server-side trigger is missing.
- Both scripts are plain `python3` and `sh`, take the manual path and
  repo root as input, and need no model. They are already suitable to
  run unattended.

## User stories

- As a maintainer merging PRs in the GitHub web UI, I want a failing
  check when a merge would orphan the manual's base marker or leave the
  manual stale, so the break is visible at merge time instead of at the
  next dev's session.
- As a PR reviewer, I want a red check on a PR whose user-facing commits
  outpace its manual, so I can ask for the manual update before
  approving.

## Functional requirements

- FR-1: The plugin provides a GitHub Actions workflow that runs
  `verify.py` against the configured manual and runs `stale.sh`, on pull
  requests and on pushes to the default branch.
- FR-2: The workflow checks out full history (`fetch-depth: 0`); a
  shallow clone would misreport a resolvable base as `BAD-BASE`.
- FR-3: A nonzero exit from either script fails the check, and the step
  output includes the script's findings plus the fix path
  (`claude -p "/living-manual:manual update"`).
- FR-4: The plugin publishes a composite GitHub Action at its repo root,
  so a documented repo's workflow obtains the scripts with
  `uses: dougstanford/living-manual@<tag>` and no second checkout step.
  The action runs both scripts and surfaces their output.
- FR-5: The plugin repo carries release tags matching the version in
  `.claude-plugin/plugin.json`, so FR-4's `uses:` can pin one. Tagging
  becomes part of the release routine; no tags exist today.
- FR-6: The action accepts the manual path and tickets directory as
  inputs, defaulting to the values in the consumer's
  `.living-manual.json`, so a repo that moved either still works.
- FR-7: The manual skill's wiring step (setup step 5) offers the
  workflow when the repo is hosted on GitHub, and records the choice in
  `.living-manual.json`.
- FR-8: This repo carries the workflow itself, running on pull requests
  and on pushes to `main`.

## Acceptance criteria

- Given a PR whose user-facing commits postdate the manual's base
  marker, when the workflow runs, then the check fails and the log lists
  the offending commits.
- Given a branch whose manual base marker does not resolve to a commit,
  when the workflow runs, then the check fails naming the orphaned sha.
- Given a PR with a current manual and resolvable base, when the
  workflow runs, then the check passes.
- Given a repo whose manual base is many commits behind HEAD, when the
  workflow runs, then the checkout has enough history for `stale.sh` to
  resolve that base, and it is not misreported as `BAD-BASE`.
- Given a repo not hosted on GitHub, when setup's wiring step runs, then
  no workflow is offered and nothing CI-related is written.
- Given a consumer workflow using `uses: dougstanford/living-manual@<tag>`,
  when it runs, then both scripts execute with no checkout of the plugin
  repo in the consumer's workflow file.
- Given a consumer whose manual lives somewhere other than the default
  path, when the action runs with that path as an input, then it checks
  the right file.
- Given a release of the plugin, when it is published, then a tag
  matching `plugin.json`'s version exists and `uses:` can pin it.
- Given this repo, when a pull request is opened, then the workflow runs
  and its result is visible on the PR.

## Decisions

Settled 2026-07-26. Q1 changed the shape of the work, so FR-4 was
rewritten rather than merely pinned, and FR-5, FR-6, FR-8 were added to
carry the consequences.

- D1 (FR-4, FR-5, FR-6): CI obtains the scripts through a composite
  GitHub Action published from this repo, referenced as
  `uses: dougstanford/living-manual@<tag>`. Chosen over the pinned
  second checkout the ticket originally proposed because it is one line
  in the consumer, versioned, and idiomatic for GitHub. The cost is
  real: this repo has no tags, so release tagging becomes a discipline
  (FR-5). Vendoring the scripts was rejected because the copies drift
  from the plugin as it evolves.
- D2 (FR-3): The check fails loudly on a stale or orphaned manual. Setup
  reports how an admin marks it required. The plugin does not write
  branch protection, so a failing check is advisory until an admin
  elects otherwise, and that is the correct division: the plugin
  supplies the signal, the repo owner decides its force.
- D3 (FR-8): The workflow runs on this repo. The defect that motivated
  the ticket shipped here, and PR #1 was exactly the web-UI merge path
  the workflow exists to catch.

## References

- `scripts/stale.sh:31` (BAD-BASE on unresolvable base)
- `scripts/verify.py` (orphaned-marker finding, shipped in PR #1)
- `scripts/install-hook.sh` (local-only enforcement)
- Manual section: The staleness guard (#guard)
- Related: TICKET-0002 / issue #3 (rewrite-proof base marker)
- Related: TICKET-0003 / issue #4, whose FR-7 keeps the queue drift
  check callable by the same workflow this ticket creates
