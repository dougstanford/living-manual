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

A block emptied in the browser is deleted outright rather than left
standing blank: its entry carries "remove", its original is the whole
element, and the blank line it sat on goes with it so the prose above
and below closes up.

Payload:
  {"edits": [{"key": "...", "original": "...", "new": "..."},
             {"key": "...", "original": "<p>...</p>", "new": "",
              "remove": true}, ...]}

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
        if e.get("remove") and e["new"].strip():
            die("%s: marked for removal but carries replacement text" % name)
        found = src.count(e["original"])
        if found == 0:
            die("%s: the text it replaces is no longer in %s. The manual "
                "changed after this edit was made; redo it against the "
                "current wording." % (name, manual))
        if found > 1:
            die("%s: the text it replaces appears %d times, so there is no "
                "way to tell which one was edited. Revise that passage by "
                "hand instead." % (name, found))
        planned.append((name, e["original"], e["new"], bool(e.get("remove"))))

    if not planned:
        print("nothing to apply")
        return
    removed = 0
    for _, original, new, remove in planned:
        if remove:
            # Take the line the block sat on with it, so deleting a
            # paragraph closes the gap instead of leaving one behind.
            i = src.index(original)
            j = i + len(original)
            k = i
            while k > 0 and src[k - 1] in " \t":
                k -= 1
            if k > 0 and src[k - 1] == "\n":
                k -= 1
            src = src[:k] + src[j:]
            removed += 1
        else:
            src = src.replace(original, new, 1)
    open(manual, "w").write(src)
    print("recopy: applied %d edit(s)%s"
          % (len(planned), ", %d of them removals" % removed if removed else ""))
    for name, _, _, remove in planned:
        print("  " + name + (" (removed)" if remove else ""))

if __name__ == "__main__":
    main()
