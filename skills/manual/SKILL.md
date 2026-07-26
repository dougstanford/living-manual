---
name: manual
description: Build and maintain a branded, interactive user's manual for this codebase. First run walks a setup flow (brand assets, codebase orientation, optional issue-tracker link to Jira or GitHub Issues, push-time guard); later runs update the manual to match the code since its base commit. Use for "/manual", "build the manual", "update the manual", or when the pre-push guard reports the manual is stale.
---

# The living manual

One HTML file, self-contained, brand-styled, interactive: clickable
headings file notes that become tickets, roadmap previews show planned
changes, a glossary explains novel concepts on first use. This skill
builds it once, then keeps it matched to the released code.

All prose you generate follows `reference/writing-style.md` in this
plugin. Read it before writing any manual content. It is binding.

Token discipline: the scripts in `scripts/` exist so you never do their
work by hand. Run them, read their compact output, act on it. Do not
re-read the whole codebase on update runs; `stale.sh` tells you exactly
what changed.

`$LM` below is the plugin root. This file lives at
`$LM/skills/manual/SKILL.md`, so resolve it from the path this skill
loaded from.

Every question you ask during setup must be answerable from what is on
the user's screen. Print the thing you are asking about (the feature
map, the palette and its proposed roles, the tracker's projects,
labels, and milestones) in your
reply first, then ask. Answer choices never reference content the user
has not been shown.

## Every invocation starts the same way

```
sh $LM/scripts/state.sh
```

Branch on the JSON: `configured: false` → setup flow. Otherwise →
update flow (or the specific request the user made).

## Setup flow (first run)

Work through these in order. Each step ends with something written to
disk, so an interrupted setup resumes cleanly (state.sh shows what
exists).

**1. Orient to the codebase.**
Run `sh $LM/scripts/inventory.sh <repo-root>`. From its output plus the
README and any changelog/roadmap docs, build the feature map:
user-facing surfaces and the shipped features on each. Read the main UI
entry point and each surface component; the manual documents what users
experience, so ground every section in the code that renders it.
**Print the full map in your reply** (a plain nested list: surface →
features), then ask the user to confirm or correct it — missing
features, wrong groupings, things that aren't user-facing. A wrong map
here costs the whole document.

**2. Locate brand.**
inventory.sh lists brand-candidate directories. Read what's there:
style guides, palettes, logo files, design docs. Extract: palette (with
semantic roles), typography, shape language, voice. Print the extracted
palette with each hex value and its proposed role before asking the
user to confirm; when roles are ambiguous, the question names the
specific colors in its options. No brand assets:
offer the neutral default palette (scaffold.py's fallback) and note it
in the config so a later brand pass knows. A logo file becomes a data
URI (downscale to ~96px first: `sips -Z 96 in.png --out small.png`,
then base64) so the manual stays self-contained.

**3. Issue tracker link (optional).**
Read `$LM/reference/trackers.md` first; it defines the supported
providers, the config schema, and the inspect-propose-commit
discipline this step follows. Run each provider's detect step (Jira:
Atlassian MCP via ToolSearch; GitHub Issues: `gh` authenticated and
the repo resolves). None usable: record
`"tracker": {"provider": "none"}` with the reason and the enable path.
Otherwise ask which provider receives tickets, offering only the
usable ones plus "none".

Then, for the chosen provider: run its inspect step and print what the
project already has (Jira: issue types, components; GitHub: labels,
milestones) before proposing anything. Propose a mapping of ticket
types (`bug`, `idea`, `feedback`) onto that existing taxonomy, plus
any optional routing (component, milestone, extra labels) drawn from
the same lists. Never assume the defaults in trackers.md fit; suggest
creating a new label or type only when nothing existing does, marked
as "would be created", and create it only on explicit confirmation.
Verify write permission the provider's way; never create a test issue
to probe. Record the confirmed mapping in the `tracker` block. Write
access missing: record `"provider": "none"` with the reason, in the
user's terms.

**4. Write the config.**
`.living-manual.json` at repo root:

```json
{
  "product": "...",
  "tagline": "...",
  "tagline_pill": "...",
  "manual_path": "docs/USER_MANUAL.html",
  "tickets_dir": "docs/tickets",
  "ticket_skill": "/living-manual:ticket",
  "user_facing_paths": ["src/", "app/src/"],
  "brand": { "ink": "...", "surface": "...", "deep": "...", "accent": "...",
             "warn": "...", "caution": "...", "font_stack": "...",
             "hero_gradient_css": "...", "logo_data_uri": "..." },
  "tracker": { "provider": "github",
               "github": { "repo": "acme/app",
                           "labels": { "bug": "bug", "idea": "enhancement",
                                       "feedback": "feedback" } } }
}
```

`user_facing_paths` are the globs whose changes make the manual stale.
Choose them from the inventory; confirm with the user.

**5. Wire the project.**
- `sh $LM/scripts/install-hook.sh` installs the pre-push guard: pushes
  block when user-facing commits postdate the manual's base marker.
- Append `templates/claude-md-snippet.md` to the repo's CLAUDE.md
  (create it if absent) so every future session, by any dev, updates
  the manual as part of a push. This is the durable half; the hook is
  the enforcement half.
- Create `tickets_dir` with a README explaining the queue and statuses.

**6. Build the manual.**
- `python3 $LM/scripts/scaffold.py $LM/templates/manual-shell.html .living-manual.json <manual_path>`
  (run from the repo root) produces the shell: full interactive
  machinery, brand applied, base commit stamped. You never write
  modal/glossary/preview code.
- Fill the content slots (`<!-- SLOT: ... -->`): TOC, an intro callout
  (with `manual-meta` class) explaining the note and preview
  affordances, one section per surface, a "What's new" seeded from
  release history. Concepts first, surfaces second, reference tables
  last. Sentence-case headings ending in periods unless the brand voice
  says otherwise. App-state illustrations use the `.mock` panel classes
  already in the shell.
- Build the data payload as JSON and apply it:
  `python3 $LM/scripts/sync-index.py <manual_path> payload.json` with
  `glossary` (novel concepts: id, label, pattern, flags, summary),
  `defined` (each concept's defining context: `sec:<id>` or
  `h3:<id-or-heading-slug>`), `previews` (roadmapped work from the
  project's plans, with `.preview-btn` icons placed inline where each
  applies), `tickets` (empty at first), and `asof`.
- Verify: `python3 $LM/scripts/verify.py <manual_path>` must print OK.
  Then load it in a browser once: click a heading, open a preview,
  hover a term. Fix what fails before reporting done.

## Update flow

```
sh $LM/scripts/stale.sh
```

`CURRENT`: say so, stop. Otherwise the output lists the commits and
user-facing files since the manual's base. Then:

1. Read the diffs that matter (`git show` per commit, or the changed
   files). Derive what changed in the user's experience, not in the
   code.
2. Revise the affected sections. New concept → glossary + defined
   entry. Shipped roadmap item → delete its preview and icon; the
   content moves into the section and "What's new".
3. Append one "What's new" release block (newest first, dated,
   user-facing language).
4. Sync data + stamps in one call:
   `python3 $LM/scripts/sync-index.py <manual_path> payload.json` with
   the changed blocks plus `asof` (today) and `base` (current short
   HEAD).
5. `python3 $LM/scripts/verify.py <manual_path>` must print OK.
   Browser-check only when slots or machinery changed.

The pre-push hook calls this flow by name
(`claude -p "/living-manual:manual update"`), so keep the update path
non-interactive: no questions unless the diff is genuinely ambiguous,
and then fail with a clear message rather than guessing.

## Rules

- The manual describes shipped behavior. Planned work lives in
  previews; never blend the two.
- One glossary alert per concept, only before its definition. The
  DEFINED_IN map moves when prose moves.
- Items with roadmap previews take notes against the plan, not current
  behavior. The shell enforces this; keep preview icons placed
  accurately so it can.
- Never edit inside the `/*@...*/` data markers by hand.
- Ticket queue truth: the TICKETS block mirrors `tickets_dir`. The
  ticket skill owns routine sync; fix drift when you see it.
