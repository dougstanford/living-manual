# Ticket queue

Tickets written by `/living-manual:ticket` from notes filed in the
manual (docs/USER_MANUAL.html) or from free-form reports.

- One file per ticket: `TICKET-NNNN-<slug>.md`, numbered by
  `next-ticket.sh`, frontmatter carries id, type, target, and status.
- Statuses: `ready` (complete, actionable), `needs-answers` (open
  questions block completeness), later `shipped` or `declined`. Resolved
  tickets keep their file as the record; the manual's index drops them.
- The manual's queue index mirrors this directory. After any manual edit
  to a ticket, rebuild it:
  `python3 <plugin>/scripts/tickets-index.py docs/tickets docs/USER_MANUAL.html`.
