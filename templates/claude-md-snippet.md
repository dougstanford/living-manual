
## User's manual (living-manual)

This project's user manual is MANUAL_PATH, maintained by the
living-manual plugin. It must reflect the app as released.

- Before any push: run `/living-manual:manual update`. It reads the
  commits since the manual's base marker and revises only what changed.
  The pre-push hook blocks pushes when the manual is stale; fix the
  manual rather than bypassing.
- The manual describes the end state of the collective commits being
  pushed, so the next dev opens a manual that matches the release.
- Notes filed from the manual become tickets via `/living-manual:ticket`
  in TICKETS_DIR. Keep the manual's queue index in sync when touching
  tickets by hand.
- Config lives in `.living-manual.json`. Prose rules live in the
  plugin's `reference/writing-style.md`.
