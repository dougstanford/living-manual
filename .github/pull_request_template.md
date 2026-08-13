<!-- Describe the change in user-facing language first: what changed, why,
     and what the reviewer should look at. The reviewer may not read the
     diff — write for that reader. See docs/WORKFLOW.md. -->

## What this does

## Why

## What to look at
<!-- If user-facing: the manual section or behavior that changed. If not,
     say so and name what covers it. -->

## Checklist (author)
- [ ] One concern only — one ticket, one release, or one fix. (If this MR
      does two unrelated things, split it before requesting review.)
- [ ] Rebased on latest `origin/main`
- [ ] `sh scripts/ci-check.sh` green locally
- [ ] Manual updated in this branch where the change is user-facing
      (`skills/`, `scripts/`, `templates/`, `reference/`), per
      `reference/maintenance.md`
- [ ] Version bumped and README pin updated, or N/A — see the release
      routine in `CLAUDE.md`
- [ ] Merge strategy is your call — merge commit, squash, or rebase are
      all safe. The manual's staleness marker is content-based, so no
      merge strategy can orphan it.
