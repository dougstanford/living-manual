# living-manual

This repo is the living-manual plugin itself. The manual below documents
the plugin, built by the plugin: dogfooding is the point. Changes to
skills/, scripts/, templates/, or reference/ are user-facing.

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
4. Once it is on `main`, tag the release point and push the tag:
   `git tag -a v<version> -m "<summary>" && git push origin v<version>`.

The release point is the first commit on `main` at which the manual is
current — never the code commit before the manual was stamped against
it. Landing through a PR, that is the merge commit; landing directly,
it is the manual-stamp commit. Test it the same way either way: check
out the candidate and run `sh scripts/ci-check.sh`. If it does not
print CURRENT, it is not the release point.

Agreement is the whole point of a pin. A consumer on `@v0.2.6` should
get scripts the v0.2.6 manual actually describes.

Merge PRs with a merge commit, not a squash. A squash rewrites the
base commit out of history and orphans the manual's marker — the very
failure the guard exists to catch, self-inflicted at merge time.
