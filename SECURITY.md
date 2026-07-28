# Security

## Reporting a vulnerability

Report privately through GitHub's
[security advisories](https://github.com/dougstanford/living-manual/security/advisories/new)
rather than by opening an issue. Include what you did, what happened,
and the version or commit you saw it on.

This is a personal project, so there is no response-time commitment.
You will get an acknowledgement when the report is read.

## What this plugin does on your machine

Worth knowing before you install it, because the answers decide what a
vulnerability here could reach.

- **It runs Python and shell scripts from this repo.** `scripts/` is
  invoked by the skills and by the pre-push hook. Read them before you
  trust them, the same as any tool you let near a checkout.
- **It installs a git hook.** `scripts/install-hook.sh` writes a
  pre-push hook that blocks pushes when the manual is stale. It runs on
  every push until you remove it.
- **It writes to your repo.** The manual, `docs/tickets/`, a CLAUDE.md
  snippet, `.living-manual.json`, and optionally a GitHub Actions
  workflow.
- **It reads your codebase** to write the manual, and reads your issue
  tracker when one is configured.
- **The manual is one static HTML file with no network calls.** Nothing
  it holds leaves the file until you copy a payload to your clipboard
  and paste it somewhere yourself.

## The one that has bitten people

A maintained manual carries its ticket queue and tracker name *inside
the file*, in the `TICKETS` and `QUEUE_SYNC` blocks. Anyone who views
source sees your backlog, whether or not the page displays it.

Never hand out the maintained manual. Run `scripts/export.py` and hand
out the export, which carries neither block. `scripts/verify.py` fails
an export that still does.
