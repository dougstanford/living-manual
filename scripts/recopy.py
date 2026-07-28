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

A renamed heading brings its contents entry with it. A table of
contents entry is a pointer to a heading, so the two must not be
allowed to drift: the entry carries "toc" naming the anchor, the label
the file holds, and the label it should read. Section order is not
touched, which is why this is a copy edit and never a reorder.

Only the contents panel is searched for that entry, so a link to the
same anchor written in prose is left alone.

Payload:
  {"edits": [{"key": "...", "original": "...", "new": "..."},
             {"key": "...", "original": "<h3 ...>New</h3>", "new": "...",
              "toc": {"anchor": "export", "original": "Handing it out",
                      "edited": "Distribution"}},
             {"key": "...", "original": "<p>...</p>", "new": "",
              "remove": true}, ...]}

`key` is the browser's name for the block. It is carried for the
message this prints, never used to find anything.
"""
import json, re, sys

NAV_RE = re.compile(r'<nav\b[^>]*class="[^"]*\btoc\b[^"]*"[^>]*>.*?</nav>', re.S)


def toc_entry_re(anchor):
    """The one contents link pointing at this anchor, split for rewrite."""
    return re.compile(r'(<a\b[^>]*href="#' + re.escape(anchor) + r'"[^>]*>)'
                      r'(.*?)(</a>)', re.S)


def find_nav(src, name):
    m = NAV_RE.search(src)
    if not m:
        die("%s: renames a heading, but the manual has no contents panel "
            "to rename with it" % name)
    return m


def check_toc(src, toc, name):
    """Locate the entry and prove it still says what the browser saw."""
    for k in ("anchor", "original", "edited"):
        if not isinstance(toc.get(k), str):
            die("%s: toc is missing %s" % (name, k))
    nav = find_nav(src, name)
    hits = toc_entry_re(toc["anchor"]).findall(nav.group(0))
    if len(hits) == 0:
        die("%s: no contents entry points at #%s, so the renamed heading "
            "has nothing to rename." % (name, toc["anchor"]))
    if len(hits) > 1:
        die("%s: %d contents entries point at #%s; the manual's contents "
            "are malformed." % (name, len(hits), toc["anchor"]))
    held = hits[0][1].strip()
    if held != toc["original"].strip():
        die("%s: the contents entry for #%s now reads %r, not %r. The "
            "manual changed after this edit was made; redo it against the "
            "current wording." % (name, toc["anchor"], held, toc["original"]))


def apply_toc(src, toc):
    nav = find_nav(src, "toc")
    def sub(m):
        return m.group(1) + toc["edited"] + m.group(3)
    renamed = toc_entry_re(toc["anchor"]).sub(sub, nav.group(0), count=1)
    return src[:nav.start()] + renamed + src[nav.end():]

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
        toc = e.get("toc")
        if toc is not None:
            if not isinstance(toc, dict):
                die("%s: toc is not an object" % name)
            if e.get("remove"):
                die("%s: marked for removal but also renames a contents "
                    "entry" % name)
            check_toc(src, toc, name)
            if toc["original"].strip() == toc["edited"].strip():
                toc = None
        planned.append((name, e["original"], e["new"],
                        bool(e.get("remove")), toc))

    if not planned:
        print("nothing to apply")
        return
    removed = 0
    renamed = 0
    for _, original, new, remove, toc in planned:
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
        if toc:
            src = apply_toc(src, toc)
            renamed += 1
    open(manual, "w").write(src)
    notes = []
    if removed:
        notes.append("%d of them removals" % removed)
    if renamed:
        notes.append("%d contents entr%s renamed with their heading"
                     % (renamed, "y" if renamed == 1 else "ies"))
    print("recopy: applied %d edit(s)%s"
          % (len(planned), (", " + ", ".join(notes)) if notes else ""))
    for name, _, _, remove, toc in planned:
        print("  " + name + (" (removed)" if remove else "")
              + (" (contents entry renamed)" if toc else ""))

if __name__ == "__main__":
    main()
