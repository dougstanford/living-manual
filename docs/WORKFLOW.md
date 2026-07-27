# living-manual development workflow

*Adopted 2026-07-27. Applies to every contributor and every Claude
session. Part I is the technical contract; Part II is the plain-language
guide for reviewing without reading code; Part III is the setup record.
Modelled on the Musiva workflow, with one rule deliberately inverted —
see §3.*

The rule in one sentence: **nothing reaches `main` except through a
green-checked merge request from a single-concern branch, merged with a
merge commit.**

---

# Part I — The technical contract

## 1. Branch roles

| Branch | Role | Direct commits |
|---|---|---|
| `main` | Trunk and release. Tagged at release points. | Never — MRs only |
| `<topic>` or `<owner>/<topic>` | All actual work. One branch = one session = one concern. | Its owner |

One trunk, not two. Musiva separates `rebuild-base` from `master`
because a large rebuild runs with two humans and several agents at once.
This repo releases by tag from `main`, so a second tier would add a
promotion step protecting nothing. Ticket branches read
`ticket-NNNN-<slug>`; anything else takes a plain topic name.

## 2. The session loop

1. **Start from fresh trunk.** `git fetch origin`, then branch from
   `origin/main` — never from another topic branch, never from a stale
   local ref. Use a `git worktree` when more than one session is active,
   so one session's commit can never sweep in another's edits.

2. **Work on one concern.** One ticket, one release. If the branch grows
   a second concern, split it.

3. **Stage explicit paths.** Never `git add -A` or `git add .` in a tree
   another session may share.

4. **Push the branch the same day it exists.**

5. **Before opening the MR:**
   - rebase onto `origin/main` (rebase, don't merge trunk in);
   - run the gates locally: `sh scripts/ci-check.sh`;
   - update the manual in the same branch when the change is
     user-facing — see `reference/maintenance.md`;
   - for a version bump, follow the release routine in `CLAUDE.md`.

6. **Open the MR into `main`**, using the PR template. Write the
   description in user-facing language; the reviewer may not read the
   diff.

7. **After merge**, the branch deletes itself (the repo has
   auto-delete on). Remove the worktree if you made one.

## 3. Review and merge rules

- **Merge method: merge commit. Squash and rebase merging are disabled
  at the repository, not merely discouraged.**

  This is the one place this workflow inverts Musiva's, and the reason
  is the guard this plugin ships. The manual stamps `manual-base: <sha>`
  and content fingerprints into the document. Squash-merge and
  rebase-merge both replay work under new SHAs, so the commit the marker
  names never lands on `main` — the marker is orphaned the moment the MR
  is merged, and every later staleness check returns a meaningless
  answer until someone re-stamps.

  That is the exact failure `verify.py` and `stale.sh` exist to catch,
  and it would be self-inflicted at merge time. Since v0.2.7 it degrades
  gracefully rather than losing information (`RESTAMP` when nothing
  user-facing moved, `MOVED` naming the paths that did), but degrading
  gracefully is not a reason to spend it.

  Each repo allows exactly the one merge method its integrity model
  survives. Musiva has no marker to orphan, so it takes squash and gets
  a linear trunk. This repo takes merge commits and keeps its markers.

- **Green CI is a precondition, not a suggestion.** `Manual reflects the
  code` must pass. A red X means the author fixes and re-pushes.
- **Never force-push `main`.** Allowed only on your own topic branch
  before review has started.
- **A revert is an MR too.**

## 4. CI — what the green checkmark certifies

`.github/workflows/manual-guard.yml` runs on every MR and on every push
to `main`, executing `scripts/ci-check.sh`:

1. `verify.py` — the manual's markers, data blocks, and script are
   intact, and its base marker resolves to a commit in this repo;
2. `stale.sh` — no user-facing commit postdates the manual's base;
3. the queue drift check — **advisory**, reported and never failing the
   build.

The split follows the enforcement principle in
`reference/maintenance.md`: block when the guard itself is disabled and
the tool can prove it locally; warn when the output is merely imperfect,
or when proving it requires an external service.

## 5. Releases

The routine lives in `CLAUDE.md` and ends in a tag. Two things the
protection does not change: tags are a separate ruleset target, so
tagging still works normally, and the release point is still the first
commit on `main` where `sh scripts/ci-check.sh` prints CURRENT — which,
landing through an MR, is the merge commit.

---

# Part II — The reviewer's guide (no code required)

This plugin's whole claim is that a manual can be trusted to match the
code. The workflow applies the same idea to the code itself:

- **`main` is the published state.** Nobody edits it directly. GitHub
  physically enforces this — a direct push is refused, and that has been
  tested, not assumed.
- **A branch is a working copy.** Every piece of work happens on its
  own, so a mess can't touch the trunk and two sessions can't bleed into
  each other.
- **A merge request is "this is ready."** GitHub calls it a pull
  request; same thing.
- **CI is the guard, run by a robot.** A green checkmark means the
  manual still matches the code. A red X means "not yet" — the author
  fixes it and the robot re-checks. You never need to know what failed.
- **A tag is a labelled shelf copy.** `@v0.2.9` always means that exact
  state, and consumers pin it as a GitHub Action.

## Reviewing

Look at three things: **the description** (plain English — what changed,
why, what you should see), **the checkmark** (green or don't merge), and
**the manual itself** where the change is user-facing. Then click Merge,
or leave a comment in plain English.

**One request, one purpose.** A review trusts that the description
matches the change, which only holds if each MR does one thing.

---

# Part III — Setup record

*Everything below is **done** (2026-07-27). Kept as the record of how
the trunk is protected and how to restore it.*

## Branch protection — ACTIVE

A repository **ruleset** named `protect-trunk` (id 19856830) covers
`refs/heads/main`, enforcement `active`, with **no bypass actors** — the
owner does not bypass it either:

| Rule | Effect |
|---|---|
| `pull_request` | No direct pushes. **Merge commit is the only allowed merge method.** Review threads must be resolved. |
| `required_status_checks` | The MR cannot merge until **Manual reflects the code** passes. |
| `non_fast_forward` | Force-pushes to `main` are refused. |
| `deletion` | `main` cannot be deleted. |

Verified by probe on 2026-07-27 — a direct push to `main` was refused
with `push declined due to repository rule violations`, naming the
missing required check.

**Approvals, deliberately zero.** Agent sessions act as `dougstanford`,
and GitHub forbids approving your own pull request, so a 1-approval
requirement would block every agent MR. The enforced gate is *MR + green
check*; the merge click is the human judgment. This matches Musiva's
reasoning exactly.

**Plan note.** This repo is public, so rulesets apply on the Free plan.
Musiva needs GitHub Pro for the same protection because it is private.
If this repo ever goes private on a Free plan, protection silently stops
applying and the workflow falls back to discipline alone.

## Repository settings — done

- **Merge commits only** (squash and rebase merging both disabled).
- "Automatically delete head branches" on.
- Actions enabled (CI needs it).

To inspect or recreate:

```
gh api repos/dougstanford/living-manual/rulesets --jq '.[].name'
gh api repos/dougstanford/living-manual/rulesets/19856830
```
