#!/usr/bin/env python3
"""recopy.py MANUAL PAYLOAD.json — apply revised prose to the manual.

The manual's copy is editable in the browser, where edits live in the
reader's own storage until they decide to keep them. Commit copy hands
them here as a payload: one entry per revised block, each carrying the
text the file held and the text that should replace it.

Replacement is by exact match, so the script can prove it is changing
the passage the reader was looking at. An original that no longer
appears means the manual moved on since the edit; one that appears
more than once means the passage is not distinctive enough to place.
Both refuse, naming the entry, rather than guessing which paragraph
was meant.

Nothing is written until every entry checks out, so a payload either
lands whole or not at all.

Payload:
  {"edits": [{"key": "...", "original": "...", "new": "..."}, ...]}

`key` is the browser's name for the block. It is carried for the
message this prints, never used to find anything.
"""
import json, sys

def die(msg):
    sys.exit("recopy: " + msg)

def main():
    if len(sys.argv) < 3:
        die("usage: recopy.py MANUAL PAYLOAD.json")
    manual, payload_path = sys.argv[1], sys.argv[2]
    src = open(manual).read()
    try:
        payload = json.load(open(payload_path))
    except Exception as e:
        die("could not read %s (%s)" % (payload_path, e))
    edits = payload.get("edits")
    if not isinstance(edits, list) or not edits:
        die("payload carries no edits")

    planned = []
    for i, e in enumerate(edits):
        if not isinstance(e, dict):
            die("edit %d is not an object" % i)
        for k in ("original", "new"):
            if not isinstance(e.get(k), str):
                die("edit %s is missing %s" % (e.get("key", i), k))
        name = e.get("key", "edit %d" % i)
        if e["original"] == e["new"]:
            print("unchanged, skipping: %s" % name)
            continue
        found = src.count(e["original"])
        if found == 0:
            die("%s: the text it replaces is no longer in %s. The manual "
                "changed after this edit was made; redo it against the "
                "current wording." % (name, manual))
        if found > 1:
            die("%s: the text it replaces appears %d times, so there is no "
                "way to tell which one was edited. Revise that passage by "
                "hand instead." % (name, found))
        planned.append((name, e["original"], e["new"]))

    if not planned:
        print("nothing to apply")
        return
    for _, original, new in planned:
        src = src.replace(original, new, 1)
    open(manual, "w").write(src)
    print("recopy: applied %d edit(s)" % len(planned))
    for name, _, _ in planned:
        print("  " + name)

if __name__ == "__main__":
    main()
