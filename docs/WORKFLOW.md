# living-manual development workflow

*Adopted 2026-07-27. Applies to every contributor and every Claude
session. Part I is the technical contract; Part II is the plain-language
guide for reviewing without reading code; Part III is the setup record.
Modelled on the Musiva workflow.*

The rule in one sentence: **nothing reaches `main` except through a
green-checked merge request from a single-concern branch.**

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

- **Merge method: any of the three. Merge commit, squash, and rebase
  are all permitted.**

  Until TICKET-0006 this repo disabled squash and rebase, because the
  manual stamped `manual-base: <sha>` into the document and those merge
  methods replay work under new SHAs — the commit the marker named never
  landed on `main`, orphaning the marker at merge time. That constraint
  is gone. The manual now records a **content hash per user-facing
  surface** (`manual-surfaces`), not a commit sha, and a content hash is
  independent of how history was rewritten: squash it, rebase it, replay
  it under any SHA, and `skills/`'s tree still hashes the same. There is
  nothing left for a merge method to orphan.

  The same property is what makes branches merge in **any order** with no
  manual conflict: a branch only rewrites the hash line for a surface it
  actually changed, so two branches touching different surfaces edit
  different lines and merge cleanly whichever lands first. Two branches
  touching the *same* surface still collide on that one line — which is
  the reconciliation a human owes anyway.

  Pick the merge method you like. Merge commits keep each branch's manual
  reconciliation as a distinct commit; squash gives a linear trunk. The
  guard is indifferent.

- **Green CI is a precondition, not a suggestion.** `Manual reflects the
  code` must pass. A red X means the author fixes and re-pushes.
- **Never force-push `main`.** Allowed only on your own topic branch
  before review has started.
- **A revert is an MR too.**

## 4. CI — what the green checkmark certifies

`.github/workflows/manual-guard.yml` runs on every MR and on every push
to `main`, executing `scripts/ci-check.sh`:

1. `verify.py` — the manual's markers, data blocks, and script are
   intact, and its `manual-surfaces` block is present and well-formed;
2. `stale.sh` — every user-facing surface's content still matches the
   hash the manual records for it;
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
commit on `main` where `sh scripts/ci-check.sh` prints CURRENT — the
merge commit when the MR merged with one, otherwise the squashed or
rebased commit that landed the manual stamp.

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
| `pull_request` | No direct pushes. **All three merge methods allowed** (merge, squash, rebase — see the TICKET-0006 note below). Review threads must be resolved. |
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

- **All three merge methods enabled** (merge, squash, rebase — relaxed
  by TICKET-0006; see below).
- "Automatically delete head branches" on.
- Actions enabled (CI needs it).

To inspect or recreate:

```
gh api repos/dougstanford/living-manual/rulesets --jq '.[].name'
gh api repos/dougstanford/living-manual/rulesets/19856830
```

## TICKET-0006 — merge methods relaxed (owner action)

The staleness marker became content-based (`manual-surfaces`), so no
merge method can orphan it and squash/rebase are safe again. The code
and docs in that ticket ship the relaxation, but the two server-side
toggles are not something the plugin can change — the repo owner applies
them once, with their own access:

```
# 1. Repository merge settings: enable squash and rebase.
gh api -X PATCH repos/dougstanford/living-manual \
  -F allow_merge_commit=true -F allow_squash_merge=true -F allow_rebase_merge=true

# 2. The protect-trunk ruleset's pull_request rule: allow all three
#    methods. Fetch the ruleset, set the pull_request rule's
#    allowed_merge_methods to ["merge","squash","rebase"], and PATCH:
gh api repos/dougstanford/living-manual/rulesets/19856830 > ruleset.json
#    (edit allowed_merge_methods in ruleset.json, then)
gh api -X PUT repos/dougstanford/living-manual/rulesets/19856830 --input ruleset.json
```

Until both are applied, the repo still enforces merge-commit-only at the
server regardless of what this record says; the record describes the
intended end state.
