# Manual maintenance (per release)

The update flow in skills/manual/SKILL.md is the procedure. This is the
checklist form, for review before reporting done.

1. `stale.sh` output consumed: every listed commit's user-facing effect
   is either reflected in a section or explicitly irrelevant.
2. Sections revised where behavior changed. No planned work described
   as shipped.
3. One "What's new" release block appended, newest first, dated,
   user-facing language, no internal jargon.
4. Previews synced: shipped items removed (content folded into sections
   and "What's new"), newly planned items added with icons placed where
   they apply.
5. Glossary synced: new concepts entered with defining context; renamed
   terms renamed in both GLOSSARY and DEFINED_IN.
6. Tickets index rebuilt (`python3 $LM/scripts/tickets-index.py
   <tickets_dir> <manual_path>`); tickets shipped by this release set
   to `status: shipped` and noted in "What's new" when user visible.
7. `asof` and `base` stamped via sync-index.py.
8. `python3 $LM/scripts/verify.py <manual_path>` prints OK. Browser
   check when machinery or slots changed: headings clickable, one
   glossary alert max per concept and none after its definition,
   previews open, note payload copies.
9. Prose passes reference/writing-style.md. Em-dash count in new prose:
   zero.
