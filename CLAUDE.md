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
4. Once it is on `main`, tag the commit that stamped the manual, and
   push the tag:
   `git tag -a v<version> -m "<summary>" && git push origin v<version>`.

Tag the manual-stamp commit, not the code commit before it. A release
is two commits: the code, then the manual stamped against it. Only at
the second do the scripts and the manual agree, and agreement is the
whole point of a pin — a consumer on `@v0.2.6` should get scripts the
v0.2.6 manual actually describes.
