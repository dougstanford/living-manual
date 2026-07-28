# living-manual

This repo is the living-manual plugin itself. The manual below documents
the plugin, built by the plugin: dogfooding is the point. Changes to
skills/, scripts/, templates/, or reference/ are user-facing.

## Start of every session

1. `git fetch origin`, then create your working branch from
   `origin/main`: `git switch -c <topic> origin/main`. Ticket work reads
   `ticket-NNNN-<slug>`. Use a `git worktree` if another session may be
   active. **Never build directly on `main`.**
2. Read `README.md` and `docs/WORKFLOW.md` before your first commit.

If the working tree has uncommitted non-trivial changes, or the session
was deliberately started on another branch, surface that instead of
forcing a switch.

## How work lands — non-negotiable

`main` is protected: direct pushes, force-pushes, and deletion are
refused by GitHub itself. Everything reaches trunk through a merge
request that passes **Manual reflects the code**.

- One branch = one session = **one concern**. If a branch grows a second
  concern, split it.
- **Never `git add -A` or `git add .`** in a tree another session may
  share — stage explicit paths.
- Push the branch the same day it exists; open the MR with
  `gh pr create --base main`.
- Rebase onto trunk; never merge trunk into your branch.
- **Merge with a merge commit. Squash and rebase merging are disabled at
  the repository, deliberately.** Both replay work under new SHAs, which
  orphans the manual's base marker the moment the MR lands — the exact
  failure the guard exists to catch. Full reasoning in
  `docs/WORKFLOW.md` §3.
- Required approvals are 0 by design (agent sessions act as the owner,
  and GitHub forbids self-approval), so the enforced gate is *MR + green
  check*. The merge click is the human judgment.
- Write the MR body in plain, user-facing language: what changed, why,
  and what to look at. The reviewer may not read the diff.

Full contract, including the protection ruleset and the reviewer's
guide: `docs/WORKFLOW.md`.

## User's manual (living-manual)

This project's user manual is docs/USER_MANUAL.html, maintained by the
living-manual plugin. It must reflect the app as released.

- Before any push: run `/living-manual:manual update`. It reads the
  commits since the manual's base marker and revises only what changed.
  The pre-push hook blocks pushes when the manual is stale; fix the
  manual rather than bypassing.
- The manual describes the end state of the collective commits being
  pushed, so the next dev opens a manual that matches the release.
- Notes filed from the manual become tickets via `/living-manual:ticket`
  in docs/tickets. Keep the manual's queue index in sync when touching
  tickets by hand.
- Config lives in `.living-manual.json`. Prose rules live in the
  plugin's `reference/writing-style.md`.

## Releasing

Consumers pin this repo as a GitHub Action
(`uses: dougstanford/living-manual@<tag>`), so a release that is not
tagged is a release nobody can pin. Every version bump ends the same way:

1. Bump `version` in `.claude-plugin/plugin.json`.
2. Update `{{PLUGIN_VERSION}}`'s example in the README to the new tag,
   so the copy-pasteable snippet is never a version behind.
3. Run `/living-manual:manual update` and let the push guard pass.
4. Regenerate the distributable copy if one goes out with the release:
   `python3 scripts/export.py docs/USER_MANUAL.html`. It is gitignored,
   so it never lands in the repo — build it from the tagged state.
5. Once it is on `main`, tag the release point and push the tag:
   `git tag -a v<version> -m "<summary>" && git push origin v<version>`.

The release point is the first commit on `main` at which the manual is
current — never the code commit before the manual was stamped against
it. Landing through a PR, that is the merge commit; landing directly,
it is the manual-stamp commit. Test it the same way either way: check
out the candidate and run `sh scripts/ci-check.sh`. If it does not
print CURRENT, it is not the release point.

Agreement is the whole point of a pin. A consumer on `@v0.2.6` should
get scripts the v0.2.6 manual actually describes.

Tagging is unaffected by branch protection: tags are a separate ruleset
target, so `git push origin v<version>` works normally even though a
direct push to `main` does not.
