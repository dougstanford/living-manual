#!/bin/sh
# next-ticket.sh [tickets-dir] — print the next TICKET-NNNN id.
DIR="${1:-docs/tickets}"
MAX=$(ls "$DIR" 2>/dev/null | grep -Eo 'TICKET-[0-9]{4}' | sort | tail -1 | grep -Eo '[0-9]{4}')
printf 'TICKET-%04d\n' $(( ${MAX:-0} + 1 ))
